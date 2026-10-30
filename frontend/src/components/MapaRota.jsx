import { MapContainer, Marker, Polyline, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function MapaRota({ rota }) {
  if (!rota?.geometria?.length) {
    return <div className="map-empty">A geometria da rota ficará disponível após o planejamento.</div>;
  }
  const positions = rota.geometria.map(([longitude, latitude]) => [latitude, longitude]);
  const center = positions[Math.floor(positions.length / 2)];
  return <MapContainer center={center} zoom={6} scrollWheelZoom={false} className="route-map">
    <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    <Polyline positions={positions} pathOptions={{ color: "#df5e35", weight: 5 }} />
    {rota.paradas.map((parada, index) => {
      const point = positions[Math.min(Math.round((parada.progresso_km / rota.distancia_km) * positions.length), positions.length - 1)];
      return <Marker key={`${parada.progresso_km}-${index}`} position={point}><Tooltip permanent={false}>Parada em {parada.progresso_km} km</Tooltip></Marker>;
    })}
  </MapContainer>;
}
