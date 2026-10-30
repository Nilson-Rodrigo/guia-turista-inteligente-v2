const BASE = import.meta.env.VITE_API_URL || "http://localhost:8001";
const operationName = (path) => {
  const exact = {
    "/api/v1/auth/demo": "entrar como visitante",
    "/api/v1/auth/me": "validar sessão",
    "/api/v1/auth/google": "entrar com Google",
    "/api/v1/auth/logout": "encerrar sessão",
    "/api/v1/roteiros": "carregar histórico",
    "/api/v1/roteiros/destinos": "carregar destinos",
    "/api/v1/roteiros/planejar": "planejar viagem",
    "/api/v1/roteiros/mapa-rota": "carregar mapa e relevo",
    "/api/v1/roteiros/custos": "calcular custos",
    "/api/v1/telemetria/resumo": "carregar telemetria",
  };
  if (exact[path]) return exact[path];
  if (path.endsWith("/exportar/gpx")) return "exportar GPX";
  if (path.endsWith("/compartilhar")) return "compartilhar roteiro";
  if (path.endsWith("/visitas")) return "atualizar visitas";
  return "realizar a operação";
};

export async function api(
  path,
  { method = "GET", body, user, raw = false, operation } = {},
) {
  const label = operation || operationName(path);
  let response;
  try {
    response = await fetch(BASE + path, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(user ? { "X-User-Id": user.id } : {}),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  } catch (error) {
    throw new Error(`${label}: ${error.message || "não foi possível conectar à API"}`);
  }
  if (!response.ok) {
    const e = await response.json().catch(() => ({}));
    throw new Error(
      `${label}: ${typeof e.detail === "string" ? e.detail : JSON.stringify(e.detail || `HTTP ${response.status}`)}`,
    );
  }
  if (raw) return response;
  if (response.status === 204) return null;
  return response.json();
}
export async function streamGuia(body, user, onChunk, signal) {
  let r;
  try {
    r = await fetch(BASE + "/api/v1/roteiros/stream-guia", {
      method: "POST",
      signal,
      headers: { "Content-Type": "application/json", "X-User-Id": user.id },
      body: JSON.stringify(body),
    });
  } catch (error) {
    throw new Error(`gerar guia com IA: ${error.message || "não foi possível conectar à API"}`);
  }
  if (!r.ok || !r.body) throw new Error(`gerar guia com IA: HTTP ${r.status}`);
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
          let e;
          try {
            e = JSON.parse(data);
          } catch {
            throw new Error("gerar guia com IA: resposta SSE inválida");
          }
          if (e.fallback) {
            throw new Error(`gerar guia com IA: ${e.chunk || "serviço indisponível"}`);
          }
          if (e.chunk) onChunk(e.chunk);
        }
      }
      if (done) break;
    }
  } finally {
    await reader.cancel();
    reader.releaseLock();
  }
}
