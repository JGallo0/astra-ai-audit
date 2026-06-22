import { useState, useEffect, useContext } from 'react'
import axios from 'axios'
import { AppCtx } from '../../App'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'

const MODULES = [
  'Elegibilidade', 'Adicionalidade', 'Durabilidade', 'Produção',
  'Produto', 'Armazenamento', 'Feedstock', 'Quantificação',
  'Emissões', 'Amostragem', 'Rastreabilidade', 'Gestão', 'Salvaguardas',
]

// Status config — ícone, label, cor (motor v1 inglês + legado português)
const STATUS_CONFIG = {
  compliant:                { icon: '✅', label: 'Conforme',              color: 'var(--green)',  bg: 'var(--green-light)' },
  partial:                  { icon: '⚠️', label: 'Parcial',               color: 'var(--amber)',  bg: 'var(--amber-light)' },
  non_compliant:            { icon: '❌', label: 'Não conforme',          color: 'var(--red)',    bg: 'var(--red-light)' },
  not_applicable:           { icon: '—',  label: 'N/A',                   color: 'var(--text-3)', bg: '#F1F5F9' },
  future_evidence_required: { icon: '🔮', label: 'Evidência futura',      color: '#7C3AED',       bg: '#F5F3FF' },
  error:                    { icon: '⚠',  label: 'Erro de análise',       color: 'var(--text-2)', bg: '#F1F5F9' },
  // legado
  'Conforme':               { icon: '✅', label: 'Conforme',              color: 'var(--green)',  bg: 'var(--green-light)' },
  'Parcialmente conforme':  { icon: '⚠️', label: 'Parcial',               color: 'var(--amber)',  bg: 'var(--amber-light)' },
  'Não conforme':           { icon: '❌', label: 'Não conforme',          color: 'var(--red)',    bg: 'var(--red-light)' },
  'Não evidenciado':        { icon: '—',  label: 'Não evidenciado',       color: 'var(--text-3)', bg: '#F1F5F9' },
  'Erro de análise':        { icon: '⚠',  label: 'Erro',                  color: 'var(--text-2)', bg: '#F1F5F9' },
}

const RISK_CLS = {
  low: 'badge-green', baixo: 'badge-green',
  medium: 'badge-amber', medio: 'badge-amber',
  high: 'badge-red', alto: 'badge-red',
  none: 'badge-gray', unknown: 'badge-gray',
}

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.error
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '3px 8px', borderRadius: 20, fontSize: 11, fontWeight: 700,
      color: cfg.color, background: cfg.bg,
    }}>
      <span style={{ fontSize: 10 }}>{cfg.icon}</span>
      {cfg.label}
    </span>
  )
}

function FindingRow({ f }) {
  const [open, setOpen] = useState(false)
  const score = Math.round(f.requirement_score ?? f.score ?? 0)
  const scoreColor = score >= 75 ? 'var(--green)' : score >= 50 ? 'var(--amber)' : 'var(--red)'

  return (
    <>
      <tr
        onClick={() => setOpen(o => !o)}
        style={{ cursor: 'pointer' }}
        className={open ? 'finding-row-open' : ''}
      >
        <td style={{ width: 110 }}>
          {f.source_url
            ? <a href={f.source_url} target="_blank" rel="noreferrer"
                style={{ fontSize: 11, color: 'var(--navy)', fontWeight: 600, textDecoration: 'none' }}
                onClick={e => e.stopPropagation()}>
                {f.requirement_id} ↗
              </a>
            : <span style={{ fontSize: 11, color: 'var(--text-3)', fontWeight: 600 }}>{f.requirement_id}</span>
          }
        </td>
        <td>
          <span className="badge badge-blue" style={{ fontSize: 10 }}>
            {(f.module || '').split(':').pop().replace(/_/g, ' ')}
          </span>
        </td>
        <td style={{ fontSize: 12, maxWidth: 280 }}>
          <span style={{ fontWeight: 600 }}>{f.title}</span>
        </td>
        <td><StatusBadge status={f.status} /></td>
        <td>
          <span className={`badge ${RISK_CLS[f.risk] || 'badge-gray'}`} style={{ fontSize: 10 }}>
            {f.risk}
          </span>
        </td>
        <td style={{ fontWeight: 700, color: scoreColor, textAlign: 'right', width: 48 }}>
          {score}
        </td>
        <td style={{ width: 20, color: 'var(--text-3)', fontSize: 12 }}>
          {open ? '▲' : '▼'}
        </td>
      </tr>

      {open && (
        <tr style={{ background: '#FAFBFD' }}>
          <td colSpan={7} style={{ padding: '10px 16px 14px', borderBottom: '1px solid var(--border)' }}>
            {f.requirement_text && (
              <div style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 8,
                padding: '6px 10px', background: '#EFF3F9', borderRadius: 6,
                borderLeft: '3px solid var(--navy)' }}>
                <span style={{ fontWeight: 700, color: 'var(--navy)' }}>Protocolo: </span>
                {f.requirement_text}
              </div>
            )}
            {f.gap && (
              <div style={{ marginBottom: 6 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--red)' }}>Gap: </span>
                <span style={{ fontSize: 12, color: 'var(--text)' }}>{f.gap}</span>
              </div>
            )}
            {f.recommendation && (
              <div style={{ marginBottom: 6 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--green)' }}>Recomendação: </span>
                <span style={{ fontSize: 12, color: 'var(--text)' }}>{f.recommendation}</span>
              </div>
            )}
            {f.notes && f.notes.length > 0 && (
              <div style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 4 }}>
                {f.notes.filter(n => !n.startsWith('[Protocolo]')).map((n, i) => (
                  <div key={i} style={{ marginBottom: 2 }}>• {n}</div>
                ))}
              </div>
            )}
            {f.source_url && (
              <a href={f.source_url} target="_blank" rel="noreferrer"
                style={{ fontSize: 11, color: 'var(--navy)', fontWeight: 600, marginTop: 6, display: 'inline-block' }}>
                📖 Ver no Isometric Registry →
              </a>
            )}
          </td>
        </tr>
      )}
    </>
  )
}

// ── Project Readiness Rating components ──────────────────────────────────────

const GRADE_COLORS = {
  'A+': { bg: '#F0FDF4', border: '#16A34A', text: '#15803D' },
  'A':  { bg: '#F0FDF4', border: '#16A34A', text: '#15803D' },
  'B+': { bg: '#FFFBEB', border: '#D97706', text: '#B45309' },
  'B':  { bg: '#FFFBEB', border: '#D97706', text: '#B45309' },
  'C':  { bg: '#FEF2F2', border: '#DC2626', text: '#B91C1C' },
}

const DIM_LABELS = {
  carbon:       'Carbon Accounting',
  additionality:'Additionality',
  permanence:   'Permanência',
  safeguards:   'Salvaguardas',
  integrity:    'Integridade do PDD',
}

function GradeBadge({ grade, label, score }) {
  const colors = GRADE_COLORS[grade] || GRADE_COLORS['C']
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16,
      background: colors.bg, border: `2px solid ${colors.border}`,
      borderRadius: 12, padding: '14px 22px',
    }}>
      <div style={{ textAlign: 'center', flexShrink: 0 }}>
        <div style={{ fontSize: 42, fontWeight: 900, color: colors.text, lineHeight: 1 }}>
          {grade}
        </div>
        <div style={{ fontSize: 10, fontWeight: 700, color: colors.text, marginTop: 2,
          textTransform: 'uppercase', letterSpacing: '.06em' }}>
          Project Readiness
        </div>
      </div>
      <div style={{ borderLeft: `1px solid ${colors.border}`, paddingLeft: 16 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: colors.text }}>{label}</div>
        <div style={{ fontSize: 12, color: 'var(--text-2)', marginTop: 2 }}>
          Score numérico: <strong>{score}%</strong>
        </div>
      </div>
    </div>
  )
}

function DimBar({ dimKey, dim }) {
  const s = dim.score || 0
  const color = s >= 80 ? '#16A34A' : s >= 60 ? '#D97706' : '#DC2626'
  const label = DIM_LABELS[dimKey] || dimKey
  const naNote = dim.na_count > 0 ? ` (${dim.na_count} N/A op.)` : ''
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>{label}{naNote}</span>
        <span style={{ fontSize: 12, fontWeight: 700, color }}>{s.toFixed(0)}%</span>
      </div>
      <div style={{ height: 7, background: 'var(--border)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${Math.min(s, 100)}%`,
          background: color, borderRadius: 4, transition: 'width .4s' }} />
      </div>
    </div>
  )
}

function ReadinessRating({ rating }) {
  if (!rating) return null
  const dims = rating.dimensions || {}
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 14 }}>
        <div>
          <div className="card-title" style={{ marginBottom: 2 }}>Project Readiness Score</div>
          <div style={{ fontSize: 11, color: 'var(--text-2)' }}>
            {rating.phase} · Modo {rating.audit_mode === 'development' ? 'Desenvolvimento' : 'Operacional'}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        {/* Grade badge */}
        <GradeBadge grade={rating.grade} label={rating.label} score={rating.overall_score} />

        {/* Dimensional bars */}
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-2)',
            textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>
            Por Dimensão
          </div>
          {Object.entries(dims).map(([key, dim]) => (
            <DimBar key={key} dimKey={key} dim={dim} />
          ))}
        </div>
      </div>

      {rating.description && (
        <div style={{ marginTop: 12, padding: '8px 12px', background: 'var(--bg-app)',
          borderRadius: 7, fontSize: 12, color: 'var(--text-2)', lineHeight: 1.5 }}>
          {rating.description}
        </div>
      )}
    </div>
  )
}

function ScoreGauge({ score }) {
  const color = score >= 75 ? 'var(--green)' : score >= 50 ? 'var(--amber)' : 'var(--red)'
  return (
    <div style={{ width:110, height:110, position:'relative', flexShrink:0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart cx="50%" cy="50%" innerRadius="65%" outerRadius="90%"
          barSize={10} data={[{ value: score, fill: color }]} startAngle={90} endAngle={-270}>
          <RadialBar dataKey="value" cornerRadius={5} background={{ fill:'var(--border)' }} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div style={{ position:'absolute', inset:0, display:'flex', flexDirection:'column',
        alignItems:'center', justifyContent:'center' }}>
        <span style={{ fontSize:20, fontWeight:800, color }}>{score}%</span>
        <span style={{ fontSize:10, color:'var(--text-2)', fontWeight:600 }}>Score</span>
      </div>
    </div>
  )
}

export default function ValidationTab() {
  const { API, projects, methodologies, activeProject } = useContext(AppCtx)

  const [selectedProjectId,  setSelectedProjectId]  = useState('')
  const [selectedMethodology, setSelectedMethodology] = useState('isometric')

  const [tab, setTab]               = useState('run')
  const [auditRuns, setAuditRuns]   = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [selectedModules, setSelectedModules] = useState([])
  const [auditMode, setAuditMode]   = useState('development')
  const [running, setRunning]       = useState(false)
  const [pollingId, setPollingId]   = useState(null)

  useEffect(() => {
    if (activeProject && !selectedProjectId) setSelectedProjectId(activeProject.id)
  }, [activeProject])

  useEffect(() => {
    return () => { if (pollingId) clearInterval(pollingId) }
  }, [pollingId])

  useEffect(() => {
    if (selectedProjectId) loadRuns(selectedProjectId)
    else setAuditRuns([])
  }, [selectedProjectId])

  async function loadRuns(projId) {
    const { data } = await axios.get(`${API}/api/projects/${projId}/audits`).catch(() => ({ data:[] }))
    setAuditRuns(data)
  }

  async function loadRun(runId) {
    const { data } = await axios.get(`${API}/api/audit/${runId}`).catch(() => ({ data:null }))
    if (data) { setSelectedRun(data); setTab('results') }
  }

  async function startAudit() {
    if (!selectedProjectId) return
    setRunning(true); setSelectedRun(null); setTab('results')
    try {
      const { data } = await axios.post(`${API}/api/projects/${selectedProjectId}/audit`, {
        methodology: selectedMethodology,
        modules: selectedModules.length > 0 ? selectedModules : null,
        audit_mode: auditMode,
      })
      const runId = data.run_id
      const id = setInterval(async () => {
        const { data: run } = await axios.get(`${API}/api/audit/${runId}`).catch(() => ({ data:null }))
        if (run && run.status !== 'running') {
          clearInterval(id); setPollingId(null); setRunning(false)
          setSelectedRun(run); loadRuns(selectedProjectId)
        }
      }, 3000)
      setPollingId(id)
    } catch { setRunning(false) }
  }

  const selectedProject = projects.find(p => p.id === selectedProjectId)
  const selectedMethodologyMeta = methodologies.find(m => m.key === selectedMethodology)

  const result        = selectedRun?.result || {}
  const findings      = result.results || result.findings || []
  const score         = result.score_data?.score ?? result.compliance_score ?? result.score ?? 0
  const scoreLabel    = result.score_label || ''
  const readinessRating = result.readiness_rating || null

  const compliant  = findings.filter(f => ['compliant','Conforme'].includes(f.status)).length
  const partial    = findings.filter(f => ['partial','future_evidence_required','Parcialmente conforme'].includes(f.status)).length
  const nonComp    = findings.filter(f => ['non_compliant','Não conforme','Não evidenciado','error'].includes(f.status)).length
  const notAppl    = findings.filter(f => f.status === 'not_applicable').length

  return (
    <div>
      {/* ── PDD × Metodologia ── */}
      <div className="card" style={{ marginBottom:16 }}>
        <div className="card-title" style={{ marginBottom:12 }}>Combinação PDD × Metodologia</div>
        <div className="grid-2" style={{ gap:12 }}>
          <div className="form-group" style={{ marginBottom:0 }}>
            <label className="form-label">PDD / Projeto</label>
            <select className="form-select" value={selectedProjectId}
              onChange={e => { setSelectedProjectId(e.target.value); setSelectedRun(null) }}>
              <option value="">— selecionar —</option>
              {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ marginBottom:0 }}>
            <label className="form-label">Metodologia</label>
            <select className="form-select" value={selectedMethodology}
              onChange={e => setSelectedMethodology(e.target.value)}>
              {methodologies.map(m => (
                <option key={m.key} value={m.key}>{m.label} {m.version}</option>
              ))}
            </select>
          </div>
        </div>

        {selectedProject && selectedMethodologyMeta && (
          <div className="mt-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="badge badge-blue" style={{ fontSize:12 }}>{selectedProject.name}</span>
              <span style={{ color:'var(--text-3)', fontWeight:700 }}>×</span>
              <span className="badge badge-green" style={{ fontSize:12 }}>
                {selectedMethodologyMeta.label} {selectedMethodologyMeta.version}
              </span>
              <span
                className="badge badge-gray"
                style={{ fontSize:10 }}
                title="Os dados extraídos do PDD ficam em cache. Auditorias repetidas são 100% determinísticas."
              >
                {selectedProject.project_data ? '⚡ cache ativo' : '🔄 extração na 1ª auditoria'}
              </span>
            </div>
            {selectedProject.project_data && (
              <button
                className="btn btn-sm btn-ghost"
                title="Força nova extração LLM dos dados do projeto (use após adicionar documentos)"
                onClick={async () => {
                  if (!confirm('Invalidar cache e forçar nova extração na próxima auditoria?')) return
                  await axios.post(`${API}/api/projects/${selectedProject.id}/reset-cache`)
                  alert('Cache invalidado. A próxima auditoria fará nova extração.')
                }}
              >
                Atualizar dados
              </button>
            )}
          </div>
        )}
      </div>

      {!selectedProjectId ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <div className="empty-state-title">Selecione um projeto e uma metodologia</div>
            <div className="empty-state-sub">Escolha a combinação acima para configurar e iniciar a auditoria.</div>
          </div>
        </div>
      ) : (
        <>
          <div className="tab-bar">
            <button className={`tab-btn${tab==='run'?     ' active':''}`} onClick={() => setTab('run')}>Configurar</button>
            <button className={`tab-btn${tab==='results'? ' active':''}`} onClick={() => setTab('results')}>Resultados</button>
            <button className={`tab-btn${tab==='history'? ' active':''}`}
              onClick={() => { setTab('history'); loadRuns(selectedProjectId) }}>Histórico</button>
          </div>

          {/* ── Configurar ── */}
          {tab === 'run' && (
            <div className="card">
              <div className="card-title">Modo de auditoria</div>
              <div className="flex gap-2" style={{ marginBottom:20 }}>
                {[
                  { key:'development',  label:'Desenvolvimento', desc:'Lacunas de evidência futura marcadas como parciais' },
                  { key:'operational',  label:'Operacional',     desc:'Avaliação estrita — evidência deve estar presente' },
                ].map(m => (
                  <button key={m.key}
                    className={`btn ${auditMode === m.key ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => setAuditMode(m.key)}
                    title={m.desc}>
                    {m.label}
                  </button>
                ))}
              </div>

              <div className="card-title" style={{ marginBottom:8 }}>Módulos de análise</div>
              <div className="alert alert-info" style={{ marginBottom:12, fontSize:12 }}>
                Deixe vazio para auditar todos os módulos. Selecione apenas os aplicáveis ao projeto.
              </div>
              <div className="flex" style={{ flexWrap:'wrap', gap:8, marginBottom:20 }}>
                {MODULES.map(m => (
                  <button key={m}
                    className={`btn btn-sm ${selectedModules.includes(m) ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => setSelectedModules(prev =>
                      prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m])}>
                    {m}
                  </button>
                ))}
              </div>

              <button className="btn btn-primary btn-lg" onClick={startAudit} disabled={running}>
                {running
                  ? <><span className="spinner" style={{width:16,height:16}} /> Executando...</>
                  : `▶ Auditar ${selectedProject?.name} × ${selectedMethodologyMeta?.label}`}
              </button>
            </div>
          )}

          {/* ── Resultados ── */}
          {tab === 'results' && (
            <>
              {running && !selectedRun && (
                <div className="card">
                  <div className="loading-box">
                    <div className="spinner" style={{width:32,height:32}} />
                    <div style={{fontWeight:700,color:'var(--navy)'}}>Auditoria em execução...</div>
                    <div style={{color:'var(--text-2)',fontSize:12}}>
                      Analisando requisito por requisito contra os documentos do projeto.
                    </div>
                  </div>
                </div>
              )}

              {selectedRun?.status === 'error' && (
                <div className="alert alert-error">Erro: {selectedRun.error || 'Erro desconhecido'}</div>
              )}

              {selectedRun?.status === 'completed' && (
                <>
                  {/* ── Header com badges de modo e projeto ── */}
                  <div className="flex items-center gap-2" style={{ marginBottom: 14, flexWrap: 'wrap' }}>
                    <span style={{
                      padding: '4px 12px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                      background: result.audit_mode === 'operational' ? '#FEF2F2' : '#EFF6FF',
                      color: result.audit_mode === 'operational' ? 'var(--red)' : 'var(--navy)',
                    }}>
                      {result.audit_mode === 'operational' ? '⚡ Modo Operacional' : '🔧 Modo Desenvolvimento'}
                    </span>
                    {selectedProject && (
                      <span className="badge badge-blue" style={{ fontSize: 11 }}>
                        {selectedProject.name}
                      </span>
                    )}
                    {selectedMethodologyMeta && (
                      <span className="badge badge-green" style={{ fontSize: 11 }}>
                        {selectedMethodologyMeta.label} {selectedMethodologyMeta.version}
                      </span>
                    )}
                  </div>

                  {/* ── Project Readiness Rating ── */}
                  <ReadinessRating rating={readinessRating} />

                  {/* ── KPIs ── */}
                  <div className="grid-4" style={{marginBottom:16}}>
                    <div className="kpi-card flex items-center gap-3">
                      <ScoreGauge score={Math.round(score)} />
                      <div>
                        <div className="kpi-label">Score de Conformidade</div>
                        <div style={{fontSize:12,color:'var(--text-2)',marginTop:4}}>
                          {scoreLabel || (score>=75?'Good':score>=50?'Moderate':'Critical')}
                        </div>
                      </div>
                    </div>
                    <div className="kpi-card">
                      <div className="kpi-value" style={{color:'var(--green)'}}>{compliant}</div>
                      <div className="kpi-label flex items-center gap-1">
                        <span style={{fontSize:13}}>✅</span> Conformes
                      </div>
                    </div>
                    <div className="kpi-card">
                      <div className="kpi-value" style={{color:'var(--amber)'}}>{partial}</div>
                      <div className="kpi-label flex items-center gap-1">
                        <span style={{fontSize:13}}>⚠️</span> Parciais
                      </div>
                    </div>
                    <div className="kpi-card">
                      <div className="kpi-value" style={{color:'#7C3AED'}}>{findings.filter(f=>f.status==='future_evidence_required').length}</div>
                      <div className="kpi-label flex items-center gap-1">
                        <span style={{fontSize:13}}>🔮</span> Ev. futura{nonComp > 0 ? ` · ${nonComp} ❌` : ''}
                      </div>
                    </div>
                  </div>

                  {/* ── Matriz de Conformidade ── */}
                  <div className="card">
                    <div className="flex items-center justify-between" style={{marginBottom:14}}>
                      <div>
                        <div className="card-title" style={{marginBottom:2}}>Matriz de Conformidade</div>
                        <div style={{fontSize:11,color:'var(--text-2)'}}>
                          Clique em qualquer linha para ver gap, recomendação e link para o protocolo
                        </div>
                      </div>
                      <div className="flex gap-2" style={{flexWrap:'wrap'}}>
                        {readinessRating && (
                          <button className="btn btn-sm btn-primary"
                            onClick={() => window.open(`${API}/api/audit/${selectedRun.id}/report?format=certificate`)}
                            title="Certificado de 1 página — acompanha o PDD em submissões">
                            ⬇ Certificado
                          </button>
                        )}
                        <button className="btn btn-sm btn-outline"
                          onClick={() => window.open(`${API}/api/audit/${selectedRun.id}/report?format=pdf`)}>
                          ⬇ Matriz PDF
                        </button>
                        <button className="btn btn-sm btn-outline"
                          onClick={() => window.open(`${API}/api/audit/${selectedRun.id}/report?format=summary_pdf`)}>
                          ⬇ Resumo PDF
                        </button>
                        <button className="btn btn-sm btn-ghost"
                          onClick={() => window.open(`${API}/api/audit/${selectedRun.id}/report?format=json`)}>
                          ⬇ JSON
                        </button>
                      </div>
                    </div>

                    {findings.length === 0
                      ? <div className="empty-state" style={{padding:32}}><div className="empty-state-sub">Sem resultados.</div></div>
                      : (
                        <div className="table-wrap">
                          <table>
                            <thead>
                              <tr>
                                <th style={{width:110}}>ID</th>
                                <th>Módulo</th>
                                <th>Requisito</th>
                                <th>Status</th>
                                <th>Risco</th>
                                <th style={{width:48, textAlign:'right'}}>Score</th>
                                <th style={{width:20}}></th>
                              </tr>
                            </thead>
                            <tbody>
                              {findings.map((f, i) => <FindingRow key={i} f={f} />)}
                            </tbody>
                          </table>
                        </div>
                      )
                    }
                  </div>
                </>
              )}
            </>
          )}

          {/* ── Histórico ── */}
          {tab === 'history' && (
            <div className="card">
              <div className="card-title">Execuções anteriores</div>
              {auditRuns.length === 0
                ? <div className="empty-state" style={{padding:32}}><div className="empty-state-sub">Nenhuma auditoria executada ainda.</div></div>
                : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr><th>ID</th><th>Metodologia</th><th>Status</th><th>Data</th><th></th></tr>
                      </thead>
                      <tbody>
                        {auditRuns.map(r => (
                          <tr key={r.id}>
                            <td style={{fontSize:11,color:'var(--text-3)',fontFamily:'monospace'}}>{r.id?.slice(0,8)}…</td>
                            <td>{r.methodology}</td>
                            <td>
                              <span className={`badge ${r.status==='completed'?'badge-green':r.status==='error'?'badge-red':'badge-amber'}`}>
                                {r.status}
                              </span>
                            </td>
                            <td style={{fontSize:12,color:'var(--text-2)'}}>
                              {r.created_at ? new Date(r.created_at).toLocaleString('pt-BR') : '—'}
                            </td>
                            <td>
                              {r.status==='completed' &&
                                <button className="btn btn-sm btn-outline" onClick={() => loadRun(r.id)}>Ver</button>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )
              }
            </div>
          )}
        </>
      )}
    </div>
  )
}
