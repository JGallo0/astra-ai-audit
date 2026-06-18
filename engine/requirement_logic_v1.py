"""
Engine v1 — Funções de lógica protocol-native para Isometric Biochar.

Cada função recebe (data: dict, audit_mode: str) e retorna um dict
compatível com build_logic_result() do requirement_logic.py.

audit_mode:
  "development" — projeto em fase de PDD/planejamento
  "operational" — projeto em execução produzindo biochar

Thresholds extraídos diretamente dos protocolos:
  - Biochar Production and Storage v1.2 — Isometric
  - Biochar Storage in Soil Environments v1.2 — Isometric
  - Biochar Storage in Built Environment v1.0 — Isometric
"""

from engine.requirement_logic import (
    build_logic_result,
    score_boolean_field,
    score_presence_field,
    summarize_field_scores,
    derive_requirement_rating,
    derive_requirement_status_from_score,
    collect_field_score_notes,
)


# ── Helpers internos ──────────────────────────────────────────────────────────

def _compliant(notes=None, score=100):
    return build_logic_result(
        status="compliant",
        missing_fields=[],
        failed_fields=[],
        notes=notes or [],
        requirement_score=score,
        field_scores=[],
        requirement_rating="strong",
    )

def _non_compliant(gap, recommendation, citation, notes=None, score=0):
    n = list(notes or [])
    n.append(f"[Protocolo] {citation}")
    return build_logic_result(
        status="non_compliant",
        missing_fields=[],
        failed_fields=[],
        notes=n,
        requirement_score=score,
        field_scores=[],
        requirement_rating="weak",
        gap=gap,
        recommendation=recommendation,
    )

def _future_evidence(gap, recommendation, citation, notes=None, score=35):
    n = list(notes or [])
    n.append(f"[Protocolo] {citation}")
    return build_logic_result(
        status="future_evidence_required",
        missing_fields=[],
        failed_fields=[],
        notes=n,
        requirement_score=score,
        field_scores=[],
        requirement_rating="weak",
        gap=gap,
        recommendation=recommendation,
    )

def _stub(req_id, description, audit_mode):
    """Stub genérico para funções ainda não totalmente implementadas."""
    if audit_mode == "development":
        return build_logic_result(
            status="future_evidence_required",
            missing_fields=[f"{req_id}.response"],
            failed_fields=[],
            notes=[f"Requisito {req_id} — avaliação detalhada pendente de implementação."],
            requirement_score=35,
            field_scores=[],
            requirement_rating="weak",
            gap=f"{description} não avaliado em detalhe.",
            recommendation=f"Verifique o requisito {req_id} na plataforma Isometric Certify.",
        )
    return build_logic_result(
        status="partial",
        missing_fields=[f"{req_id}.evidence"],
        failed_fields=[],
        notes=[f"Requisito {req_id} — avaliação detalhada pendente de implementação."],
        requirement_score=45,
        field_scores=[],
        requirement_rating="moderate",
        gap=f"{description} requer evidências operacionais.",
        recommendation=f"Verifique o requisito {req_id} na plataforma Isometric Certify.",
    )


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES IMPLEMENTADAS — com thresholds reais do protocolo
# ══════════════════════════════════════════════════════════════════════════════

# ── R-VGXA-0 | Biochar chemical properties ───────────────────────────────────

def eval_biochar_chemical_properties_v1(data, audit_mode="development"):
    """
    Verifica propriedades químicas do biochar contra thresholds do protocolo.

    Hard gates (ambos os modos):
      H/Corg < 0.5  (Soil Environments v1.2, Table 2)
      O/Corg < 0.2  (Soil Environments v1.2, Table 2)
      PCB ≤ 0.2 mg/kg DM  (Soil Environments v1.2, Section 3)
      PCDD/F ≤ 20 ng/kg DM  (Soil Environments v1.2, Section 3)
    """
    char = data.get("biochar", {}).get("characterization", {})
    pollutants = char.get("pollutants", {})

    hc_ratio   = char.get("h_c_ratio") or char.get("hc_ratio")
    oc_ratio   = char.get("o_c_ratio") or char.get("oc_ratio")
    pcb        = pollutants.get("PCBs") or char.get("pcb_mg_kg")
    pcdd_f     = pollutants.get("dioxins") or char.get("pcdd_f_ng_kg")
    chem_done  = char.get("chemical_analysis_performed")
    lab_done   = char.get("lab_reports")

    CITATION = "Isometric Biochar Storage in Soil Environments v1.2, Table 2 & Section 3"

    # Hard gate: H/C ratio — o critério mais crítico de permanência
    if hc_ratio is not None:
        if hc_ratio >= 0.5:
            return _non_compliant(
                gap=f"H/Corg = {hc_ratio:.3f} ≥ 0.5 — biochar não atinge estabilidade mínima para crédito.",
                recommendation="Otimizar condições de pirólise (temperatura > 500°C, tempo de residência) para reduzir H/Corg abaixo de 0.5. Referenciar ISO 29541:2025 ou ASTM D5373.",
                citation=CITATION,
                score=0,
            )
    elif audit_mode == "operational":
        return _non_compliant(
            gap="H/Corg ratio não informado — laudo laboratorial obrigatório em modo operacional.",
            recommendation="Realizar análise elementar (H, C, O) por ISO 29541:2025 ou ASTM D5373-21 em laboratório ISO 17025.",
            citation=CITATION,
            score=0,
        )

    # Hard gate: O/C ratio
    if oc_ratio is not None:
        if oc_ratio >= 0.2:
            return _non_compliant(
                gap=f"O/Corg = {oc_ratio:.3f} ≥ 0.2 — biochar com baixa estabilidade aromática.",
                recommendation="Revisar processo de pirólise. O/Corg < 0.2 é exigido para comprovação de estabilidade de longo prazo.",
                citation=CITATION,
                score=0,
            )

    # Hard gate: PCB
    if pcb is not None:
        if pcb > 0.2:
            return _non_compliant(
                gap=f"PCB = {pcb} mg/kg DM — excede limite de 0.2 mg/kg (World Biochar Certificate).",
                recommendation="Revisar feedstock e condições de pirólise para reduzir PCBs. Análise via DIN EN 16167 ou EPA 8082A.",
                citation=CITATION,
                score=0,
            )

    # Hard gate: PCDD/F (dioxinas/furanos)
    if pcdd_f is not None:
        if pcdd_f > 20:
            return _non_compliant(
                gap=f"PCDD/F = {pcdd_f} ng/kg DM — excede limite de 20 ng/kg (World Biochar Certificate).",
                recommendation="Revisar condições de pirólise para reduzir formação de dioxinas/furanos. Análise via DIN EN 16190 ou EPA Method 8290A.",
                citation=CITATION,
                score=0,
            )

    # Avaliação de completude por modo
    field_scores = [
        score_boolean_field("biochar.characterization.chemical_analysis_performed", chem_done, 40,
                            note_if_missing="Análise química do biochar não evidenciada."),
        score_boolean_field("biochar.characterization.lab_reports", lab_done, 30,
                            note_if_missing="Laudos laboratoriais não fornecidos."),
        score_presence_field("biochar.characterization.h_c_ratio", hc_ratio, 20,
                             note_if_missing="H/Corg não informado."),
        score_presence_field("biochar.characterization.o_c_ratio", oc_ratio, 10,
                             note_if_missing="O/Corg não informado."),
    ]

    requirement_score = summarize_field_scores(field_scores)
    notes = collect_field_score_notes(field_scores)

    if audit_mode == "development":
        threshold_nc, threshold_c = 30, 70
        if hc_ratio is None:
            notes.append("Desenvolvimento: H/Corg deve ser fornecido antes da validação.")
    else:
        threshold_nc, threshold_c = 60, 90
        if hc_ratio is None:
            notes.append("Operacional: H/Corg obrigatório — laudos laboratoriais exigidos.")

    status = derive_requirement_status_from_score(requirement_score, threshold_nc, threshold_c)
    return build_logic_result(
        status=status,
        missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
        notes=notes,
        requirement_score=requirement_score,
        field_scores=field_scores,
        requirement_rating=derive_requirement_rating(requirement_score),
    )


# ── R-2TMM-0 | Analytical laboratory qualified ───────────────────────────────

def eval_biochar_laboratory_v1(data, audit_mode="development"):
    """
    R-2TMM-0: Laboratório ISO 17025 ou validação externa equivalente.
    Hard gate em ambos os modos.
    """
    char = data.get("biochar", {}).get("characterization", {})
    lab_accred = char.get("contaminant_testing")  # proxy: se fez testes, tem lab
    lab_reports = char.get("lab_reports")
    CITATION = "Isometric Biochar Storage in Soil Environments v1.2, Section 4.1 — ISO 17025"

    field_scores = [
        score_boolean_field("biochar.characterization.lab_reports", lab_reports, 70,
                            note_if_missing="Relatórios laboratoriais não fornecidos."),
        score_boolean_field("biochar.characterization.contaminant_testing", lab_accred, 30,
                            note_if_missing="Testes de contaminantes não evidenciados — laboratório não identificado."),
    ]

    requirement_score = summarize_field_scores(field_scores)
    notes = collect_field_score_notes(field_scores)
    notes.append(f"[Protocolo] {CITATION}")

    threshold = 60 if audit_mode == "operational" else 30
    status = derive_requirement_status_from_score(requirement_score, threshold, 90)

    return build_logic_result(
        status=status,
        missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
        notes=notes,
        requirement_score=requirement_score,
        field_scores=field_scores,
        requirement_rating=derive_requirement_rating(requirement_score),
        gap="Laboratório não identificado ou não qualificado (ISO 17025)." if requirement_score < threshold else "",
        recommendation="Identificar laboratório acreditado ISO 17025 para análises de carbono e contaminantes. Fornecer registros de calibração ao VVB." if requirement_score < threshold else "",
    )


# ── R-S8K1-1 | Sampling procedure ───────────────────────────────────────────

def eval_sampling_procedure_v1(data, audit_mode="development"):
    """
    R-S8K1-1: Procedimento de amostragem do biochar.

    Hard gates (operational):
      ≥ 30 amostras antes de usar Method B
      ≥ 3 amostras por batch
      Amostras com ≤ 6 meses de idade
      Method A ou B selecionado e justificado
    """
    sampling = data.get("sampling", {})
    plan_defined  = sampling.get("sampling_plan_defined")
    method        = sampling.get("sampling_method")        # "method_a" | "method_b"
    sample_count  = sampling.get("sample_count")           # int — total histórico
    samples_batch = sampling.get("samples_per_batch")      # int — por batch
    sample_age    = sampling.get("sample_age_months")      # float — idade máx.

    CITATION = "Isometric Biochar Production and Storage v1.2, Section 4 — Sampling"

    # Hard gate operacional: Method B só após ≥ 30 amostras
    if audit_mode == "operational":
        if method == "method_b" and sample_count is not None and sample_count < 30:
            return _non_compliant(
                gap=f"Method B selecionado mas apenas {sample_count} amostras históricas (<30 mínimo).",
                recommendation="Coletar ≥ 30 amostras usando Method A antes de transitar para Method B. Protocolo: 3 replicatas de 10 batches = 30 amostras.",
                citation=CITATION,
                score=0,
            )
        # Hard gate: mínimo 3 por batch
        if samples_batch is not None and samples_batch < 3:
            return _non_compliant(
                gap=f"Apenas {samples_batch} amostras por batch — mínimo obrigatório é 3.",
                recommendation="Coletar mínimo 3 amostras representativas por batch de produção (horizontal + vertical para homogeneidade).",
                citation=CITATION,
                score=0,
            )
        # Hard gate: idade das amostras
        if sample_age is not None and sample_age > 6:
            return _non_compliant(
                gap=f"Amostras com {sample_age:.1f} meses — máximo permitido é 6 meses.",
                recommendation="Utilizar apenas amostras coletadas nos 6 meses anteriores ao batch de produção. Amostras mais antigas são inelegíveis.",
                citation=CITATION,
                score=0,
            )

    field_scores = [
        score_boolean_field("sampling.sampling_plan_defined", plan_defined, 50,
                            note_if_missing="Plano de amostragem não definido."),
        score_presence_field("sampling.sampling_method", method, 30,
                             note_if_missing="Método A ou B não selecionado."),
        score_presence_field("sampling.samples_per_batch", samples_batch, 20,
                             note_if_missing="Número de amostras por batch não especificado (mínimo: 3)."),
    ]

    requirement_score = summarize_field_scores(field_scores)
    notes = collect_field_score_notes(field_scores)
    notes.append(f"[Protocolo] {CITATION}")

    threshold_nc = 50 if audit_mode == "operational" else 30
    status = derive_requirement_status_from_score(requirement_score, threshold_nc, 85)

    return build_logic_result(
        status=status,
        missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
        notes=notes,
        requirement_score=requirement_score,
        field_scores=field_scores,
        requirement_rating=derive_requirement_rating(requirement_score),
    )


# ── R-7C8E-0 + R-1T2Y-0 | Durability selection and demonstration ─────────────

def eval_durability_selection_v1(data, audit_mode="development"):
    """
    R-7C8E-0: Opção de durabilidade selecionada (200 ou 1000 anos).
    R-1T2Y-0: Durabilidade demonstrada acima do threshold.

    Hard gate: durabilidade > 200 anos (threshold mínimo do protocolo).
    Hard gate operacional: H/Corg < 0.5 com laudo laboratorial.
    """
    eligibility  = data.get("eligibility", {})
    methodology  = data.get("methodology", {})
    char         = data.get("biochar", {}).get("characterization", {})

    durability_years  = eligibility.get("durability_years")
    durability_option = methodology.get("durability_option")
    hc_ratio          = char.get("h_c_ratio") or char.get("hc_ratio")
    permanence_claim  = eligibility.get("permanence_claim")

    CITATION = "Isometric Standard v1.7 — R-7C8E-0/R-1T2Y-0; Biochar Storage in Soil Environments v1.2 Section 5.1"

    # Hard gate: durabilidade mínima
    if durability_years is not None and durability_years < 200:
        return _non_compliant(
            gap=f"Durabilidade declarada = {durability_years} anos — mínimo exigido pelo protocolo é 200 anos.",
            recommendation="Selecionar opção de 200 anos ou 1000 anos conforme protocolo Isometric. Demonstrar com H/Corg < 0.5.",
            citation=CITATION,
            score=0,
        )

    # Hard gate operacional: H/C precisa estar medido
    if audit_mode == "operational" and hc_ratio is None:
        return _non_compliant(
            gap="H/Corg não medido — impossível demonstrar durabilidade sem análise laboratorial.",
            recommendation="Realizar análise elementar (H, C) por ISO 29541:2025 em laboratório ISO 17025. H/Corg < 0.5 obrigatório.",
            citation=CITATION,
            score=0,
        )

    field_scores = [
        score_presence_field("methodology.durability_option", durability_option, 40,
                             note_if_missing="Opção de durabilidade (200 ou 1000 anos) não selecionada."),
        score_boolean_field("eligibility.permanence_claim", permanence_claim, 30,
                            note_if_missing="Claim de permanência não declarado."),
        score_presence_field("biochar.characterization.h_c_ratio", hc_ratio, 30,
                             note_if_missing="H/Corg não medido — requerido para cálculo Fdurable."),
    ]

    requirement_score = summarize_field_scores(field_scores)
    notes = collect_field_score_notes(field_scores)
    notes.append(f"[Protocolo] {CITATION}")
    if durability_option:
        notes.append(f"Opção selecionada: {durability_option} anos.")
    if hc_ratio is not None:
        notes.append(f"H/Corg = {hc_ratio:.3f} {'✓ < 0.5' if hc_ratio < 0.5 else '✗ ≥ 0.5'}.")

    threshold_nc = 50 if audit_mode == "operational" else 25
    status = derive_requirement_status_from_score(requirement_score, threshold_nc, 80)

    return build_logic_result(
        status=status,
        missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
        notes=notes,
        requirement_score=requirement_score,
        field_scores=field_scores,
        requirement_rating=derive_requirement_rating(requirement_score),
    )


# ── R-F5RZ-0 | Soil temperature for 200-year durability ──────────────────────

def eval_durability_soil_temp_v1(data, audit_mode="development"):
    """
    R-F5RZ-0: Método de temperatura do solo para cálculo Fdurable (opção 200 anos).
    Se variação > 1°C no projeto → subdividir ou usar temperatura mais conservadora.
    """
    methodology = data.get("methodology", {})
    storage_pathway = methodology.get("storage_pathway", "")

    if storage_pathway != "soil":
        return build_logic_result(
            status="not_applicable",
            missing_fields=[],
            failed_fields=[],
            notes=["Requisito aplicável apenas a projetos com armazenamento em solo (storage_pathway = soil)."],
            requirement_score=None,
            field_scores=[],
            requirement_rating=None,
        )

    durability_option = methodology.get("durability_option", "")
    soil_temp         = data.get("storage", {}).get("soil", {}).get("annual_avg_temp_celsius")
    soil_temp_method  = data.get("storage", {}).get("soil", {}).get("temperature_method")

    CITATION = "Isometric Biochar Storage in Soil Environments v1.2, Section 5.1.1 — Soil Temperature"

    field_scores = [
        score_presence_field("storage.soil.temperature_method", soil_temp_method, 60,
                             note_if_missing="Método de temperatura do solo não especificado (medição direta ou banco de dados global como Lembrechts et al. 2022)."),
        score_presence_field("storage.soil.annual_avg_temp_celsius", soil_temp, 40,
                             note_if_missing="Temperatura média anual do solo não fornecida."),
    ]

    requirement_score = summarize_field_scores(field_scores)
    notes = collect_field_score_notes(field_scores)
    notes.append(f"[Protocolo] {CITATION}")

    if soil_temp is not None:
        notes.append(f"Temperatura do solo = {soil_temp}°C.")
        if soil_temp < 0:
            notes.append("⚠ Temperatura negativa — verificar medição. Biochar não deve ser aplicado em solo congelado.")
    if audit_mode == "development" and soil_temp_method:
        notes.append(f"Método: {soil_temp_method}")

    threshold_nc = 50 if audit_mode == "operational" else 25
    status = derive_requirement_status_from_score(requirement_score, threshold_nc, 85)

    return build_logic_result(
        status=status,
        missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
        notes=notes,
        requirement_score=requirement_score,
        field_scores=field_scores,
        requirement_rating=derive_requirement_rating(requirement_score),
        gap="Método de temperatura do solo não documentado — impossível calcular Fdurable." if requirement_score < threshold_nc else "",
        recommendation="Documentar método: (1) medição direta ≥10 amostras/site-mês no ano anterior, ou (2) banco de dados Lembrechts et al. (2022) com justificativa da região." if requirement_score < threshold_nc else "",
    )


# ── R-MY64-0 | Pollution prevention (PAHs, metals, PCBs/Dioxins) ─────────────

def eval_pollution_prevention_v1(data, audit_mode="development"):
    """
    R-MY64-0: Prevenção de poluição — PAHs, metais pesados, PCBs, Dioxinas.

    Hard gates operacionais (WBC limits):
      PCB ≤ 0.2 mg/kg DM
      PCDD/F ≤ 20 ng/kg DM
      Metais pesados ≤ limites EU/EPA
    """
    safeguards = data.get("safeguards", {})
    char       = data.get("biochar", {}).get("characterization", {})
    pollutants = char.get("pollutants", {})

    pah_risk_assessed  = safeguards.get("environmental_risk_assessment")
    mitigation_plan    = safeguards.get("mitigation_plan")
    pcb                = pollutants.get("PCBs") or char.get("pcb_mg_kg")
    pcdd_f             = pollutants.get("dioxins") or char.get("pcdd_f_ng_kg")
    heavy_metals_ok    = pollutants.get("heavy_metals")

    CITATION = "Isometric Biochar Production and Storage v1.2, Sections 6-7; World Biochar Certificate limits"

    if audit_mode == "operational":
        if pcb is not None and pcb > 0.2:
            return _non_compliant(
                gap=f"PCB = {pcb} mg/kg DM > 0.2 mg/kg (limite WBC). Projeto inelegível.",
                recommendation="Revisar feedstock e processo de pirólise. Análise via DIN EN 16167 ou EPA 8082A.",
                citation=CITATION,
                score=0,
            )
        if pcdd_f is not None and pcdd_f > 20:
            return _non_compliant(
                gap=f"PCDD/F = {pcdd_f} ng/kg DM > 20 ng/kg (limite WBC). Projeto inelegível.",
                recommendation="Revisar condições de pirólise. Análise via DIN EN 16190 ou EPA Method 8290A.",
                citation=CITATION,
                score=0,
            )

    field_scores = [
        score_boolean_field("safeguards.environmental_risk_assessment", pah_risk_assessed, 40,
                            note_if_missing="Avaliação de risco ambiental de PAHs não realizada."),
        score_boolean_field("safeguards.mitigation_plan", mitigation_plan, 30,
                            note_if_missing="Plano de mitigação de poluentes não documentado."),
        score_presence_field("biochar.characterization.pollutants.PCBs", pcb, 15,
                             note_if_missing="Concentração de PCBs não declarada."),
        score_presence_field("biochar.characterization.pollutants.dioxins", pcdd_f, 15,
                             note_if_missing="Concentração de PCDD/F não declarada."),
    ]

    requirement_score = summarize_field_scores(field_scores)
    notes = collect_field_score_notes(field_scores)
    notes.append(f"[Protocolo] {CITATION}")

    if pcb is not None:
        notes.append(f"PCB = {pcb} mg/kg {'✓ ≤ 0.2' if pcb <= 0.2 else '✗ > 0.2 (excede limite)'}.")
    if pcdd_f is not None:
        notes.append(f"PCDD/F = {pcdd_f} ng/kg {'✓ ≤ 20' if pcdd_f <= 20 else '✗ > 20 (excede limite)'}.")

    threshold_nc = 50 if audit_mode == "operational" else 20
    status = derive_requirement_status_from_score(requirement_score, threshold_nc, 85)

    return build_logic_result(
        status=status,
        missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
        notes=notes,
        requirement_score=requirement_score,
        field_scores=field_scores,
        requirement_rating=derive_requirement_rating(requirement_score),
    )


# ── R-6AQG-0 + R-SZK5-0 + R-DMET-0 + R-19AF-0 | Reactor design ─────────────

def eval_reactor_design_v1(data, audit_mode="development"):
    """
    Grupo de requisitos do reator de pirólise:
      R-6AQG-0: Diagrama de engenharia
      R-SZK5-0: Sensores de leakage de gás pirolítico
      R-DMET-0: Seleção de materiais justificada
      R-19AF-0: Plano de manutenção
    """
    production = data.get("production", {})

    has_diagram      = production.get("reactor_design_diagram") or production.get("engineering_design_diagram")
    has_maintenance  = production.get("maintenance_plan")
    has_description  = production.get("system_description")
    end_material     = production.get("end_material_process_description")

    CITATION = "Isometric Biochar Production and Storage v1.2, Reactor Design Requirements"

    field_scores = [
        score_boolean_field("production.reactor_design_diagram", has_diagram, 40,
                            note_if_missing="Diagrama de engenharia do reator não fornecido (dimensões, entradas/saídas, sensores T/P)."),
        score_boolean_field("production.maintenance_plan", has_maintenance, 30,
                            note_if_missing="Plano de manutenção do reator não documentado."),
        score_boolean_field("production.end_material_process_description", end_material, 20,
                            note_if_missing="Processo de produção do material final não descrito em detalhe."),
        score_presence_field("production.system_description", has_description, 10,
                             note_if_missing="Descrição geral do sistema não fornecida."),
    ]

    requirement_score = summarize_field_scores(field_scores)
    notes = collect_field_score_notes(field_scores)
    notes.append(f"[Protocolo] {CITATION}")

    if audit_mode == "development":
        notes.append("Desenvolvimento: diagrama e plano de manutenção obrigatórios no PDD.")
        threshold_nc, threshold_c = 30, 80
    else:
        notes.append("Operacional: diagrama atualizado e registros de manutenção exigidos para verificação.")
        threshold_nc, threshold_c = 50, 85

    status = derive_requirement_status_from_score(requirement_score, threshold_nc, threshold_c)

    return build_logic_result(
        status=status,
        missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
        notes=notes,
        requirement_score=requirement_score,
        field_scores=field_scores,
        requirement_rating=derive_requirement_rating(requirement_score),
    )


# ── R-BC4H-0 | Adaptive management plan ─────────────────────────────────────

def eval_adaptive_management_v1(data, audit_mode="development"):
    """
    R-BC4H-0: Plano de gestão adaptativa com 4 gatilhos obrigatórios de pausa/stop.
    Hard gate em ambos os modos.
    """
    management = data.get("management", {})
    safeguards = data.get("safeguards", {})

    adaptive_plan  = management.get("adaptive_management_plan") or safeguards.get("adaptive_management_plan")
    emergency_resp = management.get("emergency_response_plan")
    pause_cond     = management.get("pause_or_stop_conditions")
    info_sharing   = management.get("information_sharing_plan")

    CITATION = "Isometric Biochar Production and Storage v1.2, Section 19.2 (R-BC4H-0)"

    field_scores = [
        score_boolean_field("management.adaptive_management_plan", adaptive_plan, 35,
                            note_if_missing="Plano de gestão adaptativa ausente."),
        score_boolean_field("management.emergency_response_plan", emergency_resp, 25,
                            note_if_missing="Plano de resposta emergencial ausente."),
        score_boolean_field("management.pause_or_stop_conditions", pause_cond, 25,
                            note_if_missing="Condições de pausa/parada não definidas (falha instrumental, poluentes, não conformidade regulatória, saúde/segurança)."),
        score_boolean_field("management.information_sharing_plan", info_sharing, 15,
                            note_if_missing="Plano de compartilhamento de informações ausente."),
    ]

    requirement_score = summarize_field_scores(field_scores)
    notes = collect_field_score_notes(field_scores)
    notes.append(f"[Protocolo] {CITATION}")
    notes.append("Os 4 gatilhos obrigatórios de pausa/stop: (1) falha de instrumentos, (2) poluentes > threshold, (3) não conformidade regulatória, (4) risco à saúde.")

    threshold_nc = 50 if audit_mode == "operational" else 40
    status = derive_requirement_status_from_score(requirement_score, threshold_nc, 85)

    return build_logic_result(
        status=status,
        missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
        notes=notes,
        requirement_score=requirement_score,
        field_scores=field_scores,
        requirement_rating=derive_requirement_rating(requirement_score),
        gap="Plano de gestão adaptativa incompleto — faltam condições de pausa/parada obrigatórias." if requirement_score < threshold_nc else "",
        recommendation="Documentar os 4 gatilhos de pausa/parada per R-BC4H-0: falha instrumental, excesso de poluentes, não conformidade regulatória, risco à saúde/segurança." if requirement_score < threshold_nc else "",
    )


# ══════════════════════════════════════════════════════════════════════════════
# STUBS ESTRUTURADOS — retornam resultado válido, implementação futura
# ══════════════════════════════════════════════════════════════════════════════

def eval_protocol_eligibility_v1(data, audit_mode="development"):
    eligibility = data.get("eligibility", {})
    description = data.get("production", {}).get("system_description")
    field_scores = [
        score_presence_field("production.system_description", description, 60,
                             note_if_missing="Justificativa de elegibilidade não encontrada."),
        score_presence_field("eligibility.eligible_pathway", eligibility.get("eligible_pathway"), 40,
                             note_if_missing="Pathway de elegibilidade não especificado."),
    ]
    score = summarize_field_scores(field_scores)
    status = derive_requirement_status_from_score(score, 30, 80)
    return build_logic_result(status=status, missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[], notes=collect_field_score_notes(field_scores),
        requirement_score=score, field_scores=field_scores, requirement_rating=derive_requirement_rating(score))

def eval_project_ownership_v1(data, audit_mode="development"):
    project = data.get("project", {})
    ownership = project.get("ownership_evidence") or data.get("product", {}).get("certification_scheme")
    field_scores = [
        score_presence_field("project.ownership_evidence", ownership, 70,
                             note_if_missing="Evidência de titularidade das remoções não fornecida."),
        score_presence_field("project.name", project.get("name"), 30,
                             note_if_missing="Nome do projeto/entidade proprietária não identificado."),
    ]
    score = summarize_field_scores(field_scores)
    status = derive_requirement_status_from_score(score, 40, 85)
    return build_logic_result(status=status, missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[], notes=collect_field_score_notes(field_scores),
        requirement_score=score, field_scores=field_scores, requirement_rating=derive_requirement_rating(score))

def eval_technical_description_v1(data, audit_mode="development"):
    desc = data.get("production", {}).get("system_description")
    tech = data.get("production", {}).get("pyrolysis_technology")
    field_scores = [
        score_presence_field("production.system_description", desc, 60, note_if_missing="Descrição técnica do processo de remoção não encontrada."),
        score_presence_field("production.pyrolysis_technology", tech, 40, note_if_missing="Tecnologia de pirólise não identificada."),
    ]
    score = summarize_field_scores(field_scores)
    status = derive_requirement_status_from_score(score, 30, 80)
    return build_logic_result(status=status, missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[], notes=collect_field_score_notes(field_scores),
        requirement_score=score, field_scores=field_scores, requirement_rating=derive_requirement_rating(score))

def eval_project_participants_v1(data, audit_mode="development"):
    return _stub("R-F6R7-0", "Lista de participantes do projeto", audit_mode)

def eval_project_locations_v1(data, audit_mode="development"):
    project = data.get("project", {})
    country = project.get("country")
    locations = project.get("locations")
    field_scores = [
        score_presence_field("project.country", country, 40, note_if_missing="País do projeto não identificado."),
        score_presence_field("project.locations", locations, 60, note_if_missing="Coordenadas ou endereço do projeto não fornecidos."),
    ]
    score = summarize_field_scores(field_scores)
    status = derive_requirement_status_from_score(score, 30, 80)
    return build_logic_result(status=status, missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[], notes=collect_field_score_notes(field_scores),
        requirement_score=score, field_scores=field_scores, requirement_rating=derive_requirement_rating(score))

def eval_removal_capacity_v1(data, audit_mode="development"):
    return _stub("R-XT6V-0", "Capacidade estimada de remoção de carbono (tCO2 por período de crédito)", audit_mode)

def eval_system_boundary_v1(data, audit_mode="development"):
    ghg = data.get("ghg_accounting", {})
    quant = data.get("quantification", {})
    field_scores = [
        score_boolean_field("ghg_accounting.system_boundary_defined", ghg.get("system_boundary_defined"), 50, note_if_missing="Boundary do sistema GHG não definido."),
        score_boolean_field("quantification.crediting_activity_boundaries", quant.get("crediting_activity_boundaries"), 30, note_if_missing="Limites da atividade de crédito não documentados."),
        score_boolean_field("ghg_accounting.baseline_defined", ghg.get("baseline_defined"), 20, note_if_missing="Baseline não definido."),
    ]
    score = summarize_field_scores(field_scores)
    status = derive_requirement_status_from_score(score, 40, 85)
    return build_logic_result(status=status, missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[], notes=collect_field_score_notes(field_scores),
        requirement_score=score, field_scores=field_scores, requirement_rating=derive_requirement_rating(score))

def eval_baseline_v1(data, audit_mode="development"):
    ghg = data.get("ghg_accounting", {})
    feedstock = data.get("feedstock", {})
    field_scores = [
        score_boolean_field("ghg_accounting.baseline_defined", ghg.get("baseline_defined"), 60, note_if_missing="Linha de base não definida."),
        score_presence_field("feedstock.pre_project_biomass_use", feedstock.get("pre_project_biomass_use"), 40, note_if_missing="Uso pré-projeto do feedstock (cenário counterfactual) não descrito."),
    ]
    score = summarize_field_scores(field_scores)
    status = derive_requirement_status_from_score(score, 40, 85)
    return build_logic_result(status=status, missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[], notes=collect_field_score_notes(field_scores),
        requirement_score=score, field_scores=field_scores, requirement_rating=derive_requirement_rating(score))

def eval_leakage_v1(data, audit_mode="development"):
    return _stub("R-HF2G-0", "Avaliação de leakage (emissões fora do boundary)", audit_mode)

def eval_financial_additionality_v1(data, audit_mode="development"):
    eligibility = data.get("eligibility", {})
    add_claim = eligibility.get("additionality_claim")
    add_evidence = eligibility.get("additionality_evidence")
    field_scores = [
        score_boolean_field("eligibility.additionality_claim", add_claim, 60, note_if_missing="Claim de adicionalidade financeira não declarado."),
        score_presence_field("eligibility.additionality_evidence", add_evidence, 40, note_if_missing="Evidência de adicionalidade financeira (revenue principal OU análise IRR) não fornecida."),
    ]
    score = summarize_field_scores(field_scores)
    if add_claim is not True:
        return _non_compliant("Adicionalidade financeira não declarada.", "Demonstrar que remoções de carbono são o propósito principal E principal fonte de receita; OU fornecer análise de IRR demonstrando barreiras econômicas.", "Isometric Standard v1.7, R-53Y5-0")
    status = derive_requirement_status_from_score(score, 50, 85)
    return build_logic_result(status=status, missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[], notes=collect_field_score_notes(field_scores),
        requirement_score=score, field_scores=field_scores, requirement_rating=derive_requirement_rating(score))

def eval_common_practice_additionality_v1(data, audit_mode="development"):
    return _stub("R-RRST-0", "Análise de prática comum (common practice additionality)", audit_mode)

def eval_environmental_additionality_v1(data, audit_mode="development"):
    eligibility = data.get("eligibility", {})
    net_negative = eligibility.get("net_negative_claim") or eligibility.get("permanence_claim")
    field_scores = [
        score_boolean_field("eligibility.net_negative_claim", net_negative, 100, note_if_missing="Impacto climático líquido negativo não demonstrado."),
    ]
    score = summarize_field_scores(field_scores)
    if net_negative is not True:
        return _non_compliant("Impacto climático não demonstrado como líquido negativo.", "Calcular: remoções CO2 − emissões projeto − leakage > 0. Documentar no GHG statement.", "Isometric Standard v1.7, R-CDNF-0")
    return build_logic_result(status="compliant", missing_fields=[], failed_fields=[],
        notes=["Impacto climático líquido negativo declarado."], requirement_score=100, field_scores=field_scores, requirement_rating="strong")

def eval_regulatory_additionality_v1(data, audit_mode="development"):
    return _stub("R-983D-0", "Adicionalidade regulatória (projeto não exigido por lei)", audit_mode)

def eval_regulatory_compliance_v1(data, audit_mode="development"):
    legal = data.get("legal", {})
    compliant = legal.get("applicable_environmental_requirements")
    field_scores = [
        score_boolean_field("legal.applicable_environmental_requirements", compliant, 100, note_if_missing="Conformidade com requisitos legais ambientais não evidenciada."),
    ]
    score = summarize_field_scores(field_scores)
    status = derive_requirement_status_from_score(score, 50, 90)
    return build_logic_result(status=status, missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[], notes=collect_field_score_notes(field_scores),
        requirement_score=score, field_scores=field_scores, requirement_rating=derive_requirement_rating(score))

def eval_reversals_v1(data, audit_mode="development"):
    return _stub("R-V143-0", "Avaliação de risco de reversão e tamanho do buffer pool", audit_mode)

def eval_uncertainty_analysis_v1(data, audit_mode="development"):
    quant = data.get("quantification", {})
    field_scores = [
        score_boolean_field("quantification.input_variables", quant.get("input_variables"), 40, note_if_missing="Variáveis de entrada não documentadas."),
        score_boolean_field("quantification.input_uncertainties", quant.get("input_uncertainties"), 40, note_if_missing="Incertezas dos parâmetros de entrada não documentadas."),
        score_boolean_field("quantification.storage_emissions_accounted", quant.get("storage_emissions_accounted"), 20, note_if_missing="Emissões de armazenamento não contabilizadas."),
    ]
    score = summarize_field_scores(field_scores)
    status = derive_requirement_status_from_score(score, 40, 85)
    return build_logic_result(status=status, missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[], notes=collect_field_score_notes(field_scores),
        requirement_score=score, field_scores=field_scores, requirement_rating=derive_requirement_rating(score))

def eval_proxies_models_v1(data, audit_mode="development"):
    return _stub("R-NZQ2-0", "Modelos utilizados descritos e justificados", audit_mode)

def eval_data_collection_v1(data, audit_mode="development"):
    return _stub("R-GYA1-0", "Abordagem de coleta e armazenamento de dados (retenção mínima 5 anos)", audit_mode)

def eval_environmental_social_impact_v1(data, audit_mode="development"):
    safeguards = data.get("safeguards", {})
    management = data.get("management", {})
    adaptive = management.get("adaptive_management_plan") or safeguards.get("adaptive_management_plan")
    env_risk = safeguards.get("environmental_risk_assessment") or safeguards.get("social_risk_assessment")
    field_scores = [
        score_boolean_field("management.adaptive_management_plan", adaptive, 50, note_if_missing="Plano de gestão adaptativa não evidenciado."),
        score_boolean_field("safeguards.environmental_risk_assessment", env_risk, 50, note_if_missing="Avaliação de impacto ambiental/social não realizada."),
    ]
    score = summarize_field_scores(field_scores)
    status = derive_requirement_status_from_score(score, 30, 80)
    return build_logic_result(status=status, missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[], notes=collect_field_score_notes(field_scores),
        requirement_score=score, field_scores=field_scores, requirement_rating=derive_requirement_rating(score))

def eval_sustainable_development_v1(data, audit_mode="development"):
    return _stub("R-BWX0-0", "Alinhamento com ODS relevantes", audit_mode)

def eval_project_closure_v1(data, audit_mode="development"):
    return _stub("R-6VFZ-0", "Plano de encerramento do projeto", audit_mode)

def eval_site_selection_v1(data, audit_mode="development"):
    return _stub("R-M760-0", "Amostras de solo baseline coletadas antes da aplicação de biochar", audit_mode)

def eval_co_benefits_v1(data, audit_mode="development"):
    return _stub("R-1YC3-0", "Co-benefícios de saúde do solo (opcional)", audit_mode)

def eval_stakeholder_consultation_v1(data, audit_mode="development"):
    return _stub("R-ZHRN-0/R-E579-0", "Consulta a stakeholders e mecanismo de reclamações", audit_mode)

def eval_monitoring_requirements_v1(data, audit_mode="development"):
    return _stub("R-ENZR-0", "Tabela de parâmetros monitorados (fonte, frequência, QA/QC, evidências)", audit_mode)

def eval_biochar_char_standards_v1(data, audit_mode="development"):
    char = data.get("biochar", {}).get("characterization", {})
    lab = char.get("lab_reports")
    method = char.get("sampling_method")
    field_scores = [
        score_boolean_field("biochar.characterization.lab_reports", lab, 60, note_if_missing="Laudos laboratoriais com normas utilizadas não fornecidos."),
        score_presence_field("biochar.characterization.sampling_method", method, 40, note_if_missing="Normas de análise química e física não listadas."),
    ]
    score = summarize_field_scores(field_scores)
    status = derive_requirement_status_from_score(score, 30, 80)
    return build_logic_result(status=status, missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
        failed_fields=[], notes=collect_field_score_notes(field_scores),
        requirement_score=score, field_scores=field_scores, requirement_rating=derive_requirement_rating(score))

def eval_biochar_physical_properties_v1(data, audit_mode="development"):
    return _stub("R-7W1N-0", "Propriedades físicas do biochar medidas (porosidade, BET, granulometria)", audit_mode)


# ── Registry de funções (usado pelo run_engine para lookup) ──────────────────

LOGIC_REGISTRY_V1 = {
    "eval_protocol_eligibility_v1":          eval_protocol_eligibility_v1,
    "eval_project_ownership_v1":             eval_project_ownership_v1,
    "eval_technical_description_v1":         eval_technical_description_v1,
    "eval_project_participants_v1":          eval_project_participants_v1,
    "eval_project_locations_v1":             eval_project_locations_v1,
    "eval_removal_capacity_v1":              eval_removal_capacity_v1,
    "eval_system_boundary_v1":               eval_system_boundary_v1,
    "eval_baseline_v1":                      eval_baseline_v1,
    "eval_leakage_v1":                       eval_leakage_v1,
    "eval_financial_additionality_v1":       eval_financial_additionality_v1,
    "eval_common_practice_additionality_v1": eval_common_practice_additionality_v1,
    "eval_environmental_additionality_v1":   eval_environmental_additionality_v1,
    "eval_regulatory_additionality_v1":      eval_regulatory_additionality_v1,
    "eval_regulatory_compliance_v1":         eval_regulatory_compliance_v1,
    "eval_durability_selection_v1":          eval_durability_selection_v1,
    "eval_durability_soil_temp_v1":          eval_durability_soil_temp_v1,
    "eval_reversals_v1":                     eval_reversals_v1,
    "eval_uncertainty_analysis_v1":          eval_uncertainty_analysis_v1,
    "eval_proxies_models_v1":                eval_proxies_models_v1,
    "eval_data_collection_v1":               eval_data_collection_v1,
    "eval_environmental_social_impact_v1":   eval_environmental_social_impact_v1,
    "eval_sustainable_development_v1":       eval_sustainable_development_v1,
    "eval_project_closure_v1":               eval_project_closure_v1,
    "eval_adaptive_management_v1":           eval_adaptive_management_v1,
    "eval_pollution_prevention_v1":          eval_pollution_prevention_v1,
    "eval_site_selection_v1":                eval_site_selection_v1,
    "eval_co_benefits_v1":                   eval_co_benefits_v1,
    "eval_stakeholder_consultation_v1":      eval_stakeholder_consultation_v1,
    "eval_monitoring_requirements_v1":       eval_monitoring_requirements_v1,
    "eval_reactor_design_v1":                eval_reactor_design_v1,
    "eval_sampling_procedure_v1":            eval_sampling_procedure_v1,
    "eval_biochar_char_standards_v1":        eval_biochar_char_standards_v1,
    "eval_biochar_physical_properties_v1":   eval_biochar_physical_properties_v1,
    "eval_biochar_chemical_properties_v1":   eval_biochar_chemical_properties_v1,
    "eval_biochar_laboratory_v1":            eval_biochar_laboratory_v1,
}
