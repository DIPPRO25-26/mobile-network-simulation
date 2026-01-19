import { useState } from "react";
import { replaySimulation } from "./simulatorApi.jsx";

export default function ReplayForm({ onLog }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setStatus(null);

    try {
      await replaySimulation(file, (data) => {
        onLog(data);
      });
      setStatus("Replay finished");
    } catch {
      setStatus("Replay failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Replay Simulation</h2>

      <div className="form-row">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files[0])}
        />

        <button disabled={loading}>
          {loading ? "Replaying..." : "Replay"}
        </button>
      </div>

      {status && <p>{status}</p>}
    </form>
  );
}
