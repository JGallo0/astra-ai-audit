import { useState, useEffect, useRef, useContext } from 'react'
import axios from 'axios'
import { AppCtx } from '../../App'

function fmtSize(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function fmtDate(ts) {
  if (!ts) return '—'
  return new Date(ts * 1000).toLocaleDateString('pt-BR')
}

export default function DataRoomTab({ project }) {
  const { API, refreshProjects } = useContext(AppCtx)
  const [docs, setDocs]         = useState([])
  const [loading, setLoading]   = useState(true)
  const [uploading, setUploading] = useState(false)
  const [deleting, setDeleting] = useState(null)
  const [error, setError]       = useState('')
  const fileRef = useRef()

  function load() {
    setLoading(true)
    axios.get(`${API}/api/projects/${project.id}/documents`)
      .then(r => { setDocs(r.data); setError('') })
      .catch(() => setError('Erro ao carregar documentos.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { if (project?.id) load() }, [project?.id])

  async function handleUpload(e) {
    const files = Array.from(e.target.files)
    if (!files.length) return
    setUploading(true)
    setError('')
    const form = new FormData()
    files.forEach(f => form.append('files', f))
    try {
      await axios.post(`${API}/api/projects/${project.id}/documents`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      load()
      refreshProjects()
    } catch {
      setError('Erro ao enviar arquivo(s).')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  async function handleDelete(fileId, filename) {
    if (!confirm(`Remover "${filename}" do projeto?`)) return
    setDeleting(fileId)
    try {
      await axios.delete(`${API}/api/projects/${project.id}/documents/${fileId}`)
      setDocs(prev => prev.filter(d => d.file_id !== fileId))
      refreshProjects()
    } catch {
      setError('Erro ao remover arquivo.')
    } finally {
      setDeleting(null)
    }
  }

  const statusColor = {
    completed:  'var(--green)',
    in_progress:'var(--amber)',
    failed:     'var(--red)',
  }

  return (
    <div>
      {/* Toolbar */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div>
            <div className="card-title" style={{ marginBottom: 2 }}>Documentos do Projeto</div>
            <div style={{ fontSize: 12, color: 'var(--text-2)' }}>
              {docs.length} arquivo(s) · indexados no vector store do projeto
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-sm btn-outline" onClick={load} disabled={loading}>
              {loading ? '⟳ Atualizando…' : '⟳ Atualizar'}
            </button>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? 'Enviando…' : '+ Adicionar arquivos'}
            </button>
            <input
              ref={fileRef}
              type="file"
              multiple
              accept=".pdf,.txt,.docx,.xlsx,.csv,.md"
              style={{ display: 'none' }}
              onChange={handleUpload}
            />
          </div>
        </div>
        {error && (
          <div style={{ marginTop: 10, padding: '8px 12px', background: 'var(--red-bg)',
                        color: 'var(--red)', borderRadius: 6, fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>

      {/* File list */}
      {loading ? (
        <div className="card">
          <div className="empty-state">
            <div style={{ fontSize: 28 }}>⟳</div>
            <div className="empty-state-sub">Carregando documentos…</div>
          </div>
        </div>
      ) : docs.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">📄</div>
            <div className="empty-state-title">Nenhum documento</div>
            <div className="empty-state-sub">
              Adicione arquivos PDF, DOCX ou TXT para habilitar auditoria e chat técnico.
            </div>
            <button
              className="btn btn-primary"
              style={{ marginTop: 12 }}
              onClick={() => fileRef.current?.click()}
            >
              + Adicionar primeiro documento
            </button>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Arquivo</th>
                  <th>Tamanho</th>
                  <th>Adicionado em</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {docs.map(doc => (
                  <tr key={doc.file_id}>
                    <td>
                      <span style={{ fontWeight: 600, fontSize: 13 }}>
                        📄 {doc.filename || doc.file_id}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-2)', fontSize: 12 }}>
                      {fmtSize(doc.size_bytes)}
                    </td>
                    <td style={{ color: 'var(--text-2)', fontSize: 12 }}>
                      {fmtDate(doc.created_at)}
                    </td>
                    <td>
                      <span style={{
                        fontSize: 11, fontWeight: 600,
                        color: statusColor[doc.status] || 'var(--text-2)',
                      }}>
                        {doc.status === 'completed' ? '✓ Indexado'
                          : doc.status === 'in_progress' ? '⟳ Indexando'
                          : doc.status === 'failed' ? '✗ Falhou'
                          : doc.status || '—'}
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn btn-sm"
                        style={{ color: 'var(--red)', border: '1px solid var(--red)',
                                 background: 'transparent', opacity: deleting === doc.file_id ? 0.5 : 1 }}
                        disabled={deleting === doc.file_id}
                        onClick={() => handleDelete(doc.file_id, doc.filename)}
                      >
                        {deleting === doc.file_id ? '…' : 'Remover'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div style={{ marginTop: 12, fontSize: 11, color: 'var(--text-2)' }}>
        Remover um documento invalida o cache de extração — a próxima auditoria fará nova análise dos documentos restantes.
      </div>
    </div>
  )
}
