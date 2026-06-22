import { useContext, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { AppCtx } from '../App'

export default function Dashboard() {
  const { projects, activeProject, setActiveProject, API } = useContext(AppCtx)
  const navigate = useNavigate()
  const [stats, setStats] = useState({ total_audits: null, avg_score: null })

  useEffect(() => {
    axios.get(`${API}/api/dashboard/stats`).then(r => setStats(r.data)).catch(() => {})
  }, [API])

  function openProject(p) {
    setActiveProject(p)
    navigate('/validacao')
  }

  const total   = projects.length
  const withDocs = projects.filter(p => (p.doc_count || 0) > 0).length
  const avgDisplay = stats.avg_score != null ? `${stats.avg_score}%` : '—'
  const auditDisplay = stats.total_audits != null ? stats.total_audits : '—'

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Dashboard</div>
        <div className="page-subtitle">Portfólio de projetos de carbono</div>
      </div>

      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="kpi-card">
          <div className="kpi-value">{total}</div>
          <div className="kpi-label">Projetos</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{withDocs}</div>
          <div className="kpi-label">Com documentos</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value" style={{ color: 'var(--green)' }}>{auditDisplay}</div>
          <div className="kpi-label">Auditorias concluídas</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{avgDisplay}</div>
          <div className="kpi-label">Score médio</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Projetos</div>
        {projects.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🌱</div>
            <div className="empty-state-title">Nenhum projeto ainda</div>
            <div className="empty-state-sub">
              Clique em "Novo projeto" na sidebar para começar uma análise de elegibilidade.
            </div>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Metodologia</th>
                  <th>Documentos</th>
                  <th>Criado em</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {projects.map(p => (
                  <tr
                    key={p.id}
                    style={{ cursor: 'pointer', background: activeProject?.id === p.id ? 'var(--navy-light)' : undefined }}
                    onClick={() => openProject(p)}
                  >
                    <td><span className="font-bold">{p.name}</span></td>
                    <td><span className="badge badge-blue">{p.methodology || 'isometric'}</span></td>
                    <td>{p.doc_count || 0} arquivo(s)</td>
                    <td style={{ color: 'var(--text-2)', fontSize: 12 }}>
                      {p.created_at ? new Date(p.created_at).toLocaleDateString('pt-BR') : '—'}
                    </td>
                    <td>
                      <button
                        className="btn btn-sm btn-outline"
                        onClick={e => { e.stopPropagation(); openProject(p) }}
                      >
                        Abrir
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
