const BASE_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:5000";

async function readStream(response, onData) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      const lines = buffer.split("\n");
      
      buffer = lines.pop();

      for (const line of lines) {
        if (line.trim()) {
          try {
            const data = JSON.parse(line);
            onData(data);
          } catch (e) {
            console.error("Error parsing stream chunk", e);
          }
        }
      }
    }
  } catch (err) {
    console.error("Stream reading failed", err);
    throw err;
  }
}

export async function generateSimulation(users, events, onData) {
  const res = await fetch(`${BASE_URL}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ users, events }),
  });

  if (!res.ok) throw new Error("Generate failed");

  await readStream(res, onData);
}

export async function replaySimulation(file, onData) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/replay`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error("Replay failed");

  await readStream(res, onData);
}

export async function connectManual(data) {
  const res = await fetch(`${BASE_URL}/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) throw new Error("Connect failed");

  return await res.json();
}
