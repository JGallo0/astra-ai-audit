import { useState, useEffect, createContext, useContext } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import axios from 'axios'

import Dashboard from './pages/Dashboard'
import ProjectDetail from './pages/ProjectDetail'
import MethodologyLibrary from './pages/MethodologyLibrary'
import AuditHistory from './pages/AuditHistory'
import UserAccess from './pages/UserAccess'
import Settings from './pages/Settings'
import CreateProjectModal from './components/CreateProjectModal'

const API = import.meta.env.VITE_API_BASE || ''

export const AppCtx = createContext({})

const NAV = [
  {
    section: 'Análise',
    items: [
      { label: 'Dashboard',       icon: '⬛', path: '/' },
      { label: 'Chat Técnico',    icon: '💬', path: '/chat' },
      { label: 'Validação',       icon: '✅', path: '/validacao' },
      { label: 'Pré-Viabilidade', icon: '🔍', path: '/pre-viabilidade' },
      { label: 'Viabilidade',     icon: '📊', path: '/viabilidade' },
      { label: 'Verificação',     icon: '🛡️',  path: '/verificacao' },
    ],
  },
  {
    section: 'Ferramentas',
    items: [
      { label: 'Data Room',          icon: '📁', path: '/data-room' },
      { label: 'Preencher Documento',icon: '📝', path: '/doc-filler' },
      { label: 'Preencher Planilha', icon: '📋', path: '/sheet-filler' },
    ],
  },
  {
    section: 'Sistema',
    items: [
      { label: 'Metodologias',   icon: '📚', path: '/metodologias' },
      { label: 'Histórico',      icon: '🕐', path: '/historico' },
      { label: 'Usuários',       icon: '👥', path: '/usuarios' },
      { label: 'Configurações',  icon: '⚙️',  path: '/configuracoes' },
    ],
  },
]

function Sidebar({ projects, activeProject, setActiveProject, onNewProject }) {
  const navigate = useNavigate()
  const { pathname } = useLocation()

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-card">
          <img src="/logo-co2mply.png" alt="Co2mply" />
        </div>
      </div>

      <div className="sidebar-project">
        <div className="sidebar-project-label">Projeto ativo</div>
        <select
          value={activeProject?.id || ''}
          onChange={e => {
            const p = projects.find(x => x.id === e.target.value)
            setActiveProject(p || null)
          }}
        >
          <option value="">— selecionar projeto —</option>
          {projects.map(p => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
        <button className="sidebar-new-btn" onClick={onNewProject}>+ Novo projeto</button>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(group => (
          <div className="nav-section" key={group.section}>
            <div className="nav-section-label">{group.section}</div>
            {group.items.map(item => {
              const active = pathname === item.path || (item.path !== '/' && pathname.startsWith(item.path))
              return (
                <button
                  key={item.path}
                  className={`nav-item${active ? ' active' : ''}`}
                  onClick={() => navigate(item.path)}
                >
                  <span className="nav-item-icon">{item.icon}</span>
                  {item.label}
                </button>
              )
            })}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">Astra Carbon Intelligence</div>
      </div>
    </aside>
  )
}

function AppShell() {
  const [projects, setProjects] = useState([])
  const [activeProject, setActiveProject] = useState(null)
  const [methodologies, setMethodologies] = useState([])
  const [showCreate, setShowCreate] = useState(false)

  useEffect(() => {
    axios.get(`${API}/api/projects`).then(r => setProjects(r.data)).catch(() => {})
    axios.get(`${API}/api/methodologies`).then(r => setMethodologies(r.data)).catch(() => {})
  }, [])

  function handleProjectCreated(proj) {
    setProjects(prev => [proj, ...prev])
    setActiveProject(proj)
    setShowCreate(false)
  }

  const ctx = { API, activeProject, setActiveProject, projects, methodologies, refreshProjects: () => {
    axios.get(`${API}/api/projects`).then(r => setProjects(r.data)).catch(() => {})
  }}

  return (
    <AppCtx.Provider value={ctx}>
      <div className="app-shell">
        <Sidebar
          projects={projects}
          activeProject={activeProject}
          setActiveProject={setActiveProject}
          onNewProject={() => setShowCreate(true)}
        />

        <main className="main">
          <div className="page-wrap">
            <Routes>
              <Route path="/"                 element={<Dashboard />} />
              <Route path="/chat"             element={<ProjectDetail tab="chat" />} />
              <Route path="/validacao"        element={<ProjectDetail tab="validacao" />} />
              <Route path="/pre-viabilidade"  element={<ProjectDetail tab="pre-viabilidade" />} />
              <Route path="/viabilidade"      element={<ProjectDetail tab="viabilidade" />} />
              <Route path="/verificacao"      element={<ProjectDetail tab="verificacao" />} />
              <Route path="/data-room"        element={<ProjectDetail tab="data-room" />} />
              <Route path="/doc-filler"       element={<ProjectDetail tab="doc-filler" />} />
              <Route path="/sheet-filler"     element={<ProjectDetail tab="sheet-filler" />} />
              <Route path="/metodologias"     element={<MethodologyLibrary />} />
              <Route path="/historico"        element={<AuditHistory />} />
              <Route path="/usuarios"         element={<UserAccess />} />
              <Route path="/configuracoes"    element={<Settings />} />
            </Routes>
          </div>
        </main>

        {showCreate && (
          <CreateProjectModal
            methodologies={methodologies}
            onClose={() => setShowCreate(false)}
            onCreated={handleProjectCreated}
          />
        )}
      </div>
    </AppCtx.Provider>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}
