from matrag.textfix import clean_text


def test_symbol_font_greek_and_math():
    # As found in arXiv:1906.01475: "ν3 band", "1.57 μm", bullet points.
    assert clean_text("the 3 and 2+3-2 bands") == "the ν3 and ν2+ν3-ν2 bands"
    assert clean_text("near 1.57 m") == "near 1.57 μm"
    assert clean_text(" item,  = 0.07  0.01, T  296") == "• item, γ = 0.07 ± 0.01, T ≥ 296"
    assert clean_text("  2") == "Δν ≈ 2"


def test_plain_text_unchanged_and_ligatures():
    text = "γ_air = 0.0712(3) cm−1 atm−1 at 296 K"
    assert clean_text(text) == text
    assert clean_text("ﬁtted coeﬃcients") == "fitted coefficients"
