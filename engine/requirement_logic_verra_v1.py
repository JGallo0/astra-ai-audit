"""
Engine v1 — Funções de lógica para Verra VCS VM0044 v1.2.
"Methodology for Biochar Utilization in Soil and Non-Soil Applications"

Cada função recebe (data: dict, audit_mode: str) e retorna um dict
compatível com build_logic_result().

Thresholds extraídos diretamente do VM0044 v1.2:
  - Tabela 3: PRde,k por temperatura de pirólise
  - Applicability Conditions 1-15
  - Seções 6 (baseline), 7 (additionality), 8 (quantification), 9 (monitoramento)

Diferença estrutural vs. Isometric/Puro:
  - Permanência determinada por TEMPERATURA de pirólise (não H/Corg)
  - H/Corg é gate binário de elegibilidade para solo (≤ 0.7)
  - Baseline sempre zero (conservador) — ERSS,y = 0
  - N₂O/CH₄ do solo explicitamente excluídos como negligíveis
  - Low-tech: default PRde = 0.56, default Fe = 0.049 tCH4/t
"""

from engine.requirement_logic import build_logic_result

# ── Permanence factors — VM0044 Table 3 ──────────────────────────────────────
PRDE_HIGH   = 0.89   # > 600°C
PRDE_MEDIUM = 0.80   # 450–600°C
PRDE_LOW    = 0.65   # 350–450°C
PRDE_DEFAULT = 0.56  # temperatura desconhecida (low-tech / não medida)

# Threshold baixa temperatura — abaixo de 350°C o biochar não é elegível
TEMP_MIN_ELIGIBLE = 350.0   # °C (AC 5/8)
TEMP_HIGH = 600.0            # °C
TEMP_MEDIUM = 450.0          # °C

# H/Corg — gate de elegibilidade para aplicação em solo
HC_ORG_SOIL_LIMIT = 0.7     # AC 10

# Emissão CH₄ default para low-tech (Cornelissen et al. 2016)
FE_LOW_TECH_DEFAULT = 0.049  # tCH4/tonne biochar
GWPCH4 = 28                  # AR5

# Distância máxima sem contabilizar leakage de transporte
TRANSPORT_LEAKAGE_KM = 200.0  # km round-trip (CDM TOOL12)

# Fração máxima de HCFA (high-carbon fly ash) no feedstock
HCFA_MAX_FRACTION = 0.05     # 5% do throughput anual

# Mineral additives limit
MINERAL_ADDITIVE_MAX_FRACTION = 0.10  # 10% em massa


# ── Helpers ───────────────────────────────────────────────────────────────────

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
    n.append(f"[VM0044] {citation}")
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

def _partial(gap, recommendation, citation, notes=None, score=50):
    n = list(notes or [])
    n.append(f"[VM0044] {citation}")
    return build_logic_result(
        status="partial",
        missing_fields=[],
        failed_fields=[],
        notes=n,
        requirement_score=score,
        field_scores=[],
        requirement_rating="moderate",
        gap=gap,
        recommendation=recommendation,
    )

def _future(gap, recommendation, citation, notes=None, score=35):
    n = list(notes or [])
    n.append(f"[VM0044] {citation}")
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

def _get(data: dict, *keys, default=None):
    v = data
    for k in keys:
        if not isinstance(v, dict):
            return default
        v = v.get(k, default)
    return v


# ══════════════════════════════════════════════════════════════════════════════
# V-APPL-0 — Applicability (escopo geral)
# AC 1-3: deve ser projeto de biochar novo (greenfield), não retrofitting de
# instalação existente que já produz biochar sem fins de remoção de carbono.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_applicability_v1(data: dict, audit_mode: str = "development"):
    is_greenfield = _get(data, "verra", "is_greenfield_facility")
    has_tech_desc = _get(data, "production", "system_description")
    has_boundary  = _get(data, "carbon_accounting", "system_boundary_defined")

    if is_greenfield is False:
        return _non_compliant(
            gap="VM0044 exige instalação nova (greenfield) ou expansão documentada de instalação existente.",
            recommendation="Demonstre que a instalação não estava operando como produtora de biochar antes do projeto, ou documente a expansão incremental.",
            citation="AC 1-3 — A methodology must install and operate a new (greenfield) biochar production facility.",
        )

    score = 0
    notes = []
    if has_tech_desc:
        score += 50
        notes.append("Descrição técnica da produção presente.")
    else:
        notes.append("Ausência de descrição técnica da instalação de pirólise.")

    if has_boundary:
        score += 50
        notes.append("Fronteira do sistema definida.")
    else:
        notes.append("Fronteira do sistema não explicitada.")

    if score == 100:
        return _compliant(notes=notes)
    if score >= 50:
        return _partial(
            gap="Documentação da instalação incompleta.",
            recommendation="Detalhe descrição técnica da instalação e fronteira do sistema de acordo com a Seção 5 do VM0044.",
            citation="AC 1-3",
            notes=notes, score=score,
        )
    return _future(
        gap="Não foi possível verificar elegibilidade básica da instalação.",
        recommendation="Forneça evidência de que a instalação é nova e dedicada à produção de biochar para fins de remoção de carbono.",
        citation="AC 1-3",
        notes=notes, score=score,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-FEED-0 — Feedstock eligibility (AC 4a-4c)
# Feedstock deve ser: (a) puramente biogênico e resíduo, (b) que seria
# deixado a decompor ou queimado sem fins energéticos, (c) não importado.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_feedstock_eligibility_v1(data: dict, audit_mode: str = "development"):
    feedstock = data.get("feedstock", {})
    verra     = data.get("verra", {})

    is_waste_biogenic  = feedstock.get("is_waste_biogenic", feedstock.get("biomass_type") not in ("", None))
    is_purpose_grown   = verra.get("is_purpose_grown", False)
    is_imported        = verra.get("feedstock_imported", False)
    has_baseline_proof = _get(data, "carbon_accounting", "baseline_scenario") or verra.get("has_baseline_fate_evidence")

    notes = []

    if is_purpose_grown:
        return _non_compliant(
            gap="Feedstock purpose-grown (cultivado para este fim) não é elegível no VM0044.",
            recommendation="Utilize apenas biomassa residual — resíduos agrícolas, florestais, processamento alimentar ou similares listados na Tabela 1 do VM0044.",
            citation="AC 4a — Feedstock must be purely biogenic waste biomass and not purpose-grown.",
        )

    if is_imported:
        return _non_compliant(
            gap="Feedstock importado de outro país não é elegível no VM0044.",
            recommendation="Utilize feedstock local. VM0044 exige que o feedstock não seja importado de outros países (AC 4c).",
            citation="AC 4c — Feedstock must not have been imported from other countries.",
        )

    score = 0
    if is_waste_biogenic:
        score += 50
        notes.append("Feedstock identificado como biomassa residual biogênica.")
    else:
        notes.append("Tipo de feedstock não claramente identificado como resíduo biogênico.")

    if has_baseline_proof:
        score += 50
        notes.append("Evidência do destino do feedstock na ausência do projeto (decomposição ou queima).")
    else:
        notes.append("Sem evidência documentada do destino alternativo do feedstock (AC 4b).")

    if score == 100:
        return _compliant(notes=notes)
    if score >= 50:
        return _partial(
            gap="Faltam evidências do destino alternativo do feedstock (AC 4b).",
            recommendation="Forneça registros governamentais, dados de instalação de disposição de resíduos, literatura regional ou levantamento próprio conforme Appendix 2 do VM0044.",
            citation="AC 4b — Feedstock must have been otherwise left to decay or combusted.",
            notes=notes, score=score,
        )
    return _future(
        gap="Elegibilidade do feedstock não verificável com informações disponíveis.",
        recommendation="Documente tipo de biomassa e destino alternativo conforme AC 4.",
        citation="AC 4a-c",
        notes=notes, score=score,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-FCAT-0 — Feedstock category (AC 4d — Tabela 1)
# 7 categorias permitidas com critérios de sustentabilidade específicos.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_feedstock_category_v1(data: dict, audit_mode: str = "development"):
    feedstock = data.get("feedstock", {})
    verra     = data.get("verra", {})

    VALID_CATEGORIES = {
        "agricultural_residue",  # pruning, harvest residues, fruit/veg residues
        "food_processing",       # washing/peeling residues, expired food
        "forestry_wood",         # off-cuts, sawdust, pallets, thinnings
        "recycling_economy",     # urban green waste, biosolids, paper sludge
        "aquaculture",           # seaweed, algae, invasive aquatic species
        "animal_manure",         # swine, cattle, poultry
        "hcfa",                  # high-carbon fly ash from biomass cogeneration
    }

    biomass_type = feedstock.get("biomass_type", "")
    feedstock_category = verra.get("feedstock_category", "")
    hcfa_fraction = verra.get("hcfa_fraction")
    is_forest_biomass = feedstock.get("includes_forest_biomass", False)
    has_forest_cert = any([
        feedstock.get("certification_scheme") in ("FSC", "PEFC", "SFI"),
        verra.get("has_pefc_cert"), verra.get("has_fsc_cert"),
    ])
    # Agrícola: remoção > 50% sem docs de solo
    high_residue_removal = verra.get("high_residue_removal", False)
    has_soil_health_docs = verra.get("has_soil_health_docs", False)
    # Processamento alimentar: volume aumentado para o projeto
    residue_volume_increased = verra.get("residue_volume_increased", False)

    notes = []

    # Processamento alimentar — volume artificialmente aumentado → inelegível
    if residue_volume_increased and biomass_type in ("food_waste", "food_processing"):
        return _non_compliant(
            gap="Volume de resíduos de processamento alimentar aumentado especificamente para produção de biochar.",
            recommendation="VM0044 Tabela 1: resíduos de processamento alimentar devem ser subprodutos naturais da operação — o volume por unidade de produção não pode aumentar para fins de biochar.",
            citation="Tabela 1 — Food processing: production of residues per facility output must not increase.",
        )

    # Agrícola — remoção > 50% sem documentação de saúde do solo
    if high_residue_removal and not has_soil_health_docs and biomass_type == "agricultural_residue":
        return _partial(
            gap="Remoção de mais de 50% dos resíduos agrícolas sem documentação de saúde do solo.",
            recommendation="VM0044 Tabela 1: remoção acima de 50% dos resíduos do campo deve ser acompanhada de evidência de que não causa degradação do solo. Forneça análise de solo ou estudo agronômico.",
            citation="Tabela 1 — Agricultural waste: if removing from fields, must not lead to soil degradation; limited to 50% without documentation.",
            notes=notes, score=50,
        )

    # HCFA hard gate — máximo 5%
    if feedstock_category == "hcfa" or (hcfa_fraction is not None and hcfa_fraction > 0):
        if hcfa_fraction is not None and hcfa_fraction > HCFA_MAX_FRACTION:
            return _non_compliant(
                gap=f"HCFA representa {hcfa_fraction*100:.1f}% do throughput — máximo permitido é 5%.",
                recommendation="Reduza a fração de HCFA para ≤ 5% do throughput anual conforme Tabela 1 do VM0044.",
                citation="Tabela 1 — HCFA sustainability criteria: ≤ 5% of annual waste biomass throughput.",
            )

    # Biomassa florestal requer certificação (PEFC, FSC ou definição CDM de biomassa renovável)
    if is_forest_biomass and not has_forest_cert:
        notes.append("Biomassa florestal sem certificação PEFC/FSC detectada — aplicação em solo requer prova de fonte sustentável.")
        return _partial(
            gap="Biomassa florestal sem certificação de sustentabilidade (PEFC, FSC ou definição CDM de biomassa renovável).",
            recommendation="Obtenha certificação PEFC ou FSC, ou demonstre conformidade com a definição CDM de biomassa renovável (EB23 Annex 18). Requisito mais flexível que Puro.Earth.",
            citation="Tabela 1 — Forestry: must prove sustainable sources (PEFC, FSC, CDM renewable biomass definition).",
            notes=notes, score=45,
        )

    # Verificação de categoria
    if feedstock_category and feedstock_category not in VALID_CATEGORIES:
        return _non_compliant(
            gap=f"Categoria de feedstock '{feedstock_category}' não reconhecida na Tabela 1 do VM0044.",
            recommendation="Verifique se o feedstock se enquadra em uma das 7 categorias da Tabela 1: resíduo agrícola, processamento alimentar, madeira/florestal, economia circular, aquicultura, esterco animal ou HCFA.",
            citation="Tabela 1 — Eligible Feedstock Categories.",
        )

    if feedstock_category in VALID_CATEGORIES:
        notes.append(f"Categoria de feedstock confirmada: {feedstock_category}.")
        return _compliant(notes=notes)

    # Categoria não especificada mas biomassa parece elegível
    if biomass_type in ("agricultural_residue", "forest_biomass", "urban_wood", "food_waste"):
        notes.append("Tipo de biomassa compatível com Tabela 1, mas categoria formal não declarada no PDD.")
        return _partial(
            gap="Categoria de feedstock não declarada formalmente no PDD conforme Tabela 1.",
            recommendation="Declare explicitamente a categoria da Tabela 1 que se aplica e documente os critérios de sustentabilidade específicos dessa categoria.",
            citation="AC 4d — Feedstock must meet sustainability conditions provided in Table 1.",
            notes=notes, score=60,
        )

    return _future(
        gap="Não foi possível identificar a categoria de feedstock da Tabela 1.",
        recommendation="Especifique a categoria de feedstock conforme Tabela 1 do VM0044 e evidencie os critérios de sustentabilidade aplicáveis.",
        citation="AC 4d e Tabela 1.",
        notes=notes, score=25,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-TECH-0 — Technology class (AC 5-8: high-tech vs low-tech)
# High-tech: controle automatizado, temperatura medida continuamente.
# Low-tech: fornos simples sem automação — elegíveis mas com defaults penalizantes.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_technology_class_v1(data: dict, audit_mode: str = "development"):
    verra      = data.get("verra", {})
    production = data.get("production", {})

    tech_class    = verra.get("technology_class", "")   # "high" | "low" | ""
    has_temp_ctrl = verra.get("has_continuous_temp_monitoring", False)
    has_gas_recov = production.get("has_pyrolysis_gas_recovery") or verra.get("has_gas_recovery")
    pyrolysis_temp = verra.get("pyrolysis_temp_c")

    notes = []

    # Low-tech path — temperatura não medida continuamente
    if tech_class == "low" or (not has_temp_ctrl and pyrolysis_temp is None):
        prd = PRDE_DEFAULT
        notes.append(
            f"Instalação classificada como low-tech: PRde,k default = {prd} (temperatura não monitorada continuamente). "
            f"Isso implica permanência conservadora vs. {PRDE_HIGH} para alta temperatura."
        )
        notes.append(
            f"Emissões de CH₄ do processo: Fe default = {FE_LOW_TECH_DEFAULT} tCH4/t biochar (Cornelissen et al. 2016)."
        )
        return _partial(
            gap="Instalação low-tech sem monitoramento contínuo de temperatura.",
            recommendation=(
                f"Para maximizar créditos: implemente monitoramento contínuo de temperatura (termopar ou termoresistor). "
                f"Com T > 600°C documentado, PRde sobe de {prd} para {PRDE_HIGH} (+{(PRDE_HIGH-prd)*100:.0f}pp de créditos)."
            ),
            citation="AC 5-8 e Tabela 3 — PRde,k de default 0.56 para temperatura desconhecida.",
            notes=notes, score=55,
        )

    # Temperatura conhecida mas abaixo do mínimo
    if pyrolysis_temp is not None and pyrolysis_temp < TEMP_MIN_ELIGIBLE:
        return _non_compliant(
            gap=f"Temperatura de pirólise reportada ({pyrolysis_temp}°C) abaixo do mínimo elegível de {TEMP_MIN_ELIGIBLE}°C.",
            recommendation="O VM0044 exige temperatura de pirólise ≥ 350°C. Abaixo desse limite o biochar não alcança estabilidade mínima para geração de créditos.",
            citation="AC 5 — Eligible thermochemical technologies require minimum pyrolysis temperatures.",
        )

    # High-tech path
    if has_temp_ctrl:
        if pyrolysis_temp is not None:
            prd = (
                PRDE_HIGH   if pyrolysis_temp > TEMP_HIGH   else
                PRDE_MEDIUM if pyrolysis_temp > TEMP_MEDIUM else
                PRDE_LOW
            )
            notes.append(f"Temperatura média reportada: {pyrolysis_temp}°C → PRde,k = {prd}.")
        else:
            notes.append("Monitoramento contínuo presente mas temperatura média não declarada no PDD.")

        if has_gas_recov:
            notes.append("Recuperação de gás de pirólise documentada — PEP,p,y = 0 (emissões de processo de minimis).")
        else:
            notes.append(
                "Recuperação de gás de pirólise não confirmada. "
                "Para high-tech, PEP,p,y pode ser zero se emissões forem de minimis; documente."
            )

        return _compliant(notes=notes) if pyrolysis_temp else _partial(
            gap="Temperatura média de operação não declarada no PDD.",
            recommendation="Declare a temperatura média de operação para determinar PRde,k exato conforme Tabela 3.",
            citation="Seção 9.2 — Tprod deve ser monitorado continuamente e reportado.",
            notes=notes, score=70,
        )

    return _future(
        gap="Classificação tecnológica da instalação não determinável com informações disponíveis.",
        recommendation="Especifique se a instalação é high-tech (monitoramento automático de temperatura) ou low-tech e documente conforme AC 5-8.",
        citation="AC 5-8.",
        notes=notes, score=30,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-HCOR-0 — H/Corg gate para aplicação em solo (AC 10)
# H/Corg ≤ 0.7 — gate binário. Não entra nas equações de permanência.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_hcorg_gate_v1(data: dict, audit_mode: str = "development"):
    char      = data.get("biochar", {}).get("characterization", {})
    verra     = data.get("verra", {})
    storage   = data.get("storage", {})

    h_c_ratio     = char.get("h_c_ratio") or verra.get("h_c_ratio")
    storage_path  = storage.get("pathway", "soil")
    is_soil_app   = storage_path == "soil" or verra.get("soil_application", True)

    if not is_soil_app:
        return _compliant(
            notes=["Aplicação não-solo: H/Corg ≤ 0.7 não é requisito obrigatório para esta via. "
                   "Aplicações não-solo são elegíveis independentemente do H/Corg (AC 11-12)."]
        )

    if h_c_ratio is None:
        return _future(
            gap="H/Corg não reportado. Obrigatório para aplicação em solo.",
            recommendation="Realize análise laboratorial de H/Corg conforme IBI Biochar Testing Guidelines ou EBC Production Guidelines. Resultado deve ser ≤ 0.7 para elegibilidade em solo.",
            citation="AC 10 — Biochar for soil application must have H:Corg ≤ 0.7.",
        )

    if h_c_ratio > HC_ORG_SOIL_LIMIT:
        return _non_compliant(
            gap=f"H/Corg = {h_c_ratio:.3f} excede o limite de {HC_ORG_SOIL_LIMIT} para aplicação em solo.",
            recommendation=(
                "Biochar inelegível para aplicação em solo. Opções: (1) aumentar temperatura de pirólise para reduzir H/Corg; "
                "(2) considerar aplicação não-solo (construção civil, filtração de água) onde H/Corg não é gate; "
                "(3) alterar feedstock para obter biochar com maior estabilidade."
            ),
            citation="AC 10 — H:Corg ≤ 0.7 for any soil application.",
        )

    notes = [f"H/Corg = {h_c_ratio:.3f} — dentro do limite de {HC_ORG_SOIL_LIMIT} para aplicação em solo."]
    # Nota informativa: H/Corg não afeta PRde,k no VM0044 (ao contrário de Isometric/Puro)
    notes.append(
        "Nota VM0044: H/Corg é apenas gate de elegibilidade de solo — não afeta o fator de permanência PRde,k, "
        "que é determinado exclusivamente pela temperatura de pirólise (Tabela 3)."
    )
    return _compliant(notes=notes)


# ══════════════════════════════════════════════════════════════════════════════
# V-APPL-S — Application type eligibility (AC 11-15)
# Solo e não-solo elegíveis. Biochar como combustível ou agente redutor: proibido.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_application_type_v1(data: dict, audit_mode: str = "development"):
    verra   = data.get("verra", {})
    storage = data.get("storage", {})

    storage_path         = storage.get("pathway", "soil")
    used_as_fuel         = verra.get("used_as_fuel", False)
    used_as_reducing_agent = verra.get("used_as_reducing_agent", False)
    carbon_loss_pct      = verra.get("non_soil_carbon_loss_pct")  # % de C perdido

    if used_as_fuel or used_as_reducing_agent:
        return _non_compliant(
            gap="Biochar usado como combustível ou agente redutor não é elegível (AC 13-14).",
            recommendation="VM0044 exige que o biochar seja um sumidouro de carbono de longa duração. Usos que oxidam o carbono (combustível, agente redutor em siderurgia, carvão ativado com >50% de perda de C) são proibidos.",
            citation="AC 13-14 — Biochar must not be burned as a fuel or used as a reduction agent.",
        )

    if carbon_loss_pct is not None and carbon_loss_pct > 50:
        return _non_compliant(
            gap=f"Aplicação não-solo com perda de carbono de {carbon_loss_pct:.0f}% — excede o limite de 50%.",
            recommendation="AC 15 exige que a aplicação não-solo preserve ≥ 50% do carbono original. Revise o processo ou considere outra via de aplicação.",
            citation="AC 15 — Non-soil applications must not lose more than 50% of carbon by dry weight.",
        )

    notes = [f"Via de aplicação: {storage_path}."]
    if storage_path == "soil":
        notes.append("Aplicação em solo: sumidouro permanente de C. Elegível.")
    elif storage_path in ("built_environment", "construction"):
        notes.append("Aplicação em construção civil: elegível se biochar permanecer como sumidouro (não incinerado no fim da vida).")
        has_eol = storage.get("end_of_life")
        if not has_eol:
            return _partial(
                gap="Aplicação em construção civil sem plano de fim de vida documentado.",
                recommendation="Documente que o biochar não será incinerado ou oxidado no fim da vida útil da estrutura, conforme AC 11-12.",
                citation="AC 11-12 — Non-soil applications must demonstrate long-lived carbon sink.",
                notes=notes, score=60,
            )
    elif storage_path == "water_filtration":
        notes.append("Filtração de água: elegível se biochar não for incinerado após uso.")

    return _compliant(notes=notes)


# ══════════════════════════════════════════════════════════════════════════════
# V-REGS-0 — Adicionalidade Step 1: Regulatory Surplus
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_regulatory_surplus_v1(data: dict, audit_mode: str = "development"):
    eligibility = data.get("eligibility", {})
    has_reg_add = eligibility.get("not_required_by_law", False)
    has_env_compliance = _get(data, "legal", "regulatory_compliance", default=False)

    if not has_reg_add:
        return _future(
            gap="Demonstração de surplus regulatório ausente ou não verificável.",
            recommendation="Confirme que o projeto não é exigido por lei ou regulação local, estadual ou federal. Documente conforme VCS Standard — Step 1 de adicionalidade.",
            citation="Seção 7, Step 1 — Regulatory surplus per VCS Standard.",
        )

    notes = ["Projeto demonstra que não é exigido por regulação vigente."]
    if has_env_compliance:
        notes.append("Conformidade ambiental documentada — consistente com surplus regulatório.")
    return _compliant(notes=notes)


# ══════════════════════════════════════════════════════════════════════════════
# V-PLST-0 — Adicionalidade Step 2: Positive List
# O cumprimento das ACs do VM0044 constitui a positive list.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_positive_list_v1(data: dict, audit_mode: str = "development"):
    verra = data.get("verra", {})
    is_greenfield   = verra.get("is_greenfield_facility", None)
    is_waste        = not verra.get("is_purpose_grown", False)
    not_imported    = not verra.get("feedstock_imported", False)

    notes = []
    score = 0

    if is_greenfield is not False:
        score += 34
        notes.append("Instalação nova ou não identificada como retrofit.")
    else:
        notes.append("Instalação não-greenfield pode não cumprir positive list.")

    if is_waste:
        score += 33
        notes.append("Feedstock resíduo biogênico — alinhado com positive list.")

    if not_imported:
        score += 33
        notes.append("Feedstock local (não importado).")

    if score >= 100:
        return _compliant(notes=notes)
    if score >= 60:
        return _partial(
            gap="Cumprimento parcial das Applicability Conditions que constituem a positive list.",
            recommendation="Verifique todas as ACs do VM0044 (seção 4). O cumprimento das ACs é equivalente à positive list no Step 2 de adicionalidade.",
            citation="Seção 7, Step 2 — The applicability conditions represent the positive list.",
            notes=notes, score=score,
        )
    return _future(
        gap="Não foi possível verificar o cumprimento da positive list (ACs).",
        recommendation="Documente o cumprimento de cada Applicability Condition do VM0044.",
        citation="Seção 7, Step 2.",
        notes=notes, score=score,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-VT08-0 — Adicionalidade Step 3: VT0008 Investment Analysis
# Dois caminhos: Option 1 (investment comparison) ou Option 2 (benchmark).
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_vt0008_investment_v1(data: dict, audit_mode: str = "development"):
    eligibility = data.get("eligibility", {})
    verra       = data.get("verra", {})

    has_financial_add = eligibility.get("additionality_claim", False)
    add_method        = eligibility.get("additionality_method", "")
    vt0008_path       = verra.get("vt0008_path", "")  # "investment_comparison" | "benchmark"
    irr_without_carbon = eligibility.get("irr_without_carbon")

    notes = []

    if not has_financial_add:
        return _future(
            gap="Análise de adicionalidade financeira (VT0008) não encontrada.",
            recommendation=(
                "Aplique VT0008 Step 3: Option 1 (investment comparison analysis) — demonstre que o IRR/NPV sem receita de carbono "
                "não justifica o investimento; ou Option 2 (benchmark) — compare com benchmark do setor. "
                "Um dos dois é obrigatório."
            ),
            citation="Seção 7, Step 3 — VT0008 Additionality Assessment.",
        )

    if vt0008_path == "investment_comparison" or add_method in ("irr_npv", "cost_analysis"):
        if irr_without_carbon is not None:
            notes.append(f"IRR sem receita de carbono: {irr_without_carbon:.1%} — análise financeira documentada.")
        else:
            notes.append("Método de comparação de investimento declarado mas IRR sem carbono não quantificado.")

        return _compliant(notes=notes) if irr_without_carbon is not None else _partial(
            gap="IRR/NPV sem receita de carbono não quantificado no PDD.",
            recommendation="Quantifique o IRR ou NPV do projeto sem receita de créditos de carbono e compare com a taxa de retorno mínima aceitável do setor (VT0008 Option 1).",
            citation="Seção 7, Step 3 — VT0008 Option 1: investment comparison.",
            notes=notes, score=60,
        )

    if vt0008_path == "benchmark":
        notes.append("Análise de adicionalidade via benchmark declarada.")
        return _partial(
            gap="Benchmark setorial referenciado mas não detalhado no PDD.",
            recommendation="Documente o benchmark de performance do setor de gestão de resíduos biomássicos e demonstre que o projeto supera esse benchmark (VT0008 Option 2).",
            citation="Seção 7, Step 3 — VT0008 Option 2: benchmark analysis.",
            notes=notes, score=65,
        )

    # Adicionalidade declarada mas método VCS não especificado
    notes.append(f"Adicionalidade declarada com método '{add_method}' — não mapeado para VT0008.")
    return _partial(
        gap="Método de adicionalidade não explicitamente alinhado com VT0008.",
        recommendation="Reformule a análise de adicionalidade usando explicitamente VT0008 (Option 1 ou 2). VM0044 não aceita análise ad hoc.",
        citation="Seção 7, Step 3 — VT0008.",
        notes=notes, score=50,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-BASE-0 — Baseline (Seção 6)
# ERSS,y = 0 por convenção conservadora. Baseline é sempre zero.
# Apenas biomassa que seria decomposta ou queimada sem fins energéticos.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_baseline_v1(data: dict, audit_mode: str = "development"):
    carbon_acc = data.get("carbon_accounting", {})
    has_baseline = carbon_acc.get("baseline") or carbon_acc.get("baseline_scenario")

    notes = [
        "VM0044: baseline de emissões na fase de sourcing (ERSS,y) = 0 por convenção conservadora.",
        "Créditos derivam exclusivamente da remoção de C no biochar (produção) menos emissões do processo.",
    ]

    if has_baseline:
        notes.append("Seção de baseline presente no PDD — verificar se alinhada com a abordagem conservadora do VM0044.")
        return _compliant(notes=notes)

    return _partial(
        gap="Seção de baseline não identificada no PDD.",
        recommendation=(
            "Documente o cenário baseline conforme Seção 6 do VM0044: "
            "(1) declare que ERSS,y = 0 (abordagem conservadora); "
            "(2) forneça evidência do destino do feedstock na ausência do projeto (decomposição ou queima sem fins energéticos)."
        ),
        citation="Seção 6 — Baseline scenario: BESS,y = 0 (conservative assumption).",
        notes=notes, score=50,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-BFED-0 — Baseline feedstock fate evidence (AC 4b)
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_baseline_feedstock_v1(data: dict, audit_mode: str = "development"):
    verra      = data.get("verra", {})
    carbon_acc = data.get("carbon_accounting", {})

    has_evidence = (
        verra.get("has_baseline_fate_evidence") or
        verra.get("has_govt_waste_records") or
        verra.get("has_disposal_facility_records") or
        carbon_acc.get("baseline_scenario")
    )

    evidence_type = verra.get("baseline_evidence_type", "")

    VALID_EVIDENCE = {
        "govt_records", "disposal_records", "literature", "survey", "peer_reviewed"
    }

    notes = []

    if has_evidence:
        if evidence_type and evidence_type in VALID_EVIDENCE:
            notes.append(f"Evidência do destino do feedstock: {evidence_type}.")
        else:
            notes.append("Evidência de destino do feedstock declarada — tipo de evidência não especificado.")
        return _compliant(notes=notes)

    return _future(
        gap="Evidência do destino alternativo do feedstock ausente.",
        recommendation=(
            "Forneça pelo menos uma das seguintes evidências (AC 4b e Appendix 2 do VM0044): "
            "registros governamentais anuais; registros de instalação de disposição de resíduos; "
            "literatura existente; dados de levantamento regional; ou levantamento próprio."
        ),
        citation="AC 4b e Appendix 2.",
        notes=notes, score=20,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-PERM-0 — Permanence: PRde,k por temperatura (Tabela 3)
# DIFERENÇA CENTRAL vs. Isometric/Puro: temperatura, não H/Corg.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_permanence_v1(data: dict, audit_mode: str = "development"):
    verra = data.get("verra", {})
    char  = data.get("biochar", {}).get("characterization", {})

    pyrolysis_temp = verra.get("pyrolysis_temp_c") or char.get("pyrolysis_temp_c")
    tech_class     = verra.get("technology_class", "")

    notes = []

    if pyrolysis_temp is None or tech_class == "low":
        prd = PRDE_DEFAULT
        notes.append(
            f"Temperatura de pirólise não medida continuamente → PRde,k = {prd} (default Tabela 3)."
        )
        notes.append(
            f"Impacto: créditos reduzidos em {(PRDE_HIGH - prd)*100:.0f}pp vs. alta temperatura "
            f"(PRde_high = {PRDE_HIGH})."
        )
        return _partial(
            gap="Fator de permanência PRde,k = 0.56 (default de baixa tecnologia) aplicado.",
            recommendation=(
                f"Implemente monitoramento contínuo de temperatura (Seção 9.2, Tprod). "
                f"Com T > 600°C: PRde sobe para {PRDE_HIGH}. Com 450-600°C: {PRDE_MEDIUM}. "
                f"Cada 0.01 de PRde representa ~1% de créditos adicionais por tonelada."
            ),
            citation="Tabela 3 — Default PRde,k = 0.56 where pyrolysis temperature is unknown.",
            notes=notes, score=55,
        )

    # Temperatura conhecida
    if pyrolysis_temp < TEMP_MIN_ELIGIBLE:
        return _non_compliant(
            gap=f"Temperatura de pirólise ({pyrolysis_temp}°C) abaixo do mínimo elegível ({TEMP_MIN_ELIGIBLE}°C).",
            recommendation="Aumente temperatura de pirólise para ≥ 350°C. Abaixo desse limiar o biochar não atinge estabilidade mínima para créditos VM0044.",
            citation="AC 5 — Minimum temperature requirement.",
        )

    prd = (
        PRDE_HIGH   if pyrolysis_temp > TEMP_HIGH   else
        PRDE_MEDIUM if pyrolysis_temp > TEMP_MEDIUM else
        PRDE_LOW
    )
    notes.append(
        f"Temperatura de pirólise: {pyrolysis_temp}°C → PRde,k = {prd} (Tabela 3 VM0044)."
    )
    notes.append(
        "Nota: PRde,k no VM0044 é determinado exclusivamente pela temperatura de pirólise. "
        "H/Corg não afeta o fator de permanência (ao contrário de Isometric e Puro.Earth)."
    )

    if prd == PRDE_HIGH:
        return _compliant(notes=notes)

    return _partial(
        gap=f"PRde,k = {prd} — há margem para melhorar com temperatura mais alta.",
        recommendation=f"Para atingir PRde = {PRDE_HIGH}: eleve temperatura de operação para > {TEMP_HIGH}°C.",
        citation="Tabela 3.",
        notes=notes, score=75,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-TEMP-0 — Temperature monitoring (Seção 9.2)
# Monitoramento contínuo obrigatório para high-tech; fallback para low-tech.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_temperature_monitoring_v1(data: dict, audit_mode: str = "development"):
    verra      = data.get("verra", {})
    monitoring = data.get("monitoring", {})

    has_temp_monitoring = (
        verra.get("has_continuous_temp_monitoring") or
        monitoring.get("temperature_continuous")
    )
    calibration_plan = verra.get("has_temp_calibration_plan", False)
    tech_class = verra.get("technology_class", "")

    notes = []

    if tech_class == "low" and not has_temp_monitoring:
        notes.append(
            "Low-tech: monitoramento de temperatura contínuo não exigido. "
            f"PRde,k default = {PRDE_DEFAULT} será aplicado."
        )
        return _compliant(notes=notes, score=70)

    if not has_temp_monitoring:
        return _future(
            gap="Monitoramento contínuo de temperatura de pirólise não documentado.",
            recommendation=(
                "Instale termopar ou termoresistor com sinal registrável. Calibre contra dispositivo primário independente "
                "conforme especificação do fabricante (Seção 9.2). Agrupe dados em médias anuais para o PDD."
            ),
            citation="Seção 9.2 — Tprod: continuously measured; aggregated to annual averages.",
        )

    notes.append("Monitoramento contínuo de temperatura documentado.")
    if calibration_plan:
        notes.append("Plano de calibração do sensor de temperatura presente.")
        return _compliant(notes=notes)

    return _partial(
        gap="Monitoramento contínuo presente mas plano de calibração não documentado.",
        recommendation="Documente o procedimento de calibração periódica do sensor de temperatura conforme especificações do fabricante (Seção 9.2).",
        citation="Seção 9.2 — Calibrate per manufacturer specs or 3-yearly.",
        notes=notes, score=75,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-CARB-0 — Carbon content (FCp,t,p) — Seção 9.2
# Análise laboratorial anual ou por campanha; defaults da Tabela 4 para low-tech.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_carbon_content_v1(data: dict, audit_mode: str = "development"):
    verra = data.get("verra", {})
    char  = data.get("biochar", {}).get("characterization", {})

    has_carbon_analysis = char.get("standards") or verra.get("has_fc_lab_analysis")
    tech_class    = verra.get("technology_class", "")
    feedstock_cat = verra.get("feedstock_category", "")
    uses_default  = verra.get("uses_fc_default_table4", False)

    # Tabela 4 defaults por categoria
    FC_DEFAULTS = {
        "animal_manure":      0.38,
        "forestry_wood":      0.77,
        "agricultural_residue": 0.65,
        "aquaculture":        0.49,  # similar rice husk
        "food_processing":    0.74,  # similar nut shells
        "recycling_economy":  0.35,  # similar biosolids
        "hcfa":               0.60,  # estimativa conservadora
    }

    notes = []

    if uses_default and feedstock_cat in FC_DEFAULTS:
        fc = FC_DEFAULTS[feedstock_cat]
        notes.append(
            f"FCp default (Tabela 4) para '{feedstock_cat}': {fc:.2f} "
            f"({fc*100:.0f}% C org. por tonelada de biochar seco)."
        )
        notes.append("Default conservador aceito para low-tech ou validação inicial.")
        return _compliant(notes=notes, score=80)

    if has_carbon_analysis:
        notes.append("Análise laboratorial de carbono orgânico documentada.")
        notes.append("Frequência exigida: anual OU após mudança material no feedstock OU após mudança nos parâmetros de produção (o que ocorrer primeiro).")
        return _compliant(notes=notes)

    if tech_class == "low":
        fc_default = FC_DEFAULTS.get(feedstock_cat, 0.55)
        notes.append(
            f"Low-tech sem análise laboratorial: valor default Tabela 4 aplicável = {fc_default:.2f}."
        )
        return _partial(
            gap="Conteúdo de carbono não determinado por laboratório.",
            recommendation=(
                f"Para low-tech: use valor default da Tabela 4 ({fc_default:.2f} para '{feedstock_cat}'). "
                "Para maximizar créditos: realize análise laboratorial conforme IBI/EBC."
            ),
            citation="Seção 9.2 e Tabela 4 — FCp,t,p measured annually or via Table 4 defaults.",
            notes=notes, score=65,
        )

    return _future(
        gap="Conteúdo de carbono orgânico do biochar não determinado.",
        recommendation=(
            "Realize análise laboratorial de FCp (carbono orgânico em base seca) conforme IBI Biochar Testing "
            "Guidelines ou EBC Production Guidelines. Laboratório deve ter acreditação nacional."
        ),
        citation="Seção 9.2 — FCp,t,p: annual lab analysis per IBI or EBC guidelines.",
        notes=notes, score=20,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-MASS-0 — Mass monitoring (Mt,k,p,y) — Seção 9.2
# Pesagem contínua; calibração periódica; cross-check com NF fiscais.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_mass_monitoring_v1(data: dict, audit_mode: str = "development"):
    verra      = data.get("verra", {})
    monitoring = data.get("monitoring", {})

    has_weighing   = verra.get("has_continuous_weighing") or monitoring.get("mass_monitoring")
    has_calibration = verra.get("has_scale_calibration_plan", False)
    has_cross_check = verra.get("has_invoice_cross_check", False)

    notes = []

    if not has_weighing:
        return _future(
            gap="Sistema de pesagem contínua de biochar não documentado.",
            recommendation=(
                "Instale balanças calibradas para pesagem contínua do biochar produzido. "
                "Registre mensalmente por tipo de biochar e via de aplicação (Seção 9.2, Mt,k,p,y)."
            ),
            citation="Seção 9.2 — Mt,k,p,y: continuously recorded monthly; weighing scales adjusted for moisture.",
        )

    notes.append("Sistema de pesagem contínua presente.")

    score = 60
    if has_calibration:
        score += 20
        notes.append("Plano de calibração de balanças documentado.")
    else:
        notes.append("Calibração periódica das balanças não explicitamente documentada.")

    if has_cross_check:
        score += 20
        notes.append("Cross-check com notas fiscais/registros de vendas documentado.")
    else:
        notes.append("Cross-check com notas fiscais não mencionado — recomendado para QA/QC.")

    if score >= 100:
        return _compliant(notes=notes)
    return _partial(
        gap="Sistema de pesagem incompleto (calibração e/ou cross-check faltantes).",
        recommendation="Documente calibração periódica e cross-check anual com notas fiscais conforme Seção 9.2.",
        citation="Seção 9.2 — Calibrate scales; cross-check with sales receipts.",
        notes=notes, score=score,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-PEPS-0 — Process emissions (PEPS,p,y) — Seção 8, Equações 3-9
# High-tech: PEP = 0. Low-tech: PEP = Fe × GWPCH4 × massa.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_process_emissions_v1(data: dict, audit_mode: str = "development"):
    verra      = data.get("verra", {})
    production = data.get("production", {})

    tech_class   = verra.get("technology_class", "")
    has_gas_recov = production.get("has_pyrolysis_gas_recovery") or verra.get("has_gas_recovery")
    fe_measured  = verra.get("methane_emission_factor")
    has_energy_lca = verra.get("has_energy_lca") or _get(data, "carbon_accounting", "leakage") is not None

    notes = []

    if tech_class == "high" or has_gas_recov:
        notes.append(
            "High-tech / recuperação de gás: PEP,p,y = 0 (emissões do processo consideradas de minimis — Equação 3)."
        )
        notes.append(
            "Ainda necessário quantificar: PED (pré-tratamento), PEC (energia auxiliar). "
            "Use CDM TOOL03 e TOOL05."
        )
        return _compliant(notes=notes) if has_energy_lca else _partial(
            gap="PEP = 0 (high-tech) mas emissões de pré-tratamento (PED) e energia auxiliar (PEC) não quantificadas.",
            recommendation="Quantifique PED e PEC usando CDM TOOL03 (combustíveis fósseis) e TOOL05 (eletricidade de grid). Mesmo sem emissões do forno, esses componentes entram no PEPS.",
            citation="Equação 3 — PEPS,p,y = PED + PEP + PEC.",
            notes=notes, score=65,
        )

    if tech_class == "low" or (fe_measured is None and not has_gas_recov):
        fe = fe_measured or FE_LOW_TECH_DEFAULT
        notes.append(
            f"Low-tech: Fe = {fe} tCH4/t biochar (Cornelissen et al. 2016). "
            f"PEP,p,y = {fe} × {GWPCH4} × massa_biochar = {fe*GWPCH4:.3f} tCO2e/t biochar."
        )
        notes.append(
            f"Impacto prático: para cada 1.000 t de biochar, ~{fe*GWPCH4*1000:.0f} tCO2e de penalidade de emissão de processo."
        )

        if fe_measured:
            notes.append(f"Fator Fe medido ({fe_measured}) — mais preciso que default.")
            return _compliant(notes=notes, score=85)

        return _partial(
            gap=f"Emissão de CH₄ do processo usando default {FE_LOW_TECH_DEFAULT} tCH4/t — mensurável.",
            recommendation=(
                f"Para reduzir penalidade: meça Fe em campo ou literatura específica para seu tipo de forno. "
                f"Pode ser menor que o default {FE_LOW_TECH_DEFAULT}, aumentando créditos líquidos."
            ),
            citation="Equação 9 — PEP,p,y = Fe × GWPCH4 × Mt,k,p,y; Fe default = 0.049.",
            notes=notes, score=65,
        )

    # Tech não especificada
    return _future(
        gap="Classificação tecnológica não determinada — não é possível calcular PEPS,p,y.",
        recommendation="Classifique a instalação como high-tech ou low-tech e documente o cálculo de emissões de processo conforme Seção 8.",
        citation="Seção 8 — Equações 3 (high-tech) e 7-9 (low-tech).",
        notes=notes, score=25,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-LEAK-0 — Leakage (LEy) — Seção 8, Equação 13
# LEy ≈ 0 se transporte < 200 km. CDM TOOL12 se > 200 km.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_leakage_v1(data: dict, audit_mode: str = "development"):
    verra      = data.get("verra", {})
    carbon_acc = data.get("carbon_accounting", {})

    transport_km = verra.get("transport_distance_km")
    has_leakage  = carbon_acc.get("leakage")

    notes = []

    if transport_km is not None and transport_km <= TRANSPORT_LEAKAGE_KM:
        notes.append(
            f"Distância de transporte: {transport_km:.0f} km ≤ {TRANSPORT_LEAKAGE_KM} km → LEts,y = LEtap,y = 0."
        )
        notes.append(
            "LEas,y = 0 (feedstock resíduo — não há activity shift). "
            "LEbd,y = 0 (apenas biomassa residual). Total LEy = 0."
        )
        return _compliant(notes=notes)

    if transport_km is not None and transport_km > TRANSPORT_LEAKAGE_KM:
        notes.append(
            f"Distância de transporte: {transport_km:.0f} km > {TRANSPORT_LEAKAGE_KM} km → "
            "CDM TOOL12 obrigatório para LEts,y e/ou LEtap,y."
        )
        if has_leakage:
            notes.append("Avaliação de leakage presente no PDD.")
            return _compliant(notes=notes, score=90)
        return _partial(
            gap=f"Transporte > {TRANSPORT_LEAKAGE_KM} km sem quantificação via CDM TOOL12.",
            recommendation="Aplique CDM TOOL12 para calcular leakage de transporte (LEts,y + LEtap,y). Disponível em cdm.unfccc.int.",
            citation="Seção 8, Equação 13 — LEts,y e LEtap,y via CDM TOOL12 se distância > 200 km.",
            notes=notes, score=50,
        )

    # Distância não informada
    if has_leakage:
        notes.append("Avaliação de leakage documentada.")
        return _compliant(notes=notes, score=85)

    return _future(
        gap="Distância de transporte não informada — não é possível determinar se LEy = 0.",
        recommendation=(
            f"Informe distância de transporte (feedstock → produção + produção → aplicação). "
            f"Se ≤ {TRANSPORT_LEAKAGE_KM} km: LEy = 0. Se > {TRANSPORT_LEAKAGE_KM} km: aplicar CDM TOOL12."
        ),
        citation="Equação 13 — LEy = LEas + LEbd + LEts + LEtap.",
        notes=notes, score=30,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-APPL-E — Application stage emissions (PEAS,y)
# Tipicamente negligíveis (Eap = 0). Apenas transporte e processamento.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_application_emissions_v1(data: dict, audit_mode: str = "development"):
    verra = data.get("verra", {})

    has_appl_energy = verra.get("has_application_energy_use")
    notes = [
        "PEAS,y: emissões da fase de aplicação. "
        "Eap,k,y (utilização do biochar) = 0 por convenção — negligíveis (Seção 8)."
    ]

    if has_appl_energy:
        notes.append("Uso de energia elétrica/combustível no processamento de biochar para aplicação documentado — calcule via CDM TOOL05/TOOL03.")
        return _partial(
            gap="Emissões de processamento para aplicação (EP,k,y) identificadas mas não quantificadas.",
            recommendation="Calcule EP,k,y = PEPE (eletricidade) + PEPF (combustíveis fósseis) via CDM TOOL05/TOOL03.",
            citation="Equações 11-12 — PEAS,y = EP + Eap.",
            notes=notes, score=60,
        )

    notes.append("Emissões na aplicação consideradas negligíveis — PEAS,y ≈ 0.")
    return _compliant(notes=notes)


# ══════════════════════════════════════════════════════════════════════════════
# V-QUAL-0 — Biochar quality (IBI/EBC)
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_biochar_quality_v1(data: dict, audit_mode: str = "development"):
    char  = data.get("biochar", {}).get("characterization", {})
    verra = data.get("verra", {})

    quality_std = char.get("quality_standard", "")
    has_ibi     = quality_std in ("ibi", "IBI") or verra.get("has_ibi_certification", False)
    has_ebc     = quality_std in ("ebc", "EBC") or verra.get("has_ebc_certification", False)
    has_testing = char.get("standards") or verra.get("has_quality_testing")

    notes = []

    if has_ibi or has_ebc:
        std = "IBI" if has_ibi else "EBC"
        notes.append(f"Conformidade com {std} Biochar Testing Guidelines documentada.")
        return _compliant(notes=notes)

    if has_testing:
        notes.append("Testes de caracterização presentes mas alinhamento com IBI/EBC não explícito.")
        return _partial(
            gap="Testes de qualidade realizados mas não explicitamente alinhados com IBI ou EBC.",
            recommendation="Declare explicitamente conformidade com IBI Biochar Testing Guidelines ou EBC Production Guidelines conforme AC 5-6 do VM0044.",
            citation="AC 5-6 — Biochar must comply with IBI Testing Guidelines or EBC Production Guidelines.",
            notes=notes, score=65,
        )

    return _future(
        gap="Testes de qualidade do biochar conforme IBI/EBC não encontrados.",
        recommendation="Realize análise de caracterização do biochar conforme IBI Biochar Testing Guidelines (para aplicação em solo) ou EBC Production Guidelines e documente no PDD.",
        citation="AC 5-6.",
        notes=notes, score=15,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-CONT-0 — Contaminants (metais pesados, PAH per IBI/EBC)
# Limites determinados pelos guidelines, não pelo VM0044 diretamente.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_contaminants_v1(data: dict, audit_mode: str = "development"):
    char  = data.get("biochar", {}).get("characterization", {})

    pah_value = char.get("pah_mg_kg")
    pcb_value = char.get("pcb_mg_kg")
    heavy_metals = char.get("heavy_metals_documented", False)

    # Limites IBI Biochar Standard para aplicação em solo (categoria "premium")
    PAH_IBI_PREMIUM = 6    # mg/kg
    PAH_IBI_BASIC   = 20   # mg/kg
    PCB_IBI         = 0.5  # mg/kg

    notes = []

    if pah_value is not None:
        if pah_value <= PAH_IBI_PREMIUM:
            notes.append(f"PAH = {pah_value} mg/kg — abaixo do limite IBI Premium ({PAH_IBI_PREMIUM} mg/kg).")
        elif pah_value <= PAH_IBI_BASIC:
            notes.append(f"PAH = {pah_value} mg/kg — entre limites IBI Basic e Premium.")
        else:
            return _non_compliant(
                gap=f"PAH = {pah_value} mg/kg excede o limite IBI Basic de {PAH_IBI_BASIC} mg/kg.",
                recommendation="Biochar não elegível com este nível de PAH. Ajuste processo (temperatura, feedstock) para reduzir PAH.",
                citation="AC 5-6 — Biochar must comply with IBI Testing Guidelines (PAH ≤ 20 mg/kg para IBI Basic).",
            )

    if pcb_value is not None and pcb_value > PCB_IBI:
        return _non_compliant(
            gap=f"PCB = {pcb_value} mg/kg excede limite IBI de {PCB_IBI} mg/kg.",
            recommendation="Verifique feedstock para contaminação por PCB. Biochar inelegível com este nível.",
            citation="AC 5-6 — IBI Testing Guidelines.",
        )

    score = 0
    if pah_value is not None:
        score += 50
    else:
        notes.append("PAH não reportado — obrigatório para elegibilidade.")

    if heavy_metals:
        score += 30
        notes.append("Metais pesados documentados.")
    else:
        notes.append("Análise de metais pesados não documentada.")

    if pcb_value is not None:
        score += 20
        notes.append(f"PCB = {pcb_value} mg/kg documentado.")

    if score >= 80:
        return _compliant(notes=notes, score=score)
    if score >= 40:
        return _partial(
            gap="Caracterização de contaminantes incompleta.",
            recommendation="Complete análise de PAH, PCB e metais pesados conforme IBI Biochar Testing Guidelines.",
            citation="AC 5-6.",
            notes=notes, score=score,
        )
    return _future(
        gap="Contaminantes não analisados.",
        recommendation="Análise de PAH, PCB e metais pesados obrigatória conforme IBI/EBC para elegibilidade VM0044.",
        citation="AC 5-6.",
        notes=notes, score=score,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-MINE-0 — Mineral additives ≤ 10% (AC 7)
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_mineral_additives_v1(data: dict, audit_mode: str = "development"):
    verra = data.get("verra", {})
    mineral_fraction = verra.get("mineral_additive_fraction")
    has_additive_test = verra.get("has_mineral_additive_testing", False)

    if mineral_fraction is None:
        return _compliant(
            notes=["Aditivos minerais não reportados — sem evidência de uso."],
            score=80,
        )

    if mineral_fraction > MINERAL_ADDITIVE_MAX_FRACTION:
        return _non_compliant(
            gap=f"Aditivos minerais: {mineral_fraction*100:.1f}% — excede limite de {MINERAL_ADDITIVE_MAX_FRACTION*100:.0f}%.",
            recommendation="Reduza aditivos minerais (calcário, minerais de rocha, cinzas) para ≤ 10% em massa, ou realize testes de contaminantes no material final.",
            citation="AC 7 — Mineral additives ≤ 10% by mass; if > 10%, must meet contaminant testing.",
        )

    notes = [
        f"Aditivos minerais: {mineral_fraction*100:.1f}% — dentro do limite de {MINERAL_ADDITIVE_MAX_FRACTION*100:.0f}%."
    ]
    if not has_additive_test and mineral_fraction > 0:
        notes.append("Teste de contaminantes no material final com aditivos não documentado.")
    return _compliant(notes=notes)


# ══════════════════════════════════════════════════════════════════════════════
# V-MONI-0 — Monitoring plan (Seção 9)
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_monitoring_plan_v1(data: dict, audit_mode: str = "development"):
    monitoring = data.get("monitoring", {})
    verra      = data.get("verra", {})

    has_param_table  = monitoring.get("parameters") or monitoring.get("monitoring_plan")
    has_freq_defined = verra.get("has_monitoring_frequencies")
    has_qaqc         = verra.get("has_qaqc_procedures")

    notes = []
    score = 0

    if has_param_table:
        score += 40
        notes.append("Tabela de parâmetros de monitoramento presente.")
    else:
        notes.append("Tabela de parâmetros de monitoramento ausente.")

    if has_freq_defined:
        score += 30
        notes.append("Frequências de monitoramento definidas.")
    else:
        notes.append("Frequências de monitoramento não explicitadas.")

    if has_qaqc:
        score += 30
        notes.append("Procedimentos QA/QC documentados.")
    else:
        notes.append("QA/QC não documentado.")

    required_params = [
        "Mp,y (massa total de biochar — contínua, agregada mensalmente)",
        "FCp,t,p (carbono orgânico — anual ou por mudança de parâmetro)",
        "Tprod (temperatura de pirólise — contínua, agregada anualmente)",
        "H:Corg (por lote — para aplicação em solo)",
        "Tipos e quantidades de feedstock (contínuo, mensal)",
    ]
    notes.append("Parâmetros obrigatórios conforme Seção 9.2: " + "; ".join(required_params))

    if score >= 80:
        return _compliant(notes=notes, score=score)
    if score >= 40:
        return _partial(
            gap="Plano de monitoramento incompleto.",
            recommendation="Complete o plano incluindo todos os parâmetros da Seção 9.2 com frequências e QA/QC.",
            citation="Seção 9 — Monitoring requirements.",
            notes=notes, score=score,
        )
    return _future(
        gap="Plano de monitoramento não encontrado.",
        recommendation="Elabore plano de monitoramento conforme Seção 9 do VM0044.",
        citation="Seção 9.",
        notes=notes, score=score,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-TRCK-0 — Chain of custody (Seção 9.3)
# Rastreabilidade do feedstock até o ponto de aplicação.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_chain_of_custody_v1(data: dict, audit_mode: str = "development"):
    verra = data.get("verra", {})
    monitoring = data.get("monitoring", {})

    has_tracking = (
        verra.get("has_chain_of_custody") or
        verra.get("has_tracking_system") or
        monitoring.get("data_storage")
    )
    tracking_tool = verra.get("tracking_tool", "")

    VALID_TOOLS = {"qr_code", "gps", "mobile_app", "blockchain", "nft", "tracking_software", "records"}

    notes = []

    if not has_tracking:
        return _future(
            gap="Sistema de rastreabilidade feedstock → aplicação não documentado.",
            recommendation=(
                "Implemente sistema de rastreabilidade conforme Seção 9.3. "
                "Ferramentas aceitas: QR code, GPS, app mobile/desktop, blockchain, NFT, "
                "ou qualquer software que gere registro de custódia do sourcing até a aplicação."
            ),
            citation="Seção 9.3 — Chain of custody from sourcing stage to end-use application.",
        )

    notes.append("Sistema de rastreabilidade documentado.")
    if tracking_tool and tracking_tool in VALID_TOOLS:
        notes.append(f"Ferramenta de rastreabilidade: {tracking_tool}.")
    return _compliant(notes=notes)


# ══════════════════════════════════════════════════════════════════════════════
# V-GEOG-0 — Geographic information (Seção 9.3)
# Coordenadas geodésicas do local de aplicação.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_geographic_info_v1(data: dict, audit_mode: str = "development"):
    verra      = data.get("verra", {})
    project    = data.get("project", {})

    has_coordinates = (
        verra.get("has_application_coordinates") or
        (project.get("locations") and len(project.get("locations", [])) > 0)
    )
    has_additional_geo = verra.get("has_additional_geographic_info", False)

    notes = []

    if not has_coordinates:
        return _future(
            gap="Coordenadas geodésicas do local de aplicação do biochar não documentadas.",
            recommendation=(
                "Forneça pelo menos uma coordenada geodésica por local de aplicação, "
                "com informações geográficas adicionais suficientes para permitir amostragem pelo VVB. "
                "Exigido pela Seção 9.3 para evitar dupla contagem."
            ),
            citation="Seção 9.3 — Geographic information: at least one geodetic coordinate per application instance.",
        )

    notes.append("Coordenadas de aplicação do biochar documentadas.")
    if has_additional_geo:
        notes.append("Informações geográficas adicionais para amostragem pelo VVB presentes.")
    return _compliant(notes=notes)


# ══════════════════════════════════════════════════════════════════════════════
# V-DATA-0 — Data management (Seção 9.3)
# Backup eletrônico offsite; retenção mínima 2 anos pós-período de crédito.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_data_management_v1(data: dict, audit_mode: str = "development"):
    monitoring  = data.get("monitoring", {})
    verra       = data.get("verra", {})

    has_storage      = monitoring.get("data_storage") or monitoring.get("record_keeping")
    has_offsite_backup = verra.get("has_offsite_backup", False)
    retention_years  = _get(data, "monitoring", "data_retention_years") or verra.get("data_retention_years")

    DATA_RETENTION_MIN = 2  # anos pós-período de crédito

    notes = []
    score = 0

    if has_storage:
        score += 40
        notes.append("Sistema de armazenamento de dados documentado.")

    if has_offsite_backup:
        score += 30
        notes.append("Backup eletrônico offsite documentado.")
    else:
        notes.append("Backup offsite não explicitamente mencionado — obrigatório (Seção 9.3).")

    if retention_years is not None:
        if retention_years >= DATA_RETENTION_MIN:
            score += 30
            notes.append(f"Retenção de dados: {retention_years} anos — atende mínimo de {DATA_RETENTION_MIN} anos.")
        else:
            notes.append(f"Retenção declarada: {retention_years} anos — abaixo do mínimo de {DATA_RETENTION_MIN} anos.")
    else:
        notes.append(f"Período de retenção de dados não especificado (mínimo: {DATA_RETENTION_MIN} anos pós-crédito).")

    if score >= 80:
        return _compliant(notes=notes, score=score)
    if score >= 40:
        return _partial(
            gap="Gestão de dados incompleta (backup offsite e/ou retenção não documentados).",
            recommendation=f"Documente backup offsite eletrônico e período de retenção ≥ {DATA_RETENTION_MIN} anos após o fim do período de crédito (Seção 9.3).",
            citation="Seção 9.3 — Offsite electronic backup; documents stored for at least 2 years after crediting period.",
            notes=notes, score=score,
        )
    return _future(
        gap="Plano de gestão de dados não encontrado.",
        recommendation="Elabore plano conforme Seção 9.3 do VM0044.",
        citation="Seção 9.3.",
        notes=notes, score=score,
    )


# ══════════════════════════════════════════════════════════════════════════════
# V-REVR-0 — Reversal risk (Seção 8.4)
# VM0044 considera risco de reversão negligível para solo — sem buffer próprio.
# Buffer determinado pelo VCS Standard com base no non-permanence risk tool.
# ══════════════════════════════════════════════════════════════════════════════

def eval_verra_reversal_risk_v1(data: dict, audit_mode: str = "development"):
    verra   = data.get("verra", {})
    storage = data.get("storage", {})

    storage_path     = storage.get("pathway", "soil")
    has_risk_assess  = verra.get("has_reversal_risk_assessment") or _get(data, "permanence", "reversal_risk")
    has_natural_mit  = verra.get("has_natural_risk_mitigation")
    has_non_nat_mit  = verra.get("has_non_natural_risk_mitigation")

    notes = [
        "VM0044 Seção 8.4: risco de reversão considerado negligível após aplicação do biochar.",
        "Biochar incorporado ao solo é independente de atividades anuais — não está sujeito a reversões típicas (incêndio de floresta, morte de planta).",
    ]

    if storage_path == "soil":
        notes.append(
            "Buffer pool determinado pelo VCS Standard (non-permanence risk tool) — "
            "tipicamente baixo para biochar em solo (risco Category 1 ou 2)."
        )

    if has_risk_assess:
        notes.append("Avaliação de risco de reversão documentada.")
        return _compliant(notes=notes)

    if storage_path in ("built_environment", "construction"):
        notes.append(
            "Para construção civil: risco de reversão existe se estrutura for demolida e biochar incinerado. "
            "Documente mitigações (ex.: regulamentação municipal de demolição, rastreabilidade)."
        )
        return _partial(
            gap="Aplicação não-solo sem avaliação de risco de reversão ao fim da vida útil.",
            recommendation="Documente como o biochar será tratado ao fim da vida da estrutura (demolição). Evidencie que não será incinerado.",
            citation="Seção 8.4 — Reversal risk mitigation for non-soil applications.",
            notes=notes, score=55,
        )

    return _compliant(notes=notes, score=80)
