import { useState, useContext } from 'react'
import axios from 'axios'
import { AppCtx } from '../../App'

const VERDICT_CFG = {
  elegível:   { color: 'var(--green)',  bg: 'var(--green-bg)',  icon: '✅', label: 'Elegível' },
  possível:   { color: 'var(--amber)',  bg: '#FFFBEB',          icon: '⚠️', label: 'Possível com ajustes' },
  inelegível: { color: 'var(--red)',    bg: 'var(--red-bg)',    icon: '❌', label: 'Inelegível' },
}

const RESULT_CFG = {
  pass:    { color: 'var(--green)', icon: '✓', label: 'Atende' },
  partial: { color: 'var(--amber)', icon: '~', label: 'Parcial' },
  fail:    { color: 'var(--red)',   icon: '✗', label: 'Não atende' },
}

export default function PreViabilidadeTab({ project }) {
  const { API, methodologies } = useContext(AppCtx)
  const [methodology, setMethodology] = useState(project?.methodology || 'isometric')
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  async function runScreening() {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const r = await axios.post(
        `${API}/api/projects/${project.id}/screening?methodology=${methodology}`
      )
      setResult(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao executar triagem.')
    } finally {
      setLoading(false)
    }
  }

  const vcfg = result ? (VERDICT_CFG[result.verdict] || VERDICT_CFG['possível']) : null

  return (
    <div>
      {/* Config card */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title" style={{ marginBottom: 10 }}>Triagem de Elegibilidade</div>
        <div style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 14, lineHeight: 1.5 }}>
          Análise rápida de fit entre o projeto e os critérios-chave do padrão selecionado.
          Utiliza dados já extraídos do projeto (ou faz uma leitura rápida dos documentos).
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 200 }}>
            <label style={{ fontSize: 12, color: 'var(--text-2)', fontWeight: 600 }}>
              Padrão / Metodologia
            </label>
            <select
              value={methodology}
              onChange={e => setMethodology(e.target.value)}
              style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid var(--border)',
                       fontSize: 13, background: 'white' }}
            >
              {methodologies.length > 0
                ? methodologies.map(m => (
                    <option key={m.key} value={m.key}>{m.label}</option>
                  ))
                : <option value="isometric">Isometric Biochar v1.2</option>
              }
            </select>
          </div>

          <button
            className="btn btn-primary"
            style={{ marginTop: 18 }}
            onClick={runScreening}
            disabled={loading}
          >
            {loading ? '⟳ Analisando…' : '🔍 Executar triagem'}
          </button>
        </div>

        {error && (
          <div style={{ marginTop: 12, padding: '8px 12px', background: 'var(--red-bg)',
                        color: 'var(--red)', borderRadius: 6, fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="card">
          <div className="empty-state">
            <div style={{ fontSize: 32 }}>⟳</div>
            <div className="empty-state-title">Analisando o projeto…</div>
            <div className="empty-state-sub">
              O motor está avaliando os critérios de elegibilidade. Pode levar 15–30 segundos.
            </div>
          </div>
        </div>
      )}

      {/* Result */}
      {result && !loading && (
        <>
          {/* Verdict banner */}
          <div className="card" style={{
            background: vcfg.bg,
            border: `2px solid ${vcfg.color}`,
            marginBottom: 16,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ fontSize: 48, lineHeight: 1 }}>{vcfg.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: vcfg.color }}>
                  {vcfg.label}
                </div>
                <div style={{ fontSize: 13, color: 'var(--text)', marginTop: 4, lineHeight: 1.5 }}>
                  {result.summary}
                </div>
              </div>
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                <div style={{ fontSize: 32, fontWeight: 800, color: vcfg.color }}>
                  {result.confidence}%
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-2)' }}>Confiança</div>
                <div style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 2 }}>
                  {result.methodology_name}
                </div>
                {result.used_cache && (
                  <div style={{ fontSize: 10, color: 'var(--text-2)', marginTop: 2 }}>
                    ⚡ Dados em cache
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Criteria checks */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-title" style={{ marginBottom: 12 }}>
              Avaliação por Critério
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {(result.checks || []).map(c => {
                const rc = RESULT_CFG[c.result] || RESULT_CFG.partial
                return (
                  <div key={c.criterion_id} style={{
                    display: 'flex', gap: 12, padding: '10px 14px',
                    borderRadius: 8, background: 'var(--bg)',
                    borderLeft: `4px solid ${rc.color}`,
                  }}>
                    <div style={{
                      fontSize: 15, fontWeight: 700, color: rc.color,
                      minWidth: 18, paddingTop: 1,
                    }}>
                      {rc.icon}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                        <span style={{ fontWeight: 600, fontSize: 13 }}>{c.label}</span>
                        <span style={{
                          fontSize: 10, fontWeight: 700, color: rc.color,
                          background: rc.color + '20', padding: '1px 7px', borderRadius: 10,
                        }}>
                          {rc.label}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.4 }}>
                        {c.note}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Key actions */}
          {(result.key_actions || []).length > 0 && (
            <div className="card">
              <div className="card-title" style={{ marginBottom: 12 }}>
                Próximas Ações Recomendadas
              </div>
              <ol style={{ paddingLeft: 20, margin: 0 }}>
                {result.key_actions.map((a, i) => (
                  <li key={i} style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text)',
                                       marginBottom: 6 }}>
                    {a}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {!result && !loading && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <div className="empty-state-title">Triagem não executada</div>
            <div className="empty-state-sub">
              Clique em "Executar triagem" para avaliar a elegibilidade do projeto
              com base nos critérios do padrão selecionado.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
