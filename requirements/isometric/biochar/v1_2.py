# =========================================================
# ISOMETRIC BIOCHAR v1.2 — REQUIREMENTS (V2 ENGINE)
# =========================================================

REQUIREMENTS = [

    # =====================================================
    # 1. APPLICABILITY
    # =====================================================
    {
        "id": "ISO-BIO-APP-01",
        "name": "Biochar pathway applicability confirmed",
        "source": "Biochar Production and Storage v1.2 - Applicability",
        "fields": [
            "eligibility.net_negative_claim",
            "eligibility.additionality_claim",
            "eligibility.durability_years",
            "production.pyrolysis_technology",
            "storage.storage_environment_stable"
        ],
        "logic": "biochar_applicability"
    },

    # =====================================================
    # 2. REACTOR / PRODUCTION
    # =====================================================
    {
        "id": "ISO-BIO-REACT-01",
        "name": "Reactor and process definition documented",
        "source": "Production requirements",
        "fields": [
            "production.pyrolysis_technology",
            "production.reactor_design_diagram",
            "production.maintenance_plan"
        ],
        "logic": "reactor_definition"
    },

    # =====================================================
    # 3. STORAGE / DURABILITY
    # =====================================================
    {
        "id": "ISO-BIO-STOR-01",
        "name": "Biochar storage pathway defined",
        "source": "Storage requirements",
        "fields": [
            "storage.storage_environment_stable",
            "storage.storage_module",
            "storage.storage_monitoring_plan"
        ],
        "logic": "storage_pathway"
    },

    # =====================================================
    # 4. FEEDSTOCK
    # =====================================================
    {
        "id": "ISO-BIO-FEED-01",
        "name": "Feedstock eligibility and accounting",
        "source": "Feedstock module",
        "fields": [
            "feedstock.biomass_type",
            "feedstock.pre_project_biomass_use",
            "feedstock.feedstock_accounting_module_compliance"
        ],
        "logic": "feedstock_compliance"
    },

    # =====================================================
    # 5. MONITORING & MRV
    # =====================================================
    {
        "id": "ISO-BIO-MON-01",
        "name": "Monitoring and reporting system defined",
        "source": "Monitoring requirements",
        "fields": [
            "monitoring_reporting.monitoring_plan",
            "monitoring_reporting.uncertainty_method",
            "monitoring_reporting.verification_ready"
        ],
        "logic": "monitoring_system"
    }

]
