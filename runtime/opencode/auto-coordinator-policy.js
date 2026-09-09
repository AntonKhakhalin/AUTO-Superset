// SUPERSET_AUTO_COORDINATOR_HIDDEN_POLICY_V9824
// Moves AUTO coordinator bootstrap/policy into hidden OpenCode system context.
// The user's visible message remains the user's actual request.

import fs from "node:fs/promises";

export const SupersetAutoCoordinatorHiddenPolicy = async () => {
  if (globalThis.__supersetAutoCoordinatorHiddenPolicyV9824) return {};
  globalThis.__supersetAutoCoordinatorHiddenPolicyV9824 = true;

  if (process?.env?.SUPERSET_AUTO !== "1") return {};
  if (process?.env?.SUPERSET_AUTO_ROLE !== "coordinator") return {};
  if (process?.env?.SUPERSET_MUSE_LEAF === "1") return {};

  const policyFile = process?.env?.SUPERSET_AUTO_HIDDEN_POLICY_FILE;
  if (!policyFile) {
    // Fail closed at model-context assembly: a coordinator launched through the
    // v9.8.24 wrapper must always have its hidden policy transport available.
    return {
      "experimental.chat.system.transform": async (_input, output) => {
        output.system.push(
          "SUPERSET AUTO POLICY TRANSPORT FAILURE: do not perform repository work or orchestration. " +
          "Report that the hidden coordinator policy file is unavailable."
        );
      },
    };
  }

  let cached = null;
  let cachedMtime = -1;

  const readPolicy = async () => {
    try {
      const st = await fs.stat(policyFile);
      if (cached !== null && st.mtimeMs === cachedMtime) return cached;
      const text = await fs.readFile(policyFile, "utf8");
      if (!text.trim()) throw new Error("empty policy file");
      cached = text;
      cachedMtime = st.mtimeMs;
      return text;
    } catch (err) {
      return (
        "SUPERSET AUTO POLICY TRANSPORT FAILURE: hidden policy could not be read. " +
        "Do not perform repository work or orchestration. Report the control-plane policy failure."
      );
    }
  };

  return {
    "experimental.chat.system.transform": async (_input, output) => {
      const policy = await readPolicy();
      const marker = "SUPERSET AUTO COORDINATOR HIDDEN SYSTEM POLICY";
      if (!output.system.some((x) => typeof x === "string" && x.includes(marker))) {
        output.system.push(policy);
      }
    },
  };
};
