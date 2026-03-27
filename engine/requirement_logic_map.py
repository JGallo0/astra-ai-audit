# engine/requirement_logic_map.py

REQUIREMENT_LOGIC_MAP = {
    # =========================
    # CORE ELIGIBILITY
    # =========================
    "ELIG_001": "eval_biochar_applicability",

    # =========================
    # FEEDSTOCK
    # =========================
    "FEED_001": "eval_feedstock_requirements",

    # =========================
    # TECHNOLOGY / PRODUCTION
    # =========================
    "TECH_001": "eval_reactor_requirements",

    # =========================
    # STORAGE / DURABILITY
    # =========================
    "STOR_001": "eval_storage_requirements",

    # =========================
    # MRV / MONITORING
    # =========================
    "MRV_001": "eval_monitoring_requirements",
}
