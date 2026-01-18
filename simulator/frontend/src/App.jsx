import { useState } from "react";
import "./App.css";
import GenerateForm from "./components/GenerateForm.jsx";
import ReplayForm from "./components/ReplayForm.jsx";
import ConnectForm from "./components/ConnectForm.jsx";
import LogFeed from "./components/LogFeed.jsx";

export default function App() {
  const [logs, setLogs] = useState([]);
  const handleLog = (data) => {setLogs((prev) => [...prev, data]);};
  const clearLogs = () => setLogs([]);

  return (
    <>
      <header className="app-header">
        <h1>Simulator</h1>
        <p>Generate, replay and manual connect</p>
      </header>

      <main>
        <GenerateForm onLog={handleLog} />
        <ReplayForm onLog={handleLog} />
        <ConnectForm onLog={handleLog} />
        
        <LogFeed logs={logs} clearLogs={clearLogs} />
      </main>
    </>
  );
}
