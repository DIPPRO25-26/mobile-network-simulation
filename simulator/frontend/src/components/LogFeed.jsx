import { useEffect, useRef } from "react";

export default function LogFeed({ logs, clearLogs }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const downloadCSV = () => {
    if (!logs || logs.length === 0) return;
    const headers = ["timestamp", "imei", "x", "y"];
    const csvRows = [
      headers.join(","),
      ...logs.map((log) => {
        const row = [
          log.timestamp,
          log.imei,
          log.x,
          log.y
        ];
        return row.join(",");
      }),
    ];

    const csvString = csvRows.join("\n");
    const blob = new Blob([csvString], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    
    link.href = url;
    link.download = `simulator_${new Date().toISOString()}.csv`;
    document.body.appendChild(link);
    link.click();
    
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (logs.length === 0) return null;

  return (
    <div className="log-feed-container">
      <div className="log-header">
        <h3>Live Event Feed ({logs.length})</h3>
        <div className="button-group">
          <button onClick={downloadCSV} className="download-btn" style={{ marginRight: '10px' }}>
            Download CSV
          </button>
          <button onClick={clearLogs} className="clear-btn">Clear</button>
        </div>
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
