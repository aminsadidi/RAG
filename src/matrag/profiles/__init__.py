"""Per-corpus property profiles: the default property list and plausible ranges.

A profile is a YAML file; data/<corpus>/profile.yml overrides the one
shipped here (src/matrag/profiles/<corpus>.yml).
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

from matrag.config import Settings

_BUILTIN = Path(__file__).parent


@dataclass
class PropertySpec:
    name: str
    unit: str = ""
    range: tuple[float, float] | None = None


def load_profile(settings: Settings) -> list[PropertySpec]:
    for path in (settings.data_dir / settings.corpus / "profile.yml", _BUILTIN / f"{settings.corpus}.yml"):
        if path.exists():
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return [PropertySpec(p["name"], p.get("unit", ""), tuple(p["range"]) if p.get("range") else None)
                    for p in raw.get("properties", [])]
    return []


def plausibility(property_name: str, value: float, specs: list[PropertySpec],
                 min_similarity: float = 0.4) -> bool | None:
    """Whether the value lies in the range of the best-matching property spec.

    None when no spec with a range resembles the property name.
    """
    from matrag.evaluate import property_similarity

    scored = [(property_similarity(property_name, s.name), s) for s in specs if s.range]
    score, spec = max(scored, key=lambda x: x[0], default=(0.0, None))
    if spec is None or score < min_similarity:
        return None
    low, high = spec.range
    return low <= value <= high
