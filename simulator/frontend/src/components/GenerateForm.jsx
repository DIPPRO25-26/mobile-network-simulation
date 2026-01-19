import { useState } from "react";
import { generateSimulation } from "../components/simulatorApi.jsx";

export default function GenerateForm({ onLog }) {
  const [users, setUsers] = useState(1);
  const [events, setEvents] = useState(10);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);

    try {
      await generateSimulation(users, events, (data) => {
        onLog(data);
      });

      setStatus({ type: "success", message: "Simulation finished." });
    } catch (err) {
      setStatus({ type: "error", message: err.message || "Generate failed." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Generate Simulation</h2>

      <div className="form-row">
        <label>
          Users
          <input
            type="number"
            min="1"
            value={users}
            onChange={(e) => setUsers(Number(e.target.value))}
          />
        </label>

        <label>
          Events
          <input
            type="number"
            min="1"
            value={events}
            onChange={(e) => setEvents(Number(e.target.value))}
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Streaming..." : "Generate"}
        </button>
      </div>

      {status && (
        <div className={`status ${status.type === "error" ? "error" : ""}`}>
          {status.message}
        </div>
      )}
    </form>
  );
}
