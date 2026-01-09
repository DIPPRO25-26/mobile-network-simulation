const BASE_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:5000";

export async function generateSimulation(users, events) {
  const res = await fetch(`${BASE_URL}/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ users, events }),
  });

  if (!res.ok) {
    throw new Error("Generate failed");
  }

  return await res.blob(); 
}

export async function replaySimulation(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/replay`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error("Replay failed");
  }

  return await res.json();
}

export async function connectManual(data) {
  const res = await fetch(`${BASE_URL}/connect`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error("Connect failed");
  }

  return await res.json();
}
