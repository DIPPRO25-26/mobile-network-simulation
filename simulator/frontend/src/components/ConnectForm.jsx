import { useState, useEffect } from "react";
import { connectManual } from "../components/simulatorApi.jsx";

export default function ConnectForm({ onLog, mapSelection }) {
  const getNow = () => new Date().toISOString();

  const [form, setForm] = useState({
    imei: "",
    x: "",
    y: "",
    timestamp: getNow(),
    keepalive: false,
  });

  // Listen for map clicks
  useEffect(() => {
    if (mapSelection) {
      setForm((prev) => ({
        ...prev,
        x: mapSelection.x,
        y: mapSelection.y,
        timestamp: getNow()
      }));
    }
  }, [mapSelection]);

  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const handleChange = (e) => {
    const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setForm((prev) => ({ ...prev, [e.target.name]: value }));
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
          required
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
      <div className="form-row align-center">
        <div className="input-group">
          <input
            name="timestamp"
            placeholder="Timestamp"
            value={form.timestamp}
            onChange={handleChange}
          />
          <button type="button" onClick={handleSetNow} title="Set to current time">
            Now
          </button>
        </div>

        <label className="checkbox-label">
          <input
            type="checkbox"
            name="keepalive"
            checked={form.keepalive}
            onChange={handleChange}
          />
          <span>Keepalive</span>
        </label>

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
