// src/App.js
import React, { useEffect, useState } from "react";
import 'bootstrap/dist/css/bootstrap.min.css';
import "./App.css";
import { getRecepti, getTopRecepti, createRecept, updateRecept, deleteRecept, pretragaRecepta, oceniRecept, dodajUKupovinu, getKupovina, obrisiIzKupovine} from "./api";

function App() {
  
  const [tab, setTab] = useState("svi"); 
  const [recepti, setRecepti] = useState([]);
 
  const [topRecepti, setTopRecepti] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [nazivPretraga, setNazivPretraga] = useState("");
  const [sastojakPretraga, setSastojakPretraga] = useState("");
  
  const [detalj, setDetalj] = useState(null); 
  const [showReceptModal, setShowReceptModal] = useState(false);
  
  const [showKupovinaModal, setShowKupovinaModal] = useState(false);
  const [showListaModal, setShowListaModal] = useState(false);
  
  const [kupovina, setKupovina] = useState([]);
  const [kupovinaNamirnica, setKupovinaNamirnica] = useState({ ime: "", kolicina: "" });
  
  const prazanForm = {
    id: null,
    naziv: "",
    opis: "",
    istorija: "",
    uputstvo: "",
    tezina: "",
    vreme_pripreme: "",
    slika: "",
    sastojci: [],
  };

  const [form, setForm] = useState(prazanForm);
  const [editing, setEditing] = useState(false);
  
  const [noviSastojak, setNoviSastojak] = useState({ ime: "", kolicina: "" });
  const [ocenaValue, setOcenaValue] = useState(5);
  
  // UČITAVANJE
  async function loadAll() {
    setLoading(true);
    try {
      const r1 = await getRecepti();
      const r2 = await getTopRecepti().catch(() => []);
      setRecepti(r1 || []);
      setTopRecepti(r2 || []);
    } catch (e) {
      console.error("Greška pri učitavanju:", e);
      alert("Ne mogu da učitam recepte sa servera.");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    loadAll();
  }, []);

  // PRETRAGA
  async function pretrazi() {
    try {
      setLoading(true);
      const data = await pretragaRecepta(nazivPretraga, sastojakPretraga);
      setRecepti(data);
      setTab("svi");
    } catch (e) {
      console.error(e);
      alert("Greška pri pretrazi.");
    } finally {
      setLoading(false);
    }
  }

  // EDITOVANJE FORME
  function openEditForm(r) {
    setForm({
      id: r.id,
      naziv: r.naziv || "",
      opis: r.opis || "",
      istorija: r.istorija || "",
      uputstvo: r.uputstvo || "",
      tezina: r.tezina || "",
      vreme_pripreme: r.vreme_pripreme || "",
      slika: r.slika || "",
      sastojci: (r.sastojci || []).map(s => ({ ime: s.ime, kolicina: s.kolicina })),
    });
    setEditing(true);
    setShowReceptModal(true);
    setTab("dodaj");
  }

  // DODAVANJE SASTOJKA
  function dodajSastojak() {
    if (!noviSastojak.ime) return alert("Unesi ime sastojka");
    setForm(prev => ({ ...prev, sastojci: [...prev.sastojci, { ...noviSastojak }] }));
    setNoviSastojak({ ime: "", kolicina: "" });
  }

  // UKLANJANJE SASTOJKA
  function ukloniSastojak(i) {
    setForm(prev => ({ ...prev, sastojci: prev.sastojci.filter((_, idx) => idx !== i) }));
  }

  // ČUVANJE FORME
  async function sacuvajForm(e) {
    e && e.preventDefault();
    try {
      const payload = {
        naziv: form.naziv,
        opis: form.opis,
        istorija: form.istorija,
        uputstvo: form.uputstvo,
        tezina: form.tezina,
        vreme_pripreme: Number(form.vreme_pripreme) || null,
        slika: form.slika,
        sastojci: form.sastojci.map(s => ({ ime: s.ime, kolicina: s.kolicina })),
      };
      if (editing && form.id) {
      await updateRecept(form.id, payload);
    } else {
      await createRecept(payload);
    }
    await loadAll();                
    setShowReceptModal(false);      
    setForm(prazanForm);            
    setEditing(false);
    setTab("svi");
  } catch (err) {
    console.error(err);
    alert("Greška pri čuvanju recepta: " + err.message);
  }
}

  // BRISANJE
  const obrisiRecept = async (id) => {
  try {
    const res = await deleteRecept(id);
    if (res.poruka) {
      alert(res.poruka); 
    }
    await loadAll();
  } catch (error) {
    alert("Greška: " + error.message);
  }
};

  function otvoriDetalj(r) {
    setDetalj(r);
  }

  function zatvoriDetalj() {
    setDetalj(null);
  }

  // DODAJ OCENU
  async function dodajOcenu(receptId, vrednost) {
    try {
      await oceniRecept(receptId, vrednost)
      await loadAll();
      alert("Hvala na oceni!");
    } catch (e) {
      console.error(e);
      alert("Neuspešno dodavanje ocene.");
    }
  }

  // DODAJ U LISTU ZA KUPVINU
  async function dodajUListuZaKupovinu() {
    if (!kupovinaNamirnica.ime) return alert("Unesi ime artikla");
    try {
      await dodajUKupovinu(kupovinaNamirnica);
      const novaLista = await getKupovina();
      setKupovina(novaLista);
    } catch (err) {
      console.error(err);
      alert("Neuspešno dodavanje u kupovinu.");
    }
  }
  
  // UČITAJ LISTU PRI POKRETANJU APP
  useEffect(() => {
    getKupovina().then(setKupovina).catch(err => console.error(err))
  }, []);

  // IZBACI IZ LISTE ZA KUPOVINU
  async function izbaciIzKupovine(id) {
    try {
      await obrisiIzKupovine(id);
      setKupovina(await getKupovina());
      }catch(err){
      console.error(err);
      alert("Neuspešno brisanje stavke!");
    }
  }

  // KATAK OPIS
  function kratakOpis(opis, max = 120) {
    if (!opis) return "";
    return opis.length > max ? opis.slice(0, max).trim() + "…" : opis;
  }

  //KRAJNJI RETURN
  return (
    <div className="pozadina"
    style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.5), rgba(255,255,255,0.5)), url("/veb_lj.jpg")`,
            backgroundSize: "cover",
            backgroundRepeat: "no-repeat",
            minHeight: "100vh",
            width:"100%"
          }}>
    <div className="container-custom">
      <header className="header">
        <h1>🍽️ Kulinarski dnevnik 🍽️ </h1>
      </header>

      {/*DEO SA DUGMADIMA*/}
      <div className="toolbar mb-3">
        <button 
          className={`btn btn-filter btn-svi ${tab === "svi" ? "active" : ""}`} 
          onClick={() => setTab("svi")}
        >
          Svi recepti
        </button>

        <button 
          className={`btn btn-filter btn-top ${tab === "top" ? "active" : ""}`} 
          onClick={() => setTab("top")}
        >
          Top recepti
        </button>

        <button 
          className="btn btn-custom btn-dodaj" 
          onClick={() => setShowReceptModal(true)}
        >
          Dodaj recept
        </button>

        <button 
          className="btn btn-custom btn-kupovina" 
          onClick={() => setShowKupovinaModal(true)}
        >
          Dodaj u listu
        </button>

        <button 
          className="btn btn-custom btn-lista" 
          onClick={() => setShowListaModal(true)}
        >
          Lista za kupovinu
        </button>
        
        {/* DEO SA PRETRAGOM */}
        <div className="ms-auto d-flex gap-2" style={{ minWidth: 360 }}>
          <input className="form-control" placeholder="Pretraga po nazivu..." value={nazivPretraga} onChange={e => setNazivPretraga(e.target.value)} />
          <input className="form-control" placeholder="Pretraga po sastojku..." value={sastojakPretraga} onChange={e => setSastojakPretraga(e.target.value)} />
          <button className="btn btn-primary" onClick={pretrazi}>Pretraži</button>
          <button className="btn btn-secondary" onClick={() => { setNazivPretraga(""); setSastojakPretraga(""); loadAll(); }}>Reset</button>
        </div>
      </div>

      {/* SADRŽAJ U KARTICAMA ZA SVE I TOP RECEPTE */}
      <div>
        {tab === "svi" && (
          <div className="row">
            {loading ? <p>Učitavam...</p> :
              (recepti.length === 0 ? <p>Nema recepata.</p> :
                recepti.map(r => (
                  <div key={r.id} className="col-md-6 col-lg-4 mb-3">
                    <div className="card-custom h-100 d-flex flex-column">
                      {r.slika ? <img src={r.slika} alt={r.naziv} /> : null}
                      <div className="mt-2">
                        <h5>{r.naziv}</h5>
                        <p className="text-muted">{kratakOpis(r.opis)}</p>
                        <p><b>Težina:</b> {r.tezina ?? "—"} • <b>Vreme:</b> {r.vreme_pripreme ?? "—"} min</p>
                      </div>
                      <div className="mt-auto d-flex gap-2">
                        <button className="btn btn-outline-primary" onClick={() => otvoriDetalj(r)}>Prikaži</button>
                        <button className="btn btn-outline-secondary" onClick={() => openEditForm(r)}>Izmeni</button>
                        <button className="btn btn-danger" onClick={() => obrisiRecept(r.id)}>Obriši</button>
                        <div className="ms-auto d-flex align-items-center gap-2">
                          <select value={ocenaValue} onChange={e => setOcenaValue(e.target.value)} className="form-select form-select-sm" style={{ width: 72 }}>
                            <option value={1}>1</option>
                            <option value={2}>2</option>
                            <option value={3}>3</option>
                            <option value={4}>4</option>
                            <option value={5}>5</option>
                          </select>
                          <button className="btn btn-sm btn-outline-success" onClick={() => dodajOcenu(r.id, ocenaValue)}>Oceni</button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )
            }
          </div>
        )}

        {tab === "top" && (
          <div className="row">
            {topRecepti.length === 0 ? <p>Nema top recepata (još nema ocena).</p> :
              topRecepti.map(r => (
                <div key={r.id} className="col-md-6 col-lg-4 mb-3">
                  <div className="card-custom h-100">
                    {r.slika ? <img src={r.slika} alt={r.naziv} /> : null}
                    <h5>{r.naziv} ⭐</h5>
                    <p className="text-muted">{kratakOpis(r.opis)}</p>
                    <p><b>Prosek ocena:</b> {r.prosek_ocena ?? "—"}</p>
                    <div className="d-flex gap-2">
                      <button className="btn btn-outline-primary" onClick={() => otvoriDetalj(r)}>Prikaži</button>
                      <button className="btn btn-outline-secondary" onClick={() => openEditForm(r)}>Izmeni</button>
                    </div>
                  </div>
                </div>
              ))
            }
          </div>
        )}
      </div>

      {/* DODAVANJE RECEPTA */}
      {showReceptModal && (
        <div className="modal-backdrop">
          <div className="modal-content p-4 rounded shadow bg-white" style={{ maxWidth: "600px", margin: "80px auto" }}>
            <h3 className="mb-3">Dodaj recept</h3>

            <form onSubmit={sacuvajForm}>
              <div className="mb-3">
                <label className="form-label">Naziv recepta</label>
                <input
                  name="naziv"
                  className="form-control"
                  value={form.naziv}
                  onChange={(e) => setForm({ ...form, naziv: e.target.value })}
                  required
                />
              </div>

              <div className="mb-3">
                <label className="form-label">Opis</label>
                <textarea
                  name="opis"
                  className="form-control"
                  value={form.opis}
                  onChange={(e) => setForm({ ...form, opis: e.target.value })}
                  rows="2"
                />
              </div>

              <div className="mb-3">
                <label className="form-label">Istorija</label>
                <textarea
                  name="istorija"
                  className="form-control"
                  value={form.istorija}
                  onChange={(e) => setForm({ ...form, istorija: e.target.value })}
                  rows="2"
                />
              </div>

              <div className="mb-3">
                <label className="form-label">Uputstvo za pripremu</label>
                <textarea
                  name="uputstvo"
                  className="form-control"
                  value={form.uputstvo}
                  onChange={(e) => setForm({ ...form, uputstvo: e.target.value })}
                  rows="3"
                  required
                />
              </div>

              <div className="mb-3">
                <label className="form-label">Težina</label>
                <input
                  name="tezina"
                  className="form-control"
                  value={form.tezina}
                  onChange={(e) => setForm({ ...form, tezina: e.target.value })}
                  placeholder="Npr. lako, srednje, teško"
                  required
                />
              </div>

              <div className="mb-3">
                <label className="form-label">Vreme pripreme (min)</label>
                <input
                  type="number"
                  name="vreme_pripreme"
                  className="form-control"
                  value={form.vreme_pripreme}
                  onChange={(e) => setForm({ ...form, vreme_pripreme: e.target.value })}
                  required
                />
              </div>

              <div className="mb-3">
                <label className="form-label">URL slike (opciono)</label>
                <input
                  name="slika"
                  className="form-control"
                  value={form.slika}
                  onChange={(e) => setForm({ ...form, slika: e.target.value })}
                />
              </div>

              <div className="mb-3">
                <label className="form-label">Sastojci</label>
                <div className="d-flex gap-2 mb-2">
                  <input
                    className="form-control"
                    placeholder="Ime sastojka"
                    value={noviSastojak.ime}
                    onChange={(e) => setNoviSastojak({ ...noviSastojak, ime: e.target.value })}
                  />
                  <input
                    className="form-control"
                    placeholder="Količina"
                    value={noviSastojak.kolicina}
                    onChange={(e) => setNoviSastojak({ ...noviSastojak, kolicina: e.target.value })}
                  />
                  <button type="button" className="btn btn-secondary" onClick={dodajSastojak}>
                    ➕
                  </button>
                </div>
                <ul className="list-unstyled">
                  {form.sastojci.map((s, i) => (
                    <li key={i} className="d-flex justify-content-between align-items-center">
                      {s.ime} — {s.kolicina}
                      <button
                        type="button"
                        className="btn btn-sm btn-link text-danger"
                        onClick={() => ukloniSastojak(i)}
                      >
                        Ukloni
                      </button>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="d-flex justify-content-end gap-2 mt-4">
                <button type="submit" className="btn btn-primary">
                  Sačuvaj
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowReceptModal(false)}>
                  Zatvori
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* DETALJNIJE RECEPT */}
      {detalj && (
        <div className="modal-backdrop">
          <div className="modal-content p-4 rounded shadow bg-white" style={{ maxWidth: "700px", margin: "60px auto", maxHeight: "80vh", overflowY: "auto" }}>
            <h3>{detalj.naziv}</h3>
            {detalj.slika && (
              <img src={detalj.slika} alt={detalj.naziv} className="img-fluid mb-3" style={{ borderRadius: "8px" }} />
            )}

            <p><strong>Opis:</strong> {detalj.opis}</p>
            {detalj.istorija && <p><strong>Istorija:</strong> {detalj.istorija}</p>}
            <p><strong>Uputstvo:</strong> {detalj.uputstvo}</p>
            <p><strong>Težina:</strong> {detalj.tezina}</p>
            <p><strong>Vreme pripreme:</strong> {detalj.vreme_pripreme} min</p>

            <h5 className="mt-3">Sastojci:</h5>
            <ul>
              {detalj.sastojci?.map((s, i) => (
                <li key={i}>{s.ime} — {s.kolicina}</li>
              ))}
            </ul>

            <div className="d-flex justify-content-end gap-2 mt-4">
              <button className="btn btn-secondary" onClick={zatvoriDetalj}>Zatvori</button>
            </div>
          </div>
        </div>
      )}

      {/* DODAVANJE U LISTU ZA KUPOVINU */}
      {showKupovinaModal && (
        <div className="modal-overlay">
          <div className="modal-box">
            <h3>Dodaj stavku u kupovinu</h3>
            <form onSubmit={(e) => { e.preventDefault(); dodajUListuZaKupovinu(); }}>
              <input 
                type="text" 
                placeholder="Namirnica" 
                value={kupovinaNamirnica.ime} 
                onChange={(e) => setKupovinaNamirnica({ ...kupovinaNamirnica, ime: e.target.value })}
              />
              <input 
                type="text" 
                placeholder="Količina" 
                value={kupovinaNamirnica.kolicina}
                onChange={(e) => setKupovinaNamirnica({ ...kupovinaNamirnica, kolicina: e.target.value })}
              />
              <div className="modal-actions">
                <button type="submit" className="button-main">Dodaj</button>
                <button type="button" className="button-main" onClick={() => setShowKupovinaModal(false)}>Zatvori</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* LISTA ZA KUPOVINU */}
      {showListaModal && (
        <div className="modal-overlay">
          <div className="modal-box">
            <h3>Lista za kupovinu</h3>
            {kupovina.length === 0 ? (
              <p>Lista je prazna.</p>
            ) : (
              <ul>
          {kupovina.map((item) => (
            <li key={item.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>{item.ime} — {item.kolicina}</span>
              <button 
                className="btn btn-sm btn-danger"
                onClick={() => izbaciIzKupovine(item.id)}
              >
                ❌
              </button>
            </li>
          ))}
            </ul>
                )}
                <div className="modal-actions">
                  <button type="button" className="button-main" onClick={() => setShowListaModal(false)}>Zatvori</button>
                </div>
          </div>
        </div>
      )}
    </div>
  </div>
  );
}

export default App;
