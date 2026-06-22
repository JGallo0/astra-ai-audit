"""
Co2mply — Módulo Verificação (V&V Support)
Isometric Biochar v1.2 — dois perfis: Desenvolvedor e VVB.
100% determinístico — zero LLM.
"""
from __future__ import annotations

# ── Configuração por módulo (Isometric-specific) ──────────────────────────────

MODULE_META: dict = {
    "project_data": {
        "label": "Dados do Projeto",
        "vvb_context": "Verificar integridade e consistência dos dados fundamentais do projeto.",
        "field_items": [
            "Confirmar titularidade dos direitos de remoção — escritura, contrato ou declaração notarial",
            "Verificar coordenadas geográficas da facility de pirólise in loco (GPS vs. PDD)",
            "Confrontar descrição técnica do PDD com a realidade operacional observada",
            "Confirmar lista de participantes e responsabilidades contratuais",
            "Verificar estimativa de capacidade de remoção líquida — metodologia de cálculo",
        ],
        "evidence_to_request": [
            "Título de propriedade ou contrato de arrendamento da área",
            "Contrato de cessão de direitos de carbono",
            "Documentos de constituição da empresa proponente",
            "Cálculo de capacidade de remoção líquida (net CDR estimate)",
        ],
    },
    "protocol_and_monitoring_data": {
        "label": "Protocolo e Monitoramento",
        "vvb_context": "Núcleo técnico — contabilidade de carbono, adicionalidade e durabilidade.",
        "field_items": [
            "Verificar implementação real do plano de monitoramento vs. PDD",
            "Inspecionar sistema de data logger: temperatura do solo, sensores de campo",
            "Revisar registros de produção por batch/ciclo: volumes, temperaturas, datas",
            "Entrevistar operadores sobre procedimentos e conhecimento do protocolo",
            "Conferir rastreabilidade do biochar do reator ao campo (cadeia de custódia)",
            "Verificar documentação de adicionalidade financeira: IRR com e sem carbono",
            "Confirmar método de temperatura do solo para opção de durabilidade ≥200 anos",
            "Verificar análise de sensibilidade e tratamento de incerteza — metodologia documentada",
        ],
        "evidence_to_request": [
            "Relatórios de monitoramento (últimos 12 meses mínimo)",
            "Logs de temperatura do solo por site-mês (mín. 10 medições/site-mês)",
            "Registros de produção por batch: temperatura, tempo de residência, massa produzida",
            "Análise financeira com e sem receita de carbono (IRR test)",
            "Licenças ambientais e comunicações com órgãos regulatórios",
            "Análise de sensibilidade com intervalo de confiança documentado",
        ],
    },
    "environmental_and_social_impact": {
        "label": "Impacto Ambiental e Social",
        "vvb_context": "Salvaguardas ambientais e sociais — prevenção de poluição, co-benefícios e encerramento.",
        "field_items": [
            "Inspecionar área de aplicação do biochar — sinais visuais de contaminação ou degradação",
            "Verificar amostras de solo baseline (antes da aplicação) e monitoramento contínuo",
            "Entrevistar stakeholders locais: agricultores, comunidade vizinha, trabalhadores",
            "Verificar mecanismo de grievance: registros de reclamações e respostas dentro dos prazos",
            "Conferir laudos analíticos de PAHs, metais pesados, PCBs e PCDD/F do biochar",
            "Verificar plano de encerramento: condições de pausa/stop documentadas e conhecidas pela equipe",
            "Confirmar monitoramento de produtividade agrícola e qualidade do solo (se em operação)",
        ],
        "evidence_to_request": [
            "Laudos laboratoriais: PAHs (≤WBC limits), metais pesados, PCBs (≤0,2 mg/kg), PCDD/F (≤20 ng/kg)",
            "Amostras de solo baseline (pré-aplicação) e relatórios de monitoramento pós-aplicação",
            "Registros do mecanismo de consulta e grievance (reconhecimento ≤14 dias, resolução ≤60 dias)",
            "Comunicações com stakeholders locais (atas, e-mails, declarações)",
            "Licenças e autos de infração (se houver) de órgãos ambientais",
        ],
    },
    "stakeholder_input_process": {
        "label": "Consulta a Stakeholders",
        "vvb_context": "Processo de consulta pública — documentação, representatividade e canal de reclamações.",
        "field_items": [
            "Verificar lista de stakeholders consultados — representatividade dos grupos afetados",
            "Confirmar prazos de resposta: reconhecimento ≤14 dias, resolução ≤60 dias",
            "Revisar registros de consultas realizadas e respostas fornecidas",
            "Verificar se canais de contato estão funcionais e publicamente divulgados",
            "Entrevistar stakeholders selecionados para confirmar experiência real com o mecanismo",
        ],
        "evidence_to_request": [
            "Atas ou registros de reuniões de consulta pública",
            "Registros de notificações enviadas e recebidas",
            "Canal de grievance publicado (URL, endereço físico ou contato)",
            "Histórico de reclamações e resoluções (se houver)",
        ],
    },
    "appendix": {
        "label": "Documentação Técnica do Reator",
        "vvb_context": "Inspeção física do reator de pirólise e verificação laboratorial do biochar.",
        "field_items": [
            "Inspecionar reator fisicamente: configuração real vs. diagrama de engenharia do PDD",
            "Verificar sensores de temperatura e tempo de residência — certificados de calibração",
            "Testar funcionamento dos sensores de detecção de vazamento de gases pirolíticos",
            "Conferir registros de manutenção preventiva: frequência, responsável, itens verificados",
            "Verificar certificado ISO 17025 vigente do laboratório de caracterização contratado",
            "Revisar procedimento de amostragem: frequência, método, cadeia de custódia",
            "Conferir laudos de caracterização química: H/Corg <0,5; O/Corg <0,2",
            "Verificar propriedades físicas: granulometria, pH, teor de umidade, teor de cinzas",
            "Confirmar padrão de caracterização utilizado (EBC, IBI ou equivalente)",
        ],
        "evidence_to_request": [
            "Diagrama de engenharia do reator assinado por responsável técnico",
            "Certificados de calibração dos sensores de temperatura e tempo de residência",
            "Registros de inspeção do sensor de vazamento de gases",
            "Plano de manutenção e registros de execução (últimos 12 meses)",
            "Certificado ISO 17025 do laboratório contratado (vigente)",
            "Laudos de caracterização: H/Corg, O/Corg, PAHs (16 EPA), metais pesados, PCBs, PCDD/F",
            "Registros de amostragem com cadeia de custódia (batch nº, data, responsável, lacre)",
        ],
    },
}

MODULE_ORDER = [
    "project_data",
    "protocol_and_monitoring_data",
    "environmental_and_social_impact",
    "stakeholder_input_process",
    "appendix",
]

# Status priority for developer plan
_STATUS_PRIORITY = {
    "non_compliant":            {"order": 1, "level": "critical",    "icon": "🔴", "label": "Crítico"},
    "partial":                  {"order": 2, "level": "attention",   "icon": "🟡", "label": "Atenção"},
    "future_evidence_required": {"order": 3, "level": "attention",   "icon": "🟡", "label": "Ev. Futura"},
    "not_applicable":           {"order": 4, "level": "operational", "icon": "🔵", "label": "Verificação Operacional"},
}

_GENERIC_GAPS = {
    "Partial evidence available; some required elements are incomplete.",
    "Core requirement not met or insufficiently evidenced.",
    "Maintain current evidence and proceed to validation readiness.",
    "Provide missing documentation and strengthen evidence for identified gaps.",
    "Strengthen consistency and completeness of existing evidence.",
    "Establish missing core elements required for compliance.",
    "Providencie esta evidência quando o projeto estiver operacional.",
}


def _clean(text: str | None) -> str | None:
    t = (text or "").strip()
    return None if (not t or t in _GENERIC_GAPS) else t


# ── Developer plan ─────────────────────────────────────────────────────────────

def build_developer_plan(audit_results: list) -> dict:
    """
    Plano de ações pontuais antecedendo a vistoria do VVB.
    Derivado 100% dos resultados de auditoria — zero LLM.
    """
    critical, attention, operational = [], [], []
    compliant_count = 0

    for r in audit_results:
        status = r.get("status", "")
        if status == "compliant":
            compliant_count += 1
            continue

        cfg = _STATUS_PRIORITY.get(status)
        if not cfg:
            continue

        item = {
            "requirement_id": r.get("requirement_id", ""),
            "title":          r.get("title") or r.get("requirement_name", ""),
            "module":         r.get("module", ""),
            "module_label":   MODULE_META.get(r.get("module", ""), {}).get("label", r.get("module", "")),
            "gap":            _clean(r.get("gap")),
            "action":         _clean(r.get("recommendation")),
            "source_url":     r.get("source_url", ""),
            "status":         status,
            "score":          r.get("requirement_score"),
        }

        if cfg["level"] == "critical":
            critical.append(item)
        elif cfg["level"] == "attention":
            attention.append(item)
        elif cfg["level"] == "operational":
            item["upcoming_note"] = (
                "Requisito não exigido em fase de desenvolvimento. "
                "Será verificado pelo VVB quando o projeto estiver operacional."
            )
            operational.append(item)

    applicable = len(audit_results) - len(operational)
    readiness_pct = round(compliant_count / applicable * 100) if applicable > 0 else 0

    if readiness_pct >= 90:
        label = "Alta prontidão — ajustes finais pontuais"
    elif readiness_pct >= 75:
        label = "Boa prontidão — gaps documentais específicos a fechar"
    elif readiness_pct >= 60:
        label = "Prontidão moderada — ações relevantes antes da vistoria"
    else:
        label = "Prontidão insuficiente — trabalho significativo necessário"

    return {
        "role": "developer",
        "methodology": "Isometric Biochar v1.2",
        "readiness_pct": readiness_pct,
        "readiness_label": label,
        "summary": {
            "total": len(audit_results),
            "compliant": compliant_count,
            "critical_count": len(critical),
            "attention_count": len(attention),
            "operational_count": len(operational),
        },
        "critical": critical,
        "attention": attention,
        "operational_upcoming": operational,
    }


# ── VVB plan ───────────────────────────────────────────────────────────────────

def build_vvb_plan(all_requirements: list, audit_results: list) -> dict:
    """
    Plano de inspeção para o VVB — checklist de campo por módulo.
    Isometric Biochar v1.2 específico.
    """
    audit_index = {r.get("requirement_id"): r for r in audit_results}

    # Group requirements by module, preserving MODULE_ORDER
    by_module: dict = {k: [] for k in MODULE_ORDER}
    for req in all_requirements:
        mod = req.get("module", "other")
        if mod not in by_module:
            by_module[mod] = []
        by_module[mod].append(req)

    modules_out = []
    for mod_key in MODULE_ORDER:
        reqs = by_module.get(mod_key, [])
        if not reqs:
            continue
        meta = MODULE_META.get(mod_key, {})
        audit_ref = [audit_index.get(req.get("id") or req.get("requirement_id", ""), {})
                     for req in reqs]

        reqs_out = []
        for req, aud in zip(reqs, audit_ref):
            rid = req.get("id") or req.get("requirement_id", "")
            is_op_only = req.get("mode_applicability") == "operational_only"
            reqs_out.append({
                "requirement_id":    rid,
                "title":             req.get("title") or req.get("requirement_name", ""),
                "source_url":        req.get("source_url", ""),
                "is_operational_only": is_op_only,
                "dev_audit_status":  aud.get("status"),
            })

        op_count = sum(1 for r in reqs_out if r["is_operational_only"])
        modules_out.append({
            "key":               mod_key,
            "label":             meta.get("label", mod_key),
            "vvb_context":       meta.get("vvb_context", ""),
            "field_items":       meta.get("field_items", []),
            "evidence_to_request": meta.get("evidence_to_request", []),
            "requirements":      reqs_out,
            "req_count":         len(reqs_out),
            "operational_only_count": op_count,
        })

    total_req = sum(len(m["requirements"]) for m in modules_out)
    total_op  = sum(m["operational_only_count"] for m in modules_out)

    return {
        "role":              "vvb",
        "methodology":       "Isometric Biochar v1.2",
        "total_requirements": total_req,
        "operational_only_count": total_op,
        "modules":           modules_out,
    }
