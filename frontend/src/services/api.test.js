import { afterEach, expect, it, vi } from "vitest";
import { api, streamGuia } from "./api";

afterEach(() => vi.unstubAllGlobals());

it("identifica a operação quando a API não pode ser alcançada", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

  await expect(api("/api/v1/telemetria/resumo")).rejects.toThrow(
    "carregar telemetria: Failed to fetch",
  );
});

it("processa chunks SSE sem exigir chunk no evento final", async () => {
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(
        new TextEncoder().encode('data: {"chunk":"**Guia**"}\n\n'),
      );
      controller.enqueue(new TextEncoder().encode('data: {"done":true}\n\n'));
      controller.close();
    },
  });
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, body: stream }),
  );
  const chunks = [];

  await streamGuia({}, { id: "visitante" }, (chunk) => chunks.push(chunk));

  expect(chunks).toEqual(["**Guia**"]);
});

it("informa quando o backend envia um fallback do Gemini", async () => {
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(
        new TextEncoder().encode(
          'data: {"chunk":"Configure a chave","done":true,"fallback":true}\n\n',
        ),
      );
      controller.close();
    },
  });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, body: stream }));

  await expect(streamGuia({}, { id: "visitante" }, vi.fn())).rejects.toThrow(
    "gerar guia com IA: Configure a chave",
  );
});