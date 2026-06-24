"""
Co2mply — Dados de mercado por metodologia (Módulos 3 e 4 do Sylvera).

Fontes:
  - Sylvera Biochar Methodology Assessment (Out 2025)
  - Puro.earth Marketplace General Rules v4.2
  - Isometric Standard v1.5 — fee schedule
  - Verra Registry — fee schedule 2024
  - Transparency International CPI 2023
  - ICVCM CCP approved programs list (2025)
  - CORSIA eligible emission units list (2025)

Atualizar manualmente quando metodologias evoluírem.
Última atualização: 2026-06 (baseado em Sylvera Out 2025)
"""

# ── Status helpers ─────────────────────────────────────────────────────────────
# "approved" | "conditional" | "pending" | "not_eligible" | "not_applicable"

METHODOLOGY_MARKET_DATA: dict = {

    # ──────────────────────────────────────────────────────────────────────────
    "isometric": {
        "label":   "Isometric Biochar v1.2",
        "short":   "Isometric",

        # Módulo 3 — Custos e Prazos
        "costs": {
            "registry": {
                "account_opening_usd":   0,
                "annual_maintenance_usd": 0,
                "note": "Isometric não cobra do projeto — taxas são repassadas ao comprador.",
                "source": "Isometric Standard v1.5",
            },
            "issuance": {
                "per_credit_usd": None,
                "note": "Taxas cobradas do comprador, não do projeto. Modelo único no mercado.",
            },
            "vvb": {
                "initial_audit_range": "US$ 8.000–15.000",
                "periodic_audit_range": "US$ 5.000–10.000 / período",
                "audit_frequency": "Anual ou por período de monitoramento",
                "accredited_vvbs": ["EnergyLink Services", "SCS Global", "Bureau Veritas"],
            },
            "total_first_year_estimate_usd": "13.000–25.000",
            "total_ongoing_per_year_usd":    "5.000–10.000",
        },
        "timelines": {
            "registration_months":    "2–4",
            "first_audit_months":     "3–6",
            "first_issuance_months":  "6–12",
            "crediting_period_years": 5,
            "renewal": "Renovação a cada 5 anos com reavaliação completa",
            "issuance_deadline": "Sem prazo definido após submissão",
        },

        # Módulo 4 — Market Acceptance
        "market": {
            "standards": {
                "icroa":    {"status": "conditional", "label": "ICROA Endorsement Condicional"},
                "corsia":   {"status": "conditional", "label": "CORSIA Elegível (Condicional)"},
                "icvcm_ccp":{"status": "approved",    "label": "CCP Aprovado (v1.0 e v1.2)", "detail": "V1.2 aprovado; V1.3 em avaliação"},
                "verra_ccp":{"status": "not_applicable", "label": "N/A"},
            },
            "compliance_markets": [
                {"name": "Chile",      "status": "conditional", "note": "Créditos com < 3 anos"},
                {"name": "Cingapura", "status": "conditional", "note": "Carbon tax (condições aplicam)"},
            ],
            "buyer_profile": [
                "Corporativo voluntário (net zero)",
                "Fundos de investimento em CDR",
                "Compradores de qualidade premium",
            ],
            "price_range_usd": "80–160",
            "price_note": "Mercado CDR premium, issuance direta. Dados: Puro.earth marketplace + Sylvera intelligence (2025).",
            "market_share": "Emergente — < 5% do mercado biochar por volume",
            "strengths": [
                "Sem custo para o projeto (paga o comprador)",
                "CCP aprovado — elegível para compradores exigentes",
                "Condicional CORSIA — acesso a aviação no futuro",
            ],
            "risks": [
                "Padrão mais novo — menor liquidez histórica",
                "Transparência de preços menor (sem marketplace público)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────────────
    "puro_earth": {
        "label":   "Puro.Earth Biochar Edition 2025",
        "short":   "Puro.Earth",

        "costs": {
            "registry": {
                "account_opening_usd":   0,
                "annual_maintenance_eur": 1400,
                "annual_service_eur_est": 19890,
                "note": "Taxa de serviço anual estimada (~€19.890). Issuance fee variável por volume (tiers).",
                "source": "Puro.earth Platform Agreement 2025 — Appendix 5 Service Fees",
            },
            "issuance": {
                "per_credit_eur": "Tiered por volume acumulado",
                "note": "Menor % em maiores volumes. Consultar Agreement para tiers atuais.",
            },
            "vvb": {
                "initial_audit_range": "US$ 10.000–20.000",
                "periodic_audit_range": "US$ 8.000–15.000 / período",
                "audit_frequency": "Por período de monitoramento (trimestral a anual)",
                "accredited_vvbs": ["EnergyLink Services", "Aenor", "TÜV SÜD"],
                "assurance_standard": "ISAE 3000 (reasonable assurance)",
            },
            "total_first_year_estimate_usd": "30.000–45.000",
            "total_ongoing_per_year_usd":    "25.000–35.000",
        },
        "timelines": {
            "registration_months":   "1–3",
            "first_audit_months":    "2–4",
            "first_issuance_months": "4–8",
            "crediting_period_years": None,
            "renewal": "Auditoria de renovação a cada período + reavaliação do baseline",
            "issuance_deadline": "18 meses após submissão completa ao Issuing Body (Clar. 009 GR3)",
        },

        "market": {
            "standards": {
                "icroa":    {"status": "approved",    "label": "ICROA Aprovado"},
                "corsia":   {"status": "not_eligible","label": "Não elegível CORSIA", "detail": "Não aplicou ao programa"},
                "icvcm_ccp":{"status": "pending",     "label": "CCP Pendente — em avaliação pelo Governing Board"},
                "verra_ccp":{"status": "not_applicable", "label": "N/A"},
            },
            "compliance_markets": [],
            "buyer_profile": [
                "Corporativo voluntário europeu (net zero)",
                "Compradores CDR direto (high quality)",
                "Offtakers de longo prazo (contratos)",
            ],
            "price_range_usd": "100–200",
            "price_note": "Premium CDR europeu. Maior liquidez no marketplace Puro. Dados: Puro.earth public data + Sylvera (2025).",
            "market_share": "~35% do mercado biochar por volume de créditos",
            "strengths": [
                "Maior marketplace público de biochar (liquidez)",
                "ICROA aprovado — qualidade reconhecida",
                "Preço premium vs. Verra",
                "Pipeline de compradores estabelecido",
            ],
            "risks": [
                "Custo operacional alto (€20k+/ano)",
                "Não elegível CORSIA — exclui mercado de aviação",
                "CCP não aprovado — compradores ICVCM excluídos por ora",
                "Prazo 18 meses cria risco operacional",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────────────
    "verra_vcs": {
        "label":   "Verra VCS VM0044 v1.2",
        "short":   "Verra VCS",

        "costs": {
            "registry": {
                "account_opening_usd":   750,
                "annual_maintenance_usd": 750,
                "issuance_fee_per_credit_usd": 0.20,
                "note": "Taxa de issuance de US$0.20/crédito paga pelo projeto no momento da emissão.",
                "source": "Verra Registry Fee Schedule 2024",
            },
            "issuance": {
                "per_credit_usd": 0.20,
                "note": "Mais transparente e previsível que Puro.",
            },
            "vvb": {
                "initial_validation_range": "US$ 15.000–30.000",
                "annual_verification_range": "US$ 5.000–12.000 / período",
                "audit_frequency": "Anual (ou semestral para projetos maiores)",
                "accredited_vvbs": ["Bureau Veritas", "SCS Global", "ERM CVS", "Rina", "DNV"],
                "note": "Validação E verificação requeridas — dois processos distintos.",
            },
            "total_first_year_estimate_usd": "16.500–31.500",
            "total_ongoing_per_year_usd":    "6.000–13.000",
        },
        "timelines": {
            "registration_months":   "3–6",
            "validation_months":     "3–6",
            "first_issuance_months": "6–18",
            "crediting_period_years": 10,
            "renewal": "Renovação a cada 10 anos (Verra standard)",
            "issuance_deadline": "Sem prazo específico após verificação",
        },

        "market": {
            "standards": {
                "icroa":    {"status": "approved", "label": "ICROA Aprovado (VCS Standard)"},
                "corsia":   {"status": "approved", "label": "CORSIA Aprovado (Standard, não VM0044)", "detail": "VM0044 não incluído nas fases CORSIA existentes"},
                "icvcm_ccp":{"status": "approved", "label": "CCP Aprovado (v1.0)", "detail": "VM0044 v1.1 em avaliação"},
                "verra_ccp":{"status": "approved", "label": "CCP — VCS Standard aprovado"},
            },
            "compliance_markets": [
                {"name": "Chile",       "status": "eligible",    "note": "Créditos < 3 anos"},
                {"name": "Colômbia",   "status": "eligible",    "note": "Imposto de carbono colombiano"},
                {"name": "Cingapura",  "status": "conditional", "note": "Carbon tax (condições aplicam)"},
                {"name": "Coreia do Sul","status": "partial",   "note": "Parcialmente elegível (restrições por tipo)"},
            ],
            "buyer_profile": [
                "Corporativo (mercado voluntário amplo)",
                "Compliance (Chile, Colômbia, Cingapura)",
                "Aviação CORSIA (Standard VCS, não VM0044)",
                "Varejo e retail",
                "Fundos diversificados",
            ],
            "price_range_usd": "30–80",
            "price_note": "Mercado mais líquido mas preço menor. VM0044 pode ter premium vs. outros VCS. Dados: CBL, Xpansiv, Sylvera (2025).",
            "market_share": "~60% do mercado biochar por volume (metodologia mais usada historicamente)",
            "strengths": [
                "Maior liquidez e reconhecimento de mercado",
                "CCP aprovado — compradores premium elegíveis",
                "Acesso a mercados de compliance (Chile, Colômbia)",
                "Rede estabelecida de VVBs e compradores",
                "Custo mais previsível (US$0.20/crédito)",
            ],
            "risks": [
                "Preço por crédito menor que Isometric e Puro",
                "VM0044 não elegível CORSIA (aviação excluída)",
                "Sylvera avalia riscos de integridade mais altos vs. Iso/Puro",
                "Processo mais longo (validação + verificação separadas)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────────────
    "rainbow": {
        "label": "Rainbow Carbon",
        "short": "Rainbow",
        "costs": {
            "registry": {"note": "Dados pendentes — consultar Rainbow diretamente."},
            "vvb":      {"note": "Dados pendentes."},
            "total_first_year_estimate_usd": "A confirmar",
            "total_ongoing_per_year_usd":    "A confirmar",
        },
        "timelines": {
            "registration_months":   "A confirmar",
            "first_issuance_months": "A confirmar",
        },
        "market": {
            "standards": {
                "icroa":    {"status": "not_applicable", "label": "Não verificado"},
                "corsia":   {"status": "not_applicable", "label": "Não verificado"},
                "icvcm_ccp":{"status": "not_applicable", "label": "Não verificado"},
            },
            "compliance_markets": [],
            "buyer_profile": ["Mercado voluntário"],
            "price_range_usd": "A confirmar",
            "price_note": "Dados de mercado não disponíveis — padrão emergente.",
            "market_share": "< 1% por volume",
            "strengths": [], "risks": ["Liquidez muito baixa", "Reconhecimento limitado"],
        },
    },

    "c_sink": {
        "label": "Global C-SINK / CSI-EBI (Artisan)",
        "short": "C-SINK",
        "costs": {
            "registry": {"note": "Carbon Standards International. Dados pendentes."},
            "vvb":      {"note": "Acreditação CSI. Dados pendentes."},
            "total_first_year_estimate_usd": "A confirmar",
            "total_ongoing_per_year_usd":    "A confirmar",
        },
        "timelines": {
            "registration_months":   "A confirmar",
            "first_issuance_months": "A confirmar",
        },
        "market": {
            "standards": {
                "icroa":    {"status": "not_applicable", "label": "Não verificado"},
                "corsia":   {"status": "not_applicable", "label": "Não verificado"},
                "icvcm_ccp":{"status": "not_applicable", "label": "Não verificado"},
            },
            "compliance_markets": [],
            "buyer_profile": ["Mercado voluntário europeu"],
            "price_range_usd": "A confirmar",
            "price_note": "Padrão focado em qualidade técnica. Liquidez em desenvolvimento.",
            "market_share": "< 2% por volume",
            "strengths": ["Alta rigorosidade técnica"], "risks": ["Baixa liquidez"],
        },
    },
}
