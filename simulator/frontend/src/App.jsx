import { useState } from "react";
import "./App.css";
import GenerateForm from "./components/GenerateForm.jsx";
import ReplayForm from "./components/ReplayForm.jsx";
import ConnectForm from "./components/ConnectForm.jsx";
import LogFeed from "./components/LogFeed.jsx";
import Map from "./components/Map.jsx";

export default function App() {
  const [logs, setLogs] = useState([]);
  const [mapSelection, setMapSelection] = useState(null);

  const handleLog = (data) => {setLogs((prev) => [...prev, data]);};
  const clearLogs = () => setLogs([]);

  const handleMapClick = (x, y) => {
    setMapSelection({ x, y, ts: Date.now() });
  };

  return (
    <>
      <header className="app-header">
        <h1>Simulator</h1>
        <p>Generate, replay and manual connect</p>
      </header>

      <div className="layout-grid">
        <aside className="controls-column">
          <GenerateForm onLog={handleLog} />
          <ReplayForm onLog={handleLog} />
          <ConnectForm onLog={handleLog} mapSelection={mapSelection} />
        </aside>

        <section className="map-column">
          <Map logs={logs} onMapClick={handleMapClick} />
        </section>
      </div>

      <LogFeed logs={logs} clearLogs={clearLogs} />
    </>
  );
}
