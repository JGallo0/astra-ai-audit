import { useState, useContext, useEffect } from 'react'
import axios from 'axios'
import { AppCtx } from '../../App'

const NAVY  = '#1A3160'
const GREEN = '#16A34A'
const AMBER = '#B45309'
const RED   = '#DC2626'

const GRADE_COLOR = {
  'A+': GREEN, 'A': GREEN, 'B+': AMBER, 'B': AMBER, 'C': RED,
}

const METHOD_LABELS = {
  isometric:  'Isometric Biochar v1.2',
  puro_earth: 'Puro.Earth Edition 2025',
  rainbow:    'Rainbow Carbon',
  c_sink:     'Global C-SINK / CSI-EBI',
  verra_vcs:  'Verra VCS',
}

const DIM_LABELS = {
  feedstock_eligibility: 'Elegibilidade Feedstock',
  carbon_accounting:     'Contabilidade de Carbono',
  additionality:         'Adicionalidade',
  permanence:            'Permanência',
  monitoring:            'Monitoramento',
  environmental_social:  'Ambiental & Social',
}

const DIM_WEIGHTS = {
  feedstock_eligibility: 20,
  carbon_accounting:     25,
  additionality:         20,
  permanence:            15,
  monitoring:            10,
  environmental_social:  10,
}

function ScoreBar({ value, max = 100, color }) {
  const pct = value != null ? Math.round((value / max) * 100) : 0
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 8, background: '#F3F4F6', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color || NAVY, borderRadius: 4, transition: 'width .3s' }} />
      </div>
      <span style={{ fontSize: 12, fontWeight: 700, color: color || NAVY, minWidth: 36, textAlign: 'right' }}>
        {value != null ? `${value.toFixed(0)}%` : '—'}
      </span>
    </div>
  )
}

export default function FitMetodologicoTab({ project }) {
  const { API, methodologies } = useContext(AppCtx)
  const [selectedMethods, setSelectedMethods] = useState(['isometric', 'puro_earth'])
  const [auditMode, setAuditMode] = useState('development')
  const [result, setResult]   = useState(null)
  const [loading, setLoading]   = useState(false)
  const [loadingStep, setLoadingStep] = useState('')
  const [error, setError]       = useState('')
  const [marketData, setMarketData] = useState({})
  const [openModules, setOpenModules] = useState({ mod3: false, mod4: false })

  useEffect(() => {
    axios.get(`${API}/api/methodologies/market-overview`)
      .then(r => setMarketData(r.data))
      .catch(() => {})
  }, [API])

  function toggleMethod(key) {
    setSelectedMethods(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    )
  }

  async function runAssessment() {
    if (selectedMethods.length < 1) {
      setError('Selecione ao menos uma metodologia.'); return
    }
    setLoading(true); setLoadingStep('Extraindo perfil do projeto…'); setError(''); setResult(null)

    // Simula etapas visuais para dar feedback durante a espera
    const steps = [
      [1500,  'Extraindo perfil do projeto (ProjectProfile)…'],
      [4000,  'Rodando extração Isometric nativa…'],
      [12000, 'Avaliando requisitos Isometric…'],
      [20000, 'Avaliando requisitos Puro.Earth…'],
      [35000, 'Calculando scores por dimensão…'],
      [50000, 'Gerando análise comparativa…'],
    ]
    const timers = steps.map(([delay, msg]) =>
      setTimeout(() => setLoadingStep(msg), delay)
    )

    try {
      const r = await axios.post(`${API}/api/projects/${project.id}/assessment`, {
        methodologies: selectedMethods,
        audit_mode: auditMode,
      }, { timeout: 180000 })
      timers.forEach(clearTimeout)
      setResult(r.data)
    } catch (e) {
      timers.forEach(clearTimeout)
      setError(e.response?.data?.detail || 'Erro ao executar assessment.')
    } finally {
      setLoading(false)
      setLoadingStep('')
    }
  }

  const methods = result
    ? Object.entries(result.methodologies || {}).sort((a, b) => b[1].overall - a[1].overall)
    : []

  const dims = Object.keys(DIM_LABELS)

  return (
    <div>
      {/* Config */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title" style={{ marginBottom: 10 }}>Fit Metodológico — Methodology Assessment</div>
        <div style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 14, lineHeight: 1.5 }}>
          Avalia o projeto contra todas as metodologias selecionadas com o mesmo framework.
          A metodologia com maior score é a mais aderente ao perfil do projeto.
        </div>

        {/* Methodology selection */}
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-2)', marginBottom: 8 }}>
            Metodologias a avaliar:
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {(methodologies.length > 0 ? methodologies : [
              { key: 'isometric', label: 'Isometric Biochar v1.2' },
              { key: 'puro_earth', label: 'Puro.Earth Edition 2025' },
            ]).map(m => {
              const key = m.key || m
              const label = m.label || METHOD_LABELS[key] || key
              const active = selectedMethods.includes(key)
              return (
                <button key={key} onClick={() => toggleMethod(key)} style={{
                  padding: '6px 14px', borderRadius: 20, fontSize: 13, cursor: 'pointer',
                  border: `1px solid ${active ? NAVY : '#D1D5DB'}`,
                  background: active ? NAVY : 'white',
                  color: active ? 'white' : '#374151',
                  fontWeight: active ? 600 : 400,
                }}>
                  {label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Mode + Run */}
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-2)', marginBottom: 6 }}>Modo</div>
            <select value={auditMode} onChange={e => setAuditMode(e.target.value)}
              style={{ padding: '6px 10px', fontSize: 13, border: '1px solid var(--border)', borderRadius: 6 }}>
              <option value="development">Desenvolvimento (PDD)</option>
              <option value="operational">Operacional</option>
            </select>
          </div>
          <button className="btn btn-primary" onClick={runAssessment} disabled={loading}
            style={{ padding: '8px 24px', fontSize: 14 }}>
            {loading ? '⟳ Analisando…' : '🔍 Executar Assessment'}
          </button>
        </div>

        {error && (
          <div style={{ marginTop: 12, padding: '8px 12px', background: '#FEF2F2',
                        color: RED, borderRadius: 6, fontSize: 13 }}>{error}</div>
        )}
        {loading && (
          <div style={{
            marginTop: 14, padding: '14px 18px',
            background: '#EEF2FA', borderRadius: 10,
            border: '1px solid #C7D4EF',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 20, height: 20, border: `3px solid #1A3160`,
                borderTopColor: 'transparent', borderRadius: '50%',
                animation: 'spin 0.8s linear infinite', flexShrink: 0,
              }} />
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#1A3160' }}>
                  {loadingStep || 'Iniciando assessment…'}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 2 }}>
                  Pode levar até 60 segundos — a extração Isometric é a etapa mais longa
                </div>
              </div>
            </div>
          </div>
        )}
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>

      {result && !loading && (
        <>
          {/* Recomendação */}
          {result.recommendation && (
            <div className="card" style={{
              marginBottom: 16,
              border: `2px solid ${NAVY}`,
              background: '#EEF2FA',
            }}>
              <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
                <div style={{ fontSize: 36 }}>🏆</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-2)',
                                textTransform: 'uppercase', letterSpacing: 1 }}>
                    Metodologia Recomendada
                  </div>
                  <div style={{ fontSize: 18, fontWeight: 800, color: NAVY, marginTop: 2 }}>
                    {METHOD_LABELS[result.recommendation] || result.recommendation}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text)', marginTop: 6, lineHeight: 1.5 }}>
                    {result.recommendation_reasoning}
                  </div>
                </div>
                <div style={{ textAlign: 'center', flexShrink: 0 }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: NAVY }}>
                    +{result.recommendation_confidence?.toFixed(0)}pp
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-2)' }}>vantagem</div>
                </div>
              </div>
            </div>
          )}

          {/* Comparativo de scores */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-title" style={{ marginBottom: 14 }}>
              Score por Metodologia — 6 Dimensões Universais
            </div>

            {/* Header com nomes das metodologias */}
            <div style={{ display: 'grid',
                          gridTemplateColumns: `200px repeat(${methods.length}, 1fr)`,
                          gap: 12, marginBottom: 10 }}>
              <div />
              {methods.map(([key, data]) => {
                const grade = data.grade
                const gradeColor = GRADE_COLOR[grade] || '#6B7280'
                const isRec = key === result.recommendation
                return (
                  <div key={key} style={{
                    textAlign: 'center', padding: '10px 6px',
                    background: isRec ? '#EEF2FA' : '#F9FAFB',
                    borderRadius: 8,
                    border: isRec ? `2px solid ${NAVY}` : '1px solid #E5E7EB',
                  }}>
                    <div style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 4 }}>
                      {METHOD_LABELS[key] || key}
                    </div>
                    <div style={{ fontSize: 32, fontWeight: 800, color: gradeColor, lineHeight: 1 }}>
                      {grade}
                    </div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: gradeColor }}>
                      {data.overall?.toFixed(0)}%
                    </div>
                    {isRec && (
                      <div style={{ fontSize: 10, color: NAVY, fontWeight: 700, marginTop: 2 }}>
                        ★ Recomendado
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Dimensões */}
            {dims.map(dim => {
              const scores = methods.map(([key, data]) =>
                (data.dimensions || {})[dim] ?? null
              )
              const maxScore = Math.max(...scores.filter(s => s != null))
              return (
                <div key={dim} style={{
                  display: 'grid',
                  gridTemplateColumns: `200px repeat(${methods.length}, 1fr)`,
                  gap: 12, marginBottom: 10, alignItems: 'center',
                }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600 }}>{DIM_LABELS[dim]}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-2)' }}>
                      peso {DIM_WEIGHTS[dim]}%
                    </div>
                  </div>
                  {scores.map((score, i) => {
                    const [key] = methods[i]
                    const isBest = score === maxScore && score != null
                    const color = score == null ? '#9CA3AF'
                      : score >= 80 ? GREEN
                      : score >= 60 ? AMBER
                      : RED
                    return (
                      <div key={key} style={{
                        padding: '6px 8px',
                        background: isBest ? color + '12' : 'transparent',
                        borderRadius: 6,
                        border: isBest ? `1px solid ${color}40` : '1px solid transparent',
                      }}>
                        <ScoreBar value={score} color={color} />
                      </div>
                    )
                  })}
                </div>
              )
            })}
          </div>

          {/* Análise diferencial */}
          {(result.differential || []).length > 0 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-title" style={{ marginBottom: 12 }}>
                Diferenças Metodológicas — Onde o Projeto se Distingue
              </div>
              {result.differential.map((diff, i) => {
                const methods2 = Object.keys(result.methodologies || {})
                return (
                  <div key={i} style={{
                    padding: '10px 14px', marginBottom: 8, borderRadius: 8,
                    background: '#F9FAFB', borderLeft: `4px solid ${NAVY}`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between',
                                  alignItems: 'flex-start', gap: 12, marginBottom: 4 }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{DIM_LABELS[diff.dimension]}</div>
                      <div style={{ display: 'flex', gap: 12, flexShrink: 0, fontSize: 12 }}>
                        {methods2.map(key => (
                          <span key={key} style={{ color: GRADE_COLOR[result.methodologies[key]?.grade] || '#6B7280' }}>
                            {METHOD_LABELS[key]?.split(' ')[0]}: {(diff[key] || 0).toFixed(0)}%
                          </span>
                        ))}
                        <span style={{ fontWeight: 700, color: NAVY }}>Δ{diff.delta?.toFixed(0)}pp</span>
                      </div>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.4 }}>
                      {diff.reasoning}
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* Principais gaps por metodologia */}
          {methods.map(([key, data]) => {
            const gaps = data.gaps || []
            if (!gaps.length) return null
            return (
              <div key={key} className="card" style={{ marginBottom: 16 }}>
                <div className="card-title" style={{ marginBottom: 10 }}>
                  Gaps — {METHOD_LABELS[key] || key}
                  <span style={{ fontSize: 12, color: 'var(--text-2)', fontWeight: 400, marginLeft: 8 }}>
                    ({gaps.length} gaps identificados)
                  </span>
                </div>
                {gaps.slice(0, 5).map(g => (
                  <div key={g.requirement_id} style={{
                    padding: '8px 12px', marginBottom: 6, borderRadius: 6,
                    background: g.status === 'non_compliant' ? '#FEF2F2' : '#FFFBEB',
                    borderLeft: `3px solid ${g.status === 'non_compliant' ? RED : AMBER}`,
                  }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 2 }}>
                      <span style={{ fontFamily: 'monospace', fontSize: 11, color: NAVY,
                                     fontWeight: 700 }}>{g.requirement_id}</span>
                      <span style={{ fontSize: 12, fontWeight: 600 }}>{g.title}</span>
                    </div>
                    {g.gap && <div style={{ fontSize: 12, color: '#4B5563' }}>→ {g.gap}</div>}
                  </div>
                ))}
              </div>
            )
          })}
          {/* Módulo 3 — Custos e Prazos */}
          {Object.keys(marketData).length > 0 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <button onClick={() => setOpenModules(p => ({ ...p, mod3: !p.mod3 }))}
                style={{ width: '100%', display: 'flex', justifyContent: 'space-between',
                         alignItems: 'center', background: 'none', border: 'none',
                         cursor: 'pointer', padding: 0 }}>
                <div className="card-title" style={{ marginBottom: 0 }}>
                  Módulo 3 — Custos de Verificação e Prazos
                </div>
                <span style={{ color: NAVY, fontSize: 14 }}>{openModules.mod3 ? '▲' : '▼'}</span>
              </button>
              {openModules.mod3 && (
                <div style={{ marginTop: 14, overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                    <thead>
                      <tr style={{ background: NAVY, color: 'white' }}>
                        {['Item', ...selectedMethods.map(m => (marketData[m]?.short || m))].map(h => (
                          <th key={h} style={{ padding: '7px 10px', textAlign: h === 'Item' ? 'left' : 'center' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { label: 'Taxa abertura conta', key: d => d?.costs?.registry?.account_opening_usd != null ? (d.costs.registry.account_opening_usd === 0 ? 'Grátis' : `US$ ${d.costs.registry.account_opening_usd.toLocaleString()}`) : d?.costs?.registry?.note || '—' },
                        { label: 'Manutenção anual', key: d => { const r = d?.costs?.registry; if (!r) return '—'; if (r.annual_maintenance_usd === 0) return 'Grátis'; if (r.annual_maintenance_usd) return `US$ ${r.annual_maintenance_usd}/ano`; if (r.annual_maintenance_eur) return `€${r.annual_maintenance_eur.toLocaleString()}/ano`; return r.note || '—'; } },
                        { label: 'Taxa por crédito', key: d => d?.costs?.issuance?.per_credit_usd != null ? `US$ ${d.costs.issuance.per_credit_usd}/crédito` : (d?.costs?.issuance?.per_credit_eur || d?.costs?.issuance?.note || '—') },
                        { label: 'VVB — 1ª auditoria', key: d => d?.costs?.vvb?.initial_audit_range || d?.costs?.vvb?.initial_validation_range || '—' },
                        { label: 'VVB — periódica', key: d => d?.costs?.vvb?.periodic_audit_range || d?.costs?.vvb?.annual_verification_range || '—' },
                        { label: 'Custo total ano 1 (est.)', key: d => d?.costs?.total_first_year_estimate_usd || '—', bold: true },
                        { label: 'Custo anual recorrente', key: d => d?.costs?.total_ongoing_per_year_usd || '—' },
                        { label: 'Registro (meses)', key: d => d?.timelines?.registration_months || '—' },
                        { label: '1ª emissão (meses)', key: d => d?.timelines?.first_issuance_months || '—', bold: true },
                        { label: 'Prazo de emissão', key: d => d?.timelines?.issuance_deadline || '—' },
                      ].map(({ label, key, bold }) => (
                        <tr key={label} style={{ borderBottom: '1px solid #F3F4F6', background: bold ? '#EEF2FA' : 'white' }}>
                          <td style={{ padding: '6px 10px', fontWeight: bold ? 700 : 400 }}>{label}</td>
                          {selectedMethods.map(m => (
                            <td key={m} style={{ padding: '6px 10px', textAlign: 'center',
                                                  fontWeight: bold ? 700 : 400, fontSize: 11 }}>
                              {key(marketData[m]) || '—'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 8 }}>
                    Fontes: Sylvera Methodology Assessment (Out 2025), Puro Platform Agreement 2025, Verra Fee Schedule 2024, Isometric Standard v1.5.
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Módulo 4 — Market Acceptance */}
          {Object.keys(marketData).length > 0 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <button onClick={() => setOpenModules(p => ({ ...p, mod4: !p.mod4 }))}
                style={{ width: '100%', display: 'flex', justifyContent: 'space-between',
                         alignItems: 'center', background: 'none', border: 'none',
                         cursor: 'pointer', padding: 0 }}>
                <div className="card-title" style={{ marginBottom: 0 }}>
                  Módulo 4 — Aceitação de Mercado e Padrões
                </div>
                <span style={{ color: NAVY, fontSize: 14 }}>{openModules.mod4 ? '▲' : '▼'}</span>
              </button>
              {openModules.mod4 && (
                <div style={{ marginTop: 14 }}>
                  {/* Standards */}
                  <div style={{ overflowX: 'auto', marginBottom: 14 }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                      <thead>
                        <tr style={{ background: NAVY, color: 'white' }}>
                          {['Padrão / Certificação', ...selectedMethods.map(m => marketData[m]?.short || m)].map(h => (
                            <th key={h} style={{ padding: '7px 10px', textAlign: h.length < 20 ? 'center' : 'left' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {['icroa', 'corsia', 'icvcm_ccp'].map(std => {
                          const STD_LABELS = { icroa: 'ICROA', corsia: 'CORSIA', icvcm_ccp: 'ICVCM / CCP' }
                          const STATUS_COLORS = { approved: GREEN, conditional: AMBER, pending: '#6366F1', not_eligible: RED, not_applicable: '#9CA3AF' }
                          return (
                            <tr key={std} style={{ borderBottom: '1px solid #F3F4F6' }}>
                              <td style={{ padding: '8px 10px', fontWeight: 600 }}>{STD_LABELS[std]}</td>
                              {selectedMethods.map(m => {
                                const s = marketData[m]?.market?.standards?.[std]
                                const color = STATUS_COLORS[s?.status] || '#9CA3AF'
                                return (
                                  <td key={m} style={{ padding: '8px 10px', textAlign: 'center' }}>
                                    <span style={{ fontSize: 11, fontWeight: 600, color,
                                                   background: color + '18', padding: '2px 8px',
                                                   borderRadius: 10, display: 'inline-block' }}>
                                      {s?.label || '—'}
                                    </span>
                                    {s?.detail && <div style={{ fontSize: 10, color: '#6B7280', marginTop: 2 }}>{s.detail}</div>}
                                  </td>
                                )
                              })}
                            </tr>
                          )
                        })}
                        {/* Price range */}
                        <tr style={{ borderBottom: '1px solid #F3F4F6', background: '#EEF2FA' }}>
                          <td style={{ padding: '8px 10px', fontWeight: 700 }}>Preço médio (USD/tCO₂)</td>
                          {selectedMethods.map(m => (
                            <td key={m} style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 700, color: NAVY }}>
                              {marketData[m]?.market?.price_range_usd
                                ? `US$ ${marketData[m].market.price_range_usd}`
                                : '—'}
                            </td>
                          ))}
                        </tr>
                        {/* Market share */}
                        <tr style={{ borderBottom: '1px solid #F3F4F6' }}>
                          <td style={{ padding: '8px 10px' }}>Market share (biochar)</td>
                          {selectedMethods.map(m => (
                            <td key={m} style={{ padding: '8px 10px', textAlign: 'center', fontSize: 11 }}>
                              {marketData[m]?.market?.market_share || '—'}
                            </td>
                          ))}
                        </tr>
                        {/* Compliance markets */}
                        <tr>
                          <td style={{ padding: '8px 10px' }}>Mercados compliance</td>
                          {selectedMethods.map(m => {
                            const cms = marketData[m]?.market?.compliance_markets || []
                            return (
                              <td key={m} style={{ padding: '8px 10px', textAlign: 'center', fontSize: 11 }}>
                                {cms.length === 0 ? <span style={{ color: '#9CA3AF' }}>Nenhum</span>
                                  : cms.map(c => (
                                    <span key={c.name} style={{ display: 'inline-block', margin: '1px 2px',
                                      padding: '1px 6px', borderRadius: 8, background: '#F0FDF4',
                                      color: GREEN, fontSize: 10, fontWeight: 600 }}>
                                      {c.name}
                                    </span>
                                  ))}
                              </td>
                            )
                          })}
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  {/* Strengths / Risks per method */}
                  <div style={{ display: 'grid', gridTemplateColumns: `repeat(${selectedMethods.length}, 1fr)`, gap: 12 }}>
                    {selectedMethods.map(m => {
                      const md = marketData[m]?.market || {}
                      return (
                        <div key={m} style={{ background: '#F9FAFB', borderRadius: 8, padding: '10px 12px' }}>
                          <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 6, color: NAVY }}>
                            {marketData[m]?.short || m}
                          </div>
                          {(md.strengths || []).map(s => (
                            <div key={s} style={{ fontSize: 11, color: GREEN, marginBottom: 3 }}>✓ {s}</div>
                          ))}
                          {(md.risks || []).map(r => (
                            <div key={r} style={{ fontSize: 11, color: RED, marginBottom: 3 }}>✗ {r}</div>
                          ))}
                          {md.price_note && (
                            <div style={{ fontSize: 10, color: '#9CA3AF', marginTop: 6, lineHeight: 1.3 }}>
                              {md.price_note}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {!result && !loading && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <div className="empty-state-title">Fit Metodológico</div>
            <div className="empty-state-sub">
              Selecione as metodologias e execute o assessment para comparar a aderência do projeto a cada padrão.
              Usa o mesmo framework de extração (ProjectProfile) e dimensões universais para garantir comparabilidade.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
