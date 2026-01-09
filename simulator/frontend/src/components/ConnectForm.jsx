import { useState } from "react";
import { connectManual } from "../components/simulatorApi.jsx";

export default function ConnectForm() {
  const [form, setForm] = useState({
    imei: "",
    x: "",
    y: "",
    timestamp: "",
  });

  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);

    try {
      await connectManual(form);
      setStatus({ type: "success", message: "Connect sent successfully." });

      setForm({ imei: "", x: "", y: "", timestamp: "" });
    } catch {
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
          placeholder="X"
          value={form.x}
          onChange={handleChange}
        />

        <input
          name="y"
          placeholder="Y"
          value={form.y}
          onChange={handleChange}
        />
      </div>

      {/* Row 2: Timestamp + Send */}
      <div className="form-row">
        <input
          name="timestamp"
          placeholder="Timestamp"
          value={form.timestamp}
          onChange={handleChange}
        />

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
