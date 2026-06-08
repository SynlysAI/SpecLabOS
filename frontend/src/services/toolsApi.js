const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

/**
 * 流式解析实验方案，生成设备控制指令。
 *
 * Args:
 *     experimentPlan: 实验方案文本。
 *     onChunk: 每段流式文本的回调。
 *     onDone: 流式完成后的回调，接收指令列表和完整文本。
 *
 * Returns:
 *     用于中断的 AbortController。
 */
export function streamParseInstructions(experimentPlan, onChunk, onDone) {
  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/tools/parse-instructions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ experiment_plan: experimentPlan }),
          signal: controller.signal
        }
      );

      if (!response.ok) {
        const errText = await response.text().catch(() => "");
        throw new Error(`${response.status} ${response.statusText}${errText ? ": " + errText : ""}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop();

        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(part.slice(6));
            if (data.type === "chunk") {
              onChunk(data.text);
            } else if (data.type === "error") {
              onChunk("\n[错误] " + data.message);
              onDone([], "");
              return;
            } else if (data.type === "done") {
              onDone(data.instructions || [], data.full_text || "");
            }
          } catch {
            // 忽略不完整的 JSON 解析错误
          }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        onChunk("\n[错误] 请求失败: " + err.message);
        onDone([], "");
      }
    }
  })();

  return controller;
}
