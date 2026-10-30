// @vitest-environment jsdom
import React from "react";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import App from "./App";
const mocks = vi.hoisted(() => ({ api: vi.fn(), streamGuia: vi.fn() }));
vi.mock("./services/api", () => mocks);
vi.mock("./components/MapaRota", () => ({
  default: () => <div>Mapa renderizado</div>,
}));
afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.clearAllMocks();
});
it("visitante preenche viagem e consulta mapa, custo e histórico", async () => {
  let trips = [];
  const trip = {
    id: "1",
    origem: "Recife - PE",
    destino: "Salvador - BA",
    origem_coordenadas: [-8, -35],
    destino_coordenadas: [-13, -38],
    clima: { temperatura: "28 °C", vento: "10 km/h" },
    dias_estadia: 2,
    estilo_viagem: "Cultural",
    atrativos: [{ id: "0", nome: "Pelourinho" }],
    gastronomia: ["Acarajé"],
    visitas: [],
  };
  mocks.api.mockImplementation(async (path) => {
    if (path.endsWith("/demo"))
      return {
        usuario: { id: "v", nome: "Visitante", visitante: true },
        expires_in: 7200,
      };
    if (path.endsWith("/destinos")) return [];
    if (path.endsWith("/planejar")) {
      trips = [trip];
      return {
        json: async () => trip,
        headers: new Headers({
          "X-Process-Time": "12ms",
          "X-Request-ID": "teste",
        }),
      };
    }
    if (path.endsWith("/mapa-rota"))
      return {
        distancia_km: 800,
        duracao_minutos: 600,
        geometria: [
          [-35, -8],
          [-38, -13],
        ],
        rotas_alternativas: [],
        paradas: [],
        altimetria: { disponivel: false },
      };
    if (path.endsWith("/custos"))
      return {
        custo_total: 400,
        custo_por_passageiro: 400,
        autonomia_por_carga: 600,
      };
    if (path.endsWith("/resumo"))
      return { roteiros_gerados: 1, circuitos: { weather: "closed" } };
    if (path.endsWith("/roteiros")) return trips;
    return {};
  });
  render(<App />);
  fireEvent.click(screen.getByText("Entrar como visitante"));
  fireEvent.change(await screen.findByLabelText("Origem"), {
    target: { value: "Recife" },
  });
  fireEvent.change(screen.getByLabelText("Destino"), {
    target: { value: "Salvador" },
  });
  fireEvent.click(screen.getByText("Gerar roteiro"));
  expect(await screen.findByText("Mapa renderizado")).toBeTruthy();
  expect(await screen.findByText("Pelourinho")).toBeTruthy();
  expect((await screen.findAllByText(/400,00/)).length).toBe(2);
  expect(await screen.findByText("Abrir")).toBeTruthy();
});
