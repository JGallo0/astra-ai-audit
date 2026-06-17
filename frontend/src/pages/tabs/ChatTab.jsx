import { useState, useEffect, useRef, useContext } from 'react'
import axios from 'axios'
import { AppCtx } from '../../App'

export default function ChatTab({ project }) {
  const { API } = useContext(AppCtx)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(true)
  const bottomRef = useRef()

  useEffect(() => {
    setMessages([])
    setLoadingHistory(true)
    axios.get(`${API}/api/projects/${project.id}/chat/history`)
      .then(r => setMessages(r.data || []))
      .catch(() => {})
      .finally(() => setLoadingHistory(false))
  }, [project.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)
    try {
      const { data } = await axios.post(`${API}/api/projects/${project.id}/chat`, {
        message: text,
        history: messages.slice(-10),
      })
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Erro ao processar mensagem. Tente novamente.' }])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  async function clearHistory() {
    if (!confirm('Limpar todo o histórico de chat?')) return
    await axios.delete(`${API}/api/projects/${project.id}/chat/history`).catch(() => {})
    setMessages([])
  }

  return (
    <div className="card" style={{ padding: 0, display: 'flex', flexDirection: 'column', height: 'calc(100vh - 180px)' }}>
      <div className="flex items-center justify-between" style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)' }}>
        <div className="card-title" style={{ marginBottom: 0 }}>
          Chat Técnico
          <span className="badge badge-blue" style={{ marginLeft: 8, verticalAlign: 'middle', fontSize: 10 }}>
            RAG — documentos do projeto
          </span>
        </div>
        {messages.length > 0 && (
          <button className="btn btn-sm btn-ghost" onClick={clearHistory}>Limpar</button>
        )}
      </div>

      <div className="chat-messages">
        {loadingHistory ? (
          <div className="loading-box">
            <div className="spinner" />
            Carregando histórico...
          </div>
        ) : messages.length === 0 ? (
          <div className="empty-state" style={{ padding: '40px 24px' }}>
            <div className="empty-state-icon">💬</div>
            <div className="empty-state-title">Faça perguntas sobre o projeto</div>
            <div className="empty-state-sub">
              O assistente busca respostas diretamente nos documentos carregados no projeto.
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`chat-msg chat-msg-${m.role}`}>
              {m.content}
            </div>
          ))
        )}
        {loading && (
          <div className="chat-msg chat-msg-assistant" style={{ opacity: .6 }}>
            <span className="spinner" style={{ width: 14, height: 14, marginRight: 8 }} />
            Consultando documentos...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-wrap">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Pergunte sobre o projeto, metodologia, requisitos..."
          rows={1}
          disabled={loading}
        />
        <button className="btn btn-primary" onClick={send} disabled={loading || !input.trim()}>
          {loading ? <span className="spinner" style={{ width:14, height:14 }} /> : 'Enviar'}
        </button>
      </div>
    </div>
  )
}
