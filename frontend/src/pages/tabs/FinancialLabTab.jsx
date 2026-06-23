import { useState, useEffect, useContext, useCallback, useRef } from 'react'
import axios from 'axios'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell, ComposedChart,
  PieChart, Pie,
} from 'recharts'
import { OPEX_DEFAULTS } from './ViabilidadeTab'
import { AppCtx } from '../../App'

const NAVY  = '#1A3160'
const GREEN = '#16A34A'
const RED   = '#DC2626'
const AMBER = '#B45309'

const CURRENCY_SYMBOLS = {
  BRL:'R$', USD:'$', EUR:'€', GBP:'£', CLP:'CLP$', COP:'COP$',
  MXN:'MX$', DKK:'kr', SEK:'kr', NOK:'kr', AUD:'A$', CAD:'C$',
  ZAR:'R', INR:'₹', JPY:'¥',
}

function fmtMoeda(v, currency = 'BRL') {
  if (v == null) return '—'
  const sym = CURRENCY_SYMBOLS[currency] || currency
  const abs = Math.abs(v)
  const neg = v < 0 ? '-' : ''
  if (abs >= 1_000_000) return `${neg}${sym} ${(abs / 1_000_000).toFixed(1)}M`
  if (abs >= 1_000)     return `${neg}${sym} ${(abs / 1_000).toFixed(0)}k`
  return `${neg}${sym} ${Math.round(abs)}`
}
// Alias para compatibilidade interna
const fmtBRL = (v, cur) => fmtMoeda(v, cur)
function fmtPct(v) { return v == null ? '—' : `${Number(v).toFixed(1)}%` }

// ── Slider component ──────────────────────────────────────────────────────────

function Slider({ label, name, value, min, max, step, fmt, onChange }) {
  const pct = max > min ? ((value - min) / (max - min)) * 100 : 0
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 12, color: 'var(--text-2)', fontWeight: 600 }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 700, color: NAVY }}>{fmt ? fmt(value) : value}</span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step}
        value={value}
        onChange={e => onChange(name, parseFloat(e.target.value))}
        style={{ width: '100%', accentColor: NAVY, cursor: 'pointer' }}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-2)' }}>
        <span>{fmt ? fmt(min) : min}</span>
        <span>{fmt ? fmt(max) : max}</span>
      </div>
    </div>
  )
}

// ── Custom tooltip ────────────────────────────────────────────────────────────

function FCLTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 8,
                  padding: '8px 12px', fontSize: 12, boxShadow: '0 2px 8px rgba(0,0,0,.1)' }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.value >= 0 ? GREEN : RED }}>
          {p.name}: {fmtMoeda(p.value)}
        </div>
      ))}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function FinancialLabTab({ project }) {
  const { API } = useContext(AppCtx)
  const [base, setBase]         = useState(null)   // premissas salvas
  const [form, setForm]         = useState(null)   // premissas editáveis (sliders)
  const [resultado, setResultado] = useState(null)
  const [loading, setLoading]   = useState(true)
  const [calculating, setCalculating] = useState(false)
  const debounceRef = useRef(null)

  // Carrega viabilidade salva
  useEffect(() => {
    axios.get(`${API}/api/projects/${project.id}/viabilidade`).then(r => {
      if (r.data.premissas && r.data.resultado) {
        setBase(r.data.premissas)
        setForm(r.data.premissas)
        setResultado(r.data.resultado)
      }
    }).finally(() => setLoading(false))
  }, [project.id])

  // Recalcula com debounce quando form muda
  const recalculate = useCallback(async (premissas) => {
    setCalculating(true)
    try {
      const r = await axios.post(`${API}/api/projects/${project.id}/viabilidade/calculate`, {
        premissas, fonte: 'lab',
      })
      setResultado(r.data.resultado)
    } catch { /* silencioso */ }
    finally { setCalculating(false) }
  }, [project.id, API])

  function setField(name, value) {
    const updated = { ...form, [name]: value }
    setForm(updated)
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => recalculate(updated), 420)
  }

  // ── Loading / sem dados ───────────────────────────────────────────────────
  if (loading) return (
    <div className="card">
      <div className="empty-state">
        <div style={{ fontSize: 32 }}>⟳</div>
        <div className="empty-state-sub">Carregando…</div>
      </div>
    </div>
  )

  if (!form) return (
    <div className="card">
      <div className="empty-state">
        <div className="empty-state-icon">⚗️</div>
        <div className="empty-state-title">Financial Lab</div>
        <div className="empty-state-sub">
          Complete a análise de Viabilidade primeiro para habilitar o laboratório interativo.
        </div>
      </div>
    </div>
  )

  // ── Dados para gráficos ───────────────────────────────────────────────────
  const r      = resultado || {}
  const cur    = r.moeda_projeto || form.moeda_projeto || 'BRL'
  const anos   = r.anos || []
  const fcl    = r.fcl_anual || []
  const acum   = r.fcl_acumulado || []
  const sensi  = r.sensibilidade || []
  const irr    = r.irr
  const wacc_pct = (form.wacc || 0.12) * 100
  const irrColor = irr == null ? 'var(--text-2)' : irr >= wacc_pct ? GREEN : RED

  const fclData = anos.map((ano, i) => ({
    ano: String(ano), fcl: fcl[i] ?? 0, acum: acum[i] ?? 0,
  }))

  const sensiData = sensi.map(s => ({
    price: `$${s.preco_usd}`, irr: s.irr, npv: s.npv_brl,
  }))

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, color: NAVY }}>⚗️ Financial Lab</div>
          <div style={{ fontSize: 12, color: 'var(--text-2)' }}>
            Ajuste os parâmetros — os indicadores atualizam automaticamente
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {calculating && <span style={{ fontSize: 12, color: AMBER }}>⟳ Calculando…</span>}
          <button className="btn btn-sm btn-outline"
            onClick={() => { setForm(base); recalculate(base) }}>
            ↺ Restaurar base
          </button>
          <button className="btn btn-sm btn-outline"
            onClick={() => window.open(`${API}/api/projects/${project.id}/viabilidade/export`, '_blank')}>
            ⬇ Exportar Excel
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 16 }}>

        {/* ── Painel de sliders ─────────────────────────────────────────── */}
        <div>
          <div className="card" style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-2)', marginBottom: 12,
                          textTransform: 'uppercase', letterSpacing: 1 }}>Mercado de Carbono</div>
            <Slider label="Preço do crédito" name="preco_credito_usd"
              value={form.preco_credito_usd} min={30} max={260} step={5}
              fmt={v => `$ ${v}`} onChange={setField} />
            <Slider label={`Câmbio USD → ${cur}`} name="fx_rate"
              value={form.fx_rate} min={0.5} max={10.0} step={0.05}
              fmt={v => v?.toFixed(2) ?? '—'} onChange={setField} />
            <Slider label={`Preço biochar (${CURRENCY_SYMBOLS[cur] || cur}/t)`} name="preco_biochar"
              value={form.preco_biochar} min={0} max={3000} step={50}
              fmt={v => `${CURRENCY_SYMBOLS[cur] || cur}${v}`} onChange={setField} />
          </div>

          <div className="card" style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-2)', marginBottom: 12,
                          textTransform: 'uppercase', letterSpacing: 1 }}>Produção</div>
            <Slider label="Feedstock (t/ano)" name="feedstock_t_ano"
              value={form.feedstock_t_ano} min={100} max={50000} step={100}
              fmt={v => v != null ? `${v.toLocaleString('pt-BR')} t` : '—'} onChange={setField} />
            <Slider label="Rendimento pirólise" name="yield_pirolise"
              value={form.yield_pirolise} min={0.10} max={0.50} step={0.01}
              fmt={v => v != null ? `${(v * 100).toFixed(0)}%` : '—'} onChange={setField} />
            <Slider label="Fator carbono (tCO₂/t)" name="fator_carbono"
              value={form.fator_carbono} min={1.0} max={4.0} step={0.05}
              fmt={v => v?.toFixed(2) ?? '—'} onChange={setField} />
          </div>

          <div className="card">
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-2)', marginBottom: 12,
                          textTransform: 'uppercase', letterSpacing: 1 }}>Custos & Financeiro</div>
            <Slider label="CAPEX total" name="capex_total"
              value={form.capex_total} min={500000} max={30000000} step={100000}
              fmt={v => fmtMoeda(v, cur)} onChange={setField} />
            <Slider label="OPEX anual" name="opex_anual"
              value={form.opex_anual} min={100000} max={10000000} step={50000}
              fmt={v => fmtMoeda(v, cur)} onChange={setField} />
            <Slider label="WACC" name="wacc"
              value={form.wacc} min={0.05} max={0.30} step={0.005}
              fmt={v => v != null ? `${(v * 100).toFixed(1)}%` : '—'} onChange={setField} />
            <Slider label="Alíquota efetiva IR" name="aliquota_efetiva_ir"
              value={form.aliquota_efetiva_ir} min={0} max={0.45} step={0.01}
              fmt={v => v != null ? `${(v * 100).toFixed(0)}%` : '—'} onChange={setField} />
          </div>
        </div>

        {/* ── Painel de resultados ──────────────────────────────────────── */}
        <div>
          {/* KPI row — financeiros */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 10 }}>
            {[
              { label: 'TIR', value: irr != null ? `${irr.toFixed(1)}%` : '—', color: irrColor, sub: `WACC ${wacc_pct.toFixed(0)}%` },
              { label: 'VPL', value: fmtMoeda(r.npv, cur), color: (r.npv || 0) >= 0 ? GREEN : RED },
              { label: 'Payback', value: r.payback_year || 'N/A' },
              { label: 'EBITDA Ano 1', value: fmtMoeda(r.ebitda_yr1, cur), sub: r.margem_ebitda_pct != null ? `${r.margem_ebitda_pct.toFixed(0)}% margem` : '' },
            ].map(k => (
              <div key={k.label} style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 10, padding: '12px 14px' }}>
                <div style={{ fontSize: 20, fontWeight: 800, color: k.color || NAVY }}>{k.value}</div>
                <div style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 2 }}>{k.label}</div>
                {k.sub && <div style={{ fontSize: 10, color: 'var(--text-2)' }}>{k.sub}</div>}
              </div>
            ))}
          </div>

          {/* KPI row — operacionais */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 16 }}>
            {[
              { label: 'Biochar', value: r.biochar_t_ano != null ? `${r.biochar_t_ano.toLocaleString('pt-BR')} t/ano` : '—' },
              { label: 'Créditos gerados', value: r.creditos_tco2_ano != null ? `${r.creditos_tco2_ano.toLocaleString('pt-BR')} tCO₂e` : '—' },
              { label: 'Adicionalidade', value: r.adicionalidade_financeira ? '✓ Confirmada' : '✗ Não confirmada',
                color: r.adicionalidade_financeira ? GREEN : RED,
                sub: r.irr_sem_carbono != null ? `TIR s/carbono: ${r.irr_sem_carbono.toFixed(1)}%` : 'TIR s/carbono: inviável' },
            ].map(k => (
              <div key={k.label} style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 10, padding: '10px 14px' }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: k.color || NAVY }}>{k.value}</div>
                <div style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 2 }}>{k.label}</div>
                {k.sub && <div style={{ fontSize: 10, color: 'var(--text-2)' }}>{k.sub}</div>}
              </div>
            ))}
          </div>

          {/* OPEX Donut */}
          {(() => {
            const breakdown = form.opex_breakdown?.length ? form.opex_breakdown : OPEX_DEFAULTS
            const CAT_COLORS = {
              'Energia':      '#2563EB', 'Mão de Obra': '#16A34A', 'Logística': '#D97706',
              'Manutenção':   '#DC2626', 'Conformidade':'#7C3AED', 'Materiais': '#0891B2',
              'Outros':       '#6B7280',
            }
            // Agrupa por categoria
            const grouped = {}
            breakdown.forEach(item => {
              const cat = item.categoria || 'Outros'
              grouped[cat] = (grouped[cat] || 0) + (parseFloat(item.valor) || 0)
            })
            const pieData = Object.entries(grouped)
              .filter(([, v]) => v > 0)
              .map(([name, value]) => ({ name, value }))
            const total = pieData.reduce((s, d) => s + d.value, 0)

            if (!pieData.length) return null
            return (
              <div className="card" style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 4 }}>
                  Composição do OPEX
                </div>
                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                  <div style={{ flexShrink: 0 }}>
                    <PieChart width={180} height={180}>
                      <Pie data={pieData} cx={85} cy={85} innerRadius={52} outerRadius={80}
                           dataKey="value" paddingAngle={2}>
                        {pieData.map((d, i) => (
                          <Cell key={i} fill={CAT_COLORS[d.name] || '#6B7280'} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v) => [fmtMoeda(v, cur), '']} />
                    </PieChart>
                  </div>
                  <div style={{ flex: 1 }}>
                    {pieData.map(d => (
                      <div key={d.name} style={{ display: 'flex', justifyContent: 'space-between',
                                                  alignItems: 'center', marginBottom: 5 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                          <div style={{ width: 10, height: 10, borderRadius: 2, flexShrink: 0,
                                        background: CAT_COLORS[d.name] || '#6B7280' }} />
                          <span style={{ fontSize: 12 }}>{d.name}</span>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: 12, fontWeight: 600 }}>{fmtMoeda(d.value, cur)}</span>
                          <span style={{ fontSize: 10, color: 'var(--text-2)', marginLeft: 4 }}>
                            {total > 0 ? `${(d.value / total * 100).toFixed(0)}%` : ''}
                          </span>
                        </div>
                      </div>
                    ))}
                    <div style={{ borderTop: '1px solid var(--border)', marginTop: 6, paddingTop: 6,
                                  display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: 12, fontWeight: 700 }}>Total</span>
                      <span style={{ fontSize: 12, fontWeight: 700 }}>{fmtMoeda(total, cur)}</span>
                    </div>
                  </div>
                </div>
              </div>
            )
          })()}

          {/* Tornado */}
          {(r.tornado || []).length > 0 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 4 }}>
                Tornado de Sensibilidade — Impacto na TIR (±20%)
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 10 }}>
                Variação de cada parâmetro em ±20% mantendo os demais fixos. Em pontos percentuais.
              </div>
              <ResponsiveContainer width="100%" height={Math.max(180, r.tornado.length * 34)}>
                <BarChart
                  data={[...r.tornado].reverse()}
                  layout="vertical"
                  margin={{ top: 4, right: 40, left: 120, bottom: 4 }}
                  barCategoryGap="25%"
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F0F0F0" />
                  <XAxis type="number" tickFormatter={v => `${v > 0 ? '+' : ''}${v.toFixed(1)}pp`} tick={{ fontSize: 9 }} />
                  <YAxis type="category" dataKey="param" tick={{ fontSize: 10 }} width={116} />
                  <Tooltip formatter={(v, name) => [`${v > 0 ? '+' : ''}${v.toFixed(2)} pp`, name === 'delta_neg' ? '−20%' : '+20%']} />
                  <ReferenceLine x={0} stroke="#374151" strokeWidth={1.5} />
                  <Bar dataKey="delta_neg" name="−20%" fill={RED} opacity={0.85} radius={[0, 3, 3, 0]} />
                  <Bar dataKey="delta_pos" name="+20%" fill="#2563EB" opacity={0.85} radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Waterfall Ano 1 */}
          {r.receita_bruta_yr1 != null && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 12 }}>
                Waterfall Ano 1 — Da Receita ao FCL
              </div>
              {(() => {
                const rec   = r.receita_bruta_yr1 || 0
                const opex  = -(r.opex_yr1 || 0)
                const ebitda = r.ebitda_yr1 || 0
                const da    = -(r.da_anual || 0)
                const ebit  = r.ebit_yr1 || 0
                const trib  = -(r.trib_yr1 || 0)
                const fcl1  = ebit + (r.da_anual || 0) + trib

                // Waterfall via offset bars: invisible base + visible segment
                const steps = [
                  { name: 'Receita', base: 0,     value: rec,   total: false },
                  { name: '−OPEX',   base: ebitda, value: opex,  total: false },
                  { name: 'EBITDA',  base: 0,     value: ebitda,total: true  },
                  { name: '−DA',     base: ebit,   value: da,    total: false },
                  { name: 'EBIT',    base: 0,     value: ebit,  total: true  },
                  { name: '−IR',     base: ebit + trib, value: trib, total: false },
                  { name: '+DA',     base: ebit + trib, value: r.da_anual || 0, total: false },
                  { name: 'FCL',     base: 0,     value: fcl1,  total: true  },
                ]
                const maxAbs = Math.max(...steps.map(s => Math.abs(s.value) + Math.abs(s.base)))

                return (
                  <ResponsiveContainer width="100%" height={220}>
                    <ComposedChart data={steps} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis tickFormatter={v => fmtMoeda(v, cur)} tick={{ fontSize: 9 }} width={68} />
                      <Tooltip formatter={(v, name) => [fmtMoeda(v, cur), name]} />
                      <ReferenceLine y={0} stroke="#374151" strokeWidth={1} />
                      {/* Invisible base bar */}
                      <Bar dataKey="base" stackId="wf" fill="transparent" />
                      {/* Visible value bar */}
                      <Bar dataKey="value" stackId="wf" radius={[3, 3, 0, 0]}>
                        {steps.map((s, i) => (
                          <Cell key={i}
                            fill={s.total ? NAVY : s.value >= 0 ? GREEN : RED}
                            fillOpacity={s.total ? 1 : 0.85}
                          />
                        ))}
                      </Bar>
                    </ComposedChart>
                  </ResponsiveContainer>
                )
              })()}
            </div>
          )}

          {/* Heat Map TIR */}
          {r.heatmap && r.heatmap.matrix?.length > 1 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 4 }}>
                Heat Map TIR — Preço Carbono × {r.heatmap.fx_label}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 10 }}>
                Verde = TIR ≥ WACC ({wacc_pct.toFixed(0)}%). ✕ = cenário atual.
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ borderCollapse: 'collapse', fontSize: 11, width: '100%' }}>
                  <thead>
                    <tr>
                      <th style={{ padding: '4px 8px', background: '#F1F5F9', fontSize: 10, color: '#6B7280' }}>
                        FX \ $
                      </th>
                      {r.heatmap.prices.map(p => (
                        <th key={p} style={{ padding: '4px 6px', background: '#F1F5F9',
                                             fontWeight: 600, textAlign: 'center', minWidth: 44,
                                             fontSize: 10 }}>
                          {p}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {r.heatmap.matrix.map((row, ri) => (
                      <tr key={ri}>
                        <td style={{ padding: '4px 8px', background: '#F1F5F9',
                                     fontWeight: 600, fontSize: 10, whiteSpace: 'nowrap' }}>
                          {r.heatmap.fx_vals[ri]}
                        </td>
                        {row.map((irr_v, ci) => {
                          const isBase = Math.abs(r.heatmap.fx_vals[ri] - r.heatmap.fx_base) < 0.01 &&
                                         r.heatmap.prices[ci] === r.heatmap.price_base
                          const ok = irr_v != null && irr_v >= r.heatmap.wacc_pct
                          const bg = irr_v == null ? '#F9FAFB'
                            : ok ? `rgba(22,163,74,${Math.min(0.15 + (irr_v - r.heatmap.wacc_pct) * 0.02, 0.7)})`
                            : `rgba(220,38,38,${Math.min(0.15 + (r.heatmap.wacc_pct - irr_v) * 0.02, 0.6)})`
                          return (
                            <td key={ci} style={{
                              padding: '4px 2px', textAlign: 'center', background: bg,
                              color: irr_v == null ? '#9CA3AF' : ok ? '#14532D' : '#7F1D1D',
                              fontWeight: isBase ? 800 : 500,
                              border: isBase ? `2px solid ${NAVY}` : '1px solid #F3F4F6',
                            }}>
                              {isBase ? '✕' : irr_v != null ? `${irr_v.toFixed(0)}%` : '—'}
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* FCL Chart */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 12 }}>
              Fluxo de Caixa Livre — {r.anos?.length - 1 || 20} anos
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={fclData} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
                <XAxis dataKey="ano" tick={{ fontSize: 10 }} interval={3} />
                <YAxis tickFormatter={v => fmtMoeda(v, cur)} tick={{ fontSize: 9 }} width={64} />
                <Tooltip content={<FCLTooltip />} />
                <ReferenceLine y={0} stroke="#374151" strokeWidth={1.5} />
                <Bar dataKey="fcl" name="FCL Anual" radius={[3, 3, 0, 0]}>
                  {fclData.map((d, i) => <Cell key={i} fill={d.fcl >= 0 ? GREEN : RED} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* FCL Acumulado + Sensibilidade lado a lado */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="card">
              <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 10 }}>FCL Acumulado</div>
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={fclData} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
                  <XAxis dataKey="ano" tick={{ fontSize: 9 }} interval={3} />
                  <YAxis tickFormatter={v => fmtMoeda(v, cur)} tick={{ fontSize: 9 }} width={60} />
                  <Tooltip content={<FCLTooltip />} />
                  <ReferenceLine y={0} stroke={AMBER} strokeWidth={2} strokeDasharray="6 3" />
                  <Line dataKey="acum" name="FCL Acumulado" stroke={NAVY} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 10 }}>Sensibilidade TIR × Preço</div>
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={sensiData} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
                  <XAxis dataKey="price" tick={{ fontSize: 9 }} interval={2} />
                  <YAxis tickFormatter={v => `${v?.toFixed(0)}%`} tick={{ fontSize: 9 }} width={36} />
                  <Tooltip formatter={(v) => [`${v?.toFixed(1)}%`, 'TIR']} />
                  <ReferenceLine y={wacc_pct} stroke={AMBER} strokeWidth={2} strokeDasharray="6 3"
                    label={{ value: `WACC`, position: 'insideTopRight', fontSize: 9, fill: AMBER }} />
                  <Line dataKey="irr" name="TIR" stroke={NAVY} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
              <div style={{ marginTop: 6, fontSize: 11, color: GREEN, fontWeight: 600 }}>
                Break-even: {r.preco_breakeven_usd != null ? `$ ${r.preco_breakeven_usd}/tCO₂` : '—'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
