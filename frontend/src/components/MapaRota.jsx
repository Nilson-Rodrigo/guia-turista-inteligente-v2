import { useEffect } from "react";
import {
  MapContainer,
  Polyline,
  TileLayer,
  CircleMarker,
  Tooltip,
  useMap,
} from "react-leaflet";
import { haversineKm } from "../services/geolocation";
import "leaflet/dist/leaflet.css";
function Enquadrar({ positions }) {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(positions, { padding: [25, 25] });
  }, [map, positions]);
  return null;
}
export function pontoNaDistancia(positions, km) {
  let soma = 0;
  for (let i = 1; i < positions.length; i++) {
    const a = positions[i - 1],
      b = positions[i],
      d = haversineKm(
        { latitude: a[0], longitude: a[1] },
        { latitude: b[0], longitude: b[1] },
      );
    if (soma + d >= km) {
      const t = d ? (km - soma) / d : 0;
      return [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])];
    }
    soma += d;
  }
  return positions.at(-1);
}
export default function MapaRota({ rota }) {
  const positions = (rota?.geometria || [])
    .filter(
      (point) =>
        Array.isArray(point) &&
        point.length === 2 &&
        point.every((coordinate) => Number.isFinite(coordinate)),
    )
    .map(([lon, lat]) => [lat, lon]);
  if (!positions.length)
    return <p>Mapa indisponível para este percurso.</p>;
  return (
    <MapContainer className="route-map" center={positions[0]} zoom={6}>
      <Enquadrar positions={positions} />
      <TileLayer
        attribution="© OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {positions.length > 1 && (
        <>
          <Polyline
            positions={positions}
            pathOptions={{ color: "#302716", weight: 9, opacity: 0.9 }}
          />
          <Polyline
            positions={positions}
            pathOptions={{ color: "#df5e35", weight: 6, opacity: 1 }}
          />
        </>
      )}
      <CircleMarker center={positions[0]} radius={9} pathOptions={{ color: "#2468bd", fillColor: "#2468bd", fillOpacity: 1 }}>
        <Tooltip permanent direction="top">Origem</Tooltip>
      </CircleMarker>
      <CircleMarker center={positions.at(-1)} radius={9} pathOptions={{ color: "#a33917", fillColor: "#a33917", fillOpacity: 1 }}>
        <Tooltip permanent direction="top">Destino</Tooltip>
      </CircleMarker>
      {(rota.paradas || []).map((p) => (
        <CircleMarker
          key={p.progresso_km}
          center={pontoNaDistancia(positions, p.progresso_km)}
          radius={7}
        >
          <Tooltip>
            Parada estimada: {p.progresso_km} km. Confirme postos disponíveis.
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
