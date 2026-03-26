# engine/inference/registry.py

from .durability_inference import DurabilityInference
from .production_inference import ProductionInference
from .quantification_inference import QuantificationInference
from .product_inference import ProductInference


INFERENCE_RULES = [
    DurabilityInference(),
    ProductionInference(),
    QuantificationInference(),
    ProductInference(),
]
