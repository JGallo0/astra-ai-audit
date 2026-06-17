import { useState, useContext } from 'react'
import { AppCtx } from '../App'

export default function Settings() {
  const { API } = useContext(AppCtx)
  const [lang, setLang] = useState('pt')

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Configurações</div>
        <div className="page-subtitle">Preferências do sistema</div>
      </div>

      <div className="card">
        <div className="card-title">Geral</div>

        <div className="form-group">
          <label className="form-label">Idioma da interface</label>
          <select className="form-select" style={{ maxWidth: 220 }} value={lang} onChange={e => setLang(e.target.value)}>
            <option value="pt">Português</option>
            <option value="en">English</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Endpoint da API</label>
          <input className="form-input" style={{ maxWidth: 400 }} value={API || 'http://localhost:8000'} readOnly />
        </div>
      </div>

      <div className="card">
        <div className="card-title">Modelos de IA</div>

        <div className="form-group">
          <label className="form-label">Modelo principal</label>
          <select className="form-select" style={{ maxWidth: 280 }}>
            <option>gpt-4.1</option>
            <option>gpt-4o</option>
            <option>gpt-4-turbo</option>
          </select>
        </div>

        <div className="alert alert-info">
          As configurações de modelo são definidas via variáveis de ambiente no backend.
        </div>
      </div>

      <div className="card">
        <div className="card-title">Armazenamento</div>
        <div className="flex gap-2">
          <div className="kpi-card" style={{ flex: 1 }}>
            <div className="kpi-value" style={{ fontSize: 20 }}>Supabase</div>
            <div className="kpi-label">Banco de dados</div>
          </div>
          <div className="kpi-card" style={{ flex: 1 }}>
            <div className="kpi-value" style={{ fontSize: 20 }}>OpenAI</div>
            <div className="kpi-label">Vector Stores (RAG)</div>
          </div>
          <div className="kpi-card" style={{ flex: 1 }}>
            <div className="kpi-value" style={{ fontSize: 20 }}>Render</div>
            <div className="kpi-label">Backend</div>
          </div>
        </div>
      </div>
    </div>
  )
}
