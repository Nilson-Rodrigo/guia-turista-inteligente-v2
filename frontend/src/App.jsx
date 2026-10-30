import { useEffect, useRef, useState } from "react";
import { api, streamGuia } from "./services/api";
import { getCurrentPosition, haversineKm } from "./services/geolocation";
import RoteiroForm, { initialForm } from "./components/RoteiroForm";
import MapaRota from "./components/MapaRota";
import MarkdownContent from "./components/MarkdownContent";
import { useNetworkStatus } from "./hooks/useNetworkStatus";
const ROOT = "/api/v1/roteiros";
const money = (n) =>
  Number(n).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
export default function App() {
  const [user, setUser] = useState(null),
    [form, setForm] = useState(initialForm),
    [history, setHistory] = useState([]),
    [selected, setSelected] = useState(null),
    [mapa, setMapa] = useState(null),
    [cost, setCost] = useState(null),
    [guia, setGuia] = useState(""),
    [loading, setLoading] = useState(false),
    [guideLoading, setGuideLoading] = useState(false),
    [error, setError] = useState(""),
    [destinos, setDestinos] = useState([]),
    [suggestions, setSuggestions] = useState([]),
    [tele, setTele] = useState(null),
    [dark, setDark] = useState(localStorage.getItem("theme") === "dark"),
    [saved, setSaved] = useState(null),
    [remaining, setRemaining] = useState(0);
  const googleButton = useRef(null),
    streamController = useRef(null),
    online = useNetworkStatus();
  const [routes, setRoutes] = useState([]),
    [routeIndex, setRouteIndex] = useState(0),
    [vehicle, setVehicle] = useState(initialForm);
  function clear() {
    streamController.current?.abort();
    setError("");
    setHistory([]);
    setSelected(null);
    setMapa(null);
    setCost(null);
    setGuia("");
  }
  function activate(u) {
    clear();
    setUser(u);
    localStorage.setItem("guia_user", JSON.stringify(u));
  }
  async function loadHistory(u = user) {
    if (u) setHistory(await api(ROOT, { user: u }));
  }
  async function visitor() {
    setError("");
    try {
      const r = await api("/api/v1/auth/demo", { method: "POST" });
      activate({ ...r.usuario, expiresAt: Date.now() + r.expires_in * 1000 });
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }
  useEffect(() => {
    let cancelled = false;
    try {
      const stored = JSON.parse(localStorage.getItem("guia_user") || "null");
      setSaved(JSON.parse(localStorage.getItem("guia_google") || "null"));
      if (stored)
        api("/api/v1/auth/me", { user: stored })
          .then(() => {
            if (!cancelled) setUser(stored);
          })
          .catch(() => localStorage.removeItem("guia_user"));
    } catch {
      localStorage.removeItem("guia_user");
    }
    return () => {
      cancelled = true;
      streamController.current?.abort();
    };
  }, []);
  useEffect(() => {
    if (!user) return;
    loadHistory(user).catch((e) => setError(e.message));
    api(ROOT + "/destinos", { user })
      .then(setDestinos)
      .catch((e) => setError(e.message));
  }, [user]);
  useEffect(() => {
    if (!user?.visitante) return;
    const update = () => {
      const delta = (user.expiresAt || 0) - Date.now();
      setRemaining(Math.max(0, delta));
      if (delta <= 0) {
        clear();
        setUser(null);
        localStorage.removeItem("guia_user");
        setError("Sessão visitante expirada. Entre novamente.");
      }
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, [user]);
  useEffect(() => {
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);
  useEffect(() => {
    const id = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!id) return;
    let disposed = false;
    const setup = () => {
      if (disposed || !googleButton.current) return;
      window.google.accounts.id.initialize({
        client_id: id,
        callback: async ({ credential }) => {
          try {
            const r = await api("/api/v1/auth/google", {
              method: "POST",
              body: { credential },
            });
            localStorage.setItem("guia_google", JSON.stringify(r.usuario));
            setSaved(r.usuario);
            activate(r.usuario);
          } catch (e) {
            setError(e.message);
          }
        },
      });
      window.google.accounts.id.renderButton(googleButton.current, {
        theme: "outline",
        size: "large",
      });
    };
    if (window.google?.accounts) setup();
    else {
      let script = document.getElementById("google-identity");
      if (!script) {
        script = document.createElement("script");
        script.id = "google-identity";
        script.src = "https://accounts.google.com/gsi/client";
        script.async = true;
        document.head.appendChild(script);
      }
      script.addEventListener("load", setup);
      return () => {
        disposed = true;
        script.removeEventListener("load", setup);
      };
    }
    return () => {
      disposed = true;
    };
  }, [user]);
  async function gps() {
    setError("");
    try {
      const position = await getCurrentPosition();
      const items = destinos
        .map((d) => ({ ...d, distance: haversineKm(position, d) }))
        .filter((d) => d.distance > 400)
        .sort((a, b) => a.distance - b.distance)
        .slice(0, 4);
      setSuggestions(items);
      if (!items.length)
        setError("Nenhum destino do catálogo atende ao filtro.");
      else setError("");
    } catch (e) {
      setError(e.message);
    }
  }
  async function applyRoute(route, v) {
    if (route.altimetria?.pendente) {
      route = {
        ...route,
        altimetria: await api(ROOT + "/altimetria", {
          method: "POST",
          user,
          body: { geometria: route.geometria },
        }),
      };
    }
    setMapa(route);
    if (!route.distancia_km) {
      setCost(null);
      return;
    }
    const c = await api(ROOT + "/custos", {
      method: "POST",
      user,
      body: {
        ...v,
        distancia_km: route.distancia_km,
        penalizacao_percentual:
          route.altimetria?.penalizacao_consumo_percentual || 0,
      },
    });
    setCost(c);
    const interval = c.autonomia_por_carga * 0.82,
      paradas = [];
    for (let km = interval; km < route.distancia_km; km += interval)
      paradas.push({ progresso_km: Math.round(km) });
    setMapa({ ...route, paradas });
  }
  async function showTrip(trip, v = vehicle) {
    setError("");
    streamController.current?.abort();
    setGuia("");
    setSelected(trip);
    setCost(null);
    setMapa(null);
    const data = await api(ROOT + "/mapa-rota", {
      method: "POST",
      user,
      body: {
        origem_latitude: trip.origem_coordenadas[0],
        origem_longitude: trip.origem_coordenadas[1],
        destino_latitude: trip.destino_coordenadas[0],
        destino_longitude: trip.destino_coordenadas[1],
        autonomia_km:
          v.propulsao === "eletrico"
            ? v.capacidade_bateria * v.eficiencia_kwh
            : v.capacidade_tanque * v.consumo_medio,
      },
    });
    const all = [
      data,
      ...data.rotas_alternativas.map((r) => ({
        ...r,
        altimetria: { disponivel: false, pendente: true },
        paradas: [],
      })),
    ];
    setRoutes(all);
    setRouteIndex(0);
    await applyRoute(data, v);
    setError("");
  }
  async function submit(e) {
    e.preventDefault();
    if (loading) return;
    setLoading(true);
    setError("");
    const start = performance.now();
    try {
      setVehicle({ ...form });
      const response = await api(ROOT + "/planejar", {
        method: "POST",
        user,
        body: form,
        raw: true,
      });
      const trip = await response.json();
      await showTrip(trip, form);
      await loadHistory();
      const stats = await api("/api/v1/telemetria/resumo", { user });
      setTele({
        ...stats,
        latency: response.headers.get("X-Process-Time"),
        requestId: response.headers.get("X-Request-ID"),
        total: Math.round(performance.now() - start),
      });
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }
  async function guide() {
    setError("");
    streamController.current?.abort();
    const controller = new AbortController();
    streamController.current = controller;
    setGuia("");
    setGuideLoading(true);
    try {
      await streamGuia(
        {
          destino: selected.destino,
          dias_estadia: selected.dias_estadia,
          estilo_viagem: selected.estilo_viagem,
          clima_info: selected.clima,
          atrativos: selected.atrativos,
          gastronomia: selected.gastronomia,
        },
        user,
        (c) => setGuia((t) => t + c),
        controller.signal,
      );
    } catch (e) {
      if (e.name !== "AbortError") setError(e.message);
      else setError("");
    } finally {
      if (streamController.current === controller) setGuideLoading(false);
    }
  }
  async function visited(id) {
    setError("");
    try {
      const visits = selected.visitas.includes(id)
        ? selected.visitas.filter((v) => v !== id)
        : [...selected.visitas, id];
      const trip = await api(ROOT + "/" + selected.id + "/visitas", {
        method: "PATCH",
        user,
        body: { visitas: visits },
      });
      setSelected(trip);
      await loadHistory();
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }
  async function gpx() {
    setError("");
    try {
      const r = await api(ROOT + "/exportar/gpx", {
        method: "POST",
        user,
        body: { ...selected, geometria: mapa.geometria },
        raw: true,
      });
      const url = URL.createObjectURL(await r.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = "roteiro.gpx";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError(e.message);
    }
  }
  async function share() {
    setError("");
    try {
      const r = await api(ROOT + "/compartilhar", {
        method: "POST",
        user,
        body: { canal: "whatsapp", roteiro: selected },
      });
      window.open(r.link, "_blank", "noopener,noreferrer");
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }
  async function restore() {
    try {
      await api("/api/v1/auth/me", { user: saved });
      activate(saved);
    } catch {
      setError("Entre novamente com o Google para restaurar a conta.");
    }
  }
  async function logout() {
    try {
      await api("/api/v1/auth/logout", { method: "POST", user });
    } catch {}
    clear();
    setUser(null);
    setSaved(null);
    localStorage.removeItem("guia_user");
    localStorage.removeItem("guia_google");
  }
  return (
    <main className={dark ? "app dark" : "app"}>
      <header className="topbar">
        <h1>Guia do Turista</h1>
        <button onClick={() => setDark(!dark)} aria-label="Alternar tema">
          {dark ? "Tema claro" : "Tema escuro"}
        </button>
        {user && (
          <>
            <span>
              {user.nome}{" "}
              {user.visitante && `· ${Math.ceil(remaining / 60000)} min`}
            </span>
            {!user.visitante && (
              <button onClick={visitor}>Usar como visitante</button>
            )}
            {user.visitante && saved && (
              <button onClick={restore}>Voltar para {saved.nome}</button>
            )}
            <button onClick={logout}>Sair</button>
          </>
        )}
        <div ref={googleButton} />
      </header>
      {error && (
        <p role="alert" className="error">
          {error}
          <button onClick={() => setError("")}>Fechar</button>
        </p>
      )}
      {!online && <p role="status">Você está offline.</p>}
      {!user ? (
        <section className="hero">
          <h2>Explore o Brasil com um roteiro seu.</h2>
          <p>Mapas, clima, custos e um guia para a viagem.</p>
          <button className="primary-button" onClick={visitor}>
            Entrar como visitante
          </button>
          {!import.meta.env.VITE_GOOGLE_CLIENT_ID && (
            <p>Login Google disponível após configurar o Client ID.</p>
          )}
        </section>
      ) : (
        <>
          <section className="hero">
            <h2>Seu próximo destino começa aqui.</h2>
            <p>Planeje a rota e confirme as condições antes de viajar.</p>
          </section>
          <RoteiroForm
            form={form}
            setForm={setForm}
            loading={loading}
            onSubmit={submit}
            onGPS={gps}
            sugestoes={destinos}
          />
          {suggestions.length > 0 && (
            <section className="panel">
              <h2>Destinos sugeridos</h2>
              {suggestions.map((d) => (
                <button
                  key={d.cidade}
                  onClick={() =>
                    setForm({
                      ...form,
                      destino_cidade: d.cidade,
                      destino_uf: d.uf,
                    })
                  }
                >
                  {d.cidade} / {d.uf} · {Math.round(d.distance)} km em linha
                  reta
                </button>
              ))}
            </section>
          )}
          {tele && (
            <section className="panel" aria-label="Telemetria">
              <h2>Telemetria</h2>
              <p>
                API: {tele.latency} · Total da operação: {tele.total} ms ·
                Viagens salvas: {tele.roteiros_gerados} · Requisições ativas:{" "}
                {tele.conexoes_ativas}
              </p>
              <p>ID: {tele.requestId}</p>
              <p>
                {Object.entries(tele.circuitos || {})
                  .map(([n, s]) => `${n}: ${s}`)
                  .join(" · ")}
                . Circuito fechado não confirma disponibilidade em tempo real.
              </p>
            </section>
          )}
          {selected && (
            <section className="panel">
              <h2>
                {selected.origem} → {selected.destino}
              </h2>
              <p>
                🌡 {selected.clima.temperatura} · Sensação{" "}
                {selected.clima.sensacao || "N/D"} · Vento{" "}
                {selected.clima.vento}
              </p>
              {routes.length > 1 && (
                <label>
                  Rota
                  <select
                    value={routeIndex}
                    onChange={async (e) => {
                      const index = Number(e.target.value);
                      setRouteIndex(index);
                      try {
                        await applyRoute(routes[index], vehicle);
                        setError("");
                      } catch (err) {
                        setError(err.message);
                      }
                    }}
                  >
                    {routes.map((r, i) => (
                      <option key={i} value={i}>
                        Sugestão {i + 1}: {r.distancia_km} km ·{" "}
                        {r.duracao_minutos} min
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <MapaRota rota={mapa} />
              {cost && (
                <div className="metrics">
                  <span>Total {money(cost.custo_total)}</span>
                  <span>Por pessoa {money(cost.custo_por_passageiro)}</span>
                  <span>Autonomia {cost.autonomia_por_carga} km</span>
                  <span>Distância {mapa.distancia_km} km</span>
                </div>
              )}
              <p>
                Paradas são projeções com reserva de 18%; não representam postos
                verificados.
              </p>
              <details>
                <summary>Topografia e relevo</summary>
                {mapa?.altimetria?.disponivel ? (
                  <>
                    <p>
                      Subidas: {mapa.altimetria.ganho_subida_m} m · Descidas:{" "}
                      {mapa.altimetria.perda_descida_m} m · Máxima:{" "}
                      {mapa.altimetria.altitude_maxima_m} m · Desnível líquido:{" "}
                      {mapa.altimetria.desnivel_liquido_m} m
                    </p>
                    <p>
                      Ajuste estimado no consumo: +
                      {mapa.altimetria.penalizacao_consumo_percentual}%
                    </p>
                    <svg
                      viewBox="0 0 500 100"
                      role="img"
                      aria-label="Perfil de elevação"
                    >
                      <polyline
                        fill="none"
                        stroke="#df5e35"
                        strokeWidth="3"
                        points={(mapa.altimetria.elevacoes_m || [])
                          .map(
                            (v, i, a) =>
                              `${(i * 500) / Math.max(1, a.length - 1)},${95 - ((v - Math.min(...a)) * 85) / Math.max(1, Math.max(...a) - Math.min(...a))}`,
                          )
                          .join(" ")}
                      />
                    </svg>
                  </>
                ) : (
                  <p>
                    Dados indisponíveis para esta rota; cálculo sem ajuste de
                    relevo.
                  </p>
                )}
              </details>
              <div className="actions">
                <button disabled={!mapa?.geometria?.length} onClick={gpx}>
                  Baixar GPX
                </button>
                <button onClick={share}>Compartilhar WhatsApp</button>
                <a
                  target="_blank"
                  rel="noreferrer"
                  href={
                    "https://www.google.com/maps/dir/?api=1&origin=" +
                    encodeURIComponent(selected.origem) +
                    "&destination=" +
                    encodeURIComponent(selected.destino) +
                    "&travelmode=driving"
                  }
                >
                  Abrir no Google Maps
                </a>
                <button disabled={guideLoading} onClick={guide}>
                  {guideLoading ? "Gerando…" : "Gerar guia com IA"}
                </button>
              </div>
              <article
                className="guide-panel"
                aria-live="polite"
              >
                <MarkdownContent>{guia}</MarkdownContent>
              </article>
              <h3>Atrativos</h3>
              {selected.atrativos.length ? (
                selected.atrativos.map((a) => (
                  <label key={a.id}>
                    <input
                      type="checkbox"
                      checked={selected.visitas.includes(a.id)}
                      onChange={() => visited(a.id)}
                    />
                    {a.nome}
                  </label>
                ))
              ) : (
                <p>Destino sem atrativos no catálogo local.</p>
              )}
              <h3>Gastronomia</h3>
              <p>
                {selected.gastronomia.join(" · ") ||
                  "Destino sem gastronomia no catálogo local."}
              </p>
            </section>
          )}
          <section className="panel">
            <h2>Viagens salvas</h2>
            {!history.length && <p>Nenhuma viagem salva.</p>}
            {history.map((t) => (
              <article className="route-card" key={t.id}>
                <span>
                  {t.origem} → {t.destino}
                </span>
                <button
                  disabled={loading}
                  onClick={async () => {
                    setLoading(true);
                    try {
                      await showTrip(t);
                    } catch (e) {
                      setError(e.message);
                    } finally {
                      setLoading(false);
                    }
                  }}
                >
                  Abrir
                </button>
                <button
                  onClick={async () => {
                    try {
                      await api(ROOT + "/" + t.id, { method: "DELETE", user });
                      if (selected?.id === t.id) {
                        setSelected(null);
                        streamController.current?.abort();
                      }
                      await loadHistory();
                    } catch (e) {
                      setError(e.message);
                    }
                  }}
                >
                  Excluir
                </button>
              </article>
            ))}
          </section>
        </>
      )}
      <footer>
        Projeto acadêmico · FastAPI + React · Dados e custos sujeitos a
        confirmação.
      </footer>
    </main>
  );
}
