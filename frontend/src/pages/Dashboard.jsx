import { useContext, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { AppCtx } from '../App'

const NAVY  = '#1A3160'
const GREEN = '#16A34A'
const AMBER = '#B45309'
const RED   = '#DC2626'
const GRAY  = '#9CA3AF'

const GRADE_COLOR = {
  'A+': GREEN, 'A': GREEN, 'B+': AMBER, 'B': AMBER, 'C': RED,
}

function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? '—' : d.toLocaleDateString('pt-BR')
}

function GradeBadge({ grade, score }) {
  if (!grade) return (
    <div style={{ padding: '10px 0', textAlign: 'center', color: GRAY, fontSize: 12 }}>
      Sem auditoria
    </div>
  )
  const color = GRADE_COLOR[grade] || GRAY
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ fontSize: 40, fontWeight: 800, color, lineHeight: 1 }}>{grade}</div>
      <div>
        <div style={{ fontSize: 20, fontWeight: 700, color }}>{score?.toFixed(0)}%</div>
      </div>
    </div>
  )
}

function ProjectCard({ project, isActive, onOpen }) {
  const audit = project.last_audit
  const grade = audit?.grade
  const gradeColor = GRADE_COLOR[grade] || GRAY
  const modeLabel = audit?.audit_mode === 'operational' ? 'Operacional' : 'Dev'

  return (
    <div
      onClick={() => onOpen(project)}
      style={{
        background: 'white',
        border: `2px solid ${isActive ? NAVY : '#E5E7EB'}`,
        borderTop: `4px solid ${grade ? gradeColor : '#E5E7EB'}`,
        borderRadius: 12,
        padding: '16px',
        cursor: 'pointer',
        transition: 'box-shadow .15s',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
      }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,.08)'}
      onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: NAVY, lineHeight: 1.3 }}>
          {project.name}
        </div>
        <span style={{
          fontSize: 10, fontWeight: 700, background: '#EFF6FF', color: '#1D4ED8',
          padding: '2px 8px', borderRadius: 10, whiteSpace: 'nowrap', flexShrink: 0,
        }}>
          {project.methodology || 'isometric'}
        </span>
      </div>

      {/* Grade block */}
      {audit ? (
        <div>
          <GradeBadge grade={grade} score={audit.score} />
          <div style={{ fontSize: 11, color: GRAY, marginTop: 4 }}>
            {modeLabel} · {fmtDate(audit.completed_at)}
          </div>
        </div>
      ) : (
        <div style={{
          padding: '10px 12px', background: '#F9FAFB', borderRadius: 8,
          fontSize: 12, color: GRAY, textAlign: 'center',
        }}>
          Nenhuma auditoria concluída
        </div>
      )}

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    borderTop: '1px solid #F3F4F6', paddingTop: 10, marginTop: 'auto' }}>
        <span style={{ fontSize: 12, color: GRAY }}>
          📄 {project.doc_count || 0} arquivo(s)
        </span>
        <button
          className="btn btn-sm btn-outline"
          onClick={e => { e.stopPropagation(); onOpen(project) }}
        >
          Abrir →
        </button>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { activeProject, setActiveProject, API } = useContext(AppCtx)
  const navigate = useNavigate()

  const [portfolio, setPortfolio] = useState([])
  const [stats, setStats]         = useState({ total_audits: null, avg_score: null })
  const [loading, setLoading]     = useState(true)
  const [search, setSearch]       = useState('')

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/api/dashboard/portfolio`),
      axios.get(`${API}/api/dashboard/stats`),
    ]).then(([pRes, sRes]) => {
      setPortfolio(pRes.data)
      setStats(sRes.data)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [API])

  function openProject(p) {
    setActiveProject(p)
    navigate('/validacao')
  }

  const filtered = portfolio.filter(p =>
    p.name?.toLowerCase().includes(search.toLowerCase()) ||
    (p.methodology || '').toLowerCase().includes(search.toLowerCase())
  )

  const total     = portfolio.length
  const audited   = portfolio.filter(p => p.last_audit).length
  const withDocs  = portfolio.filter(p => (p.doc_count || 0) > 0).length
  const avgDisplay = stats.avg_score != null ? `${stats.avg_score}%` : '—'

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Portfólio de Projetos</div>
          <div className="page-subtitle">Co2mply by Astra Carbon</div>
        </div>
        <button className="btn btn-primary" style={{ alignSelf: 'center' }}
          onClick={() => navigate('/validacao')}>
          + Novo projeto
        </button>
      </div>

      {/* KPIs */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="kpi-card">
          <div className="kpi-value">{total}</div>
          <div className="kpi-label">Projetos</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value" style={{ color: GREEN }}>{audited}</div>
          <div className="kpi-label">Com auditoria</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{stats.total_audits ?? '—'}</div>
          <div className="kpi-label">Auditorias concluídas</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{avgDisplay}</div>
          <div className="kpi-label">Score médio</div>
        </div>
      </div>

      {/* Search */}
      {portfolio.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <input
            type="text"
            placeholder="Buscar projeto ou metodologia…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              width: '100%', padding: '8px 14px', fontSize: 13,
              border: '1px solid #E5E7EB', borderRadius: 8, background: 'white',
            }}
          />
        </div>
      )}

      {/* Portfolio grid */}
      {loading ? (
        <div className="card">
          <div className="empty-state">
            <div style={{ fontSize: 28 }}>⟳</div>
            <div className="empty-state-sub">Carregando portfólio…</div>
          </div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">🌱</div>
            <div className="empty-state-title">
              {portfolio.length === 0 ? 'Nenhum projeto ainda' : 'Nenhum resultado'}
            </div>
            <div className="empty-state-sub">
              {portfolio.length === 0
                ? 'Clique em "Novo projeto" na sidebar para começar.'
                : 'Tente outro termo de busca.'}
            </div>
          </div>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: 16,
        }}>
          {filtered.map(p => (
            <ProjectCard
              key={p.id}
              project={p}
              isActive={activeProject?.id === p.id}
              onOpen={openProject}
            />
          ))}
        </div>
      )}
    </div>
  )
}
