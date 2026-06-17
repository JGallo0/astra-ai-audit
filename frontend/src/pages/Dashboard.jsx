import { useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppCtx } from '../App'

const STATUS_BADGE = {
  completed: { label: 'Concluído', cls: 'badge-green' },
  running:   { label: 'Em execução', cls: 'badge-amber' },
  error:     { label: 'Erro', cls: 'badge-red' },
}

export default function Dashboard() {
  const { projects } = useContext(AppCtx)
  const navigate = useNavigate()

  const total = projects.length
  const withDocs = projects.filter(p => (p.doc_count || 0) > 0).length

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
          <div className="kpi-value" style={{ color: 'var(--green)' }}>—</div>
          <div className="kpi-label">Auditorias concluídas</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">—</div>
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
                  <tr key={p.id} style={{ cursor: 'pointer' }} onClick={() => navigate('/validacao')}>
                    <td><span className="font-bold">{p.name}</span></td>
                    <td>
                      <span className="badge badge-blue">{p.methodology}</span>
                    </td>
                    <td>{p.doc_count || 0} arquivo(s)</td>
                    <td style={{ color: 'var(--text-2)', fontSize: 12 }}>
                      {p.created_at ? new Date(p.created_at).toLocaleDateString('pt-BR') : '—'}
                    </td>
                    <td>
                      <button
                        className="btn btn-sm btn-outline"
                        onClick={e => { e.stopPropagation(); navigate('/validacao') }}
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
