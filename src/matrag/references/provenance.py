"""Where each number of the site's crystal data comes from, as one of four tiers shown next to it:

  verified  read from the page of the paper that measured it (a paper of the collection, page given)
  compiled  from a handbook or review of the collection that quotes or fits other papers' measurements (page checked)
  database  from an open database (refractiveindex.info, ndispers) that cites the original paper; not checked here
  computed  a theoretical value (DFT), not a measurement

A data file may set ``tier:`` explicitly; otherwise it follows from the document the number was read from.
"""

from matrag.catalog import doi_key

TIERS = ("verified", "compiled", "database", "computed")
# handbooks and reviews of the collection: what they give was measured elsewhere
COMPILATIONS = {
    "10.1007_b138685",  # Nikogosyan (2005), Nonlinear Optical Crystals: A Complete Survey
    "10.1007_978_3_540_46793_9",  # Dmitriev, Gurzadyan, Nikogosyan (1999), Handbook of Nonlinear Optical Crystals
    "10.1036_0071414797",  # Bass (2001), Handbook of Optics IV
    "10.1201_9781420050196",  # Weber (2003), Handbook of Optical Materials
    "10.1109_3.159516",  # Roberts (1992), review of the d coefficients
    "10.1016_j.pquantelec.2015.04.001",  # Petrov (2015), review of mid-IR crystals
    "10.1016_j.optmat.2011.03.042",  # Petrov (2012), review of mid-IR down-conversion
    "10.1002_lpor.200810075",  # Petrov et al. (2010), review of BiBO
    "10.1007_bf00323647",  # Nikogosyan (1991), review of BBO
    "10.1007_s11082_019_1782_3",  # Das (2019), review of ZnGeP2 OPOs
    "10.7498_aps.67.20181591",  # Jia et al. (2018), review of mid- and far-IR crystals
    "10.1364_josab.33.000d36",  # Schunemann et al. (2016), review of mid-IR crystals
}


def tier(doc_id: str | None, text: str = "", explicit: str | None = None, basis: str | None = None,
         doi: str | None = None) -> str:
    """The tier of a number read from ``doc_id`` (or the document of ``doi``; ``text``: the sentence that says how
    it was read)."""
    if explicit:
        if explicit not in TIERS:
            raise ValueError(f"tier must be one of {TIERS}, not {explicit!r}")
        return explicit
    if basis == "calculated":
        return "computed"
    doc = str(doc_id or "") or (doi_key(doi) if doi else "")
    if not doc:
        return "database"
    if doc in COMPILATIONS or doc.startswith(("isbn_", "book_")) or "as quoted by" in text or "quoted in" in text:
        return "compiled"
    return "verified"
