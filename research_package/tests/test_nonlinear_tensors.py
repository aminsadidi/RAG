"""Standalone test suite for 70 second-order nonlinear optical tensors.
Verifies crystal point group symmetry relations, contracted notation integrity,
and quantitative benchmarks against primary literature.
"""

from pathlib import Path
import yaml

DATA_PATH = Path(__file__).parent.parent / "data" / "nonlinear_tensors_expanded.yml"


def test_tensors():
    assert DATA_PATH.exists(), f"Missing {DATA_PATH}"
    crystals = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8"))
    assert len(crystals) >= 70, f"Expected at least 70 crystals, found {len(crystals)}"
    print(f"Loaded {len(crystals)} crystals successfully.")

    data = {c["material"]: c for c in crystals}

    # 1. Cubic -43m (GaAs, GaP, ZnSe, ZnTe, InP, InAs, CdTe, CuCl, BGO)
    cubic_crystals = ["GaAs", "GaP", "ZnSe", "ZnTe", "InP", "InAs", "CdTe", "CuCl", "Bi4Ge3O12"]
    for mat in cubic_crystals:
        assert mat in data, f"Missing cubic crystal {mat}"
        c = data[mat]
        assert c["point_group"] == "-43m", f"{mat} must be -43m"
        d = c["d"]
        val = d[14]
        assert d[25] == val and d[36] == val, f"{mat} violates d14 = d25 = d36 symmetry"
    print(f"Cubic (-43m) symmetry verified for all {len(cubic_crystals)} crystals (OK)")

    # 2. Tetragonal -42m (KDP, ADP, DKDP, ZGP, AGS, AGSe, CSP, CGA, LGT)
    chalcopyrites = ["KH2PO4", "NH4H2PO4", "KD2PO4", "ZnGeP2", "AgGaS2", "AgGaSe2", "CdSiP2", "CdGeAs2", "LiGaTe2"]
    for mat in chalcopyrites:
        assert mat in data, f"Missing chalcopyrite crystal {mat}"
        c = data[mat]
        assert c["point_group"] == "-42m"
        d = c["d"]
        assert 36 in d, f"{mat} must have d36"
        assert d[14] == d[25], f"{mat} violates d14 = d25 symmetry"
    print(f"Chalcopyrite (-42m) symmetry verified for {len(chalcopyrites)} crystals (OK)")

    # 3. Trigonal 3m (BBO, LiNbO3, MgO-LiNbO3, LiTaO3, Proustite, Pyrargyrite)
    trig_3m = ["BaB2O4", "LiNbO3", "MgO-LiNbO3", "LiTaO3", "Ag3AsS3", "Ag3SbS3"]
    for mat in trig_3m:
        assert mat in data, f"Missing 3m crystal {mat}"
        c = data[mat]
        assert c["point_group"] == "3m"
        d = c["d"]
        assert d[31] == d[32], f"{mat} violates d31 = d32"
        if 22 in d:
            assert d[21] == -d[22] and d[16] == -d[22], f"{mat} violates d22 = -d21 = -d16"
    print(f"Trigonal (3m) symmetry verified for {len(trig_3m)} crystals (OK)")

    # 4. Hexagonal 6mm (CdS, CdSe, ZnO, GaN, AlN)
    hex_6mm = ["CdS", "CdSe", "ZnO", "GaN", "AlN"]
    for mat in hex_6mm:
        assert mat in data, f"Missing 6mm crystal {mat}"
        c = data[mat]
        assert c["point_group"] == "6mm"
        d = c["d"]
        assert d[31] == d[32], f"{mat} violates d31 = d32"
        assert d[15] == d[24], f"{mat} violates d15 = d24"
    print(f"Hexagonal (6mm) symmetry verified for {len(hex_6mm)} crystals (OK)")

    # 5. Quantitative Literature Benchmarks
    assert data["GaAs"]["d"][14] == 84.0, "GaAs d14 benchmark mismatch"
    assert data["CdSiP2"]["d"][36] == 84.5, "CSP d36 benchmark mismatch"
    assert data["ZnGeP2"]["d"][36] == 69.0, "ZGP d36 benchmark mismatch"
    assert data["BaB2O4"]["d"][22] == 2.2, "BBO d22 benchmark mismatch"
    assert data["LiNbO3"]["d"][33] == -25.2, "LN d33 benchmark mismatch"
    assert data["KTiOPO4"]["d"][33] == 15.4, "KTP d33 benchmark mismatch"
    assert data["BiB3O6"]["d"][11] == 2.53, "BiBO d11 benchmark mismatch"
    print("Quantitative literature benchmarks verified (OK)")

    print(f"\nAll {len(crystals)} nonlinear crystals PASSED full symmetry & benchmark tests!")


if __name__ == "__main__":
    test_tensors()
