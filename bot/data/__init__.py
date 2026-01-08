"""Data package for IdentityCrisis bot."""

from .nicknames import DEFAULT_NICKNAMES
from .transformers import TRANSFORMERS, TRANSFORMER_NAMES, apply_rules

__all__ = ["DEFAULT_NICKNAMES", "TRANSFORMERS", "TRANSFORMER_NAMES", "apply_rules"]