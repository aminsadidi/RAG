# Colab: download the free (open-access) papers that MatRAG still needs into Google Drive.
# Run this cell in Colab. Files go to MyDrive/RAG-Optics/01_Papers_by_Category/00_New_downloads, named after
# the DOI (10.1364/oe.1.2 -> 10.1364-oe.1.2.pdf). Papers whose link is a web page, not a PDF, are listed at the
# end: open those links and save the PDF into the same folder by hand.
from google.colab import drive
import os, time, requests
drive.mount("/content/drive")
OUT = "/content/drive/MyDrive/RAG-Optics/01_Papers_by_Category/00_New_downloads"
os.makedirs(OUT, exist_ok=True)
PAPERS = [
 {
  "doi": "10.1038/s41598-019-50951-1",
  "pdf": "https://www.nature.com/articles/s41598-019-50951-1.pdf",
  "page": "https://www.nature.com/articles/s41598-019-50951-1.pdf",
  "crystal": "BNA"
 },
 {
  "doi": "10.37200/ijpr/v24i4/pr2020373",
  "pdf": "",
  "page": "https://doi.org/10.37200/ijpr/v24i4/pr2020373",
  "crystal": "BaB2O4"
 },
 {
  "doi": "10.1117/12.3009739",
  "pdf": "",
  "page": "https://vital.lib.tsu.ru/vital/access/services/Download/koha:001158344/SOURCE1",
  "crystal": "BaB2O4"
 },
 {
  "doi": "10.3390/photonics11070606",
  "pdf": "https://www.mdpi.com/2304-6732/11/7/606/pdf?version=1720600108",
  "page": "https://www.mdpi.com/2304-6732/11/7/606/pdf?version=1720600108",
  "crystal": "BaB2O4"
 },
 {
  "doi": "10.1117/1.jbo.18.3.031109",
  "pdf": "https://www.spiedigitallibrary.org/journals/journal-of-biomedical-optics/volume-18/issue-3/031109/Calibrating-the-measurement-of-wavelength-dependent-second-harmonic-generation-from/10.1117/1.JBO.18.3.031109.pdf",
  "page": "https://www.spiedigitallibrary.org/journals/journal-of-biomedical-optics/volume-18/issue-3/031109/Calibrating-the-measurement-of-wavelength-dependent-second-harmonic-generation-from/10.1117/1.JBO.18.3.031109.pdf",
  "crystal": "BaB2O4"
 },
 {
  "doi": "10.1038/s41467-026-70532-x",
  "pdf": "",
  "page": "https://doi.org/10.1038/s41467-026-70532-x",
  "crystal": "BaB2O4"
 },
 {
  "doi": "10.1364/ome.577084",
  "pdf": "",
  "page": "https://doi.org/10.1364/ome.577084",
  "crystal": "BaTiO3"
 },
 {
  "doi": "10.4028/www.scientific.net/amr.584.107",
  "pdf": "",
  "page": "https://doi.org/10.4028/www.scientific.net/amr.584.107",
  "crystal": "CO(NH2)2"
 },
 {
  "doi": "10.21883/tpl.2022.02.52853.18990",
  "pdf": "",
  "page": "https://doi.org/10.21883/tpl.2022.02.52853.18990",
  "crystal": "COANP"
 },
 {
  "doi": "10.1016/j.optcom.2013.07.032",
  "pdf": "",
  "page": "https://ibn.idsi.md/vizualizare_articol/60662",
  "crystal": "CdGa2S4"
 },
 {
  "doi": "10.1088/0256-307x/17/9/016",
  "pdf": "https://iopscience.iop.org/article/10.1088/0256-307X/17/9/016/pdf",
  "page": "https://iopscience.iop.org/article/10.1088/0256-307X/17/9/016/pdf",
  "crystal": "CdHg(SCN)4"
 },
 {
  "doi": "10.1063/1.111598",
  "pdf": "https://pubs.aip.org/aip/apl/article-pdf/64/18/2457/10165201/2457_1_online.pdf",
  "page": "https://pubs.aip.org/aip/apl/article-pdf/64/18/2457/10165201/2457_1_online.pdf",
  "crystal": "CsTiOAsO4"
 },
 {
  "doi": "10.1038/s41598-017-12370-y",
  "pdf": "https://www.nature.com/articles/s41598-017-12370-y.pdf",
  "page": "https://www.nature.com/articles/s41598-017-12370-y.pdf",
  "crystal": "Gd2(MoO4)3"
 },
 {
  "doi": "10.1103/physrevb.18.453",
  "pdf": "",
  "page": "https://tsukuba.repo.nii.ac.jp/records/7540",
  "crystal": "Gd2(MoO4)3"
 },
 {
  "doi": "10.3390/condmat5030047",
  "pdf": "",
  "page": "https://doi.org/10.3390/condmat5030047",
  "crystal": "HMQ-TMS"
 },
 {
  "doi": "10.1364/ome.4.001586",
  "pdf": "",
  "page": "https://doi.org/10.1364/ome.4.001586",
  "crystal": "HMQ-TMS"
 },
 {
  "doi": "10.1143/jjap.12.199",
  "pdf": "https://iopscience.iop.org/article/10.1143/JJAP.12.199/pdf",
  "page": "https://iopscience.iop.org/article/10.1143/JJAP.12.199/pdf",
  "crystal": "K3Li2Nb5O15"
 },
 {
  "doi": "10.1143/jjap.36.6159",
  "pdf": "https://iopscience.iop.org/article/10.1143/JJAP.36.6159/pdf",
  "page": "https://iopscience.iop.org/article/10.1143/JJAP.36.6159/pdf",
  "crystal": "La3Ga5SiO14"
 },
 {
  "doi": "10.30970/jps.24.4708",
  "pdf": "https://physics.lnu.edu.ua/jps/2020/4/pdf/4708-3.pdf",
  "page": "https://physics.lnu.edu.ua/jps/2020/4/pdf/4708-3.pdf",
  "crystal": "La3Ga5SiO14"
 },
 {
  "doi": "10.1155/2017/2980274",
  "pdf": "http://downloads.hindawi.com/journals/ijo/2017/2980274.pdf",
  "page": "http://downloads.hindawi.com/journals/ijo/2017/2980274.pdf",
  "crystal": "La3Ga5SiO14"
 },
 {
  "doi": "10.1038/s41598-019-50951-1",
  "pdf": "https://www.nature.com/articles/s41598-019-50951-1.pdf",
  "page": "https://www.nature.com/articles/s41598-019-50951-1.pdf",
  "crystal": "MNA"
 },
 {
  "doi": "10.1007/bf00886167",
  "pdf": "https://link.springer.com/content/pdf/10.1007/BF00886167.pdf",
  "page": "https://link.springer.com/content/pdf/10.1007/BF00886167.pdf",
  "crystal": "MgBaF4"
 },
 {
  "doi": "10.1038/s41586-025-10007-z",
  "pdf": "https://www.researchsquare.com/article/rs-6284969/latest.pdf",
  "page": "https://www.researchsquare.com/article/rs-6284969/latest.pdf",
  "crystal": "NH4B4O6F"
 },
 {
  "doi": "10.1088/0022-3719/6/3/017",
  "pdf": "https://iopscience.iop.org/article/10.1088/0022-3719/6/3/017/pdf",
  "page": "https://iopscience.iop.org/article/10.1088/0022-3719/6/3/017/pdf",
  "crystal": "NaNO2"
 },
 {
  "doi": "10.1070/qe1994v024n04abeh000087",
  "pdf": "https://iopscience.iop.org/article/10.1070/QE1994v024n04ABEH000087/pdf",
  "page": "https://iopscience.iop.org/article/10.1070/QE1994v024n04ABEH000087/pdf",
  "crystal": "NaNO2"
 },
 {
  "doi": "10.3390/photonics12060556",
  "pdf": "https://www.mdpi.com/2304-6732/12/6/556/pdf?version=1748769676",
  "page": "https://www.mdpi.com/2304-6732/12/6/556/pdf?version=1748769676",
  "crystal": "PbGa2GeSe6"
 },
 {
  "doi": "10.1038/374290c0",
  "pdf": "https://www.nature.com/articles/374290c0.pdf",
  "page": "https://www.nature.com/articles/374290c0.pdf",
  "crystal": "Sr2Be2B2O7"
 },
 {
  "doi": "10.1063/1.4754277",
  "pdf": "",
  "page": "https://doi.org/10.1063/1.4754277",
  "crystal": "SrB4O7"
 },
 {
  "doi": "10.1134/s0021364026600369",
  "pdf": "https://link.springer.com/content/pdf/10.1134/S0021364026600369.pdf",
  "page": "https://link.springer.com/content/pdf/10.1134/S0021364026600369.pdf",
  "crystal": "SrB4O7"
 },
 {
  "doi": "10.3390/cryst2041393",
  "pdf": "https://www.mdpi.com/2073-4352/2/4/1393/pdf?version=1349701718",
  "page": "https://www.mdpi.com/2073-4352/2/4/1393/pdf?version=1349701718",
  "crystal": "SrB4O7"
 }
]
H = {"User-Agent": "Mozilla/5.0 (MatRAG paper fetch; mailto:ethanjamescarter1995@gmail.com)"}
ok, by_hand = 0, []
for p in PAPERS:
    path = os.path.join(OUT, p["doi"].replace("/", "-") + ".pdf")
    if os.path.exists(path):
        ok += 1; continue
    for url in [u for u in (p["pdf"], p["page"]) if u]:
        try:
            r = requests.get(url, headers=H, timeout=60, allow_redirects=True)
            if r.ok and r.content[:5] == b"%PDF-":
                open(path, "wb").write(r.content); ok += 1; break
        except Exception as e:
            print("  error", p["doi"], e)
        time.sleep(1)
    else:
        by_hand.append(p)
print(f"{ok} of {len(PAPERS)} saved in {OUT}")
print("Open these by hand and save the PDF into the same folder:")
for p in by_hand:
    print(f"  {p['crystal']:14} https://doi.org/{p['doi']}   {p['page'] or p['pdf']}")
