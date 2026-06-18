from methodology_requirements.isometric_requirements import ISOMETRIC_REQUIREMENTS
from methodology_requirements.verra_vcs_requirements import VERRA_VCS_REQUIREMENTS
from methodology_requirements.puro_earth_requirements import PURO_EARTH_REQUIREMENTS
from methodology_requirements.rainbow_requirements import RAINBOW_REQUIREMENTS
from methodology_requirements.c_sink_requirements import C_SINK_REQUIREMENTS
from methodology_requirements.isometric_biochar_v1 import ISOMETRIC_BIOCHAR_V1

# ── Legacy registry (ELIG_001 style) — mantido para retrocompatibilidade ────
_LEGACY_REGISTRY = {
    "isometric":  ISOMETRIC_REQUIREMENTS,
    "verra_vcs":  VERRA_VCS_REQUIREMENTS,
    "puro_earth": PURO_EARTH_REQUIREMENTS,
    "rainbow":    RAINBOW_REQUIREMENTS,
    "c_sink":     C_SINK_REQUIREMENTS,
}

# ── Protocol-native registry (R-XXXX style) — engine v1 ────────────────────
_V1_REGISTRY = {
    "isometric": ISOMETRIC_BIOCHAR_V1,
    # futuras metodologias: "verra_vcs": VERRA_VCS_V1, etc.
}


def get_requirements_for_methodology(
    methodology_key: str,
    engine_version: str = "v1",
) -> list:
    """
    Retorna os requisitos para a metodologia e versão do engine.

    engine_version:
      "v1"     → R-XXXX IDs, protocol-native (padrão para Isometric)
      "legacy" → ELIG_001 IDs, motor original (fallback / outras metodologias)
    """
    key = (methodology_key or "").strip().lower()

    if engine_version == "v1":
        reqs = _V1_REGISTRY.get(key)
        if reqs is not None:
            return reqs
        # Fallback para legacy se v1 não disponível para essa metodologia

    return _LEGACY_REGISTRY.get(key, [])


def list_methodology_keys() -> list:
    return list(_LEGACY_REGISTRY.keys())
