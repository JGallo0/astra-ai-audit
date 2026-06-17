import { useState, useEffect, useContext } from 'react'
import { AppCtx } from '../App'
import axios from 'axios'

export default function AuditHistory() {
  const { API, activeProject } = useContext(AppCtx)
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!activeProject) return
    setLoading(true)
    axios.get(`${API}/api/projects/${activeProject.id}/audits`)
      .then(r => setRuns(r.data || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [activeProject?.id])

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Histórico de Auditorias</div>
        <div className="page-subtitle">
          {activeProject ? `Projeto: ${activeProject.name}` : 'Selecione um projeto na sidebar'}
        </div>
      </div>

      <div className="card">
        {!activeProject ? (
          <div className="empty-state">
            <div className="empty-state-icon">🕐</div>
            <div className="empty-state-title">Nenhum projeto selecionado</div>
          </div>
        ) : loading ? (
          <div className="loading-box"><div className="spinner" /> Carregando histórico...</div>
        ) : runs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🕐</div>
            <div className="empty-state-title">Sem execuções ainda</div>
            <div className="empty-state-sub">Execute uma auditoria na aba Validação para ver o histórico aqui.</div>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID da execução</th>
                  <th>Metodologia</th>
                  <th>Status</th>
                  <th>Iniciado em</th>
                  <th>Concluído em</th>
                </tr>
              </thead>
              <tbody>
                {runs.map(r => (
                  <tr key={r.id}>
                    <td style={{ fontSize: 11, color: 'var(--text-3)', fontFamily: 'monospace' }}>{r.id}</td>
                    <td>{r.methodology}</td>
                    <td>
                      <span className={`badge ${r.status === 'completed' ? 'badge-green' : r.status === 'error' ? 'badge-red' : 'badge-amber'}`}>
                        {r.status}
                      </span>
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-2)' }}>
                      {r.created_at ? new Date(r.created_at).toLocaleString('pt-BR') : '—'}
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-2)' }}>
                      {r.completed_at ? new Date(r.completed_at).toLocaleString('pt-BR') : '—'}
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
