import { useEffect, useState } from "react";
import { ArrowRight, Compass, MapPin, Moon, Plus, Sun, Trash2, UserRound } from "lucide-react";
import { calcularCustos, deletarRoteiro, listarRoteiros, loginDemo, obterMapaRota, planejar, streamGuia } from "./services/api";
import MapaRota from "./components/MapaRota.jsx";
import Toast from "./components/Toast.jsx";
import { useNetworkStatus } from "./hooks/useNetworkStatus";
import { useSessionTimer } from "./hooks/useSessionTimer";

const initialForm = { origem_cidade: "", origem_uf: "", destino_cidade: "", destino_uf: "", propulsao: "combustao", dias_estadia: 2, estilo_viagem: "Cultural", passageiros: 1, consumo_medio: 12, preco_combustivel: 6, eficiencia_kwh: 6, preco_kwh: 1 };
const ufs = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"];

export default function App() {
  const [user, setUser] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [roteiros, setRoteiros] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dark, setDark] = useState(false);
  const [guia, setGuia] = useState("");
  const [guiaLoading, setGuiaLoading] = useState(false);
  const [custos, setCustos] = useState(null);
  const [mapa, setMapa] = useState(null);
  const online = useNetworkStatus();
  const sessionTime = useSessionTimer(user);
  const [toast, setToast] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("guia_user");
    if (saved) setUser(JSON.parse(saved));
  }, []);

  useEffect(() => {
    if (user) listarRoteiros(user.id).then(setRoteiros).catch(() => setRoteiros([]));
  }, [user]);

  async function enterDemo() {
    setError("");
    try {
      const response = await loginDemo();
      setUser(response.usuario);
      localStorage.setItem("guia_user", JSON.stringify(response.usuario));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const roteiro = await planejar(form, user.id);
      setRoteiros((current) => [roteiro, ...current]);
      setToast("Roteiro criado com sucesso.");
      const distancia = Number.parseFloat(roteiro.percurso.distancia);
      if (Number.isFinite(distancia)) {
        const custo = await calcularCustos({
          distancia_km: distancia,
          propulsao: form.propulsao,
          passageiros: Number(form.passageiros),
          consumo_medio: Number(form.consumo_medio),
          preco_combustivel: Number(form.preco_combustivel),
          eficiencia_kwh: Number(form.eficiencia_kwh),
          preco_kwh: Number(form.preco_kwh),
        });
        setCustos(custo);
      }
      const mapaRota = await obterMapaRota({
        origem_latitude: roteiro.origem_coordenadas[0],
        origem_longitude: roteiro.origem_coordenadas[1],
        destino_latitude: roteiro.destino_coordenadas[0],
        destino_longitude: roteiro.destino_coordenadas[1],
        autonomia_km: form.propulsao === "eletrico" ? 360 : 600,
      });
      setMapa(mapaRota);
      setForm(initialForm);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
      window.setTimeout(() => setToast(""), 3000);
    }
  }

  async function remove(id) {
    await deletarRoteiro(id, user.id);
    setRoteiros((current) => current.filter((roteiro) => roteiro.id !== id));
  }

  async function generateGuide(destino) {
    setGuia("");
    setGuiaLoading(true);
    setError("");
    try {
      await streamGuia(destino, user.id, (chunk) => setGuia((current) => `${current}${chunk} `));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setGuiaLoading(false);
    }
  }

  if (!user) {
    return <main className="login-page"><div className="login-panel"><span className="eyebrow">BRASIL · API ASSÍNCRONA</span><h1>Planeje uma viagem que começa antes da estrada.</h1><p>Rotas, clima e contexto local reunidos em uma experiência simples.</p><button className="primary-button" onClick={enterDemo}><UserRound size={18} /> Entrar como visitante</button>{error && <p className="error">{error}</p>}</div></main>;
  }

  return <main className={dark ? "app dark" : "app"}>
    <Toast message={toast || (!online ? "Você está offline. Algumas consultas podem falhar." : "")} type={toast ? "success" : "info"} />
    <header className="topbar"><div className="brand"><Compass size={23} /><span>Guia do Turista</span></div><div className="top-actions"><button className="icon-button" title="Alternar tema" onClick={() => setDark(!dark)}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button><span className="user-pill"><UserRound size={15} /> {user.nome}</span>{sessionTime && <span className="session-pill" title="Tempo restante da sessão visitante">{sessionTime}</span>}</div></header>
    <section className="hero"><div><span className="eyebrow">ROTEIRO {String(roteiros.length + 1).padStart(2, "0")}</span><h1>O Brasil fica maior quando você sabe onde parar.</h1><p>Escolha uma origem e um destino. Nós cuidamos da rota, do clima e do primeiro mapa mental da viagem.</p></div><div className="hero-mark"><MapPin size={42} /><span>explore<br />mais perto</span></div></section>
    <section className="workspace"><form className="planner" onSubmit={submit}><div className="section-heading"><div><span className="eyebrow">PLANEJADOR</span><h2>Trace o próximo capítulo</h2></div><span className="step-badge">01 / 01</span></div><div className="route-fields"><label>Origem<input required value={form.origem_cidade} onChange={(e) => setForm({ ...form, origem_cidade: e.target.value })} placeholder="Recife" /></label><label>UF<select required value={form.origem_uf} onChange={(e) => setForm({ ...form, origem_uf: e.target.value })}><option value="">--</option>{ufs.map((uf) => <option key={uf}>{uf}</option>)}</select></label><ArrowRight className="route-arrow" size={20} /><label>Destino<input required value={form.destino_cidade} onChange={(e) => setForm({ ...form, destino_cidade: e.target.value })} placeholder="Salvador" /></label><label>UF<select required value={form.destino_uf} onChange={(e) => setForm({ ...form, destino_uf: e.target.value })}><option value="">--</option>{ufs.map((uf) => <option key={uf}>{uf}</option>)}</select></label></div><button className="primary-button" disabled={loading}>{loading ? "Consultando provedores..." : <><Plus size={18} /> Gerar roteiro</>}</button>{error && <p className="error">{error}</p>}</form><aside className="aside-note"><span className="eyebrow">SINAL ABERTO</span><h3>Uma rota boa deixa espaço para o inesperado.</h3><p>Os dados vêm de provedores geográficos e meteorológicos consultados em paralelo.</p></aside></section>
    <section className="history"><div className="section-heading"><div><span className="eyebrow">HISTÓRICO</span><h2>Suas rotas salvas</h2></div><span className="count">{roteiros.length} roteiros</span></div>{mapa && <MapaRota rota={mapa} />}{roteiros.length === 0 ? <div className="empty"><Compass size={28} /><p>Seu mapa ainda está em branco.</p></div> : <div className="route-list">{roteiros.map((roteiro) => <article className="route-card" key={roteiro.id}><div className="route-title"><strong>{roteiro.origem}</strong><ArrowRight size={17} /><strong>{roteiro.destino}</strong></div><div className="metrics"><span>🌡 {roteiro.clima.temperatura}</span><span>💧 {roteiro.clima.umidade}</span><span>🚗 {roteiro.percurso.distancia}</span><span>◷ {roteiro.percurso.tempo}</span></div><div className="card-actions"><button className="guide-button" onClick={() => generateGuide(roteiro.destino)}>{guiaLoading ? "Gerando guia..." : "Abrir guia em streaming"}</button><button className="delete-button" title="Excluir roteiro" onClick={() => remove(roteiro.id)}><Trash2 size={16} /></button></div></article>)}</div>}{guia && <article className="guide-panel"><span className="eyebrow">GUIA DO VIAJANTE · SSE</span><p>{guia}</p></article>}</section>
  </main>;
}
