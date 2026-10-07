"""Pre-configured standard Quantum Optics experimental setups and presets.
References:
  - Kwiat et al. (1995), Phys. Rev. Lett. 75, 4337.
  - Evans et al. (2010), Phys. Rev. Lett. 105, 253601.
  - Fedrizzi et al. (2007), Opt. Express 15, 15374.
  - Mosley et al. (2008), Phys. Rev. Lett. 100, 133601.
"""

from dataclasses import dataclass
from typing import Dict
from .jsa_engine import GaussianPump, PhaseMatchingFunction, JSAEngine


@dataclass
class SPDCPreset:
    name: str
    crystal: str
    phase_matching: str
    pump_lam_um: float
    pump_fwhm_nm: float
    signal_lam_um: float
    idler_lam_um: float
    crystal_length_mm: float
    ng_p: float
    ng_s: float
    ng_i: float
    poling_period_um: float = 0.0
    notes: str = ""

    def build_engine(self) -> JSAEngine:
        pump = GaussianPump(self.pump_lam_um, self.pump_fwhm_nm)
        pm = PhaseMatchingFunction(
            length_mm=self.crystal_length_mm,
            ng_p=self.ng_p,
            ng_s=self.ng_s,
            ng_i=self.ng_i,
            poling_period_um=self.poling_period_um,
        )
        return JSAEngine(
            pump=pump,
            pm=pm,
            signal_lam0_um=self.signal_lam_um,
            idler_lam0_um=self.idler_lam_um,
        )


PRESETS: Dict[str, SPDCPreset] = {
    "PPKTP_EVANS_2010": SPDCPreset(
        name="Evans et al. (2010) Telecom Factorable PPKTP",
        crystal="PPKTP",
        phase_matching="Type-II (y -> y + z)",
        pump_lam_um=0.776,
        pump_fwhm_nm=0.68,
        signal_lam_um=1.552,
        idler_lam_um=1.552,
        crystal_length_mm=20.0,
        ng_p=1.811,
        ng_s=1.767,
        ng_i=1.852,
        poling_period_um=46.2,
        notes="Engineered group-velocity matched source with purity P = 0.81 (PRL 105, 253601)",
    ),
    "PPKTP_FEDRIZZI_2007": SPDCPreset(
        name="Fedrizzi et al. (2007) High-Brightness PPKTP",
        crystal="PPKTP",
        phase_matching="Type-II (y -> y + z)",
        pump_lam_um=0.405,
        pump_fwhm_nm=0.05,
        signal_lam_um=0.810,
        idler_lam_um=0.810,
        crystal_length_mm=10.0,
        ng_p=2.045,
        ng_s=1.842,
        ng_i=1.948,
        poling_period_um=9.825,
        notes="High heralding efficiency entangled photon source at 810 nm (Opt. Express 15, 15374)",
    ),
    "KDP_MOSLEY_2008": SPDCPreset(
        name="Mosley et al. (2008) Pure Single Photons",
        crystal="KH2PO4",
        phase_matching="Type-II (e -> o + e)",
        pump_lam_um=0.415,
        pump_fwhm_nm=1.8,
        signal_lam_um=0.830,
        idler_lam_um=0.830,
        crystal_length_mm=8.0,
        ng_p=1.530,
        ng_s=1.508,
        ng_i=1.472,
        poling_period_um=0.0,
        notes="Asymmetric GVM in bulk KDP producing unheralded pure state P ~ 0.88 (PRL 100, 133601)",
    ),
    "BBO_KWIAT_1995": SPDCPreset(
        name="Kwiat et al. (1995) Bell State Singlet Source",
        crystal="BaB2O4",
        phase_matching="Type-II (e -> o + e)",
        pump_lam_um=0.405,
        pump_fwhm_nm=0.5,
        signal_lam_um=0.810,
        idler_lam_um=0.810,
        crystal_length_mm=3.0,
        ng_p=1.685,
        ng_s=1.660,
        ng_i=1.545,
        poling_period_um=0.0,
        notes="Foundational polarization-entangled singlet state (|H,V> - |V,H>)/sqrt(2) (PRL 75, 4337)",
    ),
    "PPLN_TELECOM_1550": SPDCPreset(
        name="PPLN Telecom C-Band QPM Source",
        crystal="MgO-LiNbO3",
        phase_matching="Type-0 (e -> e + e)",
        pump_lam_um=0.775,
        pump_fwhm_nm=1.0,
        signal_lam_um=1.550,
        idler_lam_um=1.550,
        crystal_length_mm=10.0,
        ng_p=2.235,
        ng_s=2.175,
        ng_i=2.175,
        poling_period_um=19.2,
        notes="Quasi-phase-matched ultra-high efficiency photon pair generation in C-band",
    ),
    "BIBO_ULTRAFAST_800": SPDCPreset(
        name="BiBO High-Brightness Femtosecond Source",
        crystal="BiB3O6",
        phase_matching="Type-I (y -> z + z)",
        pump_lam_um=0.400,
        pump_fwhm_nm=2.5,
        signal_lam_um=0.800,
        idler_lam_um=0.800,
        crystal_length_mm=2.0,
        ng_p=1.890,
        ng_s=1.815,
        ng_i=1.815,
        poling_period_um=0.0,
        notes="High effective nonlinearity (deff ~ 3.2 pm/V) for ultrafast pulsed SPDC",
    ),
}


def get_preset(name: str) -> SPDCPreset:
    """Retrieves an SPDC preset by key."""
    if name not in PRESETS:
        raise KeyError(f"Unknown preset {name!r}. Available: {list(PRESETS.keys())}")
    return PRESETS[name]
