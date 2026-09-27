"""Data model for an extracted property value.

The LLM fills ``PropertyRecord``; the pipeline then adds provenance
(``ExtractedRecord``). Keeping both the verbatim text and the parsed number
lets us check the parsing and compare values against reference databases.
"""

from typing import Literal

from pydantic import BaseModel, Field

Method = Literal["experimental", "theoretical", "compiled", "unknown"]


class PropertyRecord(BaseModel):
    material: str = Field(description="Substance, molecule or material, e.g. 'CO2', '12C16O2', 'GaAs'.")
    isotopologue: str | None = Field(None, description="Isotopologue if stated, e.g. '13C16O2'.")
    property: str = Field(description="Property name as used in the text, e.g. 'air-broadened half-width'.")
    value_text: str = Field(description="The value exactly as written, e.g. '0.0712(3)' or '1.23 × 10^-22'.")
    value: float = Field(description="The value as a plain number in the unit given in 'unit'.")
    uncertainty: float | None = Field(None, description="Absolute uncertainty in the same unit, if stated.")
    unit: str | None = Field(None, description="Unit exactly as written, e.g. 'cm-1 atm-1'.")
    spectral_position: str | None = Field(
        None, description="Band, transition, line or wavelength/wavenumber the value refers to."
    )
    temperature_K: float | None = Field(None, description="Temperature in kelvin, if stated.")
    pressure: str | None = Field(None, description="Pressure with unit, if stated.")
    broadener: str | None = Field(None, description="Perturbing gas for broadening/shift parameters, e.g. 'air', 'N2', 'self'.")
    method: Method = Field("unknown", description="How the value was obtained, as stated by the authors.")
    evidence: str = Field(description="A short verbatim quote from the text that contains the value.")


class ExtractionResult(BaseModel):
    records: list[PropertyRecord] = Field(default_factory=list)


class ExtractedRecord(PropertyRecord):
    doc_id: str
    node_id: str
    pages: str
    # Anti-hallucination checks against the source chunk text:
    evidence_verified: bool  # the evidence quote is present
    value_in_source: bool  # the value as written is present
