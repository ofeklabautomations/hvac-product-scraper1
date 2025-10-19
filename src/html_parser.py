from bs4 import BeautifulSoup
from typing import Dict, List, Tuple
import re

SPEC_HEADERS_HINTS = [
    "spec", "specification", "performance", "technical"
]

PDF_WORDS = ["submittal", "spec", "specification", "catalog", "i&o", "iom", "manual", "ahri"]

MODEL_PAT = re.compile(r"Model\s*[:#]?\s*([A-Z0-9\-\/\.]+)", re.I)


def extract_links_and_specs(html: str, base_url: str) -> Tuple[List[Tuple[str,str]], Dict[str,str], List[Tuple[str,str]]]:
    """
    Returns: (product_links, specs_kv, pdf_links)
    product_links: list of (href, text)
    specs_kv: simple key/value map from 2-col tables (best effort)
    pdf_links: list of (href, link_text)
    """
    soup = BeautifulSoup(html, "lxml")

    # product links
    product_links = []
    for a in soup.select("a"):
        href = a.get("href")
        text = (a.get_text() or "").strip()
        if href and text:
            product_links.append((href, text))

    # spec tables (very simple two-column tables)
    specs = {}
    for table in soup.select("table"):
        # quick check: does the table live near a header with spec-like text?
        header_text = " ".join(h.get_text(" ").lower() for h in table.find_all_previous(["h1","h2","h3"], limit=1))
        if any(h in header_text for h in SPEC_HEADERS_HINTS):
            for tr in table.select("tr"):
                tds = tr.find_all(["td","th"])
                if len(tds) == 2:
                    k = tds[0].get_text(" ").strip()
                    v = tds[1].get_text(" ").strip()
                    if k and v:
                        specs[k] = v

    # pdf links
    pdf_links = []
    for a in soup.select("a[href$='.pdf']"):
        txt = (a.get_text() or "").strip().lower()
        if any(w in txt for w in PDF_WORDS):
            pdf_links.append((a.get("href"), a.get_text(strip=True)))

    return product_links, specs, pdf_links


def guess_model(text: str) -> str:
    m = MODEL_PAT.search(text or "")
    return m.group(1) if m else ""

