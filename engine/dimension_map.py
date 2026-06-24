"""
Co2mply — Mapeamento de requisitos para dimensões universais comparáveis.

6 dimensões com pesos fixos permitem comparar scores entre metodologias:
qualquer projeto recebe o mesmo framework de avaliação,
independente do número de requisitos de cada padrão.
"""

# ── Dimensões universais ──────────────────────────────────────────────────────

UNIVERSAL_DIMENSIONS = {
    "feedstock_eligibility": {
        "label":   "Elegibilidade do Feedstock",
        "weight":  0.20,
        "description": "Origem e sustentabilidade da biomassa, proibições específicas",
    },
    "carbon_accounting": {
        "label":   "Contabilidade de Carbono",
        "weight":  0.25,
        "description": "LCA, linha de base, leakage, incerteza, fronteiras do sistema",
    },
    "additionality": {
        "label":   "Adicionalidade",
        "weight":  0.20,
        "description": "Financeira, regulatória, prática comum, ambiental",
    },
    "permanence": {
        "label":   "Permanência",
        "weight":  0.15,
        "description": "Durabilidade, temperatura do solo, buffer pool",
    },
    "monitoring": {
        "label":   "Monitoramento & Verificação",
        "weight":  0.10,
        "description": "Amostragem, laboratório, parâmetros, caracterização do biochar",
    },
    "environmental_social": {
        "label":   "Ambiental & Social",
        "weight":  0.10,
        "description": "PAH, stakeholders, SDG, salvaguardas, gestão adaptativa",
    },
}

# ── Mapeamento Isometric (R-XXXX → dimensão) ─────────────────────────────────

ISOMETRIC_DIMENSION_MAP = {
    # feedstock_eligibility
    "R-NK7R-0": "feedstock_eligibility",  # protocol eligibility
    "R-M858-0": "feedstock_eligibility",  # ownership
    "R-7X0X-0": "feedstock_eligibility",  # technical description
    "R-F6R7-0": "feedstock_eligibility",  # participants
    "R-A5B6-0": "feedstock_eligibility",  # location
    "R-XT6V-0": "feedstock_eligibility",  # net removal capacity

    # carbon_accounting
    "R-VHWJ-0": "carbon_accounting",   # system boundary
    "R-2VKW-0": "carbon_accounting",   # GHG sources
    "R-TGBM-0": "carbon_accounting",   # GHG statement
    "R-PGFH-0": "carbon_accounting",   # baseline
    "R-HF2G-0": "carbon_accounting",   # leakage
    "R-K6MA-0": "carbon_accounting",   # uncertainty method
    "R-Z106-0": "carbon_accounting",   # uncertainty analysis
    "R-NZQ2-0": "carbon_accounting",   # models
    "R-2AVD-0": "carbon_accounting",   # sensitivity analysis
    "R-GYA1-0": "carbon_accounting",   # data collection

    # additionality
    "R-53Y5-0": "additionality",   # financial
    "R-RRST-0": "additionality",   # common practice
    "R-CDNF-0": "additionality",   # environmental (net negative)
    "R-983D-0": "additionality",   # regulatory
    "R-KQCS-0": "additionality",   # regulatory compliance ongoing

    # permanence
    "R-7C8E-0": "permanence",  # durability selection
    "R-1T2Y-0": "permanence",  # durability demonstration
    "R-F5RZ-0": "permanence",  # soil temp method
    "R-V143-0": "permanence",  # reversal risk

    # monitoring
    "R-ENZR-0": "monitoring",  # monitoring table
    "R-S8K1-1": "monitoring",  # sampling procedure
    "R-CXEP-0": "monitoring",  # characterization standards
    "R-7W1N-0": "monitoring",  # physical properties
    "R-VGXA-0": "monitoring",  # chemical properties
    "R-2TMM-0": "monitoring",  # laboratory

    # environmental_social
    "R-9MJQ-0": "environmental_social",  # env compliance
    "R-X9EC-0": "environmental_social",  # impact assessment
    "R-4K5P-0": "environmental_social",  # no net env harm
    "R-R81B-0": "environmental_social",  # no net social harm
    "R-5KQC-0": "environmental_social",  # soil quality monitoring
    "R-BWX0-0": "environmental_social",  # SDG alignment
    "R-6VFZ-0": "environmental_social",  # closure plan
    "R-BC4H-0": "environmental_social",  # adaptive management
    "R-MY64-0": "environmental_social",  # pollution prevention
    "R-M760-0": "environmental_social",  # baseline soil samples
    "R-1YC3-0": "environmental_social",  # co-benefits
    "R-ZHRN-0": "environmental_social",  # stakeholder consultation
    "R-E579-0": "environmental_social",  # grievance
    "R-6AQG-0": "environmental_social",  # reactor diagram (appendix)
    "R-SZK5-0": "environmental_social",  # gas sensors
    "R-DMET-0": "environmental_social",  # material selection
    "R-19AF-0": "environmental_social",  # maintenance
}

# ── Mapeamento Puro.Earth (P-XXXX → dimensão) ────────────────────────────────

PURO_DIMENSION_MAP = {
    # feedstock_eligibility
    "P-PROT-0": "feedstock_eligibility",
    "P-OWNR-0": "feedstock_eligibility",
    "P-TECH-0": "feedstock_eligibility",
    "P-PART-0": "feedstock_eligibility",
    "P-GEOS-0": "feedstock_eligibility",
    "P-NETC-0": "feedstock_eligibility",
    "P-FELI-0": "feedstock_eligibility",
    "P-FFOR-0": "feedstock_eligibility",
    "P-FLAN-0": "feedstock_eligibility",
    "P-QUAL-0": "feedstock_eligibility",
    "P-NONS-0": "feedstock_eligibility",

    # carbon_accounting
    "P-BOUN-0": "carbon_accounting",
    "P-GHGS-0": "carbon_accounting",
    "P-BASE-0": "carbon_accounting",
    "P-LEAK-0": "carbon_accounting",
    "P-UNCR-0": "carbon_accounting",
    "P-MODL-0": "carbon_accounting",

    # additionality
    "P-FADD-0": "additionality",
    "P-CADD-0": "additionality",
    "P-NADD-0": "additionality",
    "P-RADD-0": "additionality",

    # permanence
    "P-DSEL-0": "permanence",
    "P-DDEM-0": "permanence",
    "P-STMP-0": "permanence",
    "P-RREV-0": "permanence",

    # monitoring
    "P-DATA-0": "monitoring",
    "P-MPRT-0": "monitoring",
    "P-SPRP-0": "monitoring",
    "P-CHAR-0": "monitoring",
    "P-CHEM-0": "monitoring",
    "P-PHYS-0": "monitoring",
    "P-LABN-0": "monitoring",
    "P-RDES-0": "monitoring",
    "P-GSEN-0": "monitoring",
    "P-RMAT-0": "monitoring",
    "P-RMNT-0": "monitoring",

    # environmental_social
    "P-ENVC-0": "environmental_social",
    "P-EISA-0": "environmental_social",
    "P-NNEH-0": "environmental_social",
    "P-NNSH-0": "environmental_social",
    "P-PLUT-0": "environmental_social",
    "P-ADPT-0": "environmental_social",
    "P-SOIL-0": "environmental_social",
    "P-AGPM-0": "environmental_social",
    "P-COBP-0": "environmental_social",
    "P-STKS-0": "environmental_social",
    "P-GRVN-0": "environmental_social",
    "P-ALIGN-0": "environmental_social",
    "P-CLOS-0": "environmental_social",
}

# ── Mapeamento Verra VCS (V-XXXX → dimensão) ─────────────────────────────────

VERRA_DIMENSION_MAP = {
    # feedstock_eligibility
    "V-APPL-0": "feedstock_eligibility",   # applicability / greenfield scope
    "V-FEED-0": "feedstock_eligibility",   # feedstock waste biogenic, non-imported
    "V-FCAT-0": "feedstock_eligibility",   # feedstock category (Table 1)
    "V-TECH-0": "feedstock_eligibility",   # technology class (high/low)
    "V-HCOR-0": "feedstock_eligibility",   # H:Corg ≤ 0.7 gate (soil)
    "V-APPL-S": "feedstock_eligibility",   # application type eligibility

    # carbon_accounting
    "V-BASE-0": "carbon_accounting",       # baseline scenario (ERSS,y = 0)
    "V-BFED-0": "carbon_accounting",       # baseline feedstock fate evidence
    "V-CARB-0": "carbon_accounting",       # carbon content FCp,t,p
    "V-PEPS-0": "carbon_accounting",       # process emissions
    "V-LEAK-0": "carbon_accounting",       # leakage (transport threshold)
    "V-APPL-E": "carbon_accounting",       # application stage emissions

    # additionality
    "V-REGS-0": "additionality",           # regulatory surplus (Step 1)
    "V-PLST-0": "additionality",           # positive list (Step 2)
    "V-VT08-0": "additionality",           # VT0008 investment analysis (Step 3)

    # permanence
    "V-PERM-0": "permanence",              # PRde,k by pyrolysis temperature
    "V-TEMP-0": "permanence",              # temperature monitoring
    "V-REVR-0": "permanence",              # reversal risk

    # monitoring
    "V-MASS-0": "monitoring",              # mass monitoring
    "V-MONI-0": "monitoring",              # monitoring plan
    "V-TRCK-0": "monitoring",              # chain of custody
    "V-GEOG-0": "monitoring",              # geographic information
    "V-DATA-0": "monitoring",              # data management

    # environmental_social (biochar quality → environmental gate)
    "V-QUAL-0": "environmental_social",    # IBI/EBC quality compliance
    "V-CONT-0": "environmental_social",    # contaminants (PAH, heavy metals)
    "V-MINE-0": "environmental_social",    # mineral additives ≤ 10%
}

# Registry por metodologia
DIMENSION_MAPS = {
    "isometric":  ISOMETRIC_DIMENSION_MAP,
    "puro_earth": PURO_DIMENSION_MAP,
    "verra_vcs":  VERRA_DIMENSION_MAP,
}


def compute_dimension_scores(
    results: list,
    methodology_key: str,
) -> dict[str, float]:
    """
    Calcula score por dimensão universal a partir dos resultados de requisitos.
    Retorna {dimension_key: score_0_100}.
    """
    dim_map = DIMENSION_MAPS.get(methodology_key, {})
    dim_scores: dict[str, list] = {d: [] for d in UNIVERSAL_DIMENSIONS}

    for r in results:
        req_id = r.get("requirement_id", "")
        status = r.get("status", "")
        score  = r.get("requirement_score")

        if status == "not_applicable":
            continue  # não penaliza

        dim = dim_map.get(req_id)
        if not dim:
            continue

        if score is not None:
            dim_scores[dim].append(float(score))
        else:
            # Fallback: status → score
            fallback = {
                "compliant":                 100,
                "partial":                    55,
                "future_evidence_required":   45,
                "non_compliant":               0,
            }
            dim_scores[dim].append(fallback.get(status, 50))

    return {
        dim: round(sum(scores) / len(scores), 1) if scores else None
        for dim, scores in dim_scores.items()
    }


def compute_weighted_score(dimension_scores: dict[str, float]) -> float:
    """Score geral ponderado pelas dimensões universais."""
    total_weight = 0.0
    weighted_sum = 0.0
    for dim, cfg in UNIVERSAL_DIMENSIONS.items():
        score = dimension_scores.get(dim)
        if score is not None:
            w = cfg["weight"]
            weighted_sum  += score * w
            total_weight  += w
    return round(weighted_sum / total_weight, 1) if total_weight > 0 else 0.0
