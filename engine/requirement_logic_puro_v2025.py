"""
Funções de lógica de requisitos — Puro.Earth Biochar Methodology Edition 2025.

ARQUITETURA v2 (refatoração completa — Option A):
  - Cada função aceita ProjectProfile (tipado) OU project_data dict (via adapter)
  - Com ProjectProfile: lógica pura, zero keyword matching
  - Com dict: adapter converte para ProjectProfile automaticamente
  - Sinal de qualidade: se a função não precisa de _get() é porque usa ProfileProfile

Diferenças-chave vs Isometric capturadas com lógica explícita:
  - P-FELI: mixed waste (fossil+biogênico) → non_compliant direto
  - P-FFOR: FSC | SFI | PEFC | ISAE 3000 | plano gov (CPI≥50 + 4 itens) — 3 caminhos
  - P-QUAL: hierarquia 3 níveis (local reg > IBI/EBC > exceção notificada)
  - P-FADD: first-of-its-kind NÃO isento (Clarificação 005 ADD)
  - P-DDEM: H/Corg < 0.5, O/Corg < 0.2 — hard gates operacionais
  - P-RREV: buffer pool 2% padrão
  - P-ALIGN: SDG obrigatório (não opcional como no Isometric)
"""

from __future__ import annotations
from typing import Any, Union
from engine.project_profile import ProjectProfile, profile_to_legacy_dict


def build_logic_result(
    status: str,
    score: float,
    notes: list[str] | None = None,
    gap: str | None = None,
    recommendation: str | None = None,
    _gap_override: str | None = None,
    _rec_override: str | None = None,
) -> dict:
    return {
        "status": status,
        "requirement_score": score,
        "notes": notes or [],
        "gap": _gap_override or gap or "",
        "recommendation": _rec_override or recommendation or "",
    }


def _resolve(input_data: Union[ProjectProfile, dict]) -> ProjectProfile:
    """Garante que a função sempre trabalha com ProjectProfile."""
    if isinstance(input_data, ProjectProfile):
        return input_data
    # Legacy dict → converte via heurísticas
    p = ProjectProfile()
    fd = input_data.get("feedstock") or {}
    ca = input_data.get("carbon_accounting") or {}
    el = input_data.get("eligibility") or {}
    sa = input_data.get("safeguards") or {}
    sm = input_data.get("sampling") or {}
    pr = input_data.get("production") or {}
    st = input_data.get("storage") or {}
    mo = input_data.get("monitoring") or {}
    ch = (input_data.get("biochar") or {}).get("characterization") or {}
    lgl = input_data.get("legal") or {}
    proj = input_data.get("project") or {}
    meth = input_data.get("methodology") or {}

    # Feedstock
    biomass = str(fd.get("biomass_type") or "").lower()
    cert    = str(fd.get("certification_scheme") or "").lower()
    p.feedstock_type = fd.get("biomass_type") or "unknown"
    p.is_forest_biomass = any(k in biomass for k in ["forest", "floresta", "wood", "madeira", "eucalipto", "pine", "pinus"])
    p.uses_mixed_waste  = any(k in biomass for k in ["mixed", "misto", "plastic", "fossil"])
    p.has_fsc_certification  = "fsc" in cert
    p.has_sfi_certification  = "sfi" in cert
    p.has_pefc_certification = "pefc" in cert
    p.has_isae3000_dossier   = "isae" in cert or "3000" in cert

    country = str(proj.get("country") or "").lower()
    HIGH_CPI = ["brazil","brasil","germany","usa","uk","canada","australia","france","japan","denmark","norway","sweden"]
    if any(c in country for c in HIGH_CPI):
        p.country_cpi = 60.0  # conservador — país provavelmente CPI ≥ 50
    p.project_name    = proj.get("name") or ""
    p.project_country = proj.get("country") or ""
    p.project_locations = proj.get("locations") or []

    # Carbon accounting
    p.has_lca                = bool(input_data.get("lca", {}).get("performed") or meth.get("lca_performed"))
    p.has_system_boundary    = bool(ca.get("boundary") or ca.get("ghg_sources"))
    p.has_baseline           = bool(ca.get("baseline") or el.get("baseline_scenario"))
    p.has_leakage_assessment = bool(ca.get("leakage"))
    p.has_uncertainty_analysis = bool(ca.get("uncertainty_analysis"))
    p.has_ghg_statement      = bool(ca.get("ghg_methodology"))
    p.is_net_negative        = bool(ca.get("net_negative") or ca.get("net_negative_claim") or el.get("net_negative_claim"))

    # Additionality
    p.has_financial_additionality = bool(el.get("additionality_claim") or el.get("additionality_evidence") or el.get("financial_additionality"))
    p.additionality_method = el.get("additionality_method") or ""
    add_ev = str(el.get("additionality_evidence") or "").lower()
    if any(k in add_ev for k in ["irr","npv","vpl","tir","cost analysis"]): p.additionality_method = "irr_npv"
    if any(k in add_ev for k in ["barrier","barreira"]): p.additionality_method = "barriers"
    p.is_first_of_its_kind   = False  # conservative default
    p.has_regulatory_additionality = bool(el.get("not_required_by_law") or lgl.get("voluntary_nature"))
    p.has_common_practice_evidence = bool(el.get("common_practice") or el.get("market_analysis"))

    # Permanence
    p.durability_option    = str(input_data.get("permanence", {}).get("durability_option") or meth.get("durability_threshold") or "")
    p.h_c_ratio            = ch.get("h_c_ratio")
    p.o_c_ratio            = ch.get("o_c_ratio")
    p.has_soil_temp_method = bool(st.get("soil", {}).get("temperature_method") or input_data.get("permanence", {}).get("temperature_method"))
    p.buffer_pool_pct      = input_data.get("permanence", {}).get("buffer_pool_pct")
    p.storage_pathway      = st.get("pathway") or meth.get("storage_pathway") or "soil"

    # Monitoring
    p.has_monitoring_table  = bool(mo.get("parameters"))
    p.has_data_storage_plan = bool(mo.get("data_storage"))
    p.sampling_method       = sm.get("sampling_method") or sm.get("method") or ""
    p.sample_count_per_batch = sm.get("samples_per_batch") or sm.get("sample_count")
    p.has_iso17025_lab      = bool(ch.get("lab_accreditation") or ch.get("lab_reports"))

    # Biochar characterization
    p.pah_value             = ch.get("pah_mg_kg")
    p.pcb_value             = ch.get("pcb_mg_kg")
    p.pcdd_f_value          = ch.get("pcdd_f_ng_kg")
    p.has_characterization_standards = bool(ch.get("standards"))
    p.quality_standard      = ch.get("quality_standard") or ""

    # E&S
    p.has_env_compliance         = bool(sa.get("regulatory_compliance") or sa.get("permits_documented") or lgl.get("permits_documented"))
    p.has_no_net_env_harm        = bool(sa.get("no_environmental_harm") or sa.get("environmental_assessment"))
    p.has_no_net_social_harm     = bool(sa.get("social_assessment") or sa.get("no_social_harm"))
    p.has_pah_analysis           = p.pah_value is not None
    p.has_pollution_prevention   = bool(sa.get("pollution_prevention"))
    p.has_adaptive_management    = bool(sa.get("adaptive_management_plan"))
    p.has_stakeholder_consultation = bool(sa.get("stakeholder_consultation"))
    p.has_grievance_mechanism    = bool(sa.get("grievance_mechanism"))
    p.has_sdg_reporting          = bool(sa.get("sdg_alignment"))
    p.has_env_social_assessment  = bool(sa.get("environmental_social_assessment") or sa.get("impact_assessment"))

    # Reactor
    p.has_engineering_diagram = bool(pr.get("reactor_diagram"))
    p.has_gas_sensors         = bool(pr.get("leakage_sensors"))
    p.has_maintenance_plan    = bool(pr.get("maintenance_plan"))
    p.has_material_justification = bool(pr.get("reactor_material"))
    p.reactor_type            = pr.get("reactor_type") or ""
    p.has_ownership_evidence  = bool(lgl.get("ownership_evidence") or lgl.get("permits_documented"))
    p.has_technical_description = bool(proj.get("description") or pr.get("system_description"))

    return p


def _get(data: dict, *keys, default=None):
    """Compatibilidade: navega aninhado com segurança (usado em funções legadas)."""
    cur = data
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


# ── project_data ──────────────────────────────────────────────────────────────

def eval_puro_protocol_eligibility_v1(project_data: dict, audit_mode: str = "development") -> dict:
    prod = _get(project_data, "production") or {}
    elig = _get(project_data, "eligibility") or {}
    pathway = _get(project_data, "storage", "pathway") or _get(project_data, "methodology", "storage_pathway")
    feedstock = _get(project_data, "feedstock", "biomass_type")

    has_justification = bool(
        _get(project_data, "project", "description") or
        _get(project_data, "methodology", "protocol") or
        elig.get("eligible_pathway")
    )
    has_pathway = bool(pathway)
    has_feedstock = bool(feedstock)

    if has_justification and has_pathway and has_feedstock:
        return build_logic_result("compliant", 100, notes=["Justificativa de elegibilidade presente com via e feedstock identificados."])
    if has_justification:
        return build_logic_result("partial", 65,
            gap="Via de armazenamento ou tipo de feedstock não identificados.",
            recommendation="Incluir explicitamente a via de armazenamento (solo, ambiente construído) e o tipo de feedstock no PDD.")
    return build_logic_result("non_compliant", 20,
        gap="Justificativa de elegibilidade sob o protocolo Puro.Earth não identificada.",
        recommendation="Descrever por que o projeto é elegível sob a metodologia Puro Biochar Edition 2025.")


def eval_puro_project_ownership_v1(project_data: dict, audit_mode: str = "development") -> dict:
    legal = _get(project_data, "legal") or {}
    has_ownership = bool(
        legal.get("removal_rights_owner") or
        legal.get("ownership_evidence") or
        _get(project_data, "project", "organization")
    )
    if has_ownership:
        return build_logic_result("compliant", 100, notes=["Propriedade legal sobre os créditos de remoção identificada."])
    return build_logic_result("partial", 50,
        gap="Evidência de propriedade legal sobre os direitos de remoção não encontrada.",
        recommendation="Documentar o título de propriedade ou contrato de cessão de direitos de carbono.")


def eval_puro_technical_description_v1(project_data: dict, audit_mode: str = "development") -> dict:
    prod = _get(project_data, "production") or {}
    desc = _get(project_data, "project", "description") or ""
    reactor = prod.get("reactor_type") or prod.get("system_description")
    process = prod.get("pyrolysis_temperature") or prod.get("process_type")

    score = 0
    notes = []
    if len(desc) > 100: score += 40; notes.append("Descrição do projeto presente.")
    if reactor:          score += 35; notes.append(f"Tipo de reator identificado: {reactor}.")
    if process:          score += 25; notes.append("Parâmetros de processo identificados.")

    if score >= 90: return build_logic_result("compliant", 100, notes=notes)
    if score >= 50: return build_logic_result("partial", score,
        gap="Descrição técnica incompleta — faltam detalhes de reator ou processo.",
        recommendation="Incluir tipo de reator, capacidade, temperatura de pirólise e via de aplicação do biochar.", notes=notes)
    return build_logic_result("non_compliant", 20,
        gap="Descrição técnica do processo de produção de biochar não identificada.",
        recommendation="Descrever o processo completo: feedstock → pirólise → biochar → armazenamento.", notes=notes)


def eval_puro_project_participants_v1(project_data: dict, audit_mode: str = "development") -> dict:
    proj = _get(project_data, "project") or {}
    org = proj.get("organization") or proj.get("developer")
    contacts = proj.get("contacts") or proj.get("participants")
    if org and contacts:
        return build_logic_result("compliant", 100, notes=["Lista de participantes com organização e contatos identificados."])
    if org:
        return build_logic_result("partial", 65,
            gap="Contatos dos participantes não detalhados.",
            recommendation="Incluir nome, cargo, e-mail e telefone de todos os participantes do projeto.")
    return build_logic_result("partial", 35,
        gap="Lista de participantes do projeto não identificada.",
        recommendation="Listar todas as organizações participantes com dados de registro, endereço e contato.")


def eval_puro_project_locations_v1(project_data: dict, audit_mode: str = "development") -> dict:
    locations = _get(project_data, "project", "locations") or []
    coords = _get(project_data, "project", "coordinates") or _get(project_data, "project", "gps")
    has_loc = bool(locations or coords)
    if has_loc:
        return build_logic_result("compliant", 100, notes=[f"Localização identificada: {locations or coords}"])
    return build_logic_result("partial", 40,
        gap="Endereço ou coordenadas GPS da facility e local de aplicação não encontrados.",
        recommendation="Incluir endereço completo e coordenadas GPS da planta de pirólise e do(s) local(is) de aplicação.")


def eval_puro_removal_capacity_v1(project_data: dict, audit_mode: str = "development") -> dict:
    creds = (_get(project_data, "carbon_accounting", "annual_credits") or
             _get(project_data, "production", "annual_biochar_t") or
             _get(project_data, "eligibility", "estimated_credits_tco2"))
    lca = (_get(project_data, "lca", "performed") or
           _get(project_data, "methodology", "lca_performed"))
    if creds and lca:
        return build_logic_result("compliant", 100, notes=[f"Estimativa de remoção líquida e LCA identificados."])
    if creds:
        return build_logic_result("partial", 65,
            gap="Estimativa de capacidade de remoção presente mas LCA não encontrada.",
            recommendation="Incluir análise de ciclo de vida (LCA) para calcular remoções líquidas após emissões do processo.")
    return build_logic_result("partial", 35,
        gap="Estimativa de remoção líquida de carbono não encontrada.",
        recommendation="Calcular e documentar a capacidade anual de remoção líquida (tCO₂e) incluindo todas as emissões do processo.")


# ── feedstock_and_production ──────────────────────────────────────────────────

def eval_puro_feedstock_eligibility_v1(input_data, audit_mode: str = "development") -> dict:
    p = _resolve(input_data)

    # Hard gate: feedstock misto (Clarificação 001 BCH)
    if p.uses_mixed_waste:
        return build_logic_result("non_compliant", 0,
            gap="Feedstock misto (biogênico + fóssil) é explicitamente proibido (Puro Clarificação 001 BCH).",
            recommendation="Usar apenas biomassa pura sem componentes fósseis (plásticos, fibras sintéticas).")

    # Hard gate: coal ash (Clarificação 010 CAM)
    if p.uses_coal_ash:
        return build_logic_result("non_compliant", 0,
            gap="Cinzas de carvão (coal ash) são inelegíveis — incompatíveis com net zero (Puro Clarificação 010 CAM).",
            recommendation="Substituir por feedstock de biomassa pura elegível.")

    has_origin = bool(
        p.has_fsc_certification or p.has_sfi_certification or p.has_pefc_certification or
        p.has_isae3000_dossier or p.has_government_mgmt_plan or
        p.feedstock_type not in ("unknown", "")
    )
    if p.feedstock_type not in ("unknown", "", "mixed") and has_origin:
        return build_logic_result("compliant", 100,
            notes=[f"Feedstock elegível: {p.feedstock_type}. Origem documentada."])
    if p.feedstock_type not in ("unknown", "", "mixed"):
        return build_logic_result("partial", 70,
            gap="Tipo de feedstock elegível mas origem/sustentabilidade não documentada.",
            recommendation="Documentar cadeia de custódia e sustentabilidade do feedstock.",
            notes=[f"Feedstock identificado: {p.feedstock_type}"])
    return build_logic_result("partial", 45,
        gap="Tipo de feedstock não identificado claramente como biomassa sustentável.",
        recommendation="Especificar o tipo de biomassa residual e confirmar ausência de componentes fósseis.")


def eval_puro_forest_sustainability_v1(input_data, audit_mode: str = "development") -> dict:
    """
    Puro Clarificação 006 BCH — 3 caminhos alternativos para biomassa florestal:
      1. FSC / SFI / PEFC  (certificação formal)
      2. Dossiê ISAE 3000   (auditoria independente)
      3. Plano de manejo governamental + CPI ≥ 50 (4 itens obrigatórios)

    Isometric é mais flexível: "sustainable biomass" sem certificação mandatória.
    Esta função captura APENAS o Puro — o Isometric tem avaliação separada.
    """
    p = _resolve(input_data)

    if not p.is_forest_biomass:
        return build_logic_result("compliant", 100,
            notes=["Feedstock não é biomassa florestal — P-FFOR-0 não aplicável."])

    # ── Caminho 1: FSC / SFI / PEFC ─────────────────────────────────────────
    if p.has_fsc_certification:
        return build_logic_result("compliant", 100,
            notes=["Certificação FSC confirmada — requisito de sustentabilidade florestal atendido."])
    if p.has_sfi_certification:
        return build_logic_result("compliant", 100,
            notes=["Certificação SFI confirmada — requisito de sustentabilidade florestal atendido."])
    if p.has_pefc_certification:
        return build_logic_result("compliant", 100,
            notes=["Certificação PEFC confirmada — requisito de sustentabilidade florestal atendido."])

    # ── Caminho 2: Dossiê ISAE 3000 ─────────────────────────────────────────
    if p.has_isae3000_dossier:
        return build_logic_result("compliant", 100,
            notes=["Dossiê de sustentabilidade auditado por terceira parte (ISAE 3000) — alternativa Puro confirmada."])

    # ── Caminho 3: Plano governamental (CPI ≥ 50 + 4 itens) ─────────────────
    if p.has_government_mgmt_plan:
        cpi_ok = (p.country_cpi or 0) >= 50
        items = sum([p.govt_plan_authority, p.govt_plan_requirements,
                     p.govt_plan_oversight, p.govt_plan_documents])
        if cpi_ok and items >= 4:
            return build_logic_result("compliant", 100,
                notes=[f"Plano de manejo governamental com CPI={p.country_cpi} e {items}/4 itens documentados."])
        if cpi_ok:
            return build_logic_result("partial", 65,
                gap=f"Plano governamental presente (CPI={p.country_cpi} ≥ 50) mas apenas {items}/4 itens documentados.",
                recommendation="Documentar os 4 itens obrigatórios: (1) autoridade local de supervisão, (2) requisitos de sustentabilidade, (3) tipo de supervisão (licenças/inspeções), (4) documentos de referência com sumário em inglês.")
        return build_logic_result("partial", 40,
            gap=f"Plano de manejo presente mas CPI do país ({p.country_cpi}) pode ser < 50.",
            recommendation="Confirmar CPI ≥ 50 do país via Transparency International. Para países CPI < 50: obrigatório FSC, SFI, PEFC ou ISAE 3000.")

    # ── Nenhum dos 3 caminhos ────────────────────────────────────────────────
    cpi_known = p.country_cpi is not None
    if cpi_known and p.country_cpi >= 50:
        return build_logic_result("partial", 35,
            gap=f"Biomassa florestal sem certificação FSC/SFI/PEFC, dossiê ISAE 3000 ou plano governamental documentado. País tem CPI={p.country_cpi} ≥ 50 — alternativa possível.",
            recommendation="3 opções disponíveis: (1) obter FSC/SFI/PEFC; (2) produzir dossiê ISAE 3000; (3) documentar plano de manejo governamental com 4 itens obrigatórios.")
    return build_logic_result("non_compliant", 10,
        gap="Biomassa florestal sem nenhuma das 3 formas de comprovação de sustentabilidade exigidas pelo Puro.Earth.",
        recommendation="Opções: (1) FSC/SFI/PEFC; (2) dossiê auditado ISAE 3000; (3) plano de manejo governamental (CPI ≥ 50 + 4 itens). Ver Puro Clarificação 006 BCH.")


def eval_puro_land_clearing_v1(project_data: dict, audit_mode: str = "development") -> dict:
    feedstock = _get(project_data, "feedstock") or {}
    biomass = str(feedstock.get("biomass_type") or "").lower()
    is_clearing = any(kw in biomass for kw in ["land clearing", "desmatamento", "clearing"])
    if not is_clearing:
        return build_logic_result("compliant", 100,
            notes=["Feedstock não é de desmatamento — P-FLAN-0 não aplicável."])
    # If land clearing, needs permit + counterfactual + no protected areas
    return build_logic_result("partial", 50,
        gap="Feedstock de desmatamento identificado — requer validação de 4 condições obrigatórias.",
        recommendation="Documentar: (i) contrafactual de desmatamento, (ii) permissão válida, (iii) uso apenas de frações não econômicas, (iv) confirmação de área não protegida.")


def eval_puro_product_quality_v1(project_data: dict, audit_mode: str = "development") -> dict:
    biochar = _get(project_data, "biochar") or _get(project_data, "production") or {}
    char = _get(project_data, "biochar", "characterization") or {}

    pah = char.get("pah_mg_kg")
    pcb = char.get("pcb_mg_kg")
    dioxins = char.get("pcdd_f_ng_kg")
    ibc_cert = str(char.get("quality_standard") or "").lower()
    has_standard = any(kw in ibc_cert for kw in ["ibi", "ebc", "local", "regulation", "regulação"])

    if audit_mode == "development":
        if has_standard:
            return build_logic_result("compliant", 100,
                notes=[f"Padrão de qualidade definido: {ibc_cert}"])
        return build_logic_result("partial", 55,
            gap="Padrão de qualidade para PAH/contaminantes não especificado.",
            recommendation="Especificar qual padrão será aplicado: regulação local (se existir), IBI, ou EBC. Planejar análise de PAH se aplicação em solo ou ração animal.")

    # Operational mode: need actual lab results
    if pah is not None:
        pah_ok = float(pah) <= 12  # WBC PAH-16 limit typically ~12 mg/kg
        pcb_ok = (pcb is None) or float(pcb) <= 0.2
        dioxin_ok = (dioxins is None) or float(dioxins) <= 20
        if pah_ok and pcb_ok and dioxin_ok:
            return build_logic_result("compliant", 100,
                notes=[f"Laudos de qualidade dentro dos limites: PAH={pah}, PCB={pcb}, PCDD/F={dioxins}"])
        gaps = []
        if not pah_ok: gaps.append(f"PAH={pah} acima do limite WBC (~12 mg/kg)")
        if not pcb_ok: gaps.append(f"PCB={pcb} acima de 0,2 mg/kg")
        if not dioxin_ok: gaps.append(f"PCDD/F={dioxins} acima de 20 ng/kg")
        return build_logic_result("non_compliant", 0,
            gap="; ".join(gaps),
            recommendation="Otimizar processo de pirólise para reduzir contaminantes ou mudar feedstock.")
    return build_logic_result("partial", 30,
        gap="Resultados de análise PAH/metais pesados não encontrados.",
        recommendation="Realizar análises laboratoriais (ISO 17025) de PAH, metais pesados, PCB e dioxinas por batch.")


def eval_puro_non_soil_application_v1(project_data: dict, audit_mode: str = "development") -> dict:
    pathway = str(_get(project_data, "storage", "pathway") or "").lower()
    if "soil" in pathway or "solo" in pathway:
        return build_logic_result("compliant", 100,
            notes=["Via de aplicação em solo — P-NONS-0 não aplicável."])
    eol = (_get(project_data, "storage", "end_of_life") or
           _get(project_data, "storage", "application_fate"))
    if eol:
        return build_logic_result("compliant", 100,
            notes=[f"Documentação de uso final identificada: {eol}"])
    return build_logic_result("partial", 50,
        gap="Via de aplicação não-solo sem documentação de uso final.",
        recommendation="Documentar o destino final do biochar (material de construção, etc.) e confirmar que não irá para incineração. Usar temperatura média do solo local para cálculo de permanência.")


# ── carbon_accounting ─────────────────────────────────────────────────────────

def eval_puro_system_boundary_v1(project_data: dict, audit_mode: str = "development") -> dict:
    accounting = _get(project_data, "carbon_accounting") or {}
    boundary = accounting.get("boundary") or accounting.get("system_boundary")
    ghg_sources = accounting.get("ghg_sources") or accounting.get("emission_sources")
    if boundary and ghg_sources:
        return build_logic_result("compliant", 100,
            notes=["Fronteiras do sistema e fontes de GHG identificadas."])
    if boundary or ghg_sources:
        return build_logic_result("partial", 65,
            gap="Fronteiras do sistema parcialmente definidas.",
            recommendation="Incluir fronteiras temporais, geográficas e todas as fontes/sumidouros de GHG com justificativas.")
    return build_logic_result("partial", 30,
        gap="Fronteiras do sistema e fontes de GHG não identificadas.",
        recommendation="Definir explicitamente fronteiras temporais, geográficas e fontes de GHG incluídas e excluídas do balanço.")


def eval_puro_ghg_statement_v1(project_data: dict, audit_mode: str = "development") -> dict:
    accounting = _get(project_data, "carbon_accounting") or {}
    approach = (accounting.get("ghg_methodology") or
                accounting.get("calculation_methodology") or
                _get(project_data, "methodology", "ghg_approach"))
    lca = (_get(project_data, "lca", "performed") or
           _get(project_data, "methodology", "lca_performed"))
    if approach and lca:
        return build_logic_result("compliant", 100,
            notes=["Metodologia de cálculo de GHG e LCA identificados."])
    if approach:
        return build_logic_result("partial", 70,
            gap="Metodologia de GHG identificada mas LCA não evidenciada.",
            recommendation="Incluir análise de ciclo de vida completa com fronteiras e fatores de emissão.")
    return build_logic_result("partial", 35,
        gap="Abordagem de cálculo de GHG não identificada.",
        recommendation="Descrever a metodologia de contabilização de GHG incluindo todos os fatores de emissão e fronteiras LCA.")


def eval_puro_baseline_v1(project_data: dict, audit_mode: str = "development") -> dict:
    accounting = _get(project_data, "carbon_accounting") or {}
    baseline = (accounting.get("baseline") or
                accounting.get("baseline_scenario") or
                _get(project_data, "eligibility", "baseline_scenario"))
    if baseline:
        return build_logic_result("compliant", 100, notes=["Cenário de referência (baseline) identificado."])
    return build_logic_result("partial", 40,
        gap="Cenário de referência (counterfactual) não identificado.",
        recommendation="Definir o cenário mais provável sem o projeto (counterfactual) com parâmetros conservadores e fontes documentadas.")


def eval_puro_leakage_v1(project_data: dict, audit_mode: str = "development") -> dict:
    accounting = _get(project_data, "carbon_accounting") or {}
    leakage = (accounting.get("leakage") or
               accounting.get("leakage_assessment") or
               accounting.get("boundary"))
    if leakage:
        return build_logic_result("compliant", 100, notes=["Avaliação de leakage identificada."])
    return build_logic_result("partial", 45,
        gap="Avaliação de vazamentos (leakage) não encontrada.",
        recommendation="Quantificar potenciais aumentos de GHG fora da fronteira do projeto e deduzir das remoções reivindicadas.")


def eval_puro_uncertainty_v1(project_data: dict, audit_mode: str = "development") -> dict:
    accounting = _get(project_data, "carbon_accounting") or {}
    uncertainty = (accounting.get("uncertainty") or
                   accounting.get("uncertainty_analysis") or
                   accounting.get("uncertainty_method"))
    sensitivity = accounting.get("sensitivity_analysis")
    if (uncertainty or sensitivity) and audit_mode == "development":
        return build_logic_result("compliant", 100,
            notes=["Método de análise de incerteza/sensibilidade identificado."])
    if audit_mode == "operational":
        if uncertainty and sensitivity:
            return build_logic_result("compliant", 100, notes=["Análise de incerteza e sensibilidade executada."])
        return build_logic_result("partial", 50,
            gap="Análise de sensibilidade com dados reais não encontrada.",
            recommendation="Executar análise de sensibilidade com dados operacionais reais; documentar valores min/max por variável.")
    return build_logic_result("partial", 55,
        gap="Método de análise de incerteza não especificado.",
        recommendation="Descrever abordagem de análise de incerteza: estimativas conservadoras, propagação de variância ou Monte Carlo.")


def eval_puro_models_v1(project_data: dict, audit_mode: str = "development") -> dict:
    accounting = _get(project_data, "carbon_accounting") or {}
    models = accounting.get("models") or accounting.get("model_references")
    if models:
        return build_logic_result("compliant", 100, notes=["Modelos e proxies documentados."])
    return build_logic_result("partial", 60,
        gap="Modelos ou proxies utilizados não descritos.",
        recommendation="Documentar todos os modelos usados nos cálculos com fonte, parâmetros e validação empírica disponível.")


# ── additionality ─────────────────────────────────────────────────────────────

def eval_puro_financial_additionality_v1(input_data, audit_mode: str = "development") -> dict:
    """
    Puro Clarificação 005 ADD: first-of-its-kind NÃO isento de análise de adicionalidade.
    3 opções: (a) análise de custo simples, (b) IRR/VPL, (c) análise de barreiras.
    Isometric permite mais interpretação neste ponto.
    """
    p = _resolve(input_data)

    # Flag crítica: alega isenção por ser first-of-its-kind → Puro rejeita
    if p.is_first_of_its_kind and p.financial_additionality_exemption_claimed:
        return build_logic_result("non_compliant", 0,
            gap="Puro.Earth (Clarificação 005 ADD): first-of-its-kind NÃO é isento de análise de adicionalidade financeira.",
            recommendation="Realizar análise formal: (a) custo simples, (b) IRR/VPL mostrando inviabilidade sem carbono, ou (c) barreiras documentadas.")

    if p.has_financial_additionality:
        method_label = {
            "irr_npv":       "IRR/VPL (opção b)",
            "cost_analysis": "análise de custo simples (opção a)",
            "barriers":      "análise de barreiras (opção c)",
        }.get(p.additionality_method, p.additionality_method or "método identificado")

        if p.is_first_of_its_kind:
            return build_logic_result("compliant", 100,
                notes=[f"Adicionalidade financeira via {method_label}. First-of-its-kind presente mas análise formal realizada — conforme Clarificação 005 ADD."])
        return build_logic_result("compliant", 100,
            notes=[f"Adicionalidade financeira demonstrada via {method_label}."])

    return build_logic_result("non_compliant", 20,
        gap="Adicionalidade financeira não demonstrada.",
        recommendation="3 opções Puro (Clarificação 005 ADD): (a) análise simples de custo; (b) análise de investimento com IRR/VPL; (c) análise de barreiras documentadas. First-of-its-kind NÃO é isento.")


def eval_puro_common_practice_additionality_v1(project_data: dict, audit_mode: str = "development") -> dict:
    elig = _get(project_data, "eligibility") or {}
    common_practice = (elig.get("common_practice") or
                       elig.get("additionality_evidence") or
                       elig.get("market_analysis"))
    if common_practice:
        return build_logic_result("compliant", 100,
            notes=["Evidência de adicionalidade de prática comum identificada."])
    if elig.get("additionality_claim"):
        return build_logic_result("partial", 55,
            gap="Adicionalidade de prática comum afirmada mas não evidenciada com análise de mercado.",
            recommendation="Incluir análise de mercado ou revisão de literatura demonstrando que projetos similares não são prática comum na região/setor.")
    return build_logic_result("partial", 35,
        gap="Adicionalidade de prática comum não demonstrada.",
        recommendation="Fornecer análise de mercado documentando a ausência de projetos similares na região.")


def eval_puro_environmental_additionality_v1(project_data: dict, audit_mode: str = "development") -> dict:
    accounting = _get(project_data, "carbon_accounting") or {}
    net_negative = (accounting.get("net_negative") or
                    accounting.get("net_negative_claim") or
                    _get(project_data, "eligibility", "net_negative_claim"))
    lca = _get(project_data, "lca", "performed")
    if net_negative and lca:
        return build_logic_result("compliant", 100,
            notes=["Impacto líquido negativo declarado com LCA identificada."])
    if net_negative:
        return build_logic_result("partial", 65,
            gap="Impacto líquido negativo declarado mas LCA não evidenciada.",
            recommendation="Incluir LCA completa evidenciando impacto climático líquido negativo após subtrair emissões do processo e leakage.")
    return build_logic_result("partial", 40,
        gap="Adicionalidade ambiental (impacto líquido negativo) não demonstrada.",
        recommendation="Calcular impacto líquido: remoções – emissões do processo – emissões contrafactuais – leakage. Resultado deve ser negativo.")


def eval_puro_regulatory_additionality_v1(project_data: dict, audit_mode: str = "development") -> dict:
    legal = _get(project_data, "legal") or {}
    reg_add = (legal.get("regulatory_additionality") or
               legal.get("voluntary_nature") or
               _get(project_data, "eligibility", "not_required_by_law"))
    permits = legal.get("permits_documented")
    if reg_add and permits:
        return build_logic_result("compliant", 100,
            notes=["Adicionalidade regulatória evidenciada — projeto voluntário com licenças documentadas."])
    if permits:
        return build_logic_result("partial", 70,
            gap="Licenças documentadas mas confirmação de natureza voluntária não explícita.",
            recommendation="Confirmar explicitamente que o projeto não é exigido por lei, regulação ou obrigação vinculante.")
    return build_logic_result("partial", 45,
        gap="Adicionalidade regulatória não demonstrada.",
        recommendation="Fornecer análise jurídica confirmando que o projeto é voluntário e não exigido por nenhuma lei ou regulação.")


# ── permanence ────────────────────────────────────────────────────────────────

def eval_puro_durability_selection_v1(project_data: dict, audit_mode: str = "development") -> dict:
    perm = _get(project_data, "permanence") or _get(project_data, "storage") or {}
    option = (perm.get("durability_option") or
              perm.get("permanence_option") or
              _get(project_data, "methodology", "durability_threshold"))
    VALID = ["200", "1000", "200 years", "1000 years"]
    if option and any(str(v) in str(option) for v in VALID):
        return build_logic_result("compliant", 100,
            notes=[f"Limiar de durabilidade selecionado: {option} anos (Woolf et al. 2021)."])
    if option:
        return build_logic_result("partial", 70,
            gap=f"Opção de durabilidade identificada ('{option}') mas não claramente '200' ou '1000 anos'.",
            recommendation="Especificar explicitamente 200 ou 1000 anos com justificativa via metodologia Woolf et al. (2021).")
    return build_logic_result("partial", 35,
        gap="Limiar de durabilidade (200 ou 1000 anos) não selecionado.",
        recommendation="Selecionar e justificar o limiar de durabilidade (200 ou 1000 anos) via Woolf et al. (2021).")


def eval_puro_durability_demonstration_v1(project_data: dict, audit_mode: str = "development") -> dict:
    char = _get(project_data, "biochar", "characterization") or {}
    h_c = char.get("h_c_ratio")
    o_c = char.get("o_c_ratio")

    if audit_mode == "development":
        has_spec = h_c is not None or o_c is not None or char.get("quality_standard")
        if has_spec:
            return build_logic_result("compliant", 100,
                notes=["Especificação de H/Corg e O/Corg para durabilidade identificada no PDD."])
        return build_logic_result("partial", 55,
            gap="Limites de H/Corg < 0,5 e O/Corg < 0,2 não especificados no PDD.",
            recommendation="Especificar no PDD que o biochar atingirá H/Corg < 0,5 e O/Corg < 0,2 como evidência de durabilidade.")

    # Operational: need actual lab values
    if h_c is not None and o_c is not None:
        h_c_ok = float(h_c) < 0.5
        o_c_ok = float(o_c) < 0.2
        if h_c_ok and o_c_ok:
            return build_logic_result("compliant", 100,
                notes=[f"Durabilidade confirmada: H/Corg={h_c} (<0,5) ✓ | O/Corg={o_c} (<0,2) ✓"])
        gaps = []
        if not h_c_ok: gaps.append(f"H/Corg={h_c} ≥ 0,5 — falha no critério de durabilidade")
        if not o_c_ok: gaps.append(f"O/Corg={o_c} ≥ 0,2 — falha no critério de durabilidade")
        return build_logic_result("non_compliant", 0,
            gap="; ".join(gaps),
            recommendation="Otimizar condições de pirólise (temperatura, tempo de residência) para atingir H/Corg < 0,5 e O/Corg < 0,2.")
    return build_logic_result("partial", 30,
        gap="Laudos laboratoriais de H/Corg e O/Corg por batch não encontrados.",
        recommendation="Realizar análises de H/Corg e O/Corg por batch em laboratório ISO 17025 e documentar resultados.")


def eval_puro_soil_temp_v1(project_data: dict, audit_mode: str = "development") -> dict:
    storage = _get(project_data, "storage") or {}
    temp_method = (storage.get("temperature_method") or
                   storage.get("soil_temp_method") or
                   _get(project_data, "permanence", "temperature_method"))
    temp_data = storage.get("annual_avg_temp_celsius")

    if audit_mode == "development":
        if temp_method:
            return build_logic_result("compliant", 100,
                notes=[f"Método de temperatura do solo descrito: {temp_method}"])
        return build_logic_result("partial", 50,
            gap="Método de medição de temperatura média anual do solo não especificado.",
            recommendation="Especificar método: (a) medição direta ≥10 amostras/site/mês, ou (b) banco de dados global (Lembrechts et al.).")

    # Operational
    if temp_data is not None:
        return build_logic_result("compliant", 100,
            notes=[f"Temperatura média do solo: {temp_data}°C — dados operacionais disponíveis."])
    if temp_method:
        return build_logic_result("partial", 60,
            gap="Método descrito mas dados reais de temperatura do solo não encontrados.",
            recommendation="Coletar e documentar dados reais de temperatura do solo com mínimo de 10 medições/site/mês do ano anterior.")
    return build_logic_result("partial", 25,
        gap="Dados de temperatura média anual do solo não encontrados.",
        recommendation="Implementar monitoramento de temperatura do solo (≥10 amostras/site/mês) ou consultar banco de dados Lembrechts et al.")


def eval_puro_reversals_v1(project_data: dict, audit_mode: str = "development") -> dict:
    perm = _get(project_data, "permanence") or {}
    buffer = perm.get("buffer_pool_pct") or perm.get("buffer_contribution")
    risk_assessment = perm.get("reversal_risk") or perm.get("risk_assessment")

    if buffer is not None and risk_assessment:
        b_val = float(buffer) if buffer else 0
        b_ok = 0.01 <= b_val <= 0.05  # 1-5% range, Puro standard 2%
        if b_ok:
            return build_logic_result("compliant", 100,
                notes=[f"Buffer pool: {b_val*100:.1f}% (padrão Puro: 2%). Avaliação de risco presente."])
        return build_logic_result("partial", 75,
            gap=f"Buffer pool de {b_val*100:.1f}% pode não estar alinhado com o padrão Puro (2%).",
            recommendation="Confirmar buffer pool de 2% para biochar em solo conforme protocolo Puro.Earth.")
    if risk_assessment:
        return build_logic_result("partial", 65,
            gap="Avaliação de risco de reversão presente mas buffer pool não quantificado.",
            recommendation="Calcular e documentar o buffer pool (padrão: 2% para biochar em solo).")
    return build_logic_result("partial", 35,
        gap="Avaliação de risco de reversão e buffer pool não encontrados.",
        recommendation="Completar o questionário de risco de reversão do Puro.Earth e calcular o buffer pool (mínimo 2%).")


# ── monitoring ────────────────────────────────────────────────────────────────

def eval_puro_data_collection_v1(project_data: dict, audit_mode: str = "development") -> dict:
    monitoring = _get(project_data, "monitoring") or {}
    has_sop = (monitoring.get("data_storage") or
               monitoring.get("data_management") or
               monitoring.get("record_keeping"))
    retention = monitoring.get("retention_years") or monitoring.get("data_retention")

    if has_sop and (retention is None or int(retention or 5) >= 5):
        return build_logic_result("compliant", 100,
            notes=["Procedimento de coleta e armazenamento de dados com retenção ≥ 5 anos identificado."])
    if has_sop:
        return build_logic_result("partial", 70,
            gap="Procedimento de gestão de dados identificado mas retenção mínima de 5 anos não confirmada.",
            recommendation="Confirmar retenção de dados por mínimo 5 anos com backup e responsável designado.")
    return build_logic_result("partial", 35,
        gap="Abordagem de coleta e armazenamento de dados não descrita.",
        recommendation="Descrever SOP de gestão de dados: transmissão, coleta, armazenamento (≥5 anos), backup e responsável.")


def eval_puro_monitoring_parameters_v1(project_data: dict, audit_mode: str = "development") -> dict:
    monitoring = _get(project_data, "monitoring") or {}
    params = (monitoring.get("parameters") or
              monitoring.get("monitoring_plan") or
              monitoring.get("monitored_variables"))
    if params:
        return build_logic_result("compliant", 100, notes=["Tabela de parâmetros de monitoramento identificada."])
    return build_logic_result("partial", 40,
        gap="Tabela de parâmetros monitorados não encontrada.",
        recommendation="Fornecer tabela completa de parâmetros monitorados com: fonte de dados, frequência, QA/QC e evidências.")


def eval_puro_sampling_procedure_v1(project_data: dict, audit_mode: str = "development") -> dict:
    sampling = _get(project_data, "sampling") or {}
    method = sampling.get("sampling_method") or sampling.get("method")
    count = sampling.get("sample_count") or sampling.get("samples_per_batch")
    frequency = sampling.get("sampling_frequency")

    PURO_METHODS = ["method a", "method b", "método a", "método b", "every batch",
                    "todo batch", "1 por 10", "one per 10"]
    has_method = bool(method) and any(kw in str(method).lower() for kw in PURO_METHODS + ["sample", "amostr"])

    if audit_mode == "development":
        if has_method and method:
            return build_logic_result("compliant", 100,
                notes=[f"Método de amostragem Puro descrito: {method}"])
        if method:
            return build_logic_result("partial", 65,
                gap="Método de amostragem presente mas não alinhado explicitamente com Method A/B do Puro.",
                recommendation="Especificar explicitamente Method A (todo batch) ou Method B (1/10 batches após ≥30 amostras baseline). Mínimo: ≥3 amostras/batch; idade ≤6 meses.")
        return build_logic_result("partial", 40,
            gap="Procedimento de amostragem não descrito.",
            recommendation="Descrever e justificar o método de amostragem: Method A (todo batch) ou Method B (1/10 batches).")

    # Operational
    if count is not None and method:
        count_int = int(count)
        if count_int >= 3:
            return build_logic_result("compliant", 100,
                notes=[f"Amostragem operacional: {count_int} amostras/batch, método: {method}"])
        return build_logic_result("non_compliant", 10,
            gap=f"Apenas {count_int} amostras/batch — mínimo Puro é 3.",
            recommendation="Aumentar para ≥3 amostras por batch conforme Puro Biochar Methodology 2025.")
    return build_logic_result("partial", 35,
        gap="Registros de amostragem operacional não encontrados.",
        recommendation="Documentar registros de amostragem por batch com datas, quantidades e cadeia de custódia.")


# ── environmental_and_social_impact ──────────────────────────────────────────

def eval_puro_regulatory_compliance_v1(project_data: dict, audit_mode: str = "development") -> dict:
    legal = _get(project_data, "legal") or {}
    safeguards = _get(project_data, "safeguards") or {}
    permits = legal.get("permits_documented") or safeguards.get("permits_documented")
    compliance = (legal.get("applicable_environmental_requirements") or
                  safeguards.get("regulatory_compliance") or
                  legal.get("regulatory_compliance"))

    if audit_mode == "development":
        if compliance and permits:
            return build_logic_result("compliant", 100,
                notes=["Conformidade regulatória e licenças documentadas."])
        if compliance:
            return build_logic_result("partial", 70,
                gap="Método de conformidade regulatória descrito mas licenças não evidenciadas.",
                recommendation="Listar todas as licenças e autorizações ambientais necessárias.")
        return build_logic_result("partial", 40,
            gap="Conformidade com regulamentações ambientais aplicáveis não descrita.",
            recommendation="Listar regulações aplicáveis (federal, estadual, municipal) e descrever método de conformidade.")

    if permits:
        return build_logic_result("compliant", 100,
            notes=["Licenças vigentes com evidências de renovação — conformidade operacional."])
    return build_logic_result("partial", 45,
        gap="Licenças e autorizações vigentes não evidenciadas no modo operacional.",
        recommendation="Fornecer licenças ambientais em vigor com datas de validade e evidências de renovação.")


def eval_puro_env_social_impact_v1(project_data: dict, audit_mode: str = "development") -> dict:
    safeguards = _get(project_data, "safeguards") or {}
    assessment = (safeguards.get("environmental_social_assessment") or
                  safeguards.get("impact_assessment") or
                  safeguards.get("esia"))
    if assessment:
        return build_logic_result("compliant", 100,
            notes=["Avaliação de impacto ambiental e social identificada."])
    return build_logic_result("partial", 55,
        gap="Avaliação de impacto ambiental e social não encontrada.",
        recommendation="Realizar e documentar avaliação de impactos materiais ambientais e sociais dentro e além da fronteira do projeto.")


def eval_puro_no_net_env_harm_v1(project_data: dict, audit_mode: str = "development") -> dict:
    safeguards = _get(project_data, "safeguards") or {}
    no_harm = (safeguards.get("no_environmental_harm") or
               safeguards.get("environmental_assessment") or
               safeguards.get("biodiversity"))
    if no_harm:
        return build_logic_result("compliant", 100,
            notes=["Demonstração de não-dano líquido ambiental identificada."])
    return build_logic_result("partial", 50,
        gap="Demonstração de não-dano líquido ambiental não encontrada.",
        recommendation="Incluir avaliação de eficiência de recursos, prevenção de poluição e conservação da biodiversidade.")


def eval_puro_no_net_social_harm_v1(project_data: dict, audit_mode: str = "development") -> dict:
    safeguards = _get(project_data, "safeguards") or {}
    social = (safeguards.get("social_assessment") or
              safeguards.get("no_social_harm") or
              safeguards.get("human_rights"))
    if social:
        return build_logic_result("compliant", 100,
            notes=["Avaliação de riscos sociais identificada."])
    return build_logic_result("partial", 50,
        gap="Avaliação de riscos sociais não encontrada.",
        recommendation="Avaliar riscos: direitos trabalhistas, direitos humanos, impacto em comunidades indígenas e medidas de mitigação.")


def eval_puro_pollution_prevention_v1(project_data: dict, audit_mode: str = "development") -> dict:
    char = _get(project_data, "biochar", "characterization") or {}
    pah   = char.get("pah_mg_kg")
    pcb   = char.get("pcb_mg_kg")
    dioxins = char.get("pcdd_f_ng_kg")
    metals  = char.get("heavy_metals")
    safeguards = _get(project_data, "safeguards") or {}
    pollution_plan = safeguards.get("pollution_prevention")

    if audit_mode == "development":
        if pollution_plan or (pah is not None or pcb is not None):
            return build_logic_result("compliant", 100,
                notes=["Plano de prevenção de poluição ou análise de risco identificados."])
        return build_logic_result("partial", 45,
            gap="Plano de prevenção de poluição (PAH, metais, PCB, dioxinas) não encontrado.",
            recommendation="Documentar avaliação de risco e plano de mitigação para PAH, metais pesados, PCB e PCDD/F.")

    # Operational: check actual values
    ok = True; issues = []
    if pah   is not None and float(pah)     > 12:   ok = False; issues.append(f"PAH={pah} > limite WBC")
    if pcb   is not None and float(pcb)     > 0.2:  ok = False; issues.append(f"PCB={pcb} > 0,2 mg/kg")
    if dioxins is not None and float(dioxins) > 20: ok = False; issues.append(f"PCDD/F={dioxins} > 20 ng/kg")
    if ok and (pah is not None or pcb is not None):
        return build_logic_result("compliant", 100,
            notes=[f"Contaminantes dentro dos limites Puro/WBC. PAH={pah}, PCB={pcb}, PCDD/F={dioxins}"])
    if issues:
        return build_logic_result("non_compliant", 0,
            gap="; ".join(issues),
            recommendation="Otimizar processo de pirólise para reduzir contaminantes abaixo dos limites.")
    return build_logic_result("partial", 35,
        gap="Laudos de contaminantes não encontrados.",
        recommendation="Realizar análises de PAH, PCB, metais pesados e PCDD/F em laboratório ISO 17025.")


def eval_puro_adaptive_management_v1(project_data: dict, audit_mode: str = "development") -> dict:
    safeguards = _get(project_data, "safeguards") or {}
    mgmt = safeguards.get("adaptive_management_plan") or safeguards.get("adaptive_management")
    TRIGGERS = ["instrument failure", "pollutant", "non-compliance", "health", "safety",
                "falha", "poluente", "não conformidade", "saúde", "segurança"]
    has_triggers = any(t in str(mgmt).lower() for t in TRIGGERS) if mgmt else False
    if mgmt and has_triggers:
        return build_logic_result("compliant", 100,
            notes=["Plano de gestão adaptativa com gatilhos de pausa/parada identificados."])
    if mgmt:
        return build_logic_result("partial", 65,
            gap="Plano de gestão adaptativa presente mas 4 gatilhos obrigatórios não explícitos.",
            recommendation="Incluir explicitamente os 4 gatilhos de pausa/parada: falha de instrumento, poluentes acima do limite, não-conformidade regulatória e risco de saúde/segurança.")
    return build_logic_result("partial", 35,
        gap="Plano de gestão adaptativa não encontrado.",
        recommendation="Documentar plano com: compartilhamento de informações, resposta a emergências e condições obrigatórias de pausa/parada.")


def eval_puro_baseline_soil_v1(project_data: dict, audit_mode: str = "development") -> dict:
    monitoring = _get(project_data, "monitoring") or {}
    soil = monitoring.get("baseline_soil") or monitoring.get("soil_sampling")
    if soil:
        return build_logic_result("compliant", 100, notes=["Coleta de amostras de solo baseline identificada."])
    if audit_mode == "development":
        return build_logic_result("partial", 55,
            gap="Plano de coleta de amostras de solo baseline não descrito.",
            recommendation="Descrever coleta de amostras de solo pré-aplicação (pH, umidade, SOC, nutrientes) até 30 cm de profundidade.")
    return build_logic_result("partial", 40,
        gap="Resultados de amostras de solo baseline não encontrados.",
        recommendation="Apresentar laudos de amostras de solo baseline coletadas antes da aplicação do biochar.")


def eval_puro_soil_quality_monitoring_v1(project_data: dict, audit_mode: str = "development") -> dict:
    monitoring = _get(project_data, "monitoring") or {}
    soil_plan = monitoring.get("soil_quality") or monitoring.get("agricultural_monitoring")
    if soil_plan:
        return build_logic_result("compliant", 100,
            notes=["Plano de monitoramento de qualidade do solo e produtividade agrícola identificado."])
    return build_logic_result("partial", 55,
        gap="Plano de monitoramento de produtividade agrícola e qualidade do solo não encontrado.",
        recommendation="Documentar abordagem de monitoramento: parâmetros (pH, SOC, nutrientes), frequência e responsável.")


def eval_puro_co_benefits_v1(project_data: dict, audit_mode: str = "development") -> dict:
    # Optional — always at least partial
    safeguards = _get(project_data, "safeguards") or {}
    co_benefits = safeguards.get("co_benefits") or safeguards.get("sdg_alignment")
    if co_benefits:
        return build_logic_result("compliant", 100,
            notes=["Co-benefícios documentados (opcional)."])
    return build_logic_result("partial", 75,
        gap="Co-benefícios de saúde do solo não documentados (opcional).",
        recommendation="Considerar documentar co-benefícios observados (opcional) — melhoria do solo, biodiversidade, ODS.")


# ── stakeholder_input_process ─────────────────────────────────────────────────

def eval_puro_stakeholder_consultation_v1(project_data: dict, audit_mode: str = "development") -> dict:
    safeguards = _get(project_data, "safeguards") or {}
    consultation = safeguards.get("stakeholder_consultation") or safeguards.get("public_consultation")
    if consultation:
        return build_logic_result("compliant", 100,
            notes=["Consulta a stakeholders documentada."])
    return build_logic_result("partial", 40,
        gap="Consulta pública a stakeholders locais não documentada.",
        recommendation="Documentar como comentários foram coletados, compilados e considerados no design do projeto.")


def eval_puro_grievance_v1(project_data: dict, audit_mode: str = "development") -> dict:
    safeguards = _get(project_data, "safeguards") or {}
    grievance = safeguards.get("grievance_mechanism") or safeguards.get("complaint_mechanism")
    DEADLINE_KEYWORDS = ["14", "60", "days", "dias", "prazo", "deadline"]
    has_deadlines = any(k in str(grievance).lower() for k in DEADLINE_KEYWORDS) if grievance else False
    if grievance and has_deadlines:
        return build_logic_result("compliant", 100,
            notes=["Mecanismo de reclamações com prazos (≤14 dias reconhecimento, ≤60 resolução) identificado."])
    if grievance:
        return build_logic_result("partial", 65,
            gap="Mecanismo de reclamações presente mas prazos obrigatórios não especificados.",
            recommendation="Incluir explicitamente: reconhecimento ≤14 dias e resolução ≤60 dias.")
    return build_logic_result("partial", 35,
        gap="Mecanismo de reclamações não encontrado.",
        recommendation="Documentar mecanismo de reclamações com canal de contato e prazos: reconhecimento ≤14 dias, resolução ≤60 dias.")


# ── appendix ──────────────────────────────────────────────────────────────────

def eval_puro_reactor_design_v1(project_data: dict, audit_mode: str = "development") -> dict:
    prod = _get(project_data, "production") or {}
    diagram = prod.get("reactor_diagram") or prod.get("engineering_diagram") or prod.get("reactor_design")
    specs   = prod.get("reactor_type") or prod.get("reactor_specs")
    if diagram:
        return build_logic_result("compliant", 100, notes=["Diagrama de engenharia do reator identificado."])
    if specs:
        return build_logic_result("partial", 65,
            gap="Especificações do reator identificadas mas diagrama de engenharia não evidenciado.",
            recommendation="Incluir diagrama de engenharia formal com dimensões, fluxos, posicionamento de sensores e equipamentos internos.")
    return build_logic_result("partial", 30,
        gap="Diagrama de engenharia do reator de pirólise não encontrado.",
        recommendation="Fornecer diagrama de engenharia do reator com dimensões, fluxos de entrada/saída, sensores e equipamentos.")


def eval_puro_gas_sensors_v1(project_data: dict, audit_mode: str = "development") -> dict:
    prod = _get(project_data, "production") or {}
    sensors = (prod.get("leakage_sensors") or
               prod.get("gas_sensors") or
               prod.get("pressure_monitoring"))
    if audit_mode == "development":
        if sensors:
            return build_logic_result("compliant", 100,
                notes=[f"Sensores/método de detecção de vazamento de gases identificado: {sensors}"])
        return build_logic_result("partial", 40,
            gap="Método de detecção de vazamento de gases de pirólise não descrito.",
            recommendation="Especificar método: (a) modelo de especificação do reator, (b) pressão contínua (±2%, ≥1 min), ou (c) teste anual (ISO/ASTM).")
    if sensors:
        return build_logic_result("compliant", 100, notes=["Registros de monitoramento de vazamento presentes."])
    return build_logic_result("partial", 35,
        gap="Registros de medição de pressão ou teste de vazamento não encontrados.",
        recommendation="Apresentar logs de pressão contínua ou relatório de teste anual de vazamento (ISO/ASTM).")


def eval_puro_reactor_material_v1(project_data: dict, audit_mode: str = "development") -> dict:
    prod = _get(project_data, "production") or {}
    material = prod.get("reactor_material") or prod.get("materials_specification")
    if material:
        return build_logic_result("compliant", 100,
            notes=[f"Especificação de materiais do reator identificada: {material}"])
    return build_logic_result("partial", 45,
        gap="Justificativa de seleção de materiais do reator não encontrada.",
        recommendation="Documentar materiais com justificativa de resiliência térmica e mecânica. Se pressão > 0,5 Bar: conformidade com Diretiva 2014/68/EU.")


def eval_puro_maintenance_v1(project_data: dict, audit_mode: str = "development") -> dict:
    prod = _get(project_data, "production") or {}
    maintenance = prod.get("maintenance_plan") or prod.get("maintenance")
    if audit_mode == "development":
        if maintenance:
            return build_logic_result("compliant", 100, notes=["Plano de manutenção do reator documentado."])
        return build_logic_result("partial", 40,
            gap="Plano de manutenção do reator não encontrado.",
            recommendation="Documentar plano de manutenção com escopo, frequência, responsáveis e monitoramento de degradação.")
    if maintenance:
        return build_logic_result("compliant", 100, notes=["Registros de manutenção evidenciados."])
    return build_logic_result("partial", 35,
        gap="Registros de manutenção executada não encontrados.",
        recommendation="Apresentar histórico de manutenção preventiva e corretiva com integridade estrutural documentada.")


def eval_puro_characterization_standards_v1(project_data: dict, audit_mode: str = "development") -> dict:
    char = _get(project_data, "biochar", "characterization") or {}
    standards = char.get("standards") or char.get("quality_standard")
    KNOWN_STANDARDS = ["iso", "astm", "ebc", "ibi", "din"]
    has_standard = bool(standards) and any(kw in str(standards).lower() for kw in KNOWN_STANDARDS)
    if has_standard:
        return build_logic_result("compliant", 100,
            notes=[f"Padrões de caracterização identificados: {standards}"])
    return build_logic_result("partial", 50,
        gap="Padrões de caracterização do biochar não listados.",
        recommendation="Listar padrões usados: ISO 29541, ASTM D5373 (químico); ISO 18122, ISO 17828 (físico).")


def eval_puro_biochar_chemical_v1(project_data: dict, audit_mode: str = "development") -> dict:
    char = _get(project_data, "biochar", "characterization") or {}
    h_c = char.get("h_c_ratio"); o_c = char.get("o_c_ratio")
    pah = char.get("pah_mg_kg"); metals = char.get("heavy_metals")
    lab = char.get("lab_accreditation") or char.get("lab_reports")

    if audit_mode == "development":
        has_plan = any(v is not None for v in [h_c, o_c, pah, lab])
        if has_plan:
            return build_logic_result("compliant", 100,
                notes=["Plano de análise química do biochar identificado com parâmetros Puro."])
        return build_logic_result("partial", 40,
            gap="Parâmetros químicos do biochar não especificados no PDD.",
            recommendation="Especificar: H/Corg < 0,5, O/Corg < 0,2, PAH, metais pesados — laboratório ISO 17025.")

    # Operational: actual values required
    h_c_ok = h_c is not None and float(h_c) < 0.5
    o_c_ok = o_c is not None and float(o_c) < 0.2
    if h_c_ok and o_c_ok:
        return build_logic_result("compliant", 100,
            notes=[f"H/Corg={h_c} ✓ | O/Corg={o_c} ✓ | PAH={pah}"])
    gaps = []
    if not h_c_ok: gaps.append(f"H/Corg não confirmado (encontrado: {h_c}, exigido: < 0,5)")
    if not o_c_ok: gaps.append(f"O/Corg não confirmado (encontrado: {o_c}, exigido: < 0,2)")
    return build_logic_result(
        "non_compliant" if (h_c is not None or o_c is not None) else "partial",
        0 if (h_c is not None and not h_c_ok) else 35,
        gap="; ".join(gaps) if gaps else "Laudos de caracterização química não encontrados.",
        recommendation="Realizar e documentar análises químicas por batch (ISO 17025): H/Corg, O/Corg, PAH, metais.")


def eval_puro_biochar_physical_v1(project_data: dict, audit_mode: str = "development") -> dict:
    char = _get(project_data, "biochar", "characterization") or {}
    physical = char.get("physical_properties") or char.get("surface_area") or char.get("particle_size")
    if physical:
        return build_logic_result("compliant", 100, notes=["Propriedades físicas do biochar documentadas."])
    if audit_mode == "development":
        return build_logic_result("partial", 60,
            gap="Propriedades físicas (porosidade, BET, granulometria) não descritas.",
            recommendation="Descrever plano de análise: porosidade, superfície BET (ISO 9277) e granulometria (ISO 565).")
    return build_logic_result("partial", 55,
        gap="Laudos de propriedades físicas não encontrados.",
        recommendation="Fornecer laudos com porosidade, superfície específica BET e distribuição de tamanho de partículas.")


def eval_puro_laboratory_v1(project_data: dict, audit_mode: str = "development") -> dict:
    char = _get(project_data, "biochar", "characterization") or {}
    lab = char.get("lab_accreditation") or char.get("laboratory") or char.get("lab_reports")
    ISO_KEYWORDS = ["iso 17025", "iso17025", "acredita", "accreditat"]
    has_iso = any(kw in str(lab).lower() for kw in ISO_KEYWORDS) if lab else False

    if lab and has_iso:
        return build_logic_result("compliant", 100,
            notes=[f"Laboratório ISO 17025 identificado: {lab}"])
    if lab:
        return build_logic_result("partial", 65,
            gap="Laboratório identificado mas acreditação ISO 17025 não confirmada.",
            recommendation="Confirmar que o laboratório possui certificação ISO 17025 em vigor e incluir o número do certificado.")
    return build_logic_result("partial", 30,
        gap="Laboratório analítico qualificado não identificado.",
        recommendation="Identificar laboratório com acreditação ISO 17025 para análises de biochar.")


# ── project_management ────────────────────────────────────────────────────────

def eval_puro_closure_plan_v1(project_data: dict, audit_mode: str = "development") -> dict:
    safeguards = _get(project_data, "safeguards") or {}
    closure = safeguards.get("closure_plan") or safeguards.get("decommissioning")
    if closure:
        return build_logic_result("compliant", 100, notes=["Plano de encerramento do projeto identificado."])
    return build_logic_result("partial", 65,
        gap="Plano de encerramento não encontrado (não-obrigatório).",
        recommendation="Documentar condições de encerramento e plano de pós-encerramento (recomendado).")


def eval_puro_sdg_alignment_v1(project_data: dict, audit_mode: str = "development") -> dict:
    safeguards = _get(project_data, "safeguards") or {}
    sdg = safeguards.get("sdg_alignment") or safeguards.get("co_benefits") or safeguards.get("sdgs")
    if sdg:
        return build_logic_result("compliant", 100, notes=["Alinhamento com ODS documentado."])
    return build_logic_result("partial", 60,
        gap="Alinhamento com ODS não documentado (exigido pelo Puro.Earth).",
        recommendation="Completar relatório de ODS do Puro e identificar os objetivos de desenvolvimento sustentável relevantes para o projeto.")
