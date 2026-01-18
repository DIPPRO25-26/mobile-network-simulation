import { useEffect, useState, useMemo, useRef } from "react";
import { getBtsLocations } from "./simulatorApi.jsx";

export default function MapVisualization({ logs, onMapClick }) {
  const [btsList, setBtsList] = useState([]);
  const svgRef = useRef(null);

  useEffect(() => {
    getBtsLocations()
      .then(setBtsList)
      .catch((err) => console.error("Failed to load BTS locations", err));
  }, []);

  const { paths, dots } = useMemo(() => {
    const grouped = {};
    const allDots = [];

    logs.forEach((log) => {
      if (log.x === undefined || log.y === undefined) return;

      const imei = log.imei;
      if (!grouped[imei]) grouped[imei] = [];
      
      grouped[imei].push({ x: log.x, y: log.y });

      let type = "success"; // green
      const detail = log.response?.detail?.toLowerCase() || "";
      const error = log.response?.error;

      if (error) {
        type = "error"; // red
      } else if (detail.includes("handover")) {
        type = "handover"; // yellow
      }

      allDots.push({
        x: log.x,
        y: log.y,
        type,
        key: log.timestamp + imei
      });
    });

    return { paths: grouped, dots: allDots };
  }, [logs]);

  const handleSvgClick = (e) => {
    if (!svgRef.current) return;
    
    const rect = svgRef.current.getBoundingClientRect();
    const scaleX = 400 / rect.width;
    const scaleY = 400 / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    if (onMapClick) {
      onMapClick(x, y);
    }
  };

  return (
    <div className="map-wrapper">
      <h3>Live Map (0-400)</h3>
      <div className="map-container">
        <svg 
          ref={svgRef}
          viewBox="0 0 400 400" 
          className="simulation-map" 
          onClick={handleSvgClick}
        >
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="400" height="400" fill="url(#grid)" />

          {btsList.map((bts) => (
            <g key={bts.bts_id} transform={`translate(${bts.x}, ${bts.y})`}>
              <polygon points="0,-5 -4,4 4,4" fill="#38bdf8" fillOpacity="0.4" stroke="#38bdf8" strokeWidth="1" />
              <text y="14" fontSize="8" fill="#38bdf8" textAnchor="middle" style={{pointerEvents:'none'}}>
                {bts.bts_id}
              </text>
            </g>
          ))}

          {Object.entries(paths).map(([imei, coords]) => {
            const points = coords.map(p => `${p.x},${p.y}`).join(" ");
            return (
              <polyline
                key={imei}
                points={points}
                fill="none"
                stroke="rgba(255, 255, 255, 0.2)"
                strokeWidth="1.5"
                strokeDasharray="4"
              />
            );
          })}

          {dots.map((dot, i) => {
            let color = "#4ade80"; // success/green
            if (dot.type === "error") color = "#ef4444"; // red
            if (dot.type === "handover") color = "#facc15"; // yellow

            return (
              <circle
                key={i}
                cx={dot.x}
                cy={dot.y}
                r="3"
                fill={color}
                stroke="#000"
                strokeWidth="0.5"
              />
            );
          })}
        </svg>
      </div>
      <p className="map-hint">Click map to set coordinates for Manual Connect</p>
    </div>
  );
}
