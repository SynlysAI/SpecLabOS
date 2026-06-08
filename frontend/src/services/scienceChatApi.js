/**
 * 科学数据助手对话 API — SSE 流式请求。
 *
 * Args:
 *     product: 产品标识，"sciverse" 或 "dianshi"。
 *     message: 用户输入的自然语言消息。
 *     onChunk: 每段流式文本的回调。
 *     onDone: 流式完成后的回调，接收完整文本。
 *
 * Returns:
 *     用于中断的 AbortController。
 */
export function streamScienceChat(product, message, onChunk, onDone) {
  const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ||
    (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tools/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product, message }),
        signal: controller.signal
      });

      if (!response.ok) {
        const errText = await response.text().catch(() => "");
        throw new Error(`${response.status} ${response.statusText}${errText ? ": " + errText : ""}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let fullText = "";

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
              fullText += data.text;
              onChunk(data.text);
            } else if (data.type === "error") {
              onChunk("[错误] " + data.message);
            } else if (data.type === "done") {
              onDone(fullText);
            }
          } catch {
            // 忽略不完整的 JSON 解析错误
          }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        onChunk("[错误] 请求失败: " + err.message);
        onDone("");
      }
    }
  })();

  return controller;
}
