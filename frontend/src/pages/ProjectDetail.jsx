import { useContext } from 'react'
import { AppCtx } from '../App'
import ChatTab from './tabs/ChatTab'
import ValidationTab from './tabs/ValidationTab'
import StubTab from './tabs/StubTab'

const TAB_MAP = {
  'chat':           { label: 'Chat Técnico',      component: ChatTab },
  'validacao':      { label: 'Validação',          component: ValidationTab },
  'pre-viabilidade':{ label: 'Pré-Viabilidade',   component: () => <StubTab icon="🔍" title="Pré-Viabilidade" desc="Triagem rápida de elegibilidade e fit metodológico. Em desenvolvimento." /> },
  'viabilidade':    { label: 'Viabilidade Completa',component: () => <StubTab icon="📊" title="Viabilidade Completa" desc="Avaliação de maturidade e prontidão do projeto. Em desenvolvimento." /> },
  'verificacao':    { label: 'Verificação',         component: () => <StubTab icon="🛡️" title="Verificação" desc="Suporte ao ciclo V&V. Em desenvolvimento." /> },
  'data-room':      { label: 'Data Room',           component: () => <StubTab icon="📁" title="Data Room" desc="Repositório de documentos do projeto. Em desenvolvimento." /> },
  'doc-filler':     { label: 'Preencher Documento', component: () => <StubTab icon="📝" title="Preencher Documento" desc="Preenchimento automático de PDDs e DPPs. Em desenvolvimento." /> },
  'sheet-filler':   { label: 'Preencher Planilha',  component: () => <StubTab icon="📋" title="Preencher Planilha" desc="Automação de planilhas de parâmetros. Em desenvolvimento." /> },
}

export default function ProjectDetail({ tab }) {
  const { activeProject } = useContext(AppCtx)
  const cfg = TAB_MAP[tab] || TAB_MAP['chat']
  const Comp = cfg.component

  if (!activeProject) {
    return (
      <div>
        <div className="page-header">
          <div className="page-title">{cfg.label}</div>
        </div>
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">📂</div>
            <div className="empty-state-title">Nenhum projeto selecionado</div>
            <div className="empty-state-sub">
              Selecione um projeto na sidebar ou crie um novo para começar.
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header flex items-center justify-between">
        <div>
          <div className="page-title">{cfg.label}</div>
          <div className="page-subtitle">{activeProject.name} · {activeProject.methodology}</div>
        </div>
      </div>
      <Comp project={activeProject} />
    </div>
  )
}
