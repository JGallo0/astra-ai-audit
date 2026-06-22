import { useState, useContext, useRef } from 'react'
import axios from 'axios'
import { AppCtx } from '../../App'

const DEFAULTS = {
  feedstock_t_ano: 5000, yield_pirolise: 0.28, fator_carbono: 2.5,
  preco_credito_usd: 120, fx_brl_usd: 5.70, preco_biochar_brl: 0,
  escalacao_carbono: 0, escalacao_fx: 0,
  capex_total_brl: 5500000, opex_anual_brl: 1200000, escalacao_opex: 0, vida_util_anos: 20,
  wacc: 0.12, regime_tributario: 'LP', horizonte_anos: 20, ano_investimento: 2026,
}

const MARKET_WARN = {
  preco_credito_usd: { low: 60, high: 220, label: 'Preço do crédito' },
  preco_biochar_brl: { high: 2500, label: 'Preço do biochar' },
  yield_pirolise:    { low: 0.18, high: 0.42, label: 'Rendimento pirólise' },
  fator_carbono:     { low: 1.8, high: 3.3, label: 'Fator de carbono' },
  wacc:              { low: 0.08, high: 0.22, label: 'WACC' },
}

function fmtBRL(v) {
  if (v == null) return '—'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v)
}
function fmtPct(v) { return v == null ? '—' : `${v.toFixed(1)}%` }
function fmtUSD(v) { return v == null ? '—' : `$ ${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}` }

function Warning({ msg, onConfirm, confirmed }) {
  return (
    <div style={{ padding: '8px 12px', borderRadius: 6, marginTop: 6,
                  background: confirmed ? '#F0FDF4' : '#FFFBEB',
                  border: `1px solid ${confirmed ? '#16A34A' : '#D97706'}`,
                  fontSize: 12, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
      <span style={{ fontSize: 16 }}>{confirmed ? '✅' : '⚠️'}</span>
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

function FieldRow({ label, name, value, onChange, type = 'number', unit, hint, step, min, warnings, confirmedWarnings, onConfirmWarning }) {
  const w = warnings?.find(w => w.field === name)
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{label}</label>
        {unit && <span style={{ fontSize: 11, color: 'var(--text-2)' }}>{unit}</span>}
      </div>
      {hint && <div style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 4 }}>{hint}</div>}
      <input
        type={type === 'select' ? undefined : 'number'}
        value={value ?? ''}
        step={step}
        min={min}
        onChange={e => onChange(name, type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value)}
        style={{ width: '100%', padding: '7px 10px', border: `1px solid ${w ? '#D97706' : 'var(--border)'}`,
                 borderRadius: 6, fontSize: 13, background: 'white' }}
      />
      {w && (
        <Warning
          msg={w.message}
          confirmed={!!confirmedWarnings?.[name]}
          onConfirm={() => onConfirmWarning(name)}
        />
      )}
    </div>
  )
}

function SelectRow({ label, name, value, onChange, options, hint }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>{label}</label>
      {hint && <div style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 4 }}>{hint}</div>}
      <select value={value} onChange={e => onChange(name, e.target.value)}
        style={{ width: '100%', padding: '7px 10px', border: '1px solid var(--border)', borderRadius: 6, fontSize: 13 }}>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

function SectionTitle({ n, title }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, marginTop: 8 }}>
      <div style={{ width: 26, height: 26, borderRadius: 13, background: 'var(--navy)',
                    color: 'white', fontWeight: 700, fontSize: 13,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        {n}
      </div>
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

export default function ViabilidadeTab({ project }) {
  const { API } = useContext(AppCtx)
  const fileRef = useRef()

  const [hasSheet, setHasSheet]         = useState(null)   // null | true | false
  const [form, setForm]                 = useState(DEFAULTS)
  const [warnings, setWarnings]         = useState([])
  const [confirmedWarnings, setConfirmedWarnings] = useState({})
  const [resultado, setResultado]       = useState(null)
  const [loading, setLoading]           = useState(false)
  const [extracting, setExtracting]     = useState(false)
  const [extractedFields, setExtractedFields] = useState({})  // highlighted fields
  const [error, setError]               = useState('')
  const [step, setStep]                 = useState('start')  // start | form | results

  function setField(name, value) {
    setForm(prev => ({ ...prev, [name]: value }))
    // Clear confirmed warning when value changes
    setConfirmedWarnings(prev => { const n = {...prev}; delete n[name]; return n })
  }

  function checkWarnings(premissas) {
    const warns = []
    Object.entries(MARKET_WARN).forEach(([field, cfg]) => {
      const v = premissas[field]
      if (v == null) return
      if (cfg.low != null && v < cfg.low)
        warns.push({ field, message: `${cfg.label}: valor ${v} abaixo do range típico de mercado (mín. recomendado: ${cfg.low}).` })
      if (cfg.high != null && v > cfg.high)
        warns.push({ field, message: `${cfg.label}: valor ${v} acima do range típico de mercado (máx. recomendado: ${cfg.high}).` })
    })
    return warns
  }

  async function handleUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setExtracting(true)
    setError('')
    const fd = new FormData()
    fd.append('file', file)
    try {
      const r = await axios.post(`${API}/api/projects/${project.id}/viabilidade/extract`, fd,
        { headers: { 'Content-Type': 'multipart/form-data' } })
      const extracted = r.data.extracted || {}
      // Merge into form, keeping defaults for nulls
      const merged = { ...DEFAULTS }
      const highlighted = {}
      Object.entries(extracted).forEach(([k, v]) => {
        if (v != null && k in DEFAULTS) {
          merged[k] = v
          highlighted[k] = true
        }
      })
      setForm(merged)
      setExtractedFields(highlighted)
      setWarnings(checkWarnings(merged))
      setStep('form')
    } catch {
      setError('Erro ao extrair dados da planilha. Verifique o arquivo e tente novamente.')
    } finally {
      setExtracting(false)
      e.target.value = ''
    }
  }

  async function handleCalculate() {
    // Check unconfirmed warnings
    const unconfirmed = warnings.filter(w => !confirmedWarnings[w.field])
    if (unconfirmed.length > 0) {
      setError(`Confirme os ${unconfirmed.length} aviso(s) de mercado antes de calcular.`)
      return
    }
    setLoading(true)
    setError('')
    try {
      const r = await axios.post(`${API}/api/projects/${project.id}/viabilidade/calculate`, {
        premissas: form,
        fonte: hasSheet ? 'planilha' : 'manual',
      })
      setResultado(r.data.resultado)
      setWarnings(r.data.warnings || [])
      setStep('results')
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro no cálculo.')
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    window.open(`${API}/api/projects/${project.id}/viabilidade/export`, '_blank')
  }

  // ── Step: START ─────────────────────────────────────────────────────────────
  if (step === 'start') return (
    <div>
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">Análise de Viabilidade Financeira</div>
        <div style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 20, lineHeight: 1.6 }}>
          Calcule IRR, VPL, payback e o teste de adicionalidade financeira a partir das premissas do projeto.
          O motor é 100% determinístico — os mesmos inputs sempre produzem o mesmo resultado.
        </div>
        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 14 }}>
          Você já possui uma planilha de modelagem financeira do projeto?
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            className="btn btn-primary"
            style={{ flex: 1, padding: '14px 0', fontSize: 15 }}
            onClick={() => { setHasSheet(true); setStep('form') }}
          >
            ✅ Sim — vou fazer upload da planilha
          </button>
          <button
            className="btn btn-outline"
            style={{ flex: 1, padding: '14px 0', fontSize: 15 }}
            onClick={() => { setHasSheet(false); setWarnings(checkWarnings(form)); setStep('form') }}
          >
            📝 Não — vou informar os dados manualmente
          </button>
        </div>
      </div>
    </div>
  )

  // ── Step: FORM ──────────────────────────────────────────────────────────────
  if (step === 'form') return (
    <div>
      {hasSheet && step === 'form' && !extractedFields.feedstock_t_ano && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-title" style={{ marginBottom: 8 }}>Upload da planilha</div>
          <div style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 12 }}>
            Formatos aceitos: .xlsx, .xls, .csv — A LLM irá extrair os parâmetros e pré-preencher o formulário para sua confirmação.
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <button className="btn btn-primary" onClick={() => fileRef.current?.click()} disabled={extracting}>
              {extracting ? '⟳ Extraindo dados…' : '📎 Selecionar arquivo'}
            </button>
            <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" style={{ display: 'none' }} onChange={handleUpload} />
            <button className="btn btn-outline" onClick={() => { setHasSheet(false); setWarnings(checkWarnings(form)) }}>
              Preencher manualmente
            </button>
          </div>
          {extracting && (
            <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-2)' }}>
              Lendo arquivo e extraindo premissas com IA… pode levar 15–30 segundos.
            </div>
          )}
        </div>
      )}

      {/* Extracted notice */}
      {Object.keys(extractedFields).length > 0 && (
        <div style={{ padding: '10px 14px', background: '#EFF6FF', border: '1px solid #3B82F6',
                      borderRadius: 8, fontSize: 13, marginBottom: 14, color: '#1E40AF' }}>
          ✨ {Object.keys(extractedFields).length} campos extraídos da planilha (destacados em azul). Revise e confirme antes de calcular.
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Coluna esquerda */}
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <SectionTitle n="1" title="Produção" />
            {[
              { name: 'feedstock_t_ano', label: 'Feedstock disponível', unit: 't/ano (base seca)', step: 100, min: 0, hint: 'Biomassa seca processável por ano' },
              { name: 'yield_pirolise', label: 'Rendimento de pirólise', unit: 'ex: 0.28 = 28%', step: 0.01, min: 0, hint: 'Fração de biochar por t de feedstock' },
              { name: 'fator_carbono', label: 'Fator de carbono', unit: 'tCO₂e / t biochar', step: 0.1, min: 0, hint: 'Créditos gerados por tonelada de biochar' },
            ].map(f => (
              <FieldRow key={f.name} {...f} value={form[f.name]} onChange={setField}
                warnings={warnings} confirmedWarnings={confirmedWarnings}
                onConfirmWarning={k => setConfirmedWarnings(p => ({ ...p, [k]: true }))}
              />
            ))}
            <div style={{ padding: '10px 12px', background: 'var(--navy-light)', borderRadius: 8, fontSize: 12 }}>
              <b>Biochar estimado:</b> {((form.feedstock_t_ano || 0) * (form.yield_pirolise || 0)).toLocaleString('pt-BR', { maximumFractionDigits: 0 })} t/ano &nbsp;|&nbsp;
              <b>Créditos:</b> {((form.feedstock_t_ano || 0) * (form.yield_pirolise || 0) * (form.fator_carbono || 0)).toLocaleString('pt-BR', { maximumFractionDigits: 0 })} tCO₂e/ano
            </div>
          </div>

          <div className="card">
            <SectionTitle n="2" title="Receitas" />
            {[
              { name: 'preco_credito_usd', label: 'Preço do crédito de carbono', unit: 'USD / tCO₂e', step: 5, min: 0 },
              { name: 'fx_brl_usd', label: 'Câmbio', unit: 'BRL / USD', step: 0.05, min: 0 },
              { name: 'preco_biochar_brl', label: 'Preço de venda do biochar', unit: 'BRL / t (0 = não vende)', step: 50, min: 0 },
            ].map(f => (
              <FieldRow key={f.name} {...f} value={form[f.name]} onChange={setField}
                warnings={warnings} confirmedWarnings={confirmedWarnings}
                onConfirmWarning={k => setConfirmedWarnings(p => ({ ...p, [k]: true }))}
              />
            ))}
            <div style={{ padding: '10px 12px', background: 'var(--navy-light)', borderRadius: 8, fontSize: 12 }}>
              <b>Receita carbono/ano:</b> {fmtBRL(
                (form.feedstock_t_ano || 0) * (form.yield_pirolise || 0) * (form.fator_carbono || 0) * (form.preco_credito_usd || 0) * (form.fx_brl_usd || 0)
              )}
            </div>
          </div>
        </div>

        {/* Coluna direita */}
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <SectionTitle n="3" title="Custos" />
            {[
              { name: 'capex_total_brl', label: 'CAPEX total', unit: 'BRL', step: 100000, min: 0, hint: 'Investimento inicial total' },
              { name: 'opex_anual_brl', label: 'OPEX anual', unit: 'BRL/ano', step: 50000, min: 0, hint: 'Custos operacionais anuais totais' },
              { name: 'vida_util_anos', label: 'Vida útil (depreciação)', unit: 'anos', step: 1, min: 1 },
            ].map(f => (
              <FieldRow key={f.name} {...f} value={form[f.name]} onChange={setField}
                warnings={warnings} confirmedWarnings={confirmedWarnings}
                onConfirmWarning={k => setConfirmedWarnings(p => ({ ...p, [k]: true }))}
              />
            ))}
          </div>

          <div className="card">
            <SectionTitle n="4" title="Financeiro" />
            <FieldRow name="wacc" label="WACC / Taxa de desconto" unit="ex: 0.12 = 12%" step={0.005} min={0}
              value={form.wacc} onChange={setField} warnings={warnings} confirmedWarnings={confirmedWarnings}
              onConfirmWarning={k => setConfirmedWarnings(p => ({ ...p, [k]: true }))}
            />
            <SelectRow name="regime_tributario" label="Regime tributário"
              value={form.regime_tributario} onChange={setField}
              options={[{ value: 'LP', label: 'Lucro Presumido (LP)' }, { value: 'LR', label: 'Lucro Real (LR)' }]}
            />
            <FieldRow name="horizonte_anos" label="Horizonte do projeto" unit="anos" step={1} min={1}
              value={form.horizonte_anos} onChange={setField} warnings={[]} confirmedWarnings={{}} onConfirmWarning={() => {}} />
            <FieldRow name="ano_investimento" label="Ano de investimento" step={1} min={2020}
              value={form.ano_investimento} onChange={setField} warnings={[]} confirmedWarnings={{}} onConfirmWarning={() => {}} />
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

  // ── Step: RESULTS ───────────────────────────────────────────────────────────
  const r = resultado || {}
  const irr = r.irr
  const irrColor = irr == null ? 'var(--text-2)' : irr >= (form.wacc * 100) ? 'var(--green)' : 'var(--red)'

  return (
    <div>
      {/* KPIs */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <KPICard label="TIR (IRR)" value={irr != null ? `${irr.toFixed(1)}%` : '—'} color={irrColor}
          sub={`WACC: ${(form.wacc * 100).toFixed(0)}%`} />
        <KPICard label="VPL" value={fmtBRL(r.npv_brl)} color={r.npv_brl >= 0 ? 'var(--green)' : 'var(--red)'} />
        <KPICard label="Payback" value={r.payback_year || 'Não atingido'} />
        <KPICard label="EBITDA Ano 1" value={fmtBRL(r.ebitda_yr1)} sub={r.margem_ebitda_pct != null ? `Margem ${r.margem_ebitda_pct.toFixed(1)}%` : ''} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        {/* Produção */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 10 }}>Produção Estimada</div>
          {[
            ['Feedstock (t/ano)', `${(form.feedstock_t_ano || 0).toLocaleString('pt-BR')} t`],
            ['Biochar produzido', `${(r.biochar_t_ano || 0).toLocaleString('pt-BR')} t/ano`],
            ['Créditos gerados', `${(r.creditos_tco2_ano || 0).toLocaleString('pt-BR')} tCO₂e/ano`],
            ['Receita bruta ano 1', fmtBRL(r.receita_bruta_yr1)],
            ['OPEX ano 1', fmtBRL(r.opex_yr1)],
          ].map(([l, v]) => (
            <div key={l} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0',
                                  borderBottom: '1px solid var(--border)', fontSize: 13 }}>
              <span style={{ color: 'var(--text-2)' }}>{l}</span>
              <span style={{ fontWeight: 600 }}>{v}</span>
            </div>
          ))}
        </div>

        {/* Adicionalidade */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 10 }}>Teste de Adicionalidade Financeira</div>
          <div style={{ padding: '12px', borderRadius: 8, marginBottom: 10,
                        background: r.adicionalidade_financeira ? '#F0FDF4' : '#FEF2F2',
                        border: `2px solid ${r.adicionalidade_financeira ? 'var(--green)' : 'var(--red)'}` }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: r.adicionalidade_financeira ? 'var(--green)' : 'var(--red)' }}>
              {r.adicionalidade_financeira ? '✓ Confirmada' : '✗ Não confirmada'}
            </div>
            <div style={{ fontSize: 12, marginTop: 4, color: 'var(--text-2)' }}>
              TIR sem receita de carbono: {r.irr_sem_carbono != null ? `${r.irr_sem_carbono.toFixed(1)}%` : 'Inviável'}
            </div>
          </div>
          {[
            ['TIR com carbono', irr != null ? `${irr.toFixed(1)}%` : '—'],
            ['TIR sem carbono', r.irr_sem_carbono != null ? `${r.irr_sem_carbono.toFixed(1)}%` : 'Inviável'],
            ['Preço break-even', r.preco_breakeven_usd != null ? fmtUSD(r.preco_breakeven_usd) + '/tCO₂' : '—'],
            ['WACC referência', fmtPct((form.wacc || 0) * 100)],
          ].map(([l, v]) => (
            <div key={l} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0',
                                  borderBottom: '1px solid var(--border)', fontSize: 13 }}>
              <span style={{ color: 'var(--text-2)' }}>{l}</span>
              <span style={{ fontWeight: 600 }}>{v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Sensibilidade */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title" style={{ marginBottom: 10 }}>Sensibilidade — Preço do Crédito × TIR</div>
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
                  const color = s.irr == null ? 'var(--text-2)' : s.irr >= wacc_pct ? 'var(--green)' : 'var(--red)'
                  return (
                    <td key={s.preco_usd} style={{ padding: '6px 8px', textAlign: 'center',
                                                   fontWeight: 700, color, background: s.irr != null && s.irr >= wacc_pct ? '#F0FDF4' : '#FEF2F2' }}>
                      {s.irr != null ? `${s.irr.toFixed(1)}%` : '—'}
                    </td>
                  )
                })}
              </tr>
            </tbody>
          </table>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 6 }}>
          Verde = TIR ≥ WACC ({fmtPct((form.wacc || 0.12) * 100)}). Linha a cada $20.
        </div>
      </div>

      {/* Ações */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <button className="btn btn-outline" onClick={() => setStep('form')}>← Editar premissas</button>
        <button className="btn btn-outline" onClick={handleExport}>⬇ Exportar Excel</button>
        <div style={{ flex: 1 }} />
        <div style={{ padding: '10px 14px', background: 'var(--navy-light)', borderRadius: 8, fontSize: 13, color: 'var(--navy)' }}>
          💡 Acesse o <b>Financial Lab</b> na sidebar para análise interativa com sliders
        </div>
      </div>
    </div>
  )
}
