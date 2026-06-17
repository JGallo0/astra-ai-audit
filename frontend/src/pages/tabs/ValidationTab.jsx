import { useState, useEffect, useContext } from 'react'
import axios from 'axios'
import { AppCtx } from '../../App'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'

const MODULES = [
  'Elegibilidade',
  'Adicionalidade',
  'Durabilidade',
  'Produção',
  'Produto',
  'Armazenamento',
  'Feedstock',
  'Quantificação',
  'Emissões',
  'Amostragem',
  'Rastreabilidade',
  'Gestão',
  'Salvaguardas',
]

const STATUS_CLS = {
  'Conforme': 'compliance-status-conforme',
  'Parcialmente conforme': 'compliance-status-parcial',
  'Não conforme': 'compliance-status-nao',
  'Não evidenciado': 'compliance-status-evidenciado',
}

const RISK_CLS = {
  baixo: 'badge-green',
  medio: 'badge-amber',
  alto:  'badge-red',
}

function ScoreGauge({ score }) {
  const color = score >= 75 ? 'var(--green)' : score >= 50 ? 'var(--amber)' : 'var(--red)'
  const data = [{ value: score, fill: color }]
  return (
    <div style={{ width: 120, height: 120, position: 'relative' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart cx="50%" cy="50%" innerRadius="65%" outerRadius="90%" barSize={10} data={data} startAngle={90} endAngle={-270}>
          <RadialBar dataKey="value" cornerRadius={5} background={{ fill: 'var(--border)' }} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ fontSize: 22, fontWeight: 800, color }}>{score}%</span>
        <span style={{ fontSize: 10, color: 'var(--text-2)', fontWeight: 600 }}>Score</span>
      </div>
    </div>
  )
}

export default function ValidationTab({ project }) {
  const { API } = useContext(AppCtx)
  const [tab, setTab] = useState('run')
  const [auditRuns, setAuditRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [selectedModules, setSelectedModules] = useState([])
  const [running, setRunning] = useState(false)
  const [pollingId, setPollingId] = useState(null)
  const [reanalysis, setReanalysis] = useState(true)

  useEffect(() => {
    loadRuns()
  }, [project.id])

  useEffect(() => {
    return () => { if (pollingId) clearInterval(pollingId) }
  }, [pollingId])

  async function loadRuns() {
    const { data } = await axios.get(`${API}/api/projects/${project.id}/audits`).catch(() => ({ data: [] }))
    setAuditRuns(data)
    if (data.length > 0 && !selectedRun) {
      const last = data[0]
      if (last.status === 'completed') await loadRun(last.id)
    }
  }

  async function loadRun(runId) {
    const { data } = await axios.get(`${API}/api/audit/${runId}`).catch(() => ({ data: null }))
    if (data) { setSelectedRun(data); setTab('results') }
  }

  async function startAudit() {
    setRunning(true)
    setSelectedRun(null)
    setTab('results')
    try {
      const { data } = await axios.post(`${API}/api/projects/${project.id}/audit`, {
        modules: selectedModules.length > 0 ? selectedModules : null,
        enable_reanalysis: reanalysis,
      })
      const runId = data.run_id
      const id = setInterval(async () => {
        const { data: run } = await axios.get(`${API}/api/audit/${runId}`).catch(() => ({ data: null }))
        if (run && run.status !== 'running') {
          clearInterval(id)
          setPollingId(null)
          setRunning(false)
          setSelectedRun(run)
          loadRuns()
        }
      }, 3000)
      setPollingId(id)
    } catch {
      setRunning(false)
    }
  }

  function toggleModule(m) {
    setSelectedModules(prev => prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m])
  }

  async function downloadReport(format) {
    if (!selectedRun) return
    const runId = selectedRun.id || Object.keys(selectedRun)[0]
    window.open(`${API}/api/audit/${runId}/report?format=${format}`, '_blank')
  }

  const result = selectedRun?.result || {}
  const findings = result.findings || result.results || []
  const score = result.compliance_score || result.score || 0
  const compliant = findings.filter(f => f.status === 'Conforme').length
  const partial = findings.filter(f => f.status === 'Parcialmente conforme').length
  const nonCompliant = findings.filter(f => ['Não conforme', 'Não evidenciado'].includes(f.status)).length

  return (
    <div>
      <div className="tab-bar">
        <button className={`tab-btn${tab === 'run' ? ' active' : ''}`} onClick={() => setTab('run')}>Configurar Auditoria</button>
        <button className={`tab-btn${tab === 'results' ? ' active' : ''}`} onClick={() => setTab('results')}>Resultados</button>
        <button className={`tab-btn${tab === 'history' ? ' active' : ''}`} onClick={() => { setTab('history'); loadRuns() }}>Histórico de Execuções</button>
      </div>

      {tab === 'run' && (
        <div className="card">
          <div className="card-title">Configuração da auditoria estruturada</div>

          <div className="form-group">
            <label className="form-label">Módulos de análise</label>
            <div className="alert alert-info" style={{ marginBottom: 12 }}>
              Deixe em branco para auditar todos os módulos da metodologia.
            </div>
            <div className="flex" style={{ flexWrap: 'wrap', gap: 8 }}>
              {MODULES.map(m => (
                <button
                  key={m}
                  className={`btn btn-sm ${selectedModules.includes(m) ? 'btn-primary' : 'btn-ghost'}`}
                  onClick={() => toggleModule(m)}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group flex items-center gap-2">
            <input
              type="checkbox"
              id="reanalysis"
              checked={reanalysis}
              onChange={e => setReanalysis(e.target.checked)}
              style={{ width: 16, height: 16, accentColor: 'var(--navy)' }}
            />
            <label htmlFor="reanalysis" style={{ fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
              Habilitar re-análise automática de requisitos com baixa confiança
            </label>
          </div>

          <button
            className="btn btn-primary btn-lg"
            onClick={startAudit}
            disabled={running}
          >
            {running
              ? <><span className="spinner" style={{ width:16, height:16 }} /> Executando auditoria...</>
              : '▶ Iniciar auditoria estruturada'
            }
          </button>
        </div>
      )}

      {tab === 'results' && (
        <>
          {running && !selectedRun && (
            <div className="card">
              <div className="loading-box">
                <div className="spinner" style={{ width: 32, height: 32 }} />
                <div style={{ fontWeight: 700, color: 'var(--navy)' }}>Auditoria em execução...</div>
                <div style={{ color: 'var(--text-2)', fontSize: 12 }}>
                  O engine está analisando cada requisito da metodologia contra os documentos do projeto.
                </div>
              </div>
            </div>
          )}

          {selectedRun?.status === 'error' && (
            <div className="alert alert-error">
              Erro na auditoria: {selectedRun.error || 'Erro desconhecido'}
            </div>
          )}

          {selectedRun?.status === 'completed' && (
            <>
              <div className="grid-4" style={{ marginBottom: 16 }}>
                <div className="kpi-card flex items-center gap-3">
                  <ScoreGauge score={score} />
                  <div>
                    <div className="kpi-label">Score de Conformidade</div>
                    <div style={{ fontSize: 12, color: 'var(--text-2)', marginTop: 4 }}>
                      {score >= 75 ? 'Alto' : score >= 50 ? 'Médio' : 'Baixo'}
                    </div>
                  </div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-value" style={{ color: 'var(--green)' }}>{compliant}</div>
                  <div className="kpi-label">Conformes</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-value" style={{ color: 'var(--amber)' }}>{partial}</div>
                  <div className="kpi-label">Parcialmente conformes</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-value" style={{ color: 'var(--red)' }}>{nonCompliant}</div>
                  <div className="kpi-label">Não conformes</div>
                </div>
              </div>

              <div className="card" style={{ marginBottom: 16 }}>
                <div className="flex items-center justify-between" style={{ marginBottom: 14 }}>
                  <div className="card-title" style={{ marginBottom: 0 }}>Matriz de Conformidade</div>
                  <div className="flex gap-2">
                    <button className="btn btn-sm btn-ghost" onClick={() => downloadReport('json')}>⬇ JSON</button>
                    <button className="btn btn-sm btn-outline" onClick={() => downloadReport('pdf')}>⬇ PDF</button>
                    <button className="btn btn-sm btn-outline" onClick={() => downloadReport('docx')}>⬇ DOCX</button>
                  </div>
                </div>

                {findings.length === 0 ? (
                  <div className="empty-state" style={{ padding: 32 }}>
                    <div className="empty-state-sub">Nenhum resultado disponível.</div>
                  </div>
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th style={{ width: 80 }}>ID</th>
                          <th>Módulo</th>
                          <th>Requisito</th>
                          <th>Status</th>
                          <th>Risco</th>
                          <th style={{ width: 60 }}>Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {findings.map((f, i) => (
                          <tr key={i}>
                            <td style={{ fontSize: 11, color: 'var(--text-3)' }}>{f.requirement_id}</td>
                            <td><span className="badge badge-blue" style={{ fontSize: 10 }}>{f.module}</span></td>
                            <td style={{ maxWidth: 320, fontSize: 12 }}>{f.title}</td>
                            <td>
                              <span className={STATUS_CLS[f.status] || 'compliance-status-evidenciado'}>
                                {f.status}
                              </span>
                            </td>
                            <td>
                              <span className={`badge ${RISK_CLS[f.risk] || 'badge-gray'}`}>{f.risk}</span>
                            </td>
                            <td style={{ fontWeight: 700, color: f.score >= 75 ? 'var(--green)' : f.score >= 50 ? 'var(--amber)' : 'var(--red)' }}>
                              {f.score}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </>
      )}

      {tab === 'history' && (
        <div className="card">
          <div className="card-title">Execuções anteriores</div>
          {auditRuns.length === 0 ? (
            <div className="empty-state" style={{ padding: 32 }}>
              <div className="empty-state-sub">Nenhuma auditoria executada ainda.</div>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Metodologia</th>
                    <th>Status</th>
                    <th>Data</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {auditRuns.map(r => (
                    <tr key={r.id}>
                      <td style={{ fontSize: 11, color: 'var(--text-3)' }}>{r.id?.slice(0, 8)}…</td>
                      <td>{r.methodology}</td>
                      <td>
                        <span className={`badge ${r.status === 'completed' ? 'badge-green' : r.status === 'error' ? 'badge-red' : 'badge-amber'}`}>
                          {r.status}
                        </span>
                      </td>
                      <td style={{ fontSize: 12, color: 'var(--text-2)' }}>
                        {r.created_at ? new Date(r.created_at).toLocaleString('pt-BR') : '—'}
                      </td>
                      <td>
                        {r.status === 'completed' && (
                          <button className="btn btn-sm btn-outline" onClick={() => loadRun(r.id)}>
                            Ver resultados
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
