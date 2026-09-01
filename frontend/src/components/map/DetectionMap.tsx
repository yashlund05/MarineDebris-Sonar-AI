import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Detection } from "../../types";
import { useAppStore } from "../../store/useAppStore";
import { getClassColor, formatConfidence } from "../../utils/classColors";
import { MapPinOff } from "lucide-react";

// Fix standard Leaflet default marker icons for Webpack/Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

interface DetectionMapProps {
  detections: Detection[];
}

function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  return null;
}

export const DetectionMap: React.FC<DetectionMapProps> = ({ detections }) => {
  const { setSelectedDetection, selectedClass, minConfidence, includeFiltered } = useAppStore();

  const georeferenced = detections.filter(
    (d) =>
      d.geotagging_available &&
      d.latitude !== null &&
      d.longitude !== null &&
      (selectedClass === "all" || d.class_name === selectedClass) &&
      d.confidence >= minConfidence &&
      (includeFiltered || !d.is_filtered)
  );

  if (georeferenced.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-bg-surface border border-border-subtle rounded-2xl p-8 text-center text-text-muted space-y-3 shadow-card">
        <div className="p-3 bg-slate-100 rounded-full text-sky-600 border border-border-subtle">
          <MapPinOff className="w-8 h-8" />
        </div>
        <p className="text-sm font-semibold text-text-primary">
          No Georeferenced Coordinates Available
        </p>
        <p className="text-xs max-w-sm text-text-muted">
          Acoustic survey targets will appear on this GIS map once processed with valid WGS84 navigation metadata.
        </p>
      </div>
    );
  }

  // Calculate center of detections
  const avgLat =
    georeferenced.reduce((acc, d) => acc + (d.latitude || 0), 0) / georeferenced.length;
  const avgLon =
    georeferenced.reduce((acc, d) => acc + (d.longitude || 0), 0) / georeferenced.length;

  return (
    <div className="h-full w-full rounded-2xl overflow-hidden border border-border-subtle shadow-card relative z-0">
      <MapContainer
        center={[avgLat, avgLon]}
        zoom={14}
        scrollWheelZoom={true}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapUpdater center={[avgLat, avgLon]} />

        {georeferenced.map((det) => {
          const lat = det.latitude;
          const lon = det.longitude;
          if (lat === undefined || lat === null || lon === undefined || lon === null) return null;
          const meta = getClassColor(det.class_name);

          // Create custom colored circle marker without neon glow
          const customIcon = L.divIcon({
            className: "custom-pin",
            html: `<div style="background-color: ${meta.color}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 1px 3px rgba(0,0,0,0.35);"></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7],
          });

          return (
            <Marker
              key={det.id}
              position={[lat, lon]}
              icon={customIcon}
              eventHandlers={{
                click: () => setSelectedDetection(det),
              }}
            >
              <Popup>
                <div className="p-1 space-y-1 font-sans text-xs">
                  <p className="font-bold text-xs" style={{ color: meta.text }}>
                    {meta.label}
                  </p>
                  <p className="font-mono text-[11px] text-slate-700">
                    Confidence: {formatConfidence(det.confidence_calibrated || det.confidence)}
                  </p>
                  <p className="font-mono text-[10px] text-slate-500">
                    {lat.toFixed(5)}°, {lon.toFixed(5)}°
                  </p>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default DetectionMap;
