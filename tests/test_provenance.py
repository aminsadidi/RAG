import pytest

from matrag.references.provenance import tier


def test_tiers_follow_the_document_the_value_was_read_from():
    assert tier("10.1063_1.360499") == "verified"  # a paper that measured it
    assert tier("10.1007_b138685") == "compiled"  # Nikogosyan's handbook
    assert tier("isbn_9780122818554") == "compiled"  # a book without a DOI
    assert tier(None, doi="10.1007/978-3-540-46793-9") == "compiled"  # a doi instead of a doc_id
    assert tier("10.1364_ao.41.005040", "dn/dT as quoted by Nikogosyan (2005)") == "compiled"
    assert tier("10.1021_jacs.7b05943", basis="calculated") == "computed"
    assert tier(None) == "database"
    assert tier("10.1063_1.360499", explicit="database") == "database"
    with pytest.raises(ValueError):
        tier("x", explicit="measured")
