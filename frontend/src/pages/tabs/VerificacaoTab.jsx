import { useState, useEffect, useContext } from 'react'
import axios from 'axios'
import { AppCtx } from '../../App'

const NAVY  = '#1A3160'
const GREEN = '#16A34A'
const RED   = '#DC2626'
const AMBER = '#B45309'
const BLUE  = '#1D4ED8'

const STATUS_STYLE = {
  compliant:   { color: GREEN, bg: '#F0FDF4', label: 'Conforme' },
  partial:     { color: AMBER, bg: '#FFFBEB', label: 'Parcial'  },
  non_compliant:{ color: RED,  bg: '#FEF2F2', label: 'Não conf.'},
  not_applicable:{ color: BLUE, bg: '#EFF6FF', label: 'Op. only'},
  future_evidence_required: { color: '#6D28D9', bg: '#F5F3FF', label: 'Ev. futura'},
}

function Badge({ status }) {
  const s = STATUS_STYLE[status] || { color: '#6B7280', bg: '#F3F4F6', label: status }
  return (
    <span style={{ fontSize: 10, fontWeight: 700, color: s.color, background: s.bg,
                   padding: '2px 7px', borderRadius: 10, whiteSpace: 'nowrap' }}>
      {s.label}
    </span>
  )
}

// ── Developer View ────────────────────────────────────────────────────────────

function PriorityGroup({ icon, color, bg, label, items, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  if (!items.length) return null
  return (
    <div style={{ marginBottom: 14 }}>
      <button onClick={() => setOpen(o => !o)} style={{
        width: '100%', display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 14px', background: bg, border: `1px solid ${color}20`,
        borderRadius: 8, cursor: 'pointer', textAlign: 'left',
      }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        <span style={{ fontWeight: 700, fontSize: 14, color, flex: 1 }}>
          {label} <span style={{ fontWeight: 400, fontSize: 12 }}>({items.length})</span>
        </span>
        <span style={{ color, fontSize: 12 }}>{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div style={{ border: `1px solid ${color}20`, borderTop: 'none',
                      borderRadius: '0 0 8px 8px', overflow: 'hidden' }}>
          {items.map((item, i) => (
            <div key={item.requirement_id} style={{
              padding: '12px 16px', borderTop: i > 0 ? '1px solid #F3F4F6' : undefined,
              borderLeft: `4px solid ${color}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <a href={item.source_url} target="_blank" rel="noopener noreferrer"
                       style={{ fontSize: 11, fontWeight: 700, color: NAVY, textDecoration: 'none',
                                fontFamily: 'monospace' }}>
                      {item.requirement_id}
                    </a>
                    <span style={{ fontSize: 12, color: '#6B7280' }}>{item.module_label}</span>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{item.title}</div>
                  {item.gap && (
                    <div style={{ fontSize: 12, color: '#4B5563', marginBottom: 4 }}>
                      <b>Gap:</b> {item.gap}
                    </div>
                  )}
                  {item.action && (
                    <div style={{ fontSize: 12, color: GREEN, fontWeight: 600 }}>
                      → {item.action}
                    </div>
                  )}
                  {item.upcoming_note && (
                    <div style={{ fontSize: 12, color: BLUE, fontStyle: 'italic' }}>
                      ℹ Evidência operacional — preparar documentação antes da vistoria.
                    </div>
                  )}
                </div>
                {item.score != null && (
                  <div style={{ fontSize: 18, fontWeight: 800, color,
                                textAlign: 'right', flexShrink: 0 }}>
                    {Math.round(item.score)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function DeveloperView({ data }) {
  const { readiness_pct, readiness_label, summary, critical, attention, operational_upcoming } = data
  const pctColor = readiness_pct >= 85 ? GREEN : readiness_pct >= 70 ? AMBER : RED

  return (
    <div>
      {/* Readiness banner */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ textAlign: 'center', flexShrink: 0 }}>
            <div style={{ fontSize: 42, fontWeight: 800, color: pctColor, lineHeight: 1 }}>
              {readiness_pct}%
            </div>
            <div style={{ fontSize: 11, color: '#6B7280', marginTop: 2 }}>Prontidão</div>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: NAVY, marginBottom: 6 }}>
              {readiness_label}
            </div>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 13 }}>
              <span style={{ color: GREEN }}>✓ {summary.compliant} conformes</span>
              {summary.critical_count > 0 &&
                <span style={{ color: RED }}>🔴 {summary.critical_count} críticos</span>}
              {summary.attention_count > 0 &&
                <span style={{ color: AMBER }}>🟡 {summary.attention_count} atenção</span>}
              <span style={{ color: BLUE }}>🔵 {summary.operational_count} verificação operacional</span>
            </div>
          </div>
        </div>

        {summary.critical_count === 0 && summary.attention_count === 0 && (
          <div style={{ marginTop: 14, padding: '10px 14px', background: '#F0FDF4',
                        border: '1px solid #16A34A', borderRadius: 8, fontSize: 13, color: GREEN }}>
            ✅ Nenhum gap crítico identificado. O projeto está bem preparado para a vistoria —
            consulte o Checklist Pré-VVB para antecipar o que o verificador irá solicitar in loco.
          </div>
        )}
      </div>

      {/* Priority groups */}
      <PriorityGroup icon="🔴" color={RED} bg="#FEF2F2" label="Crítico — resolver antes da vistoria"
        items={critical} defaultOpen={true} />
      <PriorityGroup icon="🟡" color={AMBER} bg="#FFFBEB" label="Atenção — fortalecer evidências"
        items={attention} defaultOpen={true} />
      <PriorityGroup icon="🔵" color={BLUE} bg="#EFF6FF"
        label="Requisitos Operacionais — preparar evidências antes da vistoria"
        items={operational_upcoming} defaultOpen={false} />
    </div>
  )
}

// ── VVB View ──────────────────────────────────────────────────────────────────

function VVBModuleCard({ module }) {
  const [open, setOpen] = useState(true)

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <button onClick={() => setOpen(o => !o)} style={{
        width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0,
        marginBottom: open ? 14 : 0,
      }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: NAVY }}>{module.label}</div>
          <div style={{ fontSize: 12, color: '#6B7280', marginTop: 2 }}>{module.vvb_context}</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
          <span style={{ color: '#6B7280', fontSize: 12 }}>{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {open && (
        <>
          {/* Field inspection items */}
          {module.field_items.length > 0 && (
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280',
                            textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                Itens de Inspeção In Loco
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {module.field_items.map((item, i) => (
                  <label key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start',
                                          fontSize: 13, cursor: 'pointer' }}>
                    <input type="checkbox" style={{ marginTop: 2, flexShrink: 0, accentColor: NAVY }} />
                    <span>{item}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Evidence to request */}
          {module.evidence_to_request.length > 0 && (
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280',
                            textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                Documentos / Evidências a Solicitar
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                {module.evidence_to_request.map((ev, i) => (
                  <label key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start',
                                          fontSize: 13, cursor: 'pointer' }}>
                    <input type="checkbox" style={{ marginTop: 2, flexShrink: 0, accentColor: NAVY }} />
                    <span>{ev}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Requirements table */}
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280',
                          textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
              Requisitos ({module.req_count})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {module.requirements.map(req => (
                <div key={req.requirement_id} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '6px 10px', background: req.is_operational_only ? '#EFF6FF' : '#F9FAFB',
                  borderRadius: 6, borderLeft: `3px solid ${req.is_operational_only ? BLUE : NAVY}`,
                }}>
                  <a href={req.source_url} target="_blank" rel="noopener noreferrer"
                     style={{ fontSize: 11, fontWeight: 700, color: NAVY, textDecoration: 'none',
                              fontFamily: 'monospace', flexShrink: 0 }}>
                    {req.requirement_id}
                  </a>
                  <span style={{ fontSize: 12, flex: 1 }}>{req.title}</span>
                  <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                          {req.dev_audit_status && <Badge status={req.dev_audit_status} />}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function VVBView({ data }) {
  return (
    <div>
      {/* Header */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: NAVY, marginBottom: 4 }}>
              Checklist Pré-VVB — {data.methodology}
            </div>
            <div style={{ fontSize: 13, color: '#6B7280', lineHeight: 1.5 }}>
              Itens de inspeção presencial e documentos a preparar antes da vistoria.
              Todos os {data.total_requirements} requisitos são aplicáveis — verificação pressupõe projeto operacional.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12, flexShrink: 0 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 800, color: NAVY }}>{data.total_requirements}</div>
              <div style={{ fontSize: 11, color: '#6B7280' }}>Requisitos</div>
            </div>
          </div>
        </div>
        <div style={{ marginTop: 12 }}>
          <button onClick={() => window.print()}
            style={{ padding: '7px 14px', border: `1px solid ${NAVY}`, borderRadius: 6,
                     fontSize: 12, color: NAVY, background: 'white', cursor: 'pointer' }}>
            🖨️ Imprimir / Salvar PDF
          </button>
        </div>
      </div>

      {/* Module cards */}
      {(data.modules || []).map(mod => (
        <VVBModuleCard key={mod.key} module={mod} />
      ))}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function VerificacaoTab({ project }) {
  const { API } = useContext(AppCtx)
  const [role, setRole]         = useState('developer')
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')

  async function load(selectedRole) {
    setLoading(true); setError(''); setData(null)
    try {
      const r = await axios.get(`${API}/api/projects/${project.id}/verificacao`, {
        params: { role: selectedRole, methodology: 'isometric' },
      })
      setData(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao carregar dados de verificação.')
    } finally {
      setLoading(false)
    }
  }

  function handleRoleChange(r) {
    setRole(r); load(r)
  }

  useEffect(() => { if (project?.id) load('developer') }, [project?.id])

  return (
    <div>
      {/* Role toggle */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 20, border: `1px solid ${NAVY}`,
                    borderRadius: 8, overflow: 'hidden', width: 'fit-content' }}>
        {[
          { value: 'developer', icon: '🏗️', label: 'Desenvolvedor',       sub: 'Prontidão para vistoria' },
          { value: 'vvb',       icon: '📋', label: 'Checklist Pré-VVB', sub: 'Itens para preparar o site' },
        ].map(opt => (
          <button key={opt.value} onClick={() => handleRoleChange(opt.value)} style={{
            padding: '10px 22px', border: 'none', cursor: 'pointer',
            background: role === opt.value ? NAVY : 'white',
            color: role === opt.value ? 'white' : NAVY,
            borderRight: opt.value === 'developer' ? `1px solid ${NAVY}` : 'none',
          }}>
            <div style={{ fontWeight: 700, fontSize: 13 }}>{opt.icon} {opt.label}</div>
            <div style={{ fontSize: 11, opacity: 0.75 }}>{opt.sub}</div>
          </button>
        ))}
      </div>

      {loading && (
        <div className="card">
          <div className="empty-state">
            <div style={{ fontSize: 32 }}>⟳</div>
            <div className="empty-state-sub">Preparando plano de verificação…</div>
          </div>
        </div>
      )}

      {error && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">⚠️</div>
            <div className="empty-state-title">{error}</div>
            {error.includes('auditoria') && (
              <div className="empty-state-sub">
                Acesse a aba Validação e execute uma auditoria primeiro.
              </div>
            )}
          </div>
        </div>
      )}

      {data && !loading && (
        data.role === 'developer'
          ? <DeveloperView data={data} />
          : <VVBView data={data} />
      )}
    </div>
  )
}
