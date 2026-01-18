import { useEffect, useRef } from "react";

export default function LogFeed({ logs, clearLogs }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  if (logs.length === 0) return null;

  return (
    <div className="log-feed-container">
      <div className="log-header">
        <h3>Live Event Feed ({logs.length})</h3>
        <button onClick={clearLogs} className="clear-btn">Clear</button>
      </div>
      <div className="log-window">
        {logs.map((log, index) => {
          const isError = log.response?.error !== null;
          const statusClass = isError ? "error" : "success";
          
          const detailText = isError 
            ? log.response?.error 
            : log.response?.detail || "Action completed";

          return (
            <div key={index} className="log-entry">
              <span className="timestamp">
                [{log.timestamp} UTC]
              </span>
              <span className="imei"> IMEI: {log.imei}</span>
              <span className="coords"> ({log.x}, {log.y})</span>
              
              <span className={`status-tag ${statusClass}`}>
                 {isError ? "ERROR" : "SUCCESS"}
              </span>
              
              <div className="detail">
                {detailText}
              </div>
            </div>
          );
        })}
        <div ref={endRef} />
      </div>
    </div>
  );
}
