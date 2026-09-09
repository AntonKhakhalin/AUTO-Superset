// SUPERSET_AUTO_COORDINATOR_CONVERSATION_MIRROR_V9823
// Mirrors only root-session user/assistant text into AUTO presentation state.
// Reasoning/tool/file/subtask parts are intentionally excluded.

import fs from "node:fs/promises";
import path from "node:path";

export const SupersetAutoCoordinatorConversationMirror = async ({ client }) => {
  if (globalThis.__supersetAutoCoordinatorConversationMirrorV9823) return {};
  globalThis.__supersetAutoCoordinatorConversationMirrorV9823 = true;

  if (process?.env?.SUPERSET_AUTO !== "1") return {};
  if (!process?.env?.SUPERSET_TERMINAL_ID || !process?.env?.SUPERSET_WORKSPACE_ID) return {};
  if (process?.env?.SUPERSET_MUSE_LEAF === "1") return {};

  const workspaceId = process.env.SUPERSET_WORKSPACE_ID;
  const terminalId = process.env.SUPERSET_TERMINAL_ID;
  const home = process.env.SUPERSET_HOME_DIR || path.join(process.env.HOME || "", ".superset");
  const safe = (v) => String(v || "unknown").replace(/[^A-Za-z0-9._-]+/g, "_").slice(0, 180) || "unknown";
  const dir = path.join(home, "auto", "workspace-supervisor", safe(workspaceId));
  const file = path.join(dir, "conversation.json");
  const debug = process?.env?.SUPERSET_AUTO_PRESENTATION_DEBUG === "1";
  const MAX_ENTRIES = 400;
  const MAX_TEXT = 120000;

  const roleByMessage = new Map();
  const childSessionCache = new Map();
  const pendingTextParts = new Map();
  let writing = Promise.resolve();
  let snapshot = { version: "9.8.23", workspaceId, terminalId, updatedAt: null, entries: [] };

  const log = (...args) => {
    if (debug) console.error("[auto-conversation-mirror]", ...args);
  };

  try {
    const parsed = JSON.parse(await fs.readFile(file, "utf8"));
    if (parsed && Array.isArray(parsed.entries)) snapshot = parsed;
  } catch {}

  const isChildSession = async (sessionID) => {
    if (!sessionID) return true;
    if (childSessionCache.has(sessionID)) return childSessionCache.get(sessionID);
    if (!client?.session?.list) return true;
    try {
      const sessions = await client.session.list();
      const session = sessions.data?.find((s) => s.id === sessionID);
      const isChild = !!session?.parentID;
      childSessionCache.set(sessionID, isChild);
      return isChild;
    } catch {
      // Fail closed: never mirror an unverified child/subagent conversation.
      return true;
    }
  };

  const persist = async () => {
    await fs.mkdir(dir, { recursive: true });
    const tmp = `${file}.tmp.${process.pid}.${Date.now()}`;
    await fs.writeFile(tmp, JSON.stringify(snapshot), "utf8");
    await fs.rename(tmp, file);
  };

  const enqueuePersist = () => {
    writing = writing.then(persist).catch((err) => log("persist failed", err?.message || err));
  };

  const upsertText = (part, role) => {
    const text = typeof part?.text === "string" ? part.text : "";
    if (!text || part?.synthetic === true || part?.ignored === true) return;
    if (role !== "user" && role !== "assistant") return;
    const key = `${part.sessionID}:${part.messageID}:${part.id}`;
    const now = new Date().toISOString();
    const existingIndex = snapshot.entries.findIndex((x) => x.key === key);
    const entry = {
      key,
      sessionId: part.sessionID,
      messageId: part.messageID,
      partId: part.id,
      role,
      text: text.slice(0, MAX_TEXT),
      createdAt: existingIndex >= 0 ? snapshot.entries[existingIndex].createdAt : now,
      updatedAt: now,
      complete: Boolean(part?.time?.end),
    };
    if (existingIndex >= 0) snapshot.entries[existingIndex] = entry;
    else snapshot.entries.push(entry);
    if (snapshot.entries.length > MAX_ENTRIES) snapshot.entries = snapshot.entries.slice(-MAX_ENTRIES);
    snapshot.version = "9.8.23";
    snapshot.workspaceId = workspaceId;
    snapshot.terminalId = terminalId;
    snapshot.updatedAt = now;
    enqueuePersist();
  };

  const flushPending = (messageID) => {
    const role = roleByMessage.get(messageID);
    if (!role) return;
    const pending = pendingTextParts.get(messageID);
    if (!pending) return;
    pendingTextParts.delete(messageID);
    for (const part of pending.values()) upsertText(part, role);
  };

  return {
    event: async ({ event }) => {
      const props = event?.properties || {};

      if (event.type === "session.created") {
        const info = props.info;
        if (info?.id) childSessionCache.set(info.id, Boolean(info.parentID));
        return;
      }
      if (event.type === "session.deleted") {
        const sessionID = props.sessionID ?? props.info?.id;
        if (sessionID) childSessionCache.delete(sessionID);
        return;
      }

      if (event.type === "message.updated") {
        const info = props.info;
        if (!info?.id || !info?.sessionID) return;
        if (await isChildSession(info.sessionID)) return;
        if (info.role === "user" || info.role === "assistant") {
          roleByMessage.set(info.id, info.role);
          flushPending(info.id);
        }
        return;
      }

      if (event.type === "message.part.updated") {
        const part = props.part;
        if (!part || part.type !== "text" || !part.sessionID || !part.messageID) return;
        if (await isChildSession(part.sessionID)) return;
        const role = roleByMessage.get(part.messageID);
        if (role) {
          upsertText(part, role);
        } else {
          let byPart = pendingTextParts.get(part.messageID);
          if (!byPart) {
            byPart = new Map();
            pendingTextParts.set(part.messageID, byPart);
          }
          byPart.set(part.id, part);
        }
      }
    },
  };
};
