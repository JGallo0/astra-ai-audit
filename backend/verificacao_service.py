"""
Co2mply — Módulo Verificação (V&V Support)
Isometric Biochar v1.2 e Puro.Earth Edition 2025 — dois perfis: Desenvolvedor e VVB.
100% determinístico — zero LLM.
"""
from __future__ import annotations

# ── Configuração por módulo — Isometric Biochar v1.2 ──────────────────────────

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

# ── Configuração por módulo — Puro.Earth Edition 2025 ─────────────────────────

PURO_MODULE_META: dict = {
    "project_data": {
        "label": "Dados do Projeto",
        "vvb_context": "Verificar identidade, ownership e dados fundamentais da facility.",
        "field_items": [
            "Confirmar titularidade dos direitos de remoção de carbono — contratos e GSRN",
            "Verificar coordenadas GPS da production facility vs. registro Puro.earth",
            "Confrontar descrição técnica do PDD com a realidade operacional observada",
            "Confirmar lista de participantes: proponente, operador e fornecedores de biomassa",
            "Verificar estimativa de remoção líquida — consistência com CORC factor auditado",
        ],
        "evidence_to_request": [
            "Contrato de cessão de direitos de carbono (CO₂ Removal Supplier Agreement)",
            "Documentos de constituição e KYC/KYB completado na plataforma Puro.earth",
            "GSRN (Global Service Relation Number) da facility no Puro Registry",
            "Cálculo e justificativa do CORC conversion factor (tCO₂e/t biochar)",
        ],
    },
    "feedstock_and_production": {
        "label": "Feedstock e Produção",
        "vvb_context": "Verificar elegibilidade e rastreabilidade do feedstock — área de maior diferenciação do Puro vs. Isometric.",
        "field_items": [
            "Confirmar origem do feedstock: resíduo florestal, agrícola ou outro — NENHUM componente fóssil",
            "Para biomassa florestal: verificar certificação FSC/SFI/PEFC OU dossiê ISAE 3000 OU plano gov. (CPI ≥ 50)",
            "Inspecionar registros de entrada de biomassa: peso, data, origem documentada por batch",
            "Confirmar que pyrolysis gases são recuperados OU combustados (burner, flare) — verificar no local",
            "Verificar fator de eficiência do burner se aplicável (como Exomad — fração de tempo operacional)",
            "Confirmar que biochar NÃO é usado para energia — apenas solo ou ambiente construído",
            "Verificar ausência de coal ash, plásticos ou qualquer mistura fóssil no feedstock",
            "Inspecionar processo de pirólise: temperatura, tempo de residência, registro por batch",
        ],
        "evidence_to_request": [
            "Certificado FSC/SFI/PEFC vigente OU dossiê ISAE 3000 OU plano de manejo gov. com 4 itens",
            "Registros de recebimento de biomassa (pesagem, NF, origem, data)",
            "Registros operacionais do burner/flare: horas de operação, fator de eficiência",
            "Contratos de fornecimento de biomassa com declaração de origem sustentável",
            "Documentação de destino final do biochar (solo/construção — NÃO incineração)",
            "Registros de produção por batch: temperatura, tempo de residência, massa produzida (seco)",
        ],
    },
    "carbon_accounting": {
        "label": "Contabilidade de Carbono",
        "vvb_context": "LCA completa A1→B1 — Puro é mais prescritivo que Isometric; erros de LCA são o principal motivo de Corrective Action Requests.",
        "field_items": [
            "Verificar LCA completa: A1 (biomassa), A2 (transporte), A3 (produção), A4 (transporte biochar), B1 (aplicação)",
            "Conferir fatores de emissão usados — fonte Ecoinvent/GaBi ou equivalente com referência",
            "Verificar consumo real de diesel vs. valores no LCA (causa de CARs em auditorias reais)",
            "Confirmar que emissões da chaminé não foram zeradas sem justificativa (causa de CAR)",
            "Revisar version control do LCA: usar versão final, não rascunhos desatualizados",
            "Verificar fronteiras do sistema GHG e justificativas de exclusão de fontes",
            "Confirmar que baseline counterfactual foi avaliado de forma conservadora",
            "Revisar análise de sensibilidade e incerteza — método Monte Carlo ou propagação",
        ],
        "evidence_to_request": [
            "Relatório LCA completo (versão final, auditada) — A1 a B1",
            "Planilha de cálculo do CORC claim com fórmulas auditáveis",
            "Registros de consumo real de diesel, eletricidade e outros energéticos",
            "Fatores de emissão utilizados com fonte (Ecoinvent v., GaBi, IPCC, etc.)",
            "Registros de emissões da chaminé (se aplicável) com metodologia de medição",
            "Análise de sensibilidade com valores min/max por variável",
        ],
    },
    "additionality": {
        "label": "Adicionalidade",
        "vvb_context": "Puro.Earth (Clarificação 005 ADD): first-of-its-kind NÃO isento — análise formal obrigatória.",
        "field_items": [
            "Verificar demonstração de adicionalidade financeira: custo simples, IRR/VPL ou análise de barreiras",
            "Confirmar que o projeto NÃO alega isenção por ser 'first-of-its-kind' (proibido pelo Puro 2025)",
            "Inspecionar análise financeira: IRR sem receita de carbono deve ser < WACC do projeto",
            "Confirmar ausência de subsídios ou incentivos regulatórios que tornariam o projeto viável sem carbono",
            "Verificar se biochar é prática comum na região — análise de mercado documentada",
            "Confirmar impacto líquido negativo: emissões do projeto < remoção de carbono (net negative)",
        ],
        "evidence_to_request": [
            "Análise financeira: IRR/VPL com e sem receita de carbono (Puro option b)",
            "OU análise de custo simples (option a) OU análise de barreiras documentada (option c)",
            "Declaração de que o projeto não é exigido por lei ou regulação (regulatory additionality)",
            "Análise de prática comum — evidência de baixa penetração de mercado de biochar",
            "LCA evidenciando net-negativity após todas as emissões do processo",
        ],
    },
    "permanence": {
        "label": "Permanência e Durabilidade",
        "vvb_context": "Hard gates: H/Corg < 0.5 e O/Corg < 0.2 por batch. Woolf 2021 — 200 anos.",
        "field_items": [
            "Confirmar limiar de durabilidade selecionado: 200 anos (Woolf 2021) ou 1000 anos",
            "Verificar H/Corg < 0,5 em laudos laboratoriais — por batch, ISO 17025",
            "Verificar O/Corg < 0,2 em laudos laboratoriais — por batch, ISO 17025",
            "Confirmar método de temperatura média anual do solo (MAST): medição direta ≥10/mês OU Lembrechts et al.",
            "Verificar que buffer pool foi calculado: padrão 2% para biochar em solo",
            "Para aplicações não-solo: confirmar plano de uso final — biochar NÃO vai para incineração",
        ],
        "evidence_to_request": [
            "Laudos laboratoriais (ISO 17025) por batch: H/Corg e O/Corg — histórico completo",
            "Registros de temperatura do solo com mín. 10 medições/site/mês do ano anterior",
            "OU consulta ao banco de dados Lembrechts et al. com coordenadas do projeto",
            "Cálculo do CORC conversion factor baseado em Woolf 2021 com MAST e H/Corg reais",
            "Buffer pool pool contribution: 2% documentado e deduzido do CORC claim",
            "Contratos com clientes confirmando aplicação final (solo/construção) — NÃO energia",
        ],
    },
    "monitoring": {
        "label": "Monitoramento e Amostragem",
        "vvb_context": "Puro Method A (todo batch) ou B (1/10 após ≥30 baseline). Mín. 3 amostras/batch, idade ≤6 meses.",
        "field_items": [
            "Verificar método de amostragem adotado: Method A (todo batch) ou Method B (1/10)",
            "Para Method B: confirmar que ≥30 amostras baseline foram coletadas antes da adoção",
            "Confirmar mínimo de 3 amostras por batch em todos os laudos",
            "Verificar idade das amostras no momento da análise: máx. 6 meses",
            "Conferir cadeia de custódia: batch nº, data, responsável, lacre, laboratório",
            "Inspecionar sistema de armazenamento de dados: retenção ≥5 anos, backup documentado",
            "Verificar tabela de parâmetros monitorados com frequências e QA/QC",
            "Confirmar que equipamentos de medição (balança, medidor de umidade) estão calibrados",
        ],
        "evidence_to_request": [
            "Registros de amostragem por batch: data, quantidade, responsável, nº de lacre",
            "Laudos laboratoriais (ISO 17025) com data, amostra vinculada, todos os parâmetros",
            "Certificado de calibração da balança e medidor de umidade (se aplicável)",
            "Procedimento operacional padrão (SOP) de coleta e envio de amostras",
            "Registros de armazenamento de dados com evidência de backup (≥5 anos)",
            "Tabela de parâmetros monitorados atualizada com dados reais",
        ],
    },
    "environmental_and_social_impact": {
        "label": "Impacto Ambiental, Social e ODS",
        "vvb_context": "SDG report OBRIGATÓRIO no Puro (diferente do Isometric). PAH: hierarquia regulação local > IBI/EBC.",
        "field_items": [
            "Verificar laudos de PAH — hierarquia: (1) regulação local, (2) IBI/EBC, (3) exceção notificada ao cliente",
            "Para Brasil: verificar se regulação CONAMA/estadual existe para biochar — senão, usar IBI/EBC",
            "Confirmar laudos PCB ≤ 0,2 mg/kg e PCDD/F ≤ 20 ng/kg em todos os batches",
            "Verificar metais pesados: As, Cd, Cr, Cu, Pb, Ni, Hg — limites EU/EPA/WBC",
            "Verificar plano de gestão adaptativa com 4 gatilhos: falha instrumental, poluente acima do limite, não-conformidade, risco saúde/segurança",
            "Confirmar relatório de ODS submetido à plataforma Puro.earth (obrigatório!)",
            "Verificar mecanismo de consulta: canal público ativo, prazos ≤14 e ≤60 dias",
            "Para aplicação em solo: verificar amostras baseline (pH, SOC, nutrientes) até 30cm",
        ],
        "evidence_to_request": [
            "Laudos PAH, PCB, PCDD/F, metais pesados (ISO 17025) — histórico por batch",
            "Relatório de ODS submetido à Puro.earth (template oficial Puro preenchido)",
            "Plano de gestão adaptativa com os 4 gatilhos documentados",
            "Registros do mecanismo de grievance: reclamações, respostas, prazos",
            "Amostras de solo baseline pré-aplicação (se via solo) — laudos laboratoriais",
            "Licenças ambientais vigentes (IBAMA, órgão estadual) com data de validade",
        ],
    },
    "stakeholder_input_process": {
        "label": "Consulta a Stakeholders",
        "vvb_context": "Processo de consulta documentado — mesmos prazos do Isometric (≤14/≤60 dias).",
        "field_items": [
            "Verificar lista de stakeholders consultados — abrangência dos grupos afetados",
            "Confirmar que consulta foi realizada ANTES da submissão para registro",
            "Revisar resumo dos comentários e como foram considerados no design do projeto",
            "Verificar que canal de grievance está ativo e acessível publicamente",
            "Confirmar prazos: reconhecimento ≤14 dias, resolução ≤60 dias",
            "Entrevistar 1-2 stakeholders para validar experiência real com o mecanismo",
        ],
        "evidence_to_request": [
            "Atas ou registros da consulta pública com lista de presença",
            "Registros de notificações enviadas e recebidas com timestamps",
            "Canal de grievance: URL/contato público com data de ativação",
            "Histórico de reclamações recebidas e resoluções (se houver)",
            "Declaração do proponente sobre considerações dos comentários no PDD",
        ],
    },
    "appendix": {
        "label": "Documentação Técnica do Reator",
        "vvb_context": "Hard gate: gases de pirólise recuperados/combustados. Puro adiciona requisito de Diretiva 2014/68/EU se pressão > 0.5 Bar.",
        "field_items": [
            "Inspecionar reator fisicamente: configuração real vs. diagrama de engenharia do PDD",
            "Verificar sensores de temperatura e tempo de residência — certificados de calibração recentes",
            "Inspecionar sistema de recuperação/combustão de gases pirolíticos (burner/flare) — FUNCIONAMENTO",
            "Para reactores com pressão > 0,5 Bar: verificar conformidade com Diretiva 2014/68/EU ou equivalente",
            "Conferir plano e registros de manutenção preventiva do reator",
            "Verificar certificado ISO 17025 vigente do laboratório de caracterização",
            "Revisar procedimento de amostragem e cadeia de custódia",
            "Conferir laudos: H/Corg <0,5; O/Corg <0,2; PAH, PCB, PCDD/F dentro dos limites Puro",
            "Verificar propriedades físicas: granulometria, BET (ISO 9277), pH, umidade",
        ],
        "evidence_to_request": [
            "Diagrama de engenharia do reator (assinado por responsável técnico)",
            "Certificados de calibração dos sensores (temperatura, pressão, tempo de residência)",
            "Registros de operação do burner/flare: horas de funcionamento, fator de eficiência",
            "Certificado de conformidade com 2014/68/EU se pressão > 0,5 Bar (ou norma equivalente)",
            "Plano de manutenção e histórico de execução (últimos 12 meses)",
            "Certificado ISO 17025 do laboratório (vigente)",
            "Laudos completos: H/Corg, O/Corg, PAHs, PCBs, PCDD/F, metais pesados, BET, granulometria",
        ],
    },
    "project_management": {
        "label": "Gestão do Projeto",
        "vvb_context": "SDG reporting obrigatório e plano de encerramento — específico Puro.Earth.",
        "field_items": [
            "Verificar relatório de ODS preenchido e submetido à plataforma Puro (obrigatório)",
            "Confirmar que plano de encerramento está documentado: condições de parada e pós-encerramento",
            "Verificar que o projeto está dentro do prazo de 18 meses para emissão (Clar. 009 GR3)",
            "Revisar documentação do Puro Supplier Agreement e suas cláusulas-chave",
            "Confirmar que KYB/KYC está completo e atualizado na plataforma Puro.earth",
        ],
        "evidence_to_request": [
            "Relatório de ODS submetido à Puro.earth (template oficial preenchido)",
            "Plano de encerramento e condições de pausa/stop",
            "Cronograma de submissão — confirmar prazo de 18 meses vs. data de coleta de dados",
            "Puro Platform Agreement assinado com todas as appendices",
            "Confirmação de KYB/KYC completado (screenshot ou declaração da plataforma)",
        ],
    },
}

PURO_MODULE_ORDER = [
    "project_data",
    "feedstock_and_production",
    "carbon_accounting",
    "additionality",
    "permanence",
    "monitoring",
    "environmental_and_social_impact",
    "stakeholder_input_process",
    "appendix",
    "project_management",
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

def _methodology_label(methodology: str) -> str:
    return {
        "isometric":  "Isometric Biochar v1.2",
        "puro_earth": "Puro.Earth Biochar Edition 2025",
        "rainbow":    "Rainbow Carbon",
        "c_sink":     "Global C-SINK / CSI-EBI",
        "verra_vcs":  "Verra VCS VM0044",
    }.get(methodology, methodology)


def _module_label(module: str, methodology: str) -> str:
    """Retorna o label do módulo correto para a metodologia."""
    if methodology == "puro_earth":
        return PURO_MODULE_META.get(module, {}).get("label", module)
    return MODULE_META.get(module, {}).get("label", module)


def build_developer_plan(audit_results: list, methodology: str = "isometric") -> dict:
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
            "module_label":   _module_label(r.get("module", ""), methodology),
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
        "methodology": _methodology_label(methodology),
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

def build_vvb_plan(all_requirements: list, audit_results: list, methodology: str = "isometric") -> dict:
    """
    Plano de inspeção (Checklist Pré-VVB) — por módulo.
    Suporta Isometric Biochar v1.2 e Puro.Earth Edition 2025.
    """
    audit_index = {r.get("requirement_id"): r for r in audit_results}

    # Seleciona MODULE_META e ORDER corretos
    if methodology == "puro_earth":
        meta    = PURO_MODULE_META
        order   = PURO_MODULE_ORDER
    else:
        meta    = MODULE_META
        order   = MODULE_ORDER

    # Group requirements by module, preserving order
    by_module: dict = {k: [] for k in order}
    for req in all_requirements:
        mod = req.get("module", "other")
        if mod not in by_module:
            by_module[mod] = []
        by_module[mod].append(req)

    modules_out = []
    for mod_key in order:
        reqs = by_module.get(mod_key, [])
        if not reqs:
            continue
        mod_cfg = meta.get(mod_key, {})
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
            "label":             mod_cfg.get("label", mod_key),
            "vvb_context":       mod_cfg.get("vvb_context", ""),
            "field_items":       mod_cfg.get("field_items", []),
            "evidence_to_request": mod_cfg.get("evidence_to_request", []),
            "requirements":      reqs_out,
            "req_count":         len(reqs_out),
            "operational_only_count": op_count,
        })

    total_req = sum(len(m["requirements"]) for m in modules_out)
    total_op  = sum(m["operational_only_count"] for m in modules_out)

    return {
        "role":              "vvb",
        "methodology":       _methodology_label(methodology),
        "total_requirements": total_req,
        "operational_only_count": total_op,
        "modules":           modules_out,
    }
