export const initialForm = {
  origem_cidade: "",
  origem_uf: "PI",
  destino_cidade: "",
  destino_uf: "PI",
  dias_estadia: 2,
  estilo_viagem: "Cultural",
  propulsao: "combustao",
  consumo_medio: 12,
  capacidade_tanque: 50,
  preco_combustivel: 6,
  eficiencia_kwh: 6,
  capacidade_bateria: 60,
  preco_kwh: 1,
  pedagios: 0,
  passageiros: 1,
};
export default function RoteiroForm({
  form,
  setForm,
  loading,
  onSubmit,
  sugestoes = [],
  onGPS,
}) {
  const change = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const number = (key, label, min = 0.01, max = 10000) => (
    <label key={key}>
      {label}
      <input
        type="number"
        min={min}
        max={max}
        step={key === "passageiros" || key === "dias_estadia" ? 1 : 0.01}
        required
        value={form[key]}
        onChange={(e) => change(key, Number(e.target.value))}
      />
    </label>
  );
  return (
    <form className="planner" onSubmit={onSubmit}>
      <h2>Planejar viagem</h2>
      <div className="form-grid">
        {["origem", "destino"].map((tipo) => (
          <div className="form-grid" key={tipo}>
            <label>
              {tipo === "origem" ? "Origem" : "Destino"}
              <input
                list="cidades"
                required
                value={form[tipo + "_cidade"]}
                onChange={(e) => change(tipo + "_cidade", e.target.value)}
              />
            </label>
            <label>
              UF
              <select
                value={form[tipo + "_uf"]}
                onChange={(e) => change(tipo + "_uf", e.target.value)}
              >
                {"AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO"
                  .split(" ")
                  .map((u) => (
                    <option key={u}>{u}</option>
                  ))}
              </select>
            </label>
          </div>
        ))}
        <datalist id="cidades">
          {sugestoes.map((d) => (
            <option key={d.cidade + d.uf} value={d.cidade}>
              {d.uf}
            </option>
          ))}
        </datalist>
        {number("dias_estadia", "Dias de viagem", 1, 5)}
        <label>
          Perfil
          <select
            value={form.estilo_viagem}
            onChange={(e) => change("estilo_viagem", e.target.value)}
          >
            {[
              "Cultural",
              "Gastronômico",
              "Ecoturismo / Aventura",
              "Família",
              "Romântico / Econômico",
            ].map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
        </label>
        <label>
          Veículo
          <select
            value={form.propulsao}
            onChange={(e) => change("propulsao", e.target.value)}
          >
            <option value="combustao">Combustão</option>
            <option value="eletrico">100% elétrico</option>
          </select>
        </label>
        {form.propulsao === "combustao" ? (
          <>
            {number("consumo_medio", "Consumo (km/l)")}
            {number("capacidade_tanque", "Tanque (litros)")}
            {number("preco_combustivel", "Preço por litro (R$)")}
          </>
        ) : (
          <>
            {number("eficiencia_kwh", "Eficiência (km/kWh)")}
            {number("capacidade_bateria", "Bateria (kWh)")}
            {number("preco_kwh", "Preço por kWh (R$)")}
          </>
        )}
        {number("passageiros", "Passageiros", 1, 8)}
        {number("pedagios", "Pedágios estimados (R$)", 0)}
      </div>
      <p>Pedágios informados por você; valores de viagem são estimativas.</p>
      <button type="button" onClick={onGPS}>
        Usar GPS para sugerir destinos acima de 400 km
      </button>
      <button className="primary-button" disabled={loading}>
        {loading ? "Planejando…" : "Gerar roteiro"}
      </button>
    </form>
  );
}
