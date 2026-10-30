const BASE = import.meta.env.VITE_API_URL || "http://localhost:8001";
export async function api(
  path,
  { method = "GET", body, user, raw = false } = {},
) {
  const response = await fetch(BASE + path, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(user ? { "X-User-Id": user.id } : {}),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!response.ok) {
    const e = await response.json().catch(() => ({}));
    throw new Error(
      typeof e.detail === "string"
        ? e.detail
        : JSON.stringify(e.detail || `HTTP ${response.status}`),
    );
  }
  if (raw) return response;
  if (response.status === 204) return null;
  return response.json();
}
export async function streamGuia(body, user, onChunk, signal) {
  const r = await fetch(BASE + "/api/v1/roteiros/stream-guia", {
    method: "POST",
    signal,
    headers: { "Content-Type": "application/json", "X-User-Id": user.id },
    body: JSON.stringify(body),
  });
  if (!r.ok || !r.body) throw new Error("Falha no guia: " + r.status);
  const reader = r.body.getReader(),
    decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
      const parts = buffer.split("\n\n");
      buffer = parts.pop();
      for (const part of parts) {
        const data = part
          .split("\n")
          .filter((l) => l.startsWith("data: "))
          .map((l) => l.slice(6))
          .join("\n");
        if (data) {
          const e = JSON.parse(data);
          onChunk(e.chunk);
        }
      }
      if (done) break;
    }
  } finally {
    await reader.cancel();
    reader.releaseLock();
  }
}
