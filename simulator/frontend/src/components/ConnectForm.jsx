import { useState } from "react";
import { connectManual } from "../components/simulatorApi.jsx";

export default function ConnectForm({ onLog }) {
  const getNow = () => new Date().toISOString();

  const [form, setForm] = useState({
    imei: "",
    x: "",
    y: "",
    timestamp: getNow(),
  });

  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSetNow = () => {
    setForm((prev) => ({ ...prev, timestamp: getNow() }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);

    const payload = {
      ...form,
      x: Number(form.x),
      y: Number(form.y),
    };

    try {
      const result = await connectManual(payload);
      
      onLog(result);

      setStatus({ type: "success", message: "Connect sent successfully." });

      setForm((prev) => ({ ...prev, timestamp: getNow() }));
    } catch (err) {
      setStatus({ type: "error", message: "Connect failed." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Manual Connect</h2>

      {/* Row 1: IMEI, X, Y */}
      <div className="form-row">
        <input
          name="imei"
          placeholder="IMEI"
          value={form.imei}
          onChange={handleChange}
        />

        <input
          name="x"
          type="number"
          placeholder="X"
          value={form.x}
          onChange={handleChange}
        />

        <input
          name="y"
          type="number"
          placeholder="Y"
          value={form.y}
          onChange={handleChange}
        />
      </div>

      {/* Row 2: Timestamp + Buttons */}
      <div className="form-row">
        <div style={{ display: "flex", gap: "0.5rem", flex: 1 }}>
          <input
            name="timestamp"
            placeholder="Timestamp"
            value={form.timestamp}
            onChange={handleChange}
            style={{ flex: 1 }}
          />
          <button type="button" onClick={handleSetNow} title="Set to current time">
            Now
          </button>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "Sending..." : "Send"}
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
