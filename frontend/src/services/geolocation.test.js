import { describe, expect, it } from "vitest";
import { haversineKm } from "./geolocation";

describe("haversineKm", () => {
  it("calcula a distância aproximada entre Recife e Salvador", () => {
    const distance = haversineKm(
      { latitude: -8.0476, longitude: -34.877 },
      { latitude: -12.9777, longitude: -38.5016 },
    );
    expect(distance).toBeGreaterThan(650);
    expect(distance).toBeLessThan(700);
  });

  it("retorna zero para o mesmo ponto", () => {
    expect(haversineKm({ latitude: 0, longitude: 0 }, { latitude: 0, longitude: 0 })).toBe(0);
  });
});
