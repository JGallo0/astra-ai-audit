import { useState, useContext, useEffect } from 'react'
import axios from 'axios'
import { AppCtx } from '../../App'

const NAVY  = '#1A3160'
const GREEN = '#16A34A'
const AMBER = '#B45309'
const RED   = '#DC2626'
const GRAY  = '#6B7280'

const METHOD_LABELS = {
  isometric:  'Isometric v1.2',
  puro_earth: 'Puro.Earth 2025',
  verra_vcs:  'Verra VM0044',
}
const METHOD_COLORS = {
  isometric:  '#1D4ED8',
  puro_earth: '#16A34A',
  verra_vcs:  '#D97706',
}

const LINE_ITEMS = [
  { key: 'gross_co2',         label: 'Remoção bruta (tCO₂)',    bold: false, sign: 1  },
  { key: 'e_sourcing',        label: '− Sourcing biomassa',      bold: false, sign: -1 },
  { key: 'e_processing',      label: '− Processamento',          bold: false, sign: -1 },
  { key: 'e_infrastructure',  label: '− Infraestrutura (amort.)',bold: false, sign: -1 },
  { key: 'e_biochar_use',     label: '− Transporte/aplicação',   bold: false, sign: -1 },
  { key: 'e_counter_leakage', label: '− Counterfactual/leakage', bold: false, sign: -1 },
  { key: 'buffer_pool',       label: '− Buffer pool',            bold: false, sign: -1 },
  { key: 'net_co2_year',      label: 'Net CO₂ (tCO₂/ano)',       bold: true,  sign: 1  },
]

function NumberInput({ label, value, onChange, unit, min, max, step, hint }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <label style={{ fontSize: 12, fontWeight: 600 }}>{label}</label>
        {unit && <span style={{ fontSize: 11, color: GRAY }}>{unit}</span>}
      </div>
      {hint && <div style={{ fontSize: 11, color: GRAY, marginBottom: 3 }}>{hint}</div>}
      <input type="number" value={value} min={min} max={max} step={step}
        onChange={e => onChange(parseFloat(e.target.value) || 0)}
        style={{ width: '100%', padding: '6px 9px', fontSize: 13,
                 border: '1px solid var(--border)', borderRadius: 6 }}
      />
    </div>
  )
}

export default function CreditVolumeTab({ project }) {
  const { API } = useContext(AppCtx)

  const [inputs, setInputs] = useState({
    biochar_t_dry_year:     1000,
    carbon_fraction:        0.75,
    h_c_ratio:              0.35,
    o_c_ratio:              0.15,
    mast_celsius:           20.0,
    pyrolysis_temp_celsius: 550,
    transport_km_feedstock: 30,
    transport_km_biochar:   50,
    energy_kwh_t_biochar:   174,
    capex_usd:              1000000,
    project_life_years:     20,
  })
  const [methodologies, setMethodologies] = useState(['isometric', 'puro_earth', 'verra_vcs'])
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  // Tenta pré-carregar da Viabilidade
  useEffect(() => {
    axios.get(`${API}/api/projects/${project.id}/viabilidade`).then(r => {
      const p = r.data.premissas
      const res = r.data.resultado
      if (p) {
        const biochar = (p.feedstock_t_ano || 5000) * (p.yield_pirolise || 0.28)
        const capex_usd = (p.capex_total || 5500000) / (p.fx_rate || 5.70)
        setInputs(prev => ({
          ...prev,
          biochar_t_dry_year: Math.round(biochar),
          capex_usd: Math.round(capex_usd),
          project_life_years: p.horizonte_anos || 20,
        }))
      }
      // MAST do Copernicus
      const climate = res?.climate_validation
      if (climate?.temperature?.c3s_temp) {
        setInputs(prev => ({ ...prev, mast_celsius: parseFloat(climate.temperature.c3s_temp.toFixed(1)) }))
      }
    }).catch(() => {})
  }, [project.id])

  const setField = (key, val) => setInputs(prev => ({ ...prev, [key]: val }))

  async function calculate() {
    setLoading(true); setError('')
    try {
      const r = await axios.post(`${API}/api/projects/${project.id}/credit-volume`, {
        ...inputs, methodologies,
      })
      setResult(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro no cálculo.')
    } finally {
      setLoading(false)
    }
  }

  const methods = methodologies.filter(m => result?.results?.[m])

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 16 }}>

        {/* Inputs */}
        <div>
          <div className="card" style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: GRAY, textTransform: 'uppercase',
                          letterSpacing: 1, marginBottom: 12 }}>Produção do Biochar</div>
            <NumberInput label="Biochar seco produzido" value={inputs.biochar_t_dry_year}
              onChange={v => setField('biochar_t_dry_year', v)} unit="t/ano" min={0} step={10} />
            <NumberInput label="Fração de carbono" value={inputs.carbon_fraction}
              onChange={v => setField('carbon_fraction', v)} unit="ex: 0.75 = 75%"
              min={0.4} max={1} step={0.01}
              hint="Medição laboratorial — C total / massa seca biochar" />
            <NumberInput label="H/Corg molar" value={inputs.h_c_ratio}
              onChange={v => setField('h_c_ratio', v)} unit="< 0.5 elegível" min={0.1} max={0.7} step={0.01}
              hint="Chave para o fator de permanência (Woolf 2021)" />
            <NumberInput label="O/Corg molar" value={inputs.o_c_ratio}
              onChange={v => setField('o_c_ratio', v)} unit="< 0.2 elegível" min={0.05} max={0.4} step={0.01} />
            <NumberInput label="Temp. pirólise" value={inputs.pyrolysis_temp_celsius}
              onChange={v => setField('pyrolysis_temp_celsius', v)} unit="°C" min={300} max={900} step={10}
              hint="Usada pelo modelo Verra (lookup table)" />
          </div>

          <div className="card" style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: GRAY, textTransform: 'uppercase',
                          letterSpacing: 1, marginBottom: 12 }}>Permanência</div>
            <NumberInput label="Temperatura média do solo (MAST)" value={inputs.mast_celsius}
              onChange={v => setField('mast_celsius', v)} unit="°C (Copernicus ERA5)"
              min={-5} max={40} step={0.5}
              hint="Preenchido automaticamente via Copernicus C3S se disponível" />
          </div>

          <div className="card" style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: GRAY, textTransform: 'uppercase',
                          letterSpacing: 1, marginBottom: 12 }}>LCA — Emissões</div>
            <NumberInput label="Distância coleta feedstock" value={inputs.transport_km_feedstock}
              onChange={v => setField('transport_km_feedstock', v)} unit="km" min={0} step={5} />
            <NumberInput label="Energia processamento" value={inputs.energy_kwh_t_biochar}
              onChange={v => setField('energy_kwh_t_biochar', v)} unit="kWh/t biochar" min={0} step={10} />
            <NumberInput label="Distância aplicação biochar" value={inputs.transport_km_biochar}
              onChange={v => setField('transport_km_biochar', v)} unit="km" min={0} step={5} />
            <NumberInput label="CAPEX total" value={inputs.capex_usd}
              onChange={v => setField('capex_usd', v)} unit="USD" min={0} step={10000}
              hint="Para cálculo de emissões embodied de infraestrutura (amortizado)" />
            <NumberInput label="Vida do projeto" value={inputs.project_life_years}
              onChange={v => setField('project_life_years', v)} unit="anos" min={1} max={50} step={1} />
          </div>

          <div className="card" style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: GRAY, textTransform: 'uppercase',
                          letterSpacing: 1, marginBottom: 10 }}>Metodologias</div>
            {Object.entries(METHOD_LABELS).map(([key, label]) => (
              <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 8,
                                        marginBottom: 8, cursor: 'pointer', fontSize: 13 }}>
                <input type="checkbox" checked={methodologies.includes(key)}
                  onChange={e => setMethodologies(prev =>
                    e.target.checked ? [...prev, key] : prev.filter(m => m !== key)
                  )}
                  style={{ accentColor: METHOD_COLORS[key] }}
                />
                <span style={{ color: METHOD_COLORS[key], fontWeight: 600 }}>{label}</span>
              </label>
            ))}
          </div>

          <button className="btn btn-primary" onClick={calculate} disabled={loading}
            style={{ width: '100%', padding: '10px 0', fontSize: 14 }}>
            {loading ? '⟳ Calculando…' : '⚡ Calcular Volume de Créditos'}
          </button>
          {error && <div style={{ marginTop: 8, fontSize: 12, color: RED }}>{error}</div>}
        </div>

        {/* Resultados */}
        <div>
          {result ? (
            <>
              {/* KPIs */}
              <div style={{ display: 'grid', gridTemplateColumns: `repeat(${methods.length}, 1fr)`,
                            gap: 12, marginBottom: 16 }}>
                {methods.map(m => {
                  const r = result.results[m]
                  const isMax = m === result.comparison.max_method
                  const color = METHOD_COLORS[m] || NAVY
                  return (
                    <div key={m} style={{
                      background: 'white', border: `2px solid ${isMax ? color : '#E5E7EB'}`,
                      borderTop: `4px solid ${color}`, borderRadius: 10, padding: '14px 16px',
                    }}>
                      <div style={{ fontSize: 11, color: GRAY, marginBottom: 4 }}>
                        {METHOD_LABELS[m]} {isMax ? '★ Maior volume' : ''}
                      </div>
                      <div style={{ fontSize: 28, fontWeight: 800, color }}>
                        {r.net_co2_year?.toLocaleString('pt-BR')}
                      </div>
                      <div style={{ fontSize: 11, color: GRAY }}>tCO₂/ano</div>
                      <div style={{ marginTop: 8, fontSize: 12 }}>
                        <span style={{ color: GRAY }}>20 anos: </span>
                        <span style={{ fontWeight: 600 }}>{r.net_co2_20yr?.toLocaleString('pt-BR')}</span>
                      </div>
                      <div style={{ fontSize: 11, color: GRAY, marginTop: 4 }}>
                        CORC factor: {r.corc_factor} tCO₂/t | Permanência: {(r.permanence_factor * 100).toFixed(0)}%
                      </div>
                      {!r.includes_infrastructure && (
                        <div style={{ fontSize: 10, color: AMBER, marginTop: 4 }}>
                          ℹ Infraestrutura excluída do LCA (Puro)
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Tabela LCA detalhada */}
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-title" style={{ marginBottom: 12 }}>
                  Breakdown LCA — Anual (tCO₂)
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                    <thead>
                      <tr style={{ background: NAVY, color: 'white' }}>
                        <th style={{ padding: '8px 12px', textAlign: 'left' }}>Componente</th>
                        {methods.map(m => (
                          <th key={m} style={{ padding: '8px 12px', textAlign: 'right',
                                               color: METHOD_COLORS[m] }}>
                            {METHOD_LABELS[m]}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {LINE_ITEMS.map(({ key, label, bold }) => (
                        <tr key={key} style={{
                          background: bold ? '#EEF2FA' : 'white',
                          borderBottom: bold ? `2px solid ${NAVY}` : '1px solid #F3F4F6',
                        }}>
                          <td style={{ padding: '7px 12px', fontWeight: bold ? 700 : 400 }}>{label}</td>
                          {methods.map(m => {
                            const v = result.results[m]?.[key]
                            const isZero = v === 0 || v === -0
                            return (
                              <td key={m} style={{
                                padding: '7px 12px', textAlign: 'right',
                                fontWeight: bold ? 700 : 400,
                                color: bold ? METHOD_COLORS[m]
                                  : isZero ? GRAY
                                  : v > 0 ? '#374151' : AMBER,
                              }}>
                                {v != null ? (isZero ? '—' : v.toLocaleString('pt-BR')) : '—'}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Comparativo */}
              <div className="card">
                <div className="card-title" style={{ marginBottom: 10 }}>Análise Comparativa</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                  {[
                    { label: 'Maior volume', value: METHOD_LABELS[result.comparison.max_method] || '—', color: GREEN },
                    { label: 'Spread entre metodologias', value: `${result.comparison.spread_pct}%`, color: NAVY },
                    { label: 'Média 20 anos', value: result.comparison.cumulative_20yr_average?.toLocaleString('pt-BR') + ' créditos', color: NAVY },
                  ].map(k => (
                    <div key={k.label} style={{ background: '#F9FAFB', borderRadius: 8, padding: '10px 14px' }}>
                      <div style={{ fontSize: 16, fontWeight: 700, color: k.color }}>{k.value}</div>
                      <div style={{ fontSize: 11, color: GRAY, marginTop: 2 }}>{k.label}</div>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: 12, fontSize: 11, color: GRAY, lineHeight: 1.5 }}>
                  ⚠️ Estimativa de triagem baseada em LCA de alto nível (literatura + Ecoinvent).
                  Não substitui LCA completa para emissão de créditos.
                  Calibrado vs. Sylvera Biochar Methodology Assessment (Out 2025).
                </div>
              </div>
            </>
          ) : (
            <div className="card">
              <div className="empty-state">
                <div className="empty-state-icon">📊</div>
                <div className="empty-state-title">Estimativa de Volume de Créditos</div>
                <div className="empty-state-sub" style={{ maxWidth: 400 }}>
                  Calcule quantos créditos de carbono o projeto geraria sob cada metodologia,
                  com breakdown completo do LCA (remoção bruta, emissões, buffer pool).
                  <br /><br />
                  Baseado na abordagem do Sylvera Biochar Methodology Assessment (2025).
                  Os inputs de Produção são preenchidos automaticamente a partir da Viabilidade.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
