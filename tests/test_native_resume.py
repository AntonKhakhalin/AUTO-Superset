"""Recovery contracts against a minimal Superset 1.28 host.db fixture."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from test_runtime import load


class NativeResumeTests(unittest.TestCase):
    def setUp(self):
        self.s = load('auto-workspace-supervisor')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / 'host.db'
        with sqlite3.connect(self.db) as con:
            con.executescript('''
                CREATE TABLE terminal_sessions (id TEXT PRIMARY KEY, status TEXT,
                    dispose_requested_at INTEGER, ended_at INTEGER);
                CREATE TABLE terminal_agent_bindings (terminal_id TEXT PRIMARY KEY,
                    workspace_id TEXT, agent_id TEXT, agent_session_id TEXT,
                    definition_id TEXT, ended_at INTEGER, end_reason TEXT,
                    resumed_into_terminal_id TEXT);
            ''')
        self.addCleanup(patch.stopall)
        patch.object(self.s, 'ROOT', self.root / 'registry').start()
        patch.object(self.s, 'LEGACY_REGISTRY_ROOT', self.root / 'legacy').start()
        patch.object(self.s, 'host_db_candidates', return_value=[self.db]).start()
        patch.object(self.s, 'now_epoch', return_value=1000).start()
        self.rpc = patch.object(self.s, 'run_superset', return_value=(0, '{}', '')).start()
        self.rpc.side_effect = self.respond
        self.create_result = None
        patch.object(self.s, 'explicit_resume_gate', return_value=(True, '')).start()
        self.s.ensure_dirs('workspace')
        self.reg = dict(workspaceId='workspace', workerId='original', currentTerminalId='original',
                        terminalId='original', terminalAliases=['original'], agentId='custom-opencode',
                        agentSessionId=None, state='NATIVE_RESUMING', nativeResumeState='GRACE',
                        nativeResumeDeadlineEpoch=999, nativeResumeAttemptCount=0,
                        handoff=str(self.root / 'handoff.md'), routeMode='native',
                        launchModel='fixture-model', launchEffort='high')
        self.binding('original', status='exited', reason='terminal-exited')
        self.save()
        self.reg = self.s.learn_agent_session_from_persisted_binding(self.reg)

    def respond(self, args, **kwargs):
        result = self.create_result if args[:2] == ['agents', 'create'] and self.create_result else self.rpc.return_value
        if args[:2] == ['terminals', 'close'] and result[0] == 0:
            terminal = args[args.index('--terminal') + 1]
            row = self.s.persisted_binding(terminal, 'workspace')
            # Mirror upstream: a consumed native claim is sticky.
            if row and row['end_reason'] != 'resumed':
                self.binding(terminal, status='disposed', reason='disposed', disposed=1000)
        return result

    def binding(self, terminal, *, status='active', reason=None, successor=None,
                session='provider-session', agent='opencode', definition='custom-opencode',
                workspace='workspace', disposed=None):
        ended = None if reason is None else 900
        with sqlite3.connect(self.db) as con:
            con.execute('INSERT OR REPLACE INTO terminal_sessions VALUES (?,?,?,?)',
                        (terminal, status, disposed, None if status == 'active' else 900))
            con.execute('INSERT OR REPLACE INTO terminal_agent_bindings VALUES (?,?,?,?,?,?,?,?)',
                        (terminal, workspace, agent, session, definition, ended, reason, successor))

    def save(self):
        self.s.atomic_json(self.s.registration_path('workspace', 'original'), self.reg)

    def latest(self):
        return self.s.read_json(self.s.registration_path('workspace', 'original'))

    def native(self):
        self.binding('original', status='disposed', reason='resumed', successor='successor', disposed=901)
        self.binding('successor')

    def test_native_lineage_adopts_root_session_preserving_contract(self):
        self.native()
        self.assertTrue(self.s.detect_native_auto_rebind(self.reg))
        latest = self.latest()
        self.assertEqual(latest['currentTerminalId'], 'successor')
        self.assertEqual(latest['workerId'], 'original')
        self.assertEqual(latest['handoff'], self.reg['handoff'])
        self.assertEqual(latest['agentSessionId'], 'provider-session')
        self.assertEqual(latest['nativeResumeSource'], 'superset-1.28-native')
        self.assertEqual(latest['state'], 'RUNNING')
        self.assertEqual(self.rpc.call_args.args[0][:2], ['terminals', 'send'])
        self.assertFalse(any(c.args[0][:2] == ['agents', 'create'] for c in self.rpc.call_args_list))

    def test_session_equality_alone_does_not_adopt_or_launch(self):
        self.binding('unrelated')
        self.assertFalse(self.s.detect_native_auto_rebind(self.reg))
        self.assertFalse(self.s.attempt_explicit_native_resume(self.reg)[0])
        self.assertEqual(self.latest()['currentTerminalId'], 'original')
        self.rpc.assert_not_called()

    def test_successor_must_match_full_ownership_and_be_alive(self):
        cases = [dict(session='different'), dict(agent='claude'), dict(definition='other'),
                 dict(workspace='other'), dict(status='exited', reason='terminal-exited'),
                 dict(disposed=950), dict(reason='detached')]
        for changes in cases:
            with self.subTest(changes=changes):
                self.native()
                self.binding('successor', **changes)
                self.assertFalse(self.s.detect_native_auto_rebind(self.reg))
                self.rpc.assert_not_called()

    def test_original_alive_blocks_adoption_even_with_lineage(self):
        self.native()
        self.binding('original', reason='resumed', successor='successor')
        self.assertFalse(self.s.detect_native_auto_rebind(self.reg))
        self.rpc.assert_not_called()

    def test_multiple_live_bindings_including_pending_disposal_block(self):
        self.native()
        self.binding('competitor', disposed=999, reason='disposed')
        self.assertFalse(self.s.detect_native_auto_rebind(self.reg))
        self.rpc.assert_not_called()

    def test_resume_chain_follows_successors_and_rejects_cycle(self):
        self.native()
        self.binding('successor', status='disposed', reason='resumed', successor='third')
        self.binding('third')
        self.assertEqual(self.s.verified_successor(self.reg), ('third', 'superset-1.28-native'))
        self.binding('third', status='disposed', reason='resumed', successor='original')
        self.assertIsNone(self.s.verified_successor(self.reg))

    def test_native_claim_in_flight_prevents_explicit_fallback(self):
        self.binding('original', status='exited', reason='resumed')
        self.assertFalse(self.s.attempt_explicit_native_resume(self.reg)[0])
        self.rpc.assert_not_called()

    def test_grace_and_deliberate_close_never_launch(self):
        self.reg['nativeResumeDeadlineEpoch'] = 1001
        self.save()
        self.assertFalse(self.s.attempt_explicit_native_resume(self.reg)[0])
        self.reg['nativeResumeDeadlineEpoch'] = 999
        self.save()
        for reason in ('disposed', 'detached'):
            self.binding('original', status='exited', reason=reason)
            self.assertFalse(self.s.attempt_explicit_native_resume(self.reg)[0])
        self.rpc.assert_not_called()

    def test_single_fallback_preserves_overrides_and_waits_for_binding(self):
        self.create_result = (0, '{"sessionId":"explicit-terminal"}', '')
        self.assertFalse(self.s.attempt_explicit_native_resume(self.reg)[0])
        args = self.rpc.call_args.args[0]
        for flag, expected in [('--resume-session', 'provider-session'), ('--model', 'fixture-model'),
                               ('--effort', 'high')]:
            self.assertEqual(args[args.index(flag)+1], expected)
        self.assertNotIn('--prompt', args)
        latest = self.latest()
        self.assertEqual(latest['state'], 'NATIVE_RESUMING')
        self.assertEqual(latest['currentTerminalId'], 'original')
        self.assertEqual(latest['nativeResumeDeadlineEpoch'], 1030)
        self.assertFalse(self.s.attempt_explicit_native_resume(latest)[0])
        self.assertEqual(self.rpc.call_count, 2)
        self.assertEqual(self.s.persisted_binding('original', 'workspace')['end_reason'], 'disposed')
        self.binding('explicit-terminal')
        self.assertTrue(self.s.detect_native_auto_rebind(latest))
        self.assertEqual(self.latest()['nativeResumeSource'], 'explicit-verified')

    def test_quota_gate_and_post_gate_native_claim_recheck(self):
        with patch.object(self.s, 'explicit_resume_gate', return_value=(False, 'quota closed')):
            self.assertFalse(self.s.attempt_explicit_native_resume(self.reg)[0])
        self.assertEqual(self.latest()['state'], 'SUPERVISION_LOST')
        self.save()
        def claim(_):
            self.binding('original', status='exited', reason='resumed')
            return True, ''
        with patch.object(self.s, 'explicit_resume_gate', side_effect=claim):
            self.assertFalse(self.s.attempt_explicit_native_resume(self.reg)[0])
        self.rpc.assert_not_called()

    def test_source_retirement_must_be_confirmed_before_launch(self):
        self.rpc.return_value = (127, '', 'close timeout')
        self.assertFalse(self.s.attempt_explicit_native_resume(self.reg)[0])
        self.assertEqual(self.rpc.call_count, 1)
        self.assertEqual(self.latest()['nativeResumeAttemptCount'], 0)
        self.assertEqual(self.latest()['currentTerminalId'], 'original')

    def test_native_claim_winning_retirement_race_prevents_explicit_launch(self):
        def native_wins(args, **kwargs):
            if args[:2] == ['terminals', 'close']:
                self.native()
            return 0, '{}', ''
        self.rpc.side_effect = native_wins
        self.assertTrue(self.s.attempt_explicit_native_resume(self.reg)[0])
        self.assertEqual(self.latest()['currentTerminalId'], 'successor')
        self.assertEqual(self.latest()['nativeResumeAttemptCount'], 0)
        self.assertFalse(any(c.args[0][:2] == ['agents', 'create'] for c in self.rpc.call_args_list))

    def test_unknown_rpc_outcome_does_not_adopt_a_late_native_winner(self):
        self.create_result = (127, '', 'Request timeout: create')
        self.s.attempt_explicit_native_resume(self.reg)
        self.native()
        self.assertFalse(self.s.detect_native_auto_rebind(self.latest()))
        self.assertEqual(self.rpc.call_count, 2)
        self.s.finish_recovery(self.latest(), 'unknown launch outcome')
        self.assertEqual(self.latest()['state'], 'SUPERVISION_LOST')

    def test_race_closes_only_known_explicit_terminal_and_requires_confirmed_exit(self):
        self.reg.update(nativeResumeExplicitTerminalId='explicit', nativeResumeAttemptCount=1)
        self.save()
        self.native()
        self.binding('explicit')
        self.rpc.return_value = (1, '', 'close failed')
        self.assertFalse(self.s.detect_native_auto_rebind(self.reg))
        args = self.rpc.call_args.args[0]
        self.assertEqual(args[:2], ['terminals', 'close'])
        self.assertEqual(args[args.index('--terminal')+1], 'explicit')
        self.assertFalse(self.s.detect_native_auto_rebind(self.latest()))
        self.assertEqual(self.rpc.call_count, 1)  # no repeated close or prompt
        self.binding('explicit', status='disposed', reason='disposed', disposed=1000)
        self.assertTrue(self.s.detect_native_auto_rebind(self.latest()))
        self.assertEqual(self.latest()['currentTerminalId'], 'successor')

    def test_lifecycle_cannot_rebind_or_cancel_grace(self):
        for terminal in ('unrelated', 'original'):
            self.s.process_lifecycle_event('workspace', dict(terminalId=terminal,
                agentSessionId='provider-session', eventType='Start'))
        self.assertEqual(self.latest()['currentTerminalId'], 'original')
        self.assertEqual(self.latest()['state'], 'NATIVE_RESUMING')
        self.rpc.assert_not_called()

    def test_lifecycle_tap_only_appends_event_without_mutating_registry(self):
        tap = load('auto-lifecycle-tap')
        path = self.s.registration_path('workspace', 'original')
        before = path.read_bytes()
        with patch.object(tap, 'ROOT', self.s.ROOT), patch.object(tap.sys, 'argv', [
                'tap', '--workspace', 'workspace', '--terminal', 'replacement',
                '--session', 'provider-session', '--agent', 'opencode', '--event', 'Start']):
            self.assertEqual(tap.main(), 0)
        self.assertEqual(path.read_bytes(), before)
        event = json.loads((self.s.ws_dir('workspace') / 'lifecycle.jsonl').read_text())
        self.assertEqual(event['terminalId'], 'replacement')
        self.assertEqual(event['agentSessionId'], 'provider-session')

    def test_hook_upgrade_preserves_upstream_filter_and_replaces_old_tap_once(self):
        hook = load('auto-hook-install')
        home = self.root / 'superset'
        target = home / 'hooks/notify.sh'
        target.parent.mkdir(parents=True)
        upstream = '# upstream identity filter retained\n' + hook.NEEDLE
        target.write_text(upstream + '# SUPERSET_AUTO_LIFECYCLE_TAP_V9823_HOOK\n'
                          'old managed tap\n# END SUPERSET_AUTO_LIFECYCLE_TAP_V9823_HOOK\n')
        tap = home / 'bin/auto-lifecycle-tap'
        tap.parent.mkdir(parents=True)
        tap.write_text('# fixture')
        tap.chmod(0o755)
        mirror = home / 'auto/runtime/auto-coordinator-mirror.js'
        mirror.parent.mkdir(parents=True)
        mirror.write_text('// ' + hook.MIRROR_MARKER)
        with patch.dict(hook.os.environ, {'SUPERSET_HOME_DIR': str(home)}), patch.object(hook.sys, 'argv', ['hook', '--quiet']):
            self.assertEqual(hook.main(), 0)
            first = target.read_text()
            self.assertEqual(hook.main(), 0)
        self.assertEqual(target.read_text(), first)
        self.assertTrue(first.startswith(upstream))
        self.assertNotIn('V9823_HOOK', first)
        self.assertIn('--agent "${AGENT_ID:-${SUPERSET_AGENT_ID:-}}"', first)
        self.assertEqual(first.count('# END ' + hook.MARKER), 1)

    def test_dead_terminal_snapshot_cannot_cancel_grace(self):
        self.reg['nativeResumeDeadlineEpoch'] = 1001
        self.save()
        with patch.object(self.s, 'terminal_read', return_value=(True, 'old screen', '')):
            self.s.inspect_worker(self.reg)
        self.assertEqual(self.latest()['state'], 'NATIVE_RESUMING')
        self.rpc.assert_not_called()

    def test_missing_migration_and_ambiguous_host_fail_closed(self):
        with patch.object(self.s, 'host_db_candidates', return_value=[self.db, self.db]):
            self.assertFalse(self.s.attempt_explicit_native_resume(self.reg)[0])
        with sqlite3.connect(self.db) as con:
            con.execute('ALTER TABLE terminal_agent_bindings DROP COLUMN resumed_into_terminal_id')
        self.s.inspect_worker(self.reg)
        self.assertEqual(self.latest()['state'], 'SUPERVISION_LOST')
        self.rpc.assert_not_called()

    def test_handoff_wins_and_no_recovery_launch_occurs(self):
        Path(self.reg['handoff']).write_text('SUPERSET_WORKER_DONE\nFixture complete.')
        self.s.inspect_worker(self.reg)
        self.assertEqual(self.latest()['state'], 'DONE')
        self.assertFalse(any(c.args[0][:2] == ['agents', 'create'] for c in self.rpc.call_args_list))

    def test_timed_out_continuation_is_not_repeated(self):
        self.native()
        self.rpc.return_value = (127, '', 'timeout')
        self.s.detect_native_auto_rebind(self.reg)
        self.s.send_resume_continuation(self.latest())
        self.assertEqual(self.rpc.call_count, 1)
        self.assertFalse(self.latest()['nativeResumeContinuationPending'])

    def test_structured_spawn_causes_are_sanitized_and_classified(self):
        for kind in self.s.SPAWN_FAILURES:
            with self.subTest(kind=kind):
                raw = {'error': {'cause': {'kind': kind, 'exitCode': 1, 'signal': 9,
                       'outputHead': 'PRIVATE CONTENT', 'args': ['PRIVATE CONTENT'],
                       'shell': 'PRIVATE CONTENT'}}}
                diagnostic = self.s.failure_diagnostic(json.dumps(raw))
                self.assertEqual(diagnostic, dict(kind=kind, source='control-rpc-cause', exitCode=1, signal=9))
                self.binding('original', status='exited', reason='terminal-exited')
                self.reg['terminalFailure'] = diagnostic
                self.save()
                self.s.finish_recovery(self.reg, 'automatic grace exhausted; fallback disabled')
                self.assertEqual(self.latest()['failureClass'], 'WORKER_' + kind)

    def test_daemon_diagnostics_are_control_loss_not_provider_death(self):
        errors = [
            ('Daemon exited with code 1 during startup', 'DAEMON_STARTUP_FAILED'),
            ('Request timeout: snapshot after 30000ms (daemon last spoke 4ms ago; '
             '2 other request(s) in flight; 3 earlier timeout(s) answered late, most recent 8ms after giving up)', 'DAEMON_TIMEOUT'),
            ('Failed to connect stream socket', 'CONTROL_DISCONNECTED'),
            ('No pong from client', 'CONTROL_DISCONNECTED'),
            ('TERMINAL_ATTACH_CANCELED', 'ATTACH_CANCELED_OR_DISPOSED'),
        ]
        for message, kind in errors:
            with self.subTest(kind=kind):
                self.reg['terminalFailure'] = self.s.failure_diagnostic(message)
                self.assertEqual(self.reg['terminalFailure']['kind'], kind)
                self.save()
                self.s.finish_recovery(self.reg, 'control unavailable')
                self.assertEqual(self.latest()['state'], 'SUPERVISION_LOST')
        timeout = self.s.failure_diagnostic(errors[1][0])
        self.assertTrue(timeout['lateAnswersObserved'])
        self.assertEqual(timeout['lastSpokeMsAgo'], 4)
        self.assertEqual(timeout['otherRequestsInFlight'], 2)


if __name__ == '__main__':
    unittest.main()
