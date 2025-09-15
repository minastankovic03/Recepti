const API_URL = "http://localhost:5000"; // BACKEND

export async function getRecepti() {
  const res = await fetch(`${API_URL}/recepti`);
  if (!res.ok) throw new Error("Greška pri čitanju recepata");
  return res.json();
}

export async function createRecept(body) {
  const res = await fetch(`${API_URL}/recepti`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json()
  if (!res.ok) throw new Error(data.poruka || "Greška pri kreiranju recepta");
  return data;
}

export async function updateRecept(id, body) {
  const res = await fetch(`${API_URL}/recepti/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json()
  if (!res.ok) throw new Error(data.poruka || "Greška pri ažuriranju recepta");
  return data;
}

export async function deleteRecept(id) {
  const res = await fetch(`${API_URL}/recepti/${id}`, { method: "DELETE" });
  let data = {};
  try {
    data = await res.json();
  } catch {
    data = {};
  }
  if (!res.ok) {
    throw new Error(data.poruka || "Greška pri brisanju recepta");
  }
  return data;
}

export async function pretragaRecepta(naziv, sastojak) {
  const q = new URLSearchParams();
  if (naziv) q.set("naziv",naziv);
  if (sastojak) q.set("sastojak", sastojak);
  const res =await fetch(`${API_URL}/pretraga?${q.toString()}`);
  if (!res.ok) throw new Error("Greška pri pretrazi recepta");
  return res.json();
}

export async function getTopRecepti() {
  const res = await fetch(`${API_URL}/top-recepti`);
  if (!res.ok) throw new Error("Greška pri čitanju top recepata");
  return res.json();
}

export async function oceniRecept(id, ocena) {
  const res = await fetch(`${API_URL}/recepti/${id}/ocena`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ocena }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.poruka || "Greška pri ocenjivanju");
  return data;
}

export async function dodajUKupovinu(sastojak) {
  const res = await fetch(`${API_URL}/kupovina`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sastojak),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.poruka || "Greška pri dodavanju u kupovinu");
  return data;
}

export async function getKupovina() {
  const res = await fetch(`${API_URL}/kupovina`);
  if (!res.ok) throw new Error("Greška pri čitanju liste kupovine");
  return res.json();
}

export async function obrisiIzKupovine(id) {
  const res = await fetch(`${API_URL}/kupovina/${id}`, { method: "DELETE" });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Greška pri brisanju iz kupovine");
  return data;
}
