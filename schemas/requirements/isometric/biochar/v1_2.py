# requirements/isometric/biochar/v1_2.py

REQUIREMENTS = [
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
        "logic": "biochar_applicability",
        "severity": "high",
        "required": True
    },
    {
        "id": "ISO-BIO-REACT-01",
        "name": "Reactor system requirements addressed",
        "source": "Biochar Production and Storage v1.2 - Reactor system requirements",
        "fields": [
            "production.pyrolysis_technology",
            "production.reactor_design_diagram",
            "production.maintenance_plan"
        ],
        "logic": "reactor_requirements",
        "severity": "high",
        "required": True
    },
    {
        "id": "ISO-BIO-STOR-01",
        "name": "Storage module and monitoring defined",
        "source": "Biochar Production and Storage v1.2 - Storage",
        "fields": [
            "storage.storage_module",
            "storage.storage_location",
            "storage.storage_monitoring_plan",
            "storage.loss_accounting_method"
        ],
        "logic": "storage_requirements",
        "severity": "high",
        "required": True
    },
    {
        "id": "ISO-BIO-FEED-01",
        "name": "Feedstock requirements addressed",
        "source": "Biochar Production and Storage v1.2 - Biomass feedstock accounting",
        "fields": [
            "feedstock.biomass_type",
            "feedstock.pre_project_biomass_use",
            "feedstock.feedstock_accounting_module_compliance"
        ],
        "logic": "feedstock_requirements",
        "severity": "medium",
        "required": True
    },
    {
        "id": "ISO-BIO-MON-01",
        "name": "Monitoring plan is defined",
        "source": "Biochar Production and Storage v1.2 - Monitoring and reporting",
        "fields": [
            "monitoring_reporting.monitoring_plan",
            "monitoring_reporting.uncertainty_method",
            "monitoring_reporting.verification_ready"
        ],
        "logic": "monitoring_requirements",
        "severity": "medium",
        "required": True
    }
]
