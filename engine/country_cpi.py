"""
Índice de Percepção de Corrupção (CPI) por país — Transparency International 2023.
Fonte: https://www.transparency.org/en/cpi/2023

Puro.Earth Clarificação 006 BCH usa CPI ≥ 50 como threshold para aceitar
plano de manejo governamental como alternativa à certificação FSC/SFI/PEFC.

Países com CPI < 50: somente FSC/SFI/PEFC ou dossiê ISAE 3000 são aceitos.
"""

# CPI 2023 — score de 0 (mais corrupto) a 100 (mais transparente)
COUNTRY_CPI: dict = {

    # ── ≥ 80 — Alta transparência ──────────────────────────────────────────────
    "denmark":       90,
    "finland":       87,
    "new zealand":   85,
    "norway":        84,
    "singapore":     83,
    "sweden":        82,
    "switzerland":   82,
    "netherlands":   79,
    "germany":       79,
    "luxembourg":    78,

    # ── 70–79 ────────────────────────────────────────────────────────────────
    "ireland":       77,
    "canada":        76,
    "australia":     75,
    "estonia":       74,
    "japan":         73,
    "uk":            71, "united kingdom": 71, "england": 71, "britain": 71,
    "france":        71,
    "austria":       71,
    "usa":           69, "united states": 69,
    "iceland":       72,
    "belgium":       73,

    # ── 60–69 ────────────────────────────────────────────────────────────────
    "israel":        62,
    "south korea":   63,
    "taiwan":        67,
    "spain":         60,
    "portugal":      61,
    "italy":         56,
    "poland":        54,
    "latvia":        55,
    "lithuania":     59,
    "czech republic":57,
    "slovenia":      56,
    "seychelles":    71,

    # ── 50–59 — threshold mínimo Puro ────────────────────────────────────────
    "chile":         52,
    "hungary":       42,  # abaixo de 50
    "malaysia":      50,  # exatamente no threshold
    "mauritius":     54,
    "botswana":      59,
    "cape verde":    58,
    "namibia":       51,
    "costa rica":    53,
    "uruguay":       73,  # acima — bem governado

    # ── < 50 — Plano governamental NÃO disponível no Puro ────────────────────
    # América do Sul
    "brazil":        36, "brasil": 36,
    "argentina":     37,
    "colombia":      39,
    "peru":          44,
    "ecuador":       34,
    "bolivia":       27,
    "paraguay":      24,
    "venezuela":     13,

    # América Central / Caribe
    "mexico":        31, "méxico": 31,
    "guatemala":     23,
    "honduras":      23,
    "nicaragua":     17,

    # África
    "ghana":         43,
    "senegal":       43,
    "kenya":         31,
    "tanzania":      38,
    "uganda":        26,
    "ethiopia":      37,
    "nigeria":       25,
    "south africa":  41,
    "cameroon":      26,
    "mozambique":    26,
    "zimbabwe":      24,
    "madagascar":    25,

    # Ásia
    "india":         39,
    "indonesia":     34,
    "vietnam":       41, "viet nam": 41,
    "thailand":      35,
    "china":         45,
    "philippines":   34,
    "myanmar":       20,
    "cambodia":      22,
    "pakistan":      29,
    "bangladesh":    25,

    # Oriente Médio
    "iran":          24,
    "iraq":          23,
    "egypt":         35,
}


def get_cpi(country: str) -> int | None:
    """
    Retorna o CPI do país, ou None se desconhecido.
    Busca case-insensitive com normalização básica.
    """
    if not country:
        return None
    key = country.lower().strip()
    # Busca direta
    if key in COUNTRY_CPI:
        return COUNTRY_CPI[key]
    # Busca parcial (ex: "minas gerais, brazil" → "brazil")
    for name, cpi in COUNTRY_CPI.items():
        if name in key or key in name:
            return cpi
    return None


def cpi_allows_govt_plan(country: str) -> bool:
    """
    Retorna True se o país qualifica para o caminho de plano governamental
    do Puro.Earth (CPI ≥ 50 conforme Clarificação 006 BCH).
    Retorna False se CPI < 50 ou país desconhecido.
    """
    cpi = get_cpi(country)
    if cpi is None:
        return False  # Conservador: sem dado → não qualifica
    return cpi >= 50
