import { useState, useContext, useRef } from 'react'
import axios from 'axios'
import { AppCtx } from '../../App'

// ── Moedas ────────────────────────────────────────────────────────────────────

const CURRENCIES = [
  { value: 'BRL', label: 'BRL — Real Brasileiro',     symbol: 'R$',   fx: 5.70  },
  { value: 'USD', label: 'USD — Dólar Americano',      symbol: '$',    fx: 1.0   },
  { value: 'EUR', label: 'EUR — Euro',                 symbol: '€',    fx: 0.92  },
  { value: 'GBP', label: 'GBP — Libra Esterlina',      symbol: '£',    fx: 0.79  },
  { value: 'CLP', label: 'CLP — Peso Chileno',         symbol: 'CLP$', fx: 940   },
  { value: 'COP', label: 'COP — Peso Colombiano',      symbol: 'COP$', fx: 4100  },
  { value: 'MXN', label: 'MXN — Peso Mexicano',        symbol: 'MX$',  fx: 17.5  },
  { value: 'DKK', label: 'DKK — Coroa Dinamarquesa',   symbol: 'kr',   fx: 6.9   },
  { value: 'SEK', label: 'SEK — Coroa Sueca',          symbol: 'kr',   fx: 10.4  },
  { value: 'NOK', label: 'NOK — Coroa Norueguesa',     symbol: 'kr',   fx: 10.6  },
  { value: 'AUD', label: 'AUD — Dólar Australiano',    symbol: 'A$',   fx: 1.55  },
  { value: 'CAD', label: 'CAD — Dólar Canadense',      symbol: 'C$',   fx: 1.36  },
  { value: 'ZAR', label: 'ZAR — Rand Sul-Africano',    symbol: 'R',    fx: 18.5  },
  { value: 'INR', label: 'INR — Rúpia Indiana',        symbol: '₹',   fx: 83.0  },
  { value: 'JPY', label: 'JPY — Iene Japonês',         symbol: '¥',   fx: 155   },
]

function getCurrency(code) {
  return CURRENCIES.find(c => c.value === code) || CURRENCIES[0]
}

// ── Defaults ─────────────────────────────────────────────────────────────────

// Defaults de CAPEX baseados no projeto Nova Esperança (BCNE)
export const CAPEX_DEFAULTS = [
  // Infraestrutura
  { id: 'terraplanagem',        nome: 'Terraplanagem e drenagem',         valor: 300000,  categoria: 'Infraestrutura' },
  { id: 'infra_civil',          nome: 'Infraestrutura civil',              valor: 400000,  categoria: 'Infraestrutura' },
  { id: 'subestacao',           nome: 'Subestação de energia',            valor: 400000,  categoria: 'Infraestrutura' },
  // Equipamentos
  { id: 'reator_pirolise',      nome: 'Reator de pirólise',               valor: 2210000, categoria: 'Equipamentos' },
  { id: 'linha_cominuicao',     nome: 'Linha de cominuição / triturador', valor: 240000,  categoria: 'Equipamentos' },
  { id: 'secador_biomassa',     nome: 'Secador de biomassa',              valor: 150000,  categoria: 'Equipamentos' },
  { id: 'frete_seguro',         nome: 'Frete, seguro e sobressalentes',   valor: 312000,  categoria: 'Equipamentos' },
  { id: 'montagem',             nome: 'Montagem e comissionamento',       valor: 450000,  categoria: 'Equipamentos' },
  // Intangíveis (Carbono)
  { id: 'acv_lca',              nome: 'Análise de Ciclo de Vida (ACV)',   valor: 45000,   categoria: 'Intangíveis' },
  { id: 'mrv_dataroom',         nome: 'Plano de MRV e data room',         valor: 150000,  categoria: 'Intangíveis' },
  { id: 'auditoria_inicial',    nome: 'Auditoria e certificação inicial', valor: 100000,  categoria: 'Intangíveis' },
  { id: 'servicos_consultoria', nome: 'Consultoria especializada',        valor: 741000,  categoria: 'Intangíveis' },
]

const CAPEX_TOTAL_DEFAULT = CAPEX_DEFAULTS.reduce((s, i) => s + i.valor, 0) // 5.498.000

// Defaults de OPEX baseados no projeto Nova Esperança (BCNE, 5.000 t/ano feedstock)
// Valores de referência auditados — ajustar conforme o projeto
export const OPEX_DEFAULTS = [
  // Energia
  { id: 'energia_eletrica_var', nome: 'Energia elétrica (variável)',    valor: 624000, categoria: 'Energia' },
  { id: 'demanda_contratada',   nome: 'Demanda elétrica contratada',    valor: 129000, categoria: 'Energia' },
  { id: 'diesel_startup',       nome: 'Diesel / startup reator',        valor: 19700,  categoria: 'Energia' },
  // Mão de Obra
  { id: 'mao_de_obra',          nome: 'Mão de obra operacional',        valor: 355000, categoria: 'Mão de Obra' },
  // Logística
  { id: 'logistica_coleta',     nome: 'Coleta de feedstock',            valor: 142000, categoria: 'Logística' },
  { id: 'logistica_transporte', nome: 'Transporte de feedstock',        valor: 237000, categoria: 'Logística' },
  // Manutenção
  { id: 'manutencao_reator',    nome: 'O&M do reator e equipamentos',   valor: 22000,  categoria: 'Manutenção' },
  // Conformidade (carbono)
  { id: 'auditoria',            nome: 'Auditoria e verificação',         valor: 100000, categoria: 'Conformidade' },
  { id: 'lca_mrv',              nome: 'LCA / MRV anual',                valor: 35000,  categoria: 'Conformidade' },
  { id: 'treinamento',          nome: 'Treinamento e outros fixos',      valor: 10000,  categoria: 'Conformidade' },
  // Materiais
  { id: 'bigbag_embalagem',     nome: 'Big bags e embalagem',           valor: 25000,  categoria: 'Materiais' },
  { id: 'material_lab',         nome: 'Material de laboratório',         valor: 36000,  categoria: 'Materiais' },
]

const OPEX_TOTAL_DEFAULT = OPEX_DEFAULTS.reduce((s, i) => s + i.valor, 0) // ~1.734.700

const DEFAULTS = {
  moeda_projeto: 'BRL', moeda_credito: 'USD',
  feedstock_t_ano: 5000, yield_pirolise: 0.28, fator_carbono: 2.5,
  preco_credito_usd: 120, fx_rate: 5.70, preco_biochar: 0,
  escalacao_carbono: 0, escalacao_fx: 0,
  capex_total:    CAPEX_TOTAL_DEFAULT,
  capex_breakdown: CAPEX_DEFAULTS.map(i => ({ ...i })),
  opex_anual:     OPEX_TOTAL_DEFAULT,
  opex_breakdown:  OPEX_DEFAULTS.map(i => ({ ...i })),
  escalacao_opex: 0, vida_util_anos: 20,
  wacc: 0.12, aliquota_efetiva_ir: 0.20, horizonte_anos: 20, ano_investimento: 2026,
}

const MARKET_WARN = {
  preco_credito_usd: { low: 60, high: 220, label: 'Preço do crédito' },
  yield_pirolise:    { low: 0.18, high: 0.42, label: 'Rendimento pirólise' },
  fator_carbono:     { low: 1.8, high: 3.3, label: 'Fator de carbono' },
  wacc:              { low: 0.08, high: 0.22, label: 'WACC' },
  aliquota_efetiva_ir: { low: 0.05, high: 0.38, label: 'Alíquota efetiva IR' },
}

// ── Formatação ────────────────────────────────────────────────────────────────

function fmtMoeda(v, currency = 'BRL') {
  if (v == null) return '—'
  const sym = getCurrency(currency).symbol
  const abs = Math.abs(v)
  const neg = v < 0 ? '-' : ''
  if (abs >= 1_000_000) return `${neg}${sym} ${(abs / 1_000_000).toFixed(1)}M`
  if (abs >= 1_000)     return `${neg}${sym} ${(abs / 1_000).toFixed(0)}k`
  return `${neg}${sym} ${Math.round(abs).toLocaleString('pt-BR')}`
}
function fmtPct(v)  { return v == null ? '—' : `${Number(v).toFixed(1)}%` }
function fmtUSD(v)  { return v == null ? '—' : `$ ${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}` }

// ── Sub-componentes ───────────────────────────────────────────────────────────

function Warning({ msg, onConfirm, confirmed }) {
  return (
    <div style={{ padding: '8px 12px', borderRadius: 6, marginTop: 6,
                  background: confirmed ? '#F0FDF4' : '#FFFBEB',
                  border: `1px solid ${confirmed ? '#16A34A' : '#D97706'}`,
                  fontSize: 12, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
      <span>{confirmed ? '✅' : '⚠️'}</span>
      <div style={{ flex: 1 }}>
        <div style={{ color: confirmed ? '#16A34A' : '#92400E' }}>{msg}</div>
        {!confirmed && (
          <button onClick={onConfirm} style={{
            marginTop: 4, fontSize: 11, padding: '2px 8px', cursor: 'pointer',
            border: '1px solid #D97706', borderRadius: 4, background: 'white', color: '#92400E',
          }}>
            Confirmo — assumo responsabilidade por este valor
          </button>
        )}
      </div>
    </div>
  )
}

function FieldRow({ label, name, value, onChange, unit, hint, step, min, warnings, confirmedWarnings, onConfirmWarning }) {
  const w = warnings?.find(w => w.field === name)
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <label style={{ fontSize: 13, fontWeight: 600 }}>{label}</label>
        {unit && <span style={{ fontSize: 11, color: 'var(--text-2)' }}>{unit}</span>}
      </div>
      {hint && <div style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 4 }}>{hint}</div>}
      <input type="number" value={value ?? ''} step={step} min={min}
        onChange={e => onChange(name, parseFloat(e.target.value) || 0)}
        style={{ width: '100%', padding: '7px 10px', fontSize: 13,
                 border: `1px solid ${w ? '#D97706' : 'var(--border)'}`, borderRadius: 6 }}
      />
      {w && <Warning msg={w.message} confirmed={!!confirmedWarnings?.[name]}
                    onConfirm={() => onConfirmWarning(name)} />}
    </div>
  )
}

function SectionTitle({ n, title }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, marginTop: 4 }}>
      <div style={{ width: 26, height: 26, borderRadius: 13, background: 'var(--navy)',
                    color: 'white', fontWeight: 700, fontSize: 13,
                    display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{n}</div>
      <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--navy)' }}>{title}</div>
    </div>
  )
}

function KPICard({ label, value, color, sub }) {
  return (
    <div style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 10,
                  padding: '14px 16px', flex: 1, minWidth: 120 }}>
      <div style={{ fontSize: 22, fontWeight: 800, color: color || 'var(--navy)' }}>{value}</div>
      <div style={{ fontSize: 12, color: 'var(--text-2)', marginTop: 2 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

// ── OPEX Detalhado ────────────────────────────────────────────────────────────

const CATEGORIA_COLORS = {
  // OPEX
  'Energia':        '#2563EB',
  'Mão de Obra':    '#16A34A',
  'Logística':      '#D97706',
  'Manutenção':     '#DC2626',
  'Conformidade':   '#7C3AED',
  'Materiais':      '#0891B2',
  // CAPEX
  'Infraestrutura': '#059669',
  'Equipamentos':   '#1D4ED8',
  'Intangíveis':    '#9333EA',
  // Genérico
  'Outros':         '#6B7280',
}

function CostDetailForm({ breakdown, onChange, symbol, totalLabel = 'Total Anual' }) {
  const total = breakdown.reduce((s, i) => s + (parseFloat(i.valor) || 0), 0)

  function updateItem(id, field, value) {
    const updated = breakdown.map(item =>
      item.id === id ? { ...item, [field]: field === 'valor' ? parseFloat(value) || 0 : value } : item
    )
    onChange(updated)
  }

  function removeItem(id) {
    onChange(breakdown.filter(i => i.id !== id))
  }

  function addCustom() {
    const newItem = {
      id:        `custom_${Date.now()}`,
      nome:      '',
      valor:     0,
      categoria: 'Outros',
    }
    onChange([...breakdown, newItem])
  }

  // Agrupa por categoria mantendo ordem de aparição
  const categories = []
  const seen = new Set()
  breakdown.forEach(item => {
    if (!seen.has(item.categoria)) {
      seen.add(item.categoria)
      categories.push(item.categoria)
    }
  })

  return (
    <div>
      <div style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 10, lineHeight: 1.4 }}>
        Valores de referência: Projeto Nova Esperança (biochar ~5.000 t/ano feedstock). Ajuste conforme seu projeto.
      </div>

      {categories.map(cat => {
        const items = breakdown.filter(i => i.categoria === cat)
        const catColor = CATEGORIA_COLORS[cat] || '#6B7280'
        const catTotal = items.reduce((s, i) => s + (parseFloat(i.valor) || 0), 0)

        return (
          <div key={cat} style={{ marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between',
                          padding: '4px 8px', background: catColor + '15',
                          borderLeft: `3px solid ${catColor}`, marginBottom: 4, borderRadius: '0 4px 4px 0' }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: catColor }}>{cat}</span>
              <span style={{ fontSize: 11, color: catColor }}>
                {symbol} {catTotal.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
              </span>
            </div>

            {items.map(item => (
              <div key={item.id} style={{ display: 'flex', gap: 6, alignItems: 'center',
                                          marginBottom: 4, paddingLeft: 8 }}>
                {/* Nome — editável apenas para customizados */}
                {item.id.startsWith('custom_') ? (
                  <input
                    value={item.nome}
                    onChange={e => updateItem(item.id, 'nome', e.target.value)}
                    placeholder="Nome do custo"
                    style={{ flex: 1, fontSize: 12, padding: '4px 8px',
                             border: '1px solid var(--border)', borderRadius: 5 }}
                  />
                ) : (
                  <span style={{ flex: 1, fontSize: 12, color: 'var(--text)' }}>{item.nome}</span>
                )}
                {/* Valor */}
                <input
                  type="number"
                  value={item.valor}
                  min={0}
                  step={1000}
                  onChange={e => updateItem(item.id, 'valor', e.target.value)}
                  style={{ width: 110, fontSize: 12, padding: '4px 8px', textAlign: 'right',
                           border: '1px solid var(--border)', borderRadius: 5 }}
                />
                {/* Remover (sempre disponível) */}
                <button onClick={() => removeItem(item.id)}
                  style={{ border: 'none', background: 'none', cursor: 'pointer',
                           color: '#9CA3AF', fontSize: 15, lineHeight: 1, padding: '0 2px' }}>
                  ×
                </button>
              </div>
            ))}
          </div>
        )
      })}

      {/* Adicionar linha */}
      <button onClick={addCustom} style={{
        width: '100%', padding: '6px 0', marginTop: 4, marginBottom: 12,
        border: '1px dashed #9CA3AF', borderRadius: 6, background: 'transparent',
        cursor: 'pointer', fontSize: 12, color: '#6B7280',
      }}>
        + Adicionar linha de custo
      </button>

      {/* Total */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '8px 12px', background: 'var(--navy-light)', borderRadius: 8 }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--navy)' }}>{totalLabel}</span>
        <span style={{ fontSize: 16, fontWeight: 800, color: 'var(--navy)' }}>
          {symbol} {total.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
        </span>
      </div>
    </div>
  )
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function ViabilidadeTab({ project }) {
  const { API } = useContext(AppCtx)
  const fileRef = useRef()

  const [hasSheet, setHasSheet]   = useState(null)
  const [form, setForm]           = useState(DEFAULTS)
  const [warnings, setWarnings]   = useState([])
  const [confirmedWarnings, setConfirmedWarnings] = useState({})
  const [resultado, setResultado] = useState(null)
  const [loading, setLoading]     = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [extractedFields, setExtractedFields] = useState({})
  const [error, setError]         = useState('')
  const [step, setStep]           = useState('start')

  const moeda = getCurrency(form.moeda_projeto)
  const showFx = form.moeda_projeto !== 'USD'

  function setField(name, value) {
    setForm(prev => ({ ...prev, [name]: value }))
    setConfirmedWarnings(prev => { const n = { ...prev }; delete n[name]; return n })
  }

  function setOpexBreakdown(breakdown) {
    const total = breakdown.reduce((s, i) => s + (parseFloat(i.valor) || 0), 0)
    setForm(prev => ({ ...prev, opex_breakdown: breakdown, opex_anual: total }))
  }

  function setCapexBreakdown(breakdown) {
    const total = breakdown.reduce((s, i) => s + (parseFloat(i.valor) || 0), 0)
    setForm(prev => ({ ...prev, capex_breakdown: breakdown, capex_total: total }))
  }

  function handleCurrencyChange(code) {
    const c = getCurrency(code)
    setForm(prev => ({ ...prev, moeda_projeto: code, fx_rate: c.fx }))
  }

  function checkWarnings(premissas) {
    return Object.entries(MARKET_WARN).map(([field, cfg]) => {
      const v = premissas[field]
      if (v == null) return null
      if (cfg.low != null && v < cfg.low)
        return { field, message: `${cfg.label}: ${v} abaixo do range típico (mín. ${cfg.low}).` }
      if (cfg.high != null && v > cfg.high)
        return { field, message: `${cfg.label}: ${v} acima do range típico (máx. ${cfg.high}).` }
      return null
    }).filter(Boolean)
  }

  async function handleUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setExtracting(true); setError('')
    const fd = new FormData()
    fd.append('file', file)
    try {
      const r = await axios.post(`${API}/api/projects/${project.id}/viabilidade/extract`, fd,
        { headers: { 'Content-Type': 'multipart/form-data' } })
      const extracted = r.data.extracted || {}
      const merged = { ...DEFAULTS }
      const highlighted = {}
      Object.entries(extracted).forEach(([k, v]) => {
        if (v != null && k in DEFAULTS) { merged[k] = v; highlighted[k] = true }
      })
      setForm(merged); setExtractedFields(highlighted)
      setWarnings(checkWarnings(merged)); setStep('form')
    } catch { setError('Erro ao extrair dados. Verifique o arquivo.') }
    finally { setExtracting(false); e.target.value = '' }
  }

  async function handleCalculate() {
    const unconfirmed = warnings.filter(w => !confirmedWarnings[w.field])
    if (unconfirmed.length > 0) {
      setError(`Confirme os ${unconfirmed.length} aviso(s) antes de calcular.`); return
    }
    setLoading(true); setError('')
    try {
      const r = await axios.post(`${API}/api/projects/${project.id}/viabilidade/calculate`, {
        premissas: form, fonte: hasSheet ? 'planilha' : 'manual',
      })
      setResultado(r.data.resultado); setWarnings(r.data.warnings || [])
      setStep('results')
    } catch (e) { setError(e.response?.data?.detail || 'Erro no cálculo.') }
    finally { setLoading(false) }
  }

  // ── START ──────────────────────────────────────────────────────────────────
  if (step === 'start') return (
    <div className="card">
      <div className="card-title">Análise de Viabilidade Financeira</div>
      <div style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 20, lineHeight: 1.6 }}>
        Calcule IRR, VPL, payback e o teste de adicionalidade financeira.
        Motor 100% determinístico — mesmos inputs, mesmo resultado.
      </div>
      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 14 }}>
        Você já possui uma planilha de modelagem financeira do projeto?
      </div>
      <div style={{ display: 'flex', gap: 12 }}>
        <button className="btn btn-primary" style={{ flex: 1, padding: '14px 0', fontSize: 15 }}
          onClick={() => { setHasSheet(true); setStep('form') }}>
          ✅ Sim — fazer upload da planilha
        </button>
        <button className="btn btn-outline" style={{ flex: 1, padding: '14px 0', fontSize: 15 }}
          onClick={() => { setHasSheet(false); setWarnings(checkWarnings(form)); setStep('form') }}>
          📝 Não — preencher manualmente
        </button>
      </div>
    </div>
  )

  // ── FORM ───────────────────────────────────────────────────────────────────
  if (step === 'form') {
    const biocharEst = (form.feedstock_t_ano || 0) * (form.yield_pirolise || 0)
    const creditosEst = biocharEst * (form.fator_carbono || 0)
    const receitaEst = creditosEst * (form.preco_credito_usd || 0) * (showFx ? (form.fx_rate || 1) : 1)

    return (
      <div>
        {/* Upload card */}
        {hasSheet && !extractedFields.feedstock_t_ano && (
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-title" style={{ marginBottom: 8 }}>Upload da planilha</div>
            <div style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 12 }}>
              Formatos aceitos: .xlsx, .xls, .csv — A IA extrai os parâmetros e pré-preenche o formulário.
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-primary" onClick={() => fileRef.current?.click()} disabled={extracting}>
                {extracting ? '⟳ Extraindo…' : '📎 Selecionar arquivo'}
              </button>
              <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv"
                style={{ display: 'none' }} onChange={handleUpload} />
              <button className="btn btn-outline"
                onClick={() => { setHasSheet(false); setWarnings(checkWarnings(form)) }}>
                Preencher manualmente
              </button>
            </div>
          </div>
        )}

        {Object.keys(extractedFields).length > 0 && (
          <div style={{ padding: '10px 14px', background: '#EFF6FF', border: '1px solid #3B82F6',
                        borderRadius: 8, fontSize: 13, marginBottom: 14, color: '#1E40AF' }}>
            ✨ {Object.keys(extractedFields).length} campos extraídos da planilha. Revise e confirme.
          </div>
        )}

        {/* Moeda — topo do formulário */}
        <div className="card" style={{ marginBottom: 16 }}>
          <SectionTitle n="0" title="Moeda do Projeto" />
          <div style={{ display: 'grid', gridTemplateColumns: showFx ? '1fr 1fr' : '1fr', gap: 16 }}>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                Moeda do projeto
              </label>
              <select value={form.moeda_projeto} onChange={e => handleCurrencyChange(e.target.value)}
                style={{ width: '100%', padding: '7px 10px', fontSize: 13,
                         border: '1px solid var(--border)', borderRadius: 6 }}>
                {CURRENCIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
              <div style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 4 }}>
                Créditos de carbono sempre cotados em USD.
              </div>
            </div>
            {showFx && (
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                  Câmbio USD → {form.moeda_projeto}
                </label>
                <input type="number" value={form.fx_rate ?? ''} step={0.01} min={0}
                  onChange={e => setField('fx_rate', parseFloat(e.target.value) || 0)}
                  style={{ width: '100%', padding: '7px 10px', fontSize: 13,
                           border: '1px solid var(--border)', borderRadius: 6 }}
                />
                <div style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 4 }}>
                  1 USD = {form.fx_rate} {form.moeda_projeto}
                </div>
              </div>
            )}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            {/* Bloco 1 */}
            <div className="card" style={{ marginBottom: 16 }}>
              <SectionTitle n="1" title="Produção" />
              <FieldRow name="feedstock_t_ano" label="Feedstock disponível" unit="t/ano (base seca)"
                step={100} min={0} hint="Biomassa seca processável por ano"
                value={form.feedstock_t_ano} onChange={setField}
                warnings={warnings} confirmedWarnings={confirmedWarnings}
                onConfirmWarning={k => setConfirmedWarnings(p => ({ ...p, [k]: true }))} />
              <FieldRow name="yield_pirolise" label="Rendimento de pirólise" unit="fração (0.28 = 28%)"
                step={0.01} min={0}
                value={form.yield_pirolise} onChange={setField}
                warnings={warnings} confirmedWarnings={confirmedWarnings}
                onConfirmWarning={k => setConfirmedWarnings(p => ({ ...p, [k]: true }))} />
              <FieldRow name="fator_carbono" label="Fator de carbono" unit="tCO₂e / t biochar"
                step={0.1} min={0}
                value={form.fator_carbono} onChange={setField}
                warnings={warnings} confirmedWarnings={confirmedWarnings}
                onConfirmWarning={k => setConfirmedWarnings(p => ({ ...p, [k]: true }))} />
              <div style={{ padding: '10px 12px', background: 'var(--navy-light)', borderRadius: 8, fontSize: 12 }}>
                <b>Biochar:</b> {biocharEst.toLocaleString('pt-BR', { maximumFractionDigits: 0 })} t/ano &nbsp;|&nbsp;
                <b>Créditos:</b> {creditosEst.toLocaleString('pt-BR', { maximumFractionDigits: 0 })} tCO₂e/ano
              </div>
            </div>

            {/* Bloco 2 */}
            <div className="card">
              <SectionTitle n="2" title="Receitas" />
              <FieldRow name="preco_credito_usd" label="Preço do crédito de carbono" unit="USD / tCO₂e"
                step={5} min={0}
                value={form.preco_credito_usd} onChange={setField}
                warnings={warnings} confirmedWarnings={confirmedWarnings}
                onConfirmWarning={k => setConfirmedWarnings(p => ({ ...p, [k]: true }))} />
              <FieldRow name="preco_biochar" label={`Preço de venda do biochar`}
                unit={`${moeda.symbol}/t (0 = não vende)`} step={50} min={0}
                value={form.preco_biochar} onChange={setField}
                warnings={warnings} confirmedWarnings={confirmedWarnings}
                onConfirmWarning={k => setConfirmedWarnings(p => ({ ...p, [k]: true }))} />
              <div style={{ padding: '10px 12px', background: 'var(--navy-light)', borderRadius: 8, fontSize: 12 }}>
                <b>Receita carbono/ano:</b> {fmtMoeda(receitaEst, form.moeda_projeto)}
              </div>
            </div>
          </div>

          <div>
            {/* Bloco 3 — CAPEX */}
            <div className="card" style={{ marginBottom: 16 }}>
              <SectionTitle n="3" title="CAPEX — Investimento Inicial" />
              <FieldRow name="vida_util_anos" label="Vida útil (depreciação)" unit="anos"
                step={1} min={1}
                value={form.vida_util_anos} onChange={setField}
                warnings={[]} confirmedWarnings={{}} onConfirmWarning={() => {}} />
              <div style={{ marginTop: 8, paddingTop: 10, borderTop: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontSize: 11, color: 'var(--text-2)' }}>
                    Ref.: Nova Esperança (BCNE). Ajuste conforme seu projeto.
                  </span>
                </div>
                <CostDetailForm
                  breakdown={form.capex_breakdown?.length ? form.capex_breakdown : CAPEX_DEFAULTS.map(i => ({ ...i }))}
                  onChange={setCapexBreakdown}
                  symbol={moeda.symbol}
                  totalLabel="Total CAPEX"
                />
              </div>
            </div>

            {/* Bloco 3b — OPEX */}
            <div className="card" style={{ marginBottom: 16 }}>
              <SectionTitle n="4" title="OPEX — Custos Operacionais Anuais" />
              <div style={{ marginBottom: 6 }}>
                <span style={{ fontSize: 11, color: 'var(--text-2)' }}>
                  Ref.: Nova Esperança (BCNE, ~5.000 t/ano feedstock). Ajuste conforme seu projeto.
                </span>
              </div>
              <CostDetailForm
                breakdown={form.opex_breakdown?.length ? form.opex_breakdown : OPEX_DEFAULTS.map(i => ({ ...i }))}
                onChange={setOpexBreakdown}
                symbol={moeda.symbol}
                totalLabel="Total OPEX Anual"
              />
            </div>

            {/* Bloco 5 — Financeiro */}
            <div className="card">
              <SectionTitle n="5" title="Financeiro" />
              <FieldRow name="wacc" label="WACC / Taxa de desconto" unit="fração (0.12 = 12%)"
                step={0.005} min={0}
                value={form.wacc} onChange={setField}
                warnings={warnings} confirmedWarnings={confirmedWarnings}
                onConfirmWarning={k => setConfirmedWarnings(p => ({ ...p, [k]: true }))} />
              <FieldRow name="aliquota_efetiva_ir"
                label="Alíquota efetiva de IR" unit="fração (ex: 0.20 = 20%)"
                hint="Inclui todos os tributos sobre o lucro (IR, CSLL ou equivalente local)"
                step={0.01} min={0}
                value={form.aliquota_efetiva_ir} onChange={setField}
                warnings={warnings} confirmedWarnings={confirmedWarnings}
                onConfirmWarning={k => setConfirmedWarnings(p => ({ ...p, [k]: true }))} />
              <FieldRow name="horizonte_anos" label="Horizonte do projeto" unit="anos"
                step={1} min={1}
                value={form.horizonte_anos} onChange={setField}
                warnings={[]} confirmedWarnings={{}} onConfirmWarning={() => {}} />
              <FieldRow name="ano_investimento" label="Ano de investimento" step={1} min={2020}
                value={form.ano_investimento} onChange={setField}
                warnings={[]} confirmedWarnings={{}} onConfirmWarning={() => {}} />
            </div>
          </div>
        </div>

        {error && (
          <div style={{ padding: '10px 14px', background: 'var(--red-bg)', color: 'var(--red)',
                        borderRadius: 8, fontSize: 13, marginTop: 12 }}>{error}</div>
        )}
        <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
          <button className="btn btn-outline" onClick={() => setStep('start')}>← Voltar</button>
          <button className="btn btn-primary" style={{ flex: 1, padding: '12px 0', fontSize: 15 }}
            onClick={handleCalculate} disabled={loading}>
            {loading ? '⟳ Calculando…' : '⚡ Calcular Viabilidade'}
          </button>
        </div>
      </div>
    )
  }

  // ── RESULTS ────────────────────────────────────────────────────────────────
  const r = resultado || {}
  const cur = r.moeda_projeto || form.moeda_projeto
  const irr = r.irr
  const irrColor = irr == null ? 'var(--text-2)' : irr >= (form.wacc * 100) ? 'var(--green)' : 'var(--red)'

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <KPICard label="TIR (IRR)" value={irr != null ? `${irr.toFixed(1)}%` : '—'} color={irrColor}
          sub={`WACC: ${(form.wacc * 100).toFixed(0)}%`} />
        <KPICard label="VPL" value={fmtMoeda(r.npv, cur)} color={(r.npv || 0) >= 0 ? 'var(--green)' : 'var(--red)'} />
        <KPICard label="Payback" value={r.payback_year || 'Não atingido'} />
        <KPICard label="EBITDA Ano 1" value={fmtMoeda(r.ebitda_yr1, cur)}
          sub={r.margem_ebitda_pct != null ? `Margem ${r.margem_ebitda_pct.toFixed(1)}%` : ''} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 10 }}>Produção Estimada</div>
          {[
            ['Feedstock', `${(form.feedstock_t_ano || 0).toLocaleString('pt-BR')} t/ano`],
            ['Biochar', `${(r.biochar_t_ano || 0).toLocaleString('pt-BR')} t/ano`],
            ['Créditos', `${(r.creditos_tco2_ano || 0).toLocaleString('pt-BR')} tCO₂e/ano`],
            ['Receita bruta ano 1', fmtMoeda(r.receita_bruta_yr1, cur)],
            ['OPEX ano 1', fmtMoeda(r.opex_yr1, cur)],
          ].map(([l, v]) => (
            <div key={l} style={{ display: 'flex', justifyContent: 'space-between',
                                   padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
              <span style={{ color: 'var(--text-2)' }}>{l}</span>
              <span style={{ fontWeight: 600 }}>{v}</span>
            </div>
          ))}
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 10 }}>Teste de Adicionalidade Financeira</div>
          <div style={{ padding: '12px', borderRadius: 8, marginBottom: 10,
                        background: r.adicionalidade_financeira ? '#F0FDF4' : '#FEF2F2',
                        border: `2px solid ${r.adicionalidade_financeira ? 'var(--green)' : 'var(--red)'}` }}>
            <div style={{ fontSize: 20, fontWeight: 800,
                          color: r.adicionalidade_financeira ? 'var(--green)' : 'var(--red)' }}>
              {r.adicionalidade_financeira ? '✓ Confirmada' : '✗ Não confirmada'}
            </div>
            <div style={{ fontSize: 12, marginTop: 4, color: 'var(--text-2)' }}>
              TIR sem receita de carbono: {r.irr_sem_carbono != null ? `${r.irr_sem_carbono.toFixed(1)}%` : 'Inviável'}
            </div>
          </div>
          {[
            ['TIR com carbono', irr != null ? `${irr.toFixed(1)}%` : '—'],
            ['TIR sem carbono', r.irr_sem_carbono != null ? `${r.irr_sem_carbono.toFixed(1)}%` : 'Inviável'],
            ['Break-even', r.preco_breakeven_usd != null ? `${fmtUSD(r.preco_breakeven_usd)}/tCO₂` : '—'],
            ['WACC', fmtPct((form.wacc || 0.12) * 100)],
          ].map(([l, v]) => (
            <div key={l} style={{ display: 'flex', justifyContent: 'space-between',
                                   padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
              <span style={{ color: 'var(--text-2)' }}>{l}</span>
              <span style={{ fontWeight: 600 }}>{v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Sensibilidade */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title" style={{ marginBottom: 10 }}>
          Sensibilidade — Preço do Crédito (USD) × TIR
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ background: 'var(--navy)', color: 'white' }}>
                {(r.sensibilidade || []).filter((_, i) => i % 2 === 0).map(s => (
                  <th key={s.preco_usd} style={{ padding: '6px 8px', textAlign: 'center' }}>
                    ${s.preco_usd}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                {(r.sensibilidade || []).filter((_, i) => i % 2 === 0).map(s => {
                  const wacc_pct = (form.wacc || 0.12) * 100
                  const ok = s.irr != null && s.irr >= wacc_pct
                  return (
                    <td key={s.preco_usd} style={{ padding: '6px 8px', textAlign: 'center',
                                                    fontWeight: 700,
                                                    color: s.irr == null ? 'var(--text-2)' : ok ? 'var(--green)' : 'var(--red)',
                                                    background: ok ? '#F0FDF4' : '#FEF2F2' }}>
                      {s.irr != null ? `${s.irr.toFixed(1)}%` : '—'}
                    </td>
                  )
                })}
              </tr>
            </tbody>
          </table>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 6 }}>
          Verde = TIR ≥ WACC ({fmtPct((form.wacc || 0.12) * 100)}). Moeda: {cur}.
        </div>
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <button className="btn btn-outline" onClick={() => setStep('form')}>← Editar premissas</button>
        <button className="btn btn-outline"
          onClick={() => window.open(`${API}/api/projects/${project.id}/viabilidade/export`, '_blank')}>
          ⬇ Exportar Excel
        </button>
        <div style={{ flex: 1 }} />
        <div style={{ padding: '10px 14px', background: 'var(--navy-light)', borderRadius: 8,
                      fontSize: 13, color: 'var(--navy)' }}>
          💡 Acesse o <b>Financial Lab</b> na sidebar para análise interativa com sliders
        </div>
      </div>
    </div>
  )
}
