from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring


def gerar_gpx(
    origem: str,
    destino: str,
    geometria: list[list[float]],
) -> bytes:
    namespace = "http://www.topografix.com/GPX/1/1"
    root = Element(
        "gpx",
        {
            "version": "1.1",
            "creator": "Guia do Turista Inteligente",
            "xmlns": namespace,
        },
    )
    metadata = SubElement(root, "metadata")
    SubElement(metadata, "name").text = f"{origem} para {destino}"
    SubElement(metadata, "time").text = datetime.now(timezone.utc).isoformat()
    track = SubElement(root, "trk")
    SubElement(track, "name").text = f"Rota {origem} - {destino}"
    segment = SubElement(track, "trkseg")
    for longitude, latitude in geometria:
        SubElement(segment, "trkpt", {"lat": str(latitude), "lon": str(longitude)})
    return tostring(root, encoding="utf-8", xml_declaration=True)
