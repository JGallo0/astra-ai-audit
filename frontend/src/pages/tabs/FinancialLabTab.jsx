import { useState, useEffect, useContext, useCallback, useRef } from 'react'
import axios from 'axios'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts'
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
            <Slider label="Câmbio (BRL/USD)" name="fx_brl_usd"
              value={form.fx_brl_usd} min={4.0} max={8.0} step={0.05}
              fmt={v => v.toFixed(2)} onChange={setField} />
            <Slider label="Preço biochar (BRL/t)" name="preco_biochar_brl"
              value={form.preco_biochar_brl} min={0} max={3000} step={50}
              fmt={v => `R$${v}`} onChange={setField} />
          </div>

          <div className="card" style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-2)', marginBottom: 12,
                          textTransform: 'uppercase', letterSpacing: 1 }}>Produção</div>
            <Slider label="Feedstock (t/ano)" name="feedstock_t_ano"
              value={form.feedstock_t_ano} min={100} max={50000} step={100}
              fmt={v => `${v.toLocaleString('pt-BR')} t`} onChange={setField} />
            <Slider label="Rendimento pirólise" name="yield_pirolise"
              value={form.yield_pirolise} min={0.10} max={0.50} step={0.01}
              fmt={v => `${(v * 100).toFixed(0)}%`} onChange={setField} />
            <Slider label="Fator carbono (tCO₂/t)" name="fator_carbono"
              value={form.fator_carbono} min={1.0} max={4.0} step={0.05}
              fmt={v => v.toFixed(2)} onChange={setField} />
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
              fmt={v => `${(v * 100).toFixed(1)}%`} onChange={setField} />
            <Slider label="Alíquota efetiva IR" name="aliquota_efetiva_ir"
              value={form.aliquota_efetiva_ir} min={0} max={0.45} step={0.01}
              fmt={v => `${(v * 100).toFixed(0)}%`} onChange={setField} />
          </div>
        </div>

        {/* ── Painel de resultados ──────────────────────────────────────── */}
        <div>
          {/* KPI row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 16 }}>
            {[
              { label: 'TIR', value: irr != null ? `${irr.toFixed(1)}%` : '—', color: irrColor, sub: `WACC ${wacc_pct.toFixed(0)}%` },
              { label: 'VPL', value: fmtMoeda(r.npv, cur), color: (r.npv || 0) >= 0 ? GREEN : RED },
              { label: 'Payback', value: r.payback_year || 'N/A' },
              { label: 'EBITDA Ano 1', value: fmtMoeda(r.ebitda_yr1, cur), sub: r.margem_ebitda_pct != null ? `${r.margem_ebitda_pct.toFixed(0)}% margem` : '' },
            ].map(k => (
              <div key={k.label} style={{ background: 'white', border: '1px solid var(--border)',
                                          borderRadius: 10, padding: '12px 14px' }}>
                <div style={{ fontSize: 20, fontWeight: 800, color: k.color || NAVY }}>{k.value}</div>
                <div style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 2 }}>{k.label}</div>
                {k.sub && <div style={{ fontSize: 10, color: 'var(--text-2)' }}>{k.sub}</div>}
              </div>
            ))}
          </div>

          {/* FCL Chart */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 12 }}>
              Fluxo de Caixa Livre — 20 anos
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={fclData} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
                <XAxis dataKey="ano" tick={{ fontSize: 10 }} interval={3} />
                <YAxis tickFormatter={v => fmtBRL(v)} tick={{ fontSize: 10 }} width={60} />
                <Tooltip content={<FCLTooltip />} />
                <ReferenceLine y={0} stroke="#374151" strokeWidth={1.5} />
                <Bar dataKey="fcl" name="FCL Anual" radius={[3, 3, 0, 0]}>
                  {fclData.map((d, i) => (
                    <Cell key={i} fill={d.fcl >= 0 ? GREEN : RED} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* FCL Acumulado */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 12 }}>
              FCL Acumulado — Payback
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={fclData} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
                <XAxis dataKey="ano" tick={{ fontSize: 10 }} interval={3} />
                <YAxis tickFormatter={v => fmtBRL(v)} tick={{ fontSize: 10 }} width={60} />
                <Tooltip content={<FCLTooltip />} />
                <ReferenceLine y={0} stroke={AMBER} strokeWidth={2} strokeDasharray="6 3"
                  label={{ value: 'Break-even', position: 'insideTopLeft', fontSize: 10, fill: AMBER }} />
                <Line dataKey="acum" name="FCL Acumulado" stroke={NAVY} strokeWidth={2.5}
                  dot={false} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Sensitivity */}
          <div className="card">
            <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 12 }}>
              Sensibilidade TIR × Preço do Crédito
            </div>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={sensiData} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
                <XAxis dataKey="price" tick={{ fontSize: 10 }} interval={2} />
                <YAxis tickFormatter={v => `${v?.toFixed(0)}%`} tick={{ fontSize: 10 }} width={42} />
                <Tooltip formatter={(v) => [`${v?.toFixed(1)}%`, 'TIR']} />
                <ReferenceLine y={wacc_pct} stroke={AMBER} strokeWidth={2} strokeDasharray="6 3"
                  label={{ value: `WACC ${wacc_pct.toFixed(0)}%`, position: 'insideTopLeft', fontSize: 10, fill: AMBER }} />
                <Line dataKey="irr" name="TIR" stroke={NAVY} strokeWidth={2.5}
                  dot={false} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
            <div style={{ marginTop: 8, padding: '8px 12px', background: '#F0FDF4', borderRadius: 6,
                          fontSize: 12, color: GREEN, fontWeight: 600 }}>
              Break-even: {r.preco_breakeven_usd != null ? `$ ${r.preco_breakeven_usd} / tCO₂` : '—'} &nbsp;|&nbsp;
              Adicionalidade: {r.adicionalidade_financeira ? '✓ Confirmada' : '✗ Não confirmada'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
