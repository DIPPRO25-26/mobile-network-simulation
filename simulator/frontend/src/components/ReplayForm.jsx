import { useState } from "react";
import { replaySimulation } from "./simulatorApi.jsx";

export default function ReplayForm() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    try {
  await replaySimulation(file);
  setStatus("Replay successful");
} catch {
  setStatus("Replay failed");
}
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Replay Simulation</h2>

      <input
        type="file"
        accept=".csv"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button>Replay</button>

      {status && <p>{status}</p>}
    </form>
  );
}
