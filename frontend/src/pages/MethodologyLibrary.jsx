import { useState, useEffect, useContext } from 'react'
import axios from 'axios'
import { AppCtx } from '../App'

export default function MethodologyLibrary() {
  const { API, methodologies } = useContext(AppCtx)
  const [selected, setSelected] = useState(null)
  const [requirements, setRequirements] = useState([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')

  async function loadRequirements(key) {
    setSelected(key)
    setLoading(true)
    const { data } = await axios.get(`${API}/api/methodologies/${key}/requirements`).catch(() => ({ data: [] }))
    setRequirements(data)
    setLoading(false)
  }

  const filtered = requirements.filter(r =>
    !search || [r.id, r.title, r.module].some(f => (f || '').toLowerCase().includes(search.toLowerCase()))
  )

  const modules = [...new Set(requirements.map(r => r.module).filter(Boolean))]

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Biblioteca de Metodologias</div>
        <div className="page-subtitle">Requisitos estruturados por padrão</div>
      </div>

      <div className="flex gap-3" style={{ marginBottom: 20 }}>
        {methodologies.map(m => (
          <button
            key={m.key}
            className={`btn ${selected === m.key ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => loadRequirements(m.key)}
          >
            {m.label} <span style={{ fontSize: 11, opacity: .7 }}>{m.version}</span>
          </button>
        ))}
      </div>

      {!selected && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">📚</div>
            <div className="empty-state-title">Selecione uma metodologia</div>
            <div className="empty-state-sub">Veja todos os requisitos estruturados disponíveis para auditoria.</div>
          </div>
        </div>
      )}

      {selected && loading && (
        <div className="card">
          <div className="loading-box"><div className="spinner" /> Carregando requisitos...</div>
        </div>
      )}

      {selected && !loading && requirements.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between" style={{ marginBottom: 16 }}>
            <div className="card-title" style={{ marginBottom: 0 }}>
              {requirements.length} requisitos · {modules.length} módulos
            </div>
            <input
              className="form-input"
              style={{ width: 260 }}
              placeholder="Buscar por ID, título, módulo..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style={{ width: 90 }}>ID</th>
                  <th style={{ width: 140 }}>Módulo</th>
                  <th>Requisito</th>
                  <th style={{ width: 100 }}>Obrigatoriedade</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r, i) => (
                  <tr key={i}>
                    <td style={{ fontSize: 11, color: 'var(--text-3)', fontWeight: 600 }}>{r.id}</td>
                    <td><span className="badge badge-blue" style={{ fontSize: 10 }}>{r.module}</span></td>
                    <td style={{ fontSize: 12 }}>
                      <div style={{ fontWeight: 600, marginBottom: 2 }}>{r.title}</div>
                      {r.description && <div style={{ color: 'var(--text-2)', fontSize: 11 }}>{r.description}</div>}
                    </td>
                    <td>
                      <span className={`badge ${r.mandatory ? 'badge-red' : 'badge-gray'}`}>
                        {r.mandatory ? 'Obrigatório' : 'Condicional'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selected && !loading && requirements.length === 0 && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-sub">Requisitos não disponíveis para esta metodologia ainda.</div>
          </div>
        </div>
      )}
    </div>
  )
}
