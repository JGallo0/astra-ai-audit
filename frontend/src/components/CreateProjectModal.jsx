import { useState, useRef } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_BASE || ''

export default function CreateProjectModal({ methodologies, onClose, onCreated }) {
  const [name, setName] = useState('')
  const [methodology, setMethodology] = useState(methodologies[0]?.key || 'isometric')
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef()

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim()) { setError('Informe o nome do projeto.'); return }
    setLoading(true)
    setError('')
    try {
      const fd = new FormData()
      fd.append('name', name.trim())
      fd.append('methodology', methodology)
      files.forEach(f => fd.append('files', f))
      const { data } = await axios.post(`${API}/api/projects`, fd)
      onCreated(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao criar projeto.')
    } finally {
      setLoading(false)
    }
  }

  function addFiles(newFiles) {
    setFiles(prev => [...prev, ...Array.from(newFiles)])
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-title">Novo projeto de carbono</div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Nome do projeto</label>
            <input
              className="form-input"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Ex.: Nova Esperança Biochar 2025"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Metodologia</label>
            <select className="form-select" value={methodology} onChange={e => setMethodology(e.target.value)}>
              {methodologies.map(m => (
                <option key={m.key} value={m.key}>{m.label} {m.version}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Documentos do projeto</label>
            <div
              className={`upload-zone${dragOver ? ' drag-over' : ''}`}
              onClick={() => inputRef.current?.click()}
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={e => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files) }}
            >
              <div className="upload-zone-icon">📄</div>
              <div className="upload-zone-text">Arraste ou clique para adicionar arquivos</div>
              <div className="upload-zone-sub">PDF, DOCX, XLSX, CSV, TXT, JSON</div>
              <input
                ref={inputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.xlsx,.csv,.txt,.json"
                style={{ display: 'none' }}
                onChange={e => addFiles(e.target.files)}
              />
            </div>
            {files.length > 0 && (
              <div className="mt-2" style={{ fontSize: 12, color: 'var(--text-2)' }}>
                {files.length} arquivo(s) selecionado(s):
                {files.map((f, i) => (
                  <span key={i} style={{ display: 'block', marginLeft: 8 }}>• {f.name}</span>
                ))}
              </div>
            )}
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          <div className="flex gap-2 mt-4" style={{ justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-ghost" onClick={onClose} disabled={loading}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <><span className="spinner" style={{ width:14, height:14 }} /> Criando...</> : 'Criar projeto'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
