"""
Co2mply — RAG (Red/Amber/Green) por parâmetro para o Fit Metodológico.

Agrupa requisitos individuais (R-XXXX / P-XXXX) em parâmetros de alto nível
equivalentes aos usados no Sylvera Biochar Methodology Assessment (2025).

RAG thresholds:
  Green (baixo risco):   score médio ≥ 80%
  Amber (risco médio):   score médio 55–79%
  Red   (alto risco):    score médio < 55%
  N/A:                   todos os requisitos not_applicable
"""

from __future__ import annotations

# ── Parâmetros por pilar (alinhados ao Sylvera) ───────────────────────────────

RAG_PARAMETERS: dict = {

    "carbon_accounting": {
        "label": "Contabilidade de Carbono",
        "parameters": [
            {
                "id":   "gross_removal",
                "name": "Gross removal quantification",
                "desc": "Remoção bruta mensurada via modelo validado",
                "req_ids": {
                    "isometric":  ["R-XT6V-0", "R-TGBM-0"],
                    "puro_earth": ["P-NETC-0", "P-GHGS-0"],
                },
            },
            {
                "id":   "baseline",
                "name": "Baseline credibility",
                "desc": "Cenário de referência conservador e evidenciado",
                "req_ids": {
                    "isometric":  ["R-PGFH-0"],
                    "puro_earth": ["P-BASE-0"],
                },
            },
            {
                "id":   "leakage",
                "name": "Leakage assessment",
                "desc": "Emissões fora da fronteira quantificadas",
                "req_ids": {
                    "isometric":  ["R-HF2G-0"],
                    "puro_earth": ["P-LEAK-0"],
                },
            },
            {
                "id":   "lca_quality",
                "name": "LCA quality & boundary",
                "desc": "LCA completa com boundary e fontes de GHG definidos",
                "req_ids": {
                    "isometric":  ["R-VHWJ-0", "R-2VKW-0"],
                    "puro_earth": ["P-BOUN-0", "P-MODL-0"],
                },
            },
            {
                "id":   "uncertainty",
                "name": "Uncertainty & sensitivity analysis",
                "desc": "Análise de incerteza e sensibilidade documentada",
                "req_ids": {
                    "isometric":  ["R-K6MA-0", "R-Z106-0", "R-2AVD-0"],
                    "puro_earth": ["P-UNCR-0"],
                },
            },
        ],
    },

    "additionality": {
        "label": "Adicionalidade",
        "parameters": [
            {
                "id":   "financial_add",
                "name": "Financial additionality",
                "desc": "Projeto não viável economicamente sem receita de carbono",
                "req_ids": {
                    "isometric":  ["R-53Y5-0"],
                    "puro_earth": ["P-FADD-0"],
                },
                "methodology_note": {
                    "puro_earth": "First-of-its-kind NÃO isento (Clar. 005 ADD)",
                    "isometric":  "Mais flexível na interpretação",
                },
            },
            {
                "id":   "regulatory_surplus",
                "name": "Policy & regulatory surplus",
                "desc": "Projeto não exigido por lei ou regulação existente",
                "req_ids": {
                    "isometric":  ["R-983D-0", "R-KQCS-0"],
                    "puro_earth": ["P-RADD-0", "P-ENVC-0"],
                },
            },
            {
                "id":   "common_practice",
                "name": "Common practice",
                "desc": "Atividades similares não são prática comum",
                "req_ids": {
                    "isometric":  ["R-RRST-0"],
                    "puro_earth": ["P-CADD-0"],
                },
            },
            {
                "id":   "env_additionality",
                "name": "Environmental additionality (net negative)",
                "desc": "Impacto líquido negativo após todas as emissões",
                "req_ids": {
                    "isometric":  ["R-CDNF-0"],
                    "puro_earth": ["P-NADD-0"],
                },
            },
        ],
    },

    "permanence": {
        "label": "Permanência",
        "parameters": [
            {
                "id":   "durability_selection",
                "name": "Durability threshold & model",
                "desc": "Limiar de durabilidade selecionado (200 ou 1000 anos)",
                "req_ids": {
                    "isometric":  ["R-7C8E-0"],
                    "puro_earth": ["P-DSEL-0"],
                },
            },
            {
                "id":   "durability_demo",
                "name": "Durability demonstrated (H/Corg, O/Corg)",
                "desc": "H/Corg < 0.5 e O/Corg < 0.2 confirmados em lab",
                "req_ids": {
                    "isometric":  ["R-1T2Y-0", "R-F5RZ-0"],
                    "puro_earth": ["P-DDEM-0", "P-STMP-0"],
                },
            },
            {
                "id":   "reversal_risk",
                "name": "Reversal risk & buffer pool",
                "desc": "Avaliação de risco de reversão e buffer pool calculado",
                "req_ids": {
                    "isometric":  ["R-V143-0"],
                    "puro_earth": ["P-RREV-0"],
                },
            },
        ],
    },

    "environmental_social": {
        "label": "Salvaguardas e Co-benefícios",
        "parameters": [
            {
                "id":   "pollution",
                "name": "Pollution prevention (PAH/metals/PCB/PCDD-F)",
                "desc": "Contaminantes dentro dos limites WBC/IBI/EBC",
                "req_ids": {
                    "isometric":  ["R-MY64-0"],
                    "puro_earth": ["P-PLUT-0", "P-QUAL-0"],
                },
            },
            {
                "id":   "community",
                "name": "Community safeguarding",
                "desc": "Consulta pública e mecanismo de grievance",
                "req_ids": {
                    "isometric":  ["R-ZHRN-0", "R-E579-0"],
                    "puro_earth": ["P-STKS-0", "P-GRVN-0"],
                },
            },
            {
                "id":   "env_impact",
                "name": "Environmental safeguarding",
                "desc": "Do no net harm — biodiversidade e ecossistemas",
                "req_ids": {
                    "isometric":  ["R-9MJQ-0", "R-4K5P-0", "R-X9EC-0"],
                    "puro_earth": ["P-ENVC-0", "P-NNEH-0", "P-EISA-0"],
                },
            },
            {
                "id":   "sdg",
                "name": "Sustainable Development Goals (SDGs)",
                "desc": "Alinhamento e reporte de ODS",
                "req_ids": {
                    "isometric":  ["R-BWX0-0"],
                    "puro_earth": ["P-ALIGN-0"],
                },
                "methodology_note": {
                    "puro_earth": "SDG report OBRIGATÓRIO — template Puro deve ser submetido",
                    "isometric":  "ODS mencionado em salvaguardas, não é entregável separado",
                },
            },
        ],
    },

    "monitoring": {
        "label": "Monitoramento & Verificação",
        "parameters": [
            {
                "id":   "monitoring_plan",
                "name": "Monitoring parameter table",
                "desc": "Tabela de parâmetros com frequência e QA/QC",
                "req_ids": {
                    "isometric":  ["R-ENZR-0", "R-GYA1-0"],
                    "puro_earth": ["P-MPRT-0", "P-DATA-0"],
                },
            },
            {
                "id":   "sampling",
                "name": "Sampling procedure",
                "desc": "Method A/B, mín. 3/batch, idade ≤6 meses",
                "req_ids": {
                    "isometric":  ["R-S8K1-1"],
                    "puro_earth": ["P-SPRP-0"],
                },
            },
            {
                "id":   "lab",
                "name": "Analytical laboratory (ISO 17025)",
                "desc": "Laboratório acreditado identificado",
                "req_ids": {
                    "isometric":  ["R-2TMM-0"],
                    "puro_earth": ["P-LABN-0"],
                },
            },
        ],
    },

    "feedstock_eligibility": {
        "label": "Elegibilidade do Feedstock",
        "parameters": [
            {
                "id":   "feedstock_eligible",
                "name": "Feedstock eligibility",
                "desc": "Biomassa sustentável — sem componentes fósseis",
                "req_ids": {
                    "isometric":  ["R-NK7R-0"],
                    "puro_earth": ["P-FELI-0"],
                },
                "methodology_note": {
                    "puro_earth": "Mistura fossil+bio ELIMINATÓRIA (Clar. 001 BCH)",
                },
            },
            {
                "id":   "forest_sustainability",
                "name": "Forest biomass sustainability",
                "desc": "FSC/SFI/PEFC ou ISAE 3000 ou plano gov. (CPI ≥ 50)",
                "req_ids": {
                    "isometric":  [],   # Isometric avalia internamente, sem R-XXXX dedicado
                    "puro_earth": ["P-FFOR-0"],
                },
                "methodology_note": {
                    "isometric":  "Avalia 'sustainable biomass' de forma flexível — sem certificação formal obrigatória",
                    "puro_earth": "BLOQUEADOR sem FSC/ISAE3000/plano gov. — diferença estrutural vs. Isometric",
                },
            },
            {
                "id":   "project_description",
                "name": "Technical description & ownership",
                "desc": "PDD técnico completo com ownership dos créditos",
                "req_ids": {
                    "isometric":  ["R-M858-0", "R-7X0X-0", "R-F6R7-0"],
                    "puro_earth": ["P-OWNR-0", "P-TECH-0", "P-PART-0"],
                },
            },
        ],
    },
}


def compute_rag_scores(findings: list, methodology: str) -> dict:
    """
    Computa RAG (Red/Amber/Green) por parâmetro para uma metodologia.

    Returns:
        {
          "carbon_accounting": {
            "label": "...",
            "parameters": [
              {"id": "...", "name": "...", "rag": "green"|"amber"|"red"|"na",
               "score": 85.0, "methodology_note": "..."},
              ...
            ]
          },
          ...
        }
    """
    # Índice de findings por ID
    results_by_id = {r.get("requirement_id", ""): r for r in findings}

    output = {}
    for pillar_key, pillar_cfg in RAG_PARAMETERS.items():
        params_out = []
        for param in pillar_cfg["parameters"]:
            req_ids = param.get("req_ids", {}).get(methodology, [])

            if not req_ids:
                # Metodologia não tem este requisito (ex: Isometric sem P-FFOR-0)
                params_out.append({
                    "id":    param["id"],
                    "name":  param["name"],
                    "desc":  param["desc"],
                    "rag":   "na",
                    "score": None,
                    "methodology_note": param.get("methodology_note", {}).get(methodology, ""),
                })
                continue

            scores = []
            all_na = True
            for rid in req_ids:
                r = results_by_id.get(rid)
                if not r:
                    continue
                if r.get("status") == "not_applicable":
                    continue
                all_na = False
                s = r.get("requirement_score")
                if s is not None:
                    scores.append(float(s))

            if all_na or not scores:
                rag = "na"
                avg = None
            else:
                avg = sum(scores) / len(scores)
                rag = "green" if avg >= 80 else "amber" if avg >= 55 else "red"

            params_out.append({
                "id":    param["id"],
                "name":  param["name"],
                "desc":  param["desc"],
                "rag":   rag,
                "score": round(avg, 0) if avg is not None else None,
                "methodology_note": param.get("methodology_note", {}).get(methodology, ""),
            })

        output[pillar_key] = {
            "label":      pillar_cfg["label"],
            "parameters": params_out,
        }

    return output
