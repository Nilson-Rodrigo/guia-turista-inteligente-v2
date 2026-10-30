const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `Falha HTTP ${response.status}`);
  }
  return response.status === 204 ? null : response.json();
}

export function loginDemo() {
  return request("/api/v1/auth/demo", { method: "POST" });
}

export function planejar(payload, userId) {
  return request("/api/v1/roteiros/planejar", {
    method: "POST",
    headers: { "X-User-Id": userId },
    body: JSON.stringify(payload),
  });
}

export function listarRoteiros(userId) {
  return request("/api/v1/roteiros", { headers: { "X-User-Id": userId } });
}

export function calcularCustos(payload) {
  return request("/api/v1/roteiros/custos", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function obterMapaRota(payload) {
  return request("/api/v1/roteiros/mapa-rota", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deletarRoteiro(id, userId) {
  return request(`/api/v1/roteiros/${id}`, {
    method: "DELETE",
    headers: { "X-User-Id": userId },
  });
}

export async function streamGuia(destino, userId, onChunk) {
  const response = await fetch(`${API_URL}/api/v1/roteiros/stream-guia`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": userId,
    },
    body: JSON.stringify({ destino, dias_estadia: 2, estilo_viagem: "Cultural" }),
  });
  if (!response.ok || !response.body) {
    throw new Error(`Falha no streaming HTTP ${response.status}`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const eventos = buffer.split("\n\n");
    buffer = eventos.pop() || "";
    for (const evento of eventos) {
      const linha = evento.split("\n").find((item) => item.startsWith("data: "));
      if (linha && linha.slice(6) !== "[DONE]") onChunk(linha.slice(6));
    }
  }
}
