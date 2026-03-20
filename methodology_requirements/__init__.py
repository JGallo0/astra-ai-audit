from methodology_requirements.isometric_requirements import ISOMETRIC_REQUIREMENTS
from methodology_requirements.verra_vcs_requirements import VERRA_VCS_REQUIREMENTS
from methodology_requirements.puro_earth_requirements import PURO_EARTH_REQUIREMENTS
from methodology_requirements.rainbow_requirements import RAINBOW_REQUIREMENTS
from methodology_requirements.c_sink_requirements import C_SINK_REQUIREMENTS


REQUIREMENTS_REGISTRY = {
    "isometric": ISOMETRIC_REQUIREMENTS,
    "verra_vcs": VERRA_VCS_REQUIREMENTS,
    "puro_earth": PURO_EARTH_REQUIREMENTS,
    "rainbow": RAINBOW_REQUIREMENTS,
    "c_sink": C_SINK_REQUIREMENTS,
}


def get_requirements_for_methodology(methodology_key: str):
    return REQUIREMENTS_REGISTRY.get((methodology_key or "").strip().lower(), [])
