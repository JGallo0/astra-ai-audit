APP_NAME = "AuditorIA"
APP_TAGLINE = {
    "pt": "Auditoria inteligente para projetos de carbono",
    "en": "Smart audit for carbon projects",
}
APP_SUBTITLE = {
    "pt": "Auditor técnico documental de projetos de biochar e créditos de carbono",
    "en": "Technical document auditor for biochar and carbon credit projects",
}

LOGO_DEFAULT_PATH = "assets/auditoria_logo.png"

THEME = {
    "primary": "#1A4D4E",        # Deep Forest
    "secondary": "#4CAF50",      # Bio Green
    "accent": "#A2D729",         # Digital Lime
    "danger": "#D90429",         # Alert Red
    "warning": "#F9C74F",        # Caution Amber
    "success": "#2D6A4F",        # Veridiano Safe
    "background": "#EEF4F1",,     # Soft Slate
    "card": "#FFFFFF",           # Pure White
    "text": "#1E293B",           # Dark Slate
    "text_secondary": "#64748B", # Slate Gray
    "border": "#E2E8F0",         # Light Border
    "hover": "#8BBD1E",          # Lime Darken
    "info": "#3B82F6",           # Logic Blue
    "critical": "#B91C1C",       # Deep Red
    "progress": "#4CAF50",       # Growth Green
    "font_primary": "Inter, sans-serif",
    "font_secondary": "'IBM Plex Sans', sans-serif",
}

I18N = {
    "pt": {
        "language_label": "Idioma",
        "mode_label": "Modo de operação",
        "chat_mode": "Chat técnico",
        "full_audit_mode": "Auditoria completa Isometric",
        "project_name": "Nome do projeto",
        "modules_to_audit": "Módulos a auditar",
        "execution_mode": "Modo de execução",
        "fast_mode": "Rápido",
        "complete_mode": "Completo",
        "show_trails": "Exibir trilha de auditoria detalhada",
        "estimated_effort": "Estimativa pré-execução",
        "run_audit": "Executar auditoria completa",
        "cost_estimate": "Custo estimado",
        "session_cost": "Sessão acumulada",
        "progress": "Progresso",
        "current_module": "Módulo atual",
        "current_step": "Etapa atual",
        "history": "Histórico da sessão",
        "summary_tab": "Resumo",
        "matrix_tab": "Matriz",
        "details_tab": "Detalhes",
        "downloads_tab": "Downloads",
        "history_tab": "Histórico",
        "filters": "Filtros",
        "status_filter": "Filtrar por status",
        "risk_filter": "Filtrar por risco",
        "module_filter": "Filtrar por módulo",
        "reanalyze_failures": "Reanalisar apenas falhas",
        "show_sources": "Mostrar fontes utilizadas",
        "show_snippets": "Mostrar trechos recuperados",
        "show_attributes": "Mostrar atributos técnicos",
        "clear_session": "Limpar conversa / sessão",
        "unauthorized": "Acesso não autorizado.",
        "login_required": "Este app requer autenticação para acesso.",
    },
    "en": {
        "language_label": "Language",
        "mode_label": "Operating mode",
        "chat_mode": "Technical chat",
        "full_audit_mode": "Full Isometric audit",
        "project_name": "Project name",
        "modules_to_audit": "Modules to audit",
        "execution_mode": "Execution mode",
        "fast_mode": "Fast",
        "complete_mode": "Complete",
        "show_trails": "Show detailed audit trail",
        "estimated_effort": "Pre-run estimate",
        "run_audit": "Run full audit",
        "cost_estimate": "Estimated cost",
        "session_cost": "Session accumulated",
        "progress": "Progress",
        "current_module": "Current module",
        "current_step": "Current step",
        "history": "Session history",
        "summary_tab": "Summary",
        "matrix_tab": "Matrix",
        "details_tab": "Details",
        "downloads_tab": "Downloads",
        "history_tab": "History",
        "filters": "Filters",
        "status_filter": "Filter by status",
        "risk_filter": "Filter by risk",
        "module_filter": "Filter by module",
        "reanalyze_failures": "Reanalyze failures only",
        "show_sources": "Show sources used",
        "show_snippets": "Show retrieved snippets",
        "show_attributes": "Show technical attributes",
        "clear_session": "Clear conversation / session",
        "unauthorized": "Unauthorized access.",
        "login_required": "This app requires authentication.",
    },
}


def t(lang: str, key: str) -> str:
    return I18N.get(lang, I18N["pt"]).get(key, key)
