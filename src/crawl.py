import argparse
import os
import time
import json
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm
from playwright.sync_api import sync_playwright

from .site_config import SiteConfig
from .robots import allowed
from .html_parser import extract_links_and_specs, guess_model
from .pdf_parser import extract_kv_from_pdf
from .utils import sha256_bytes, safe_filename, ensure_dir, join_url
from .save import (
    init_outputs, append_row, PRODUCTS_CSV, DOCS_CSV, PRODUCT_HEADERS, DOC_HEADERS,
    append_normalized
)
from .classify import classify_product_type
from .normalizer import normalize_specs

load_dotenv()
USER_AGENT = os.getenv("USER_AGENT", "Load55Scraper/0.2")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
CRAWL_DELAY = float(os.getenv("CRAWL_DELAY", "2"))

DENY_DEFAULT = ["/privacy", "/terms", "/careers", "/contact", "/news"]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def http_get(url: str) -> requests.Response:
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    return r


def is_denied(url: str, deny_patterns):
    path = urlparse(url).path.lower()
    for pat in deny_patterns:
        if pat.lower() in path:
            return True
    return False


def collect_product_links(page, selectors, base_url, deny_patterns, max_links=500):
    found = set()
    for sel in selectors:
        anchors = page.query_selector_all(sel)
        for a in anchors:
            href = a.get_attribute("href")
            if not href:
                continue
            full = join_url(base_url, href)
            if full in found:
                continue
            if is_denied(full, deny_patterns):
                continue
            if urlparse(full).netloc != urlparse(base_url).netloc:
                continue
            found.add(full)
            if len(found) >= max_links:
                return list(found)
    return list(found)


def download_pdf(url: str) -> bytes:
    resp = http_get(url)
    return resp.content


def site_from_url(url: str, manufacturer: str = None):
    netloc = urlparse(url).netloc
    base_url = f"https://{netloc}"
    start_urls = [url]
    return SiteConfig(
        manufacturer=manufacturer or netloc.split(".")[-2].upper(),
        base_url=base_url,
        start_urls=start_urls,
        product_link_selectors=["a[href*='/product']","a[href*='/products/']","a[href$='.pdf']"],
        deny_patterns=[],
        pdf_keywords=["submittal","spec","catalog","i&o","iom","manual","ahri"],
        max_depth=2,
    )


def run(cfg: SiteConfig, limit: int, default_product_type: str = None, output_dir: str = None, progress_json: bool = False):
    if output_dir:
        # Use custom output directory for job-specific results
        import os
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "files"), exist_ok=True)
        # Update save module paths
        import sys
        sys.modules['src.save'].PRODUCTS_CSV = os.path.join(output_dir, "products.csv")
        sys.modules['src.save'].DOCS_CSV = os.path.join(output_dir, "documents.csv")
        sys.modules['src.save'].NORMALIZED_CSV = os.path.join(output_dir, "normalized_products.csv")
        sys.modules['src.save'].init_outputs()
    else:
        init_outputs()
    
    deny_patterns = (cfg.deny_patterns or []) + DENY_DEFAULT

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()

        visited = set()
        queue = [(u, 0) for u in cfg.start_urls]
        pbar = tqdm(total=limit, desc=f"Crawling {cfg.manufacturer}")

        while queue and pbar.n < limit:
            url, depth = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            if not allowed(USER_AGENT, cfg.base_url, url):
                continue
            if is_denied(url, deny_patterns):
                continue

            try:
                page.goto(url, wait_until="load", timeout=45000)
            except Exception:
                continue

            html = page.content()
            soup = BeautifulSoup(html, "lxml")
            title = (soup.title.string if soup.title else "").strip()
            text_blob = soup.get_text(" ")

            product_links, specs_html, pdf_links = extract_links_and_specs(html, cfg.base_url)
            # Merge raw specs from HTML + PDFs
            raw_specs = dict(specs_html)

            # PDF docs
            for href, link_text in pdf_links:
                pdf_url = join_url(cfg.base_url, href)
                if not allowed(USER_AGENT, cfg.base_url, pdf_url):
                    continue
                try:
                    pdf_bytes = download_pdf(pdf_url)
                except Exception:
                    continue
                h = sha256_bytes(pdf_bytes)
                fname = safe_filename(f"{cfg.manufacturer}_{h}.pdf")
                out_path = os.path.join(OUTPUT_DIR, "files", fname)
                ensure_dir(os.path.dirname(out_path))
                with open(out_path, "wb") as f:
                    f.write(pdf_bytes)

                # Attempt KV extraction from PDF
                try:
                    pdf_kv = extract_kv_from_pdf(pdf_bytes)
                    for k, v in pdf_kv.items():
                        raw_specs.setdefault(k, v)
                except Exception:
                    pass

                append_row(DOCS_CSV, dict(zip(DOC_HEADERS, [
                    cfg.manufacturer, url, link_text.strip(), fname, h, pdf_url
                ])))

            # If the page looks like a product detail, save it
            if raw_specs or pdf_links:
                model_guess = guess_model(text_blob)
                append_row(PRODUCTS_CSV, dict(zip(PRODUCT_HEADERS, [
                    cfg.manufacturer, title, url, model_guess, json.dumps(raw_specs, ensure_ascii=False)
                ])))
                # Classify type (allow override)
                ptype = default_product_type or classify_product_type(title, url, text_blob)
                # Normalize
                normalized = normalize_specs(raw_specs, ptype)
                # Patch in a few universal fields
                normalized_row = {
                    "manufacturer": cfg.manufacturer,
                    "product_type": ptype,
                    "product_title": title,
                    "product_url": url,
                    "model": normalized.get("model") or model_guess or "",
                    "refrigerant": normalized.get("refrigerant"),
                    "capacity_ton": normalized.get("capacity_ton"),
                    "eer": normalized.get("eer"),
                    "ieer": normalized.get("ieer"),
                    "seer2": normalized.get("seer2"),
                    "power_supply": normalized.get("power_supply"),
                    "mca_a": normalized.get("mca_a"),
                    "mop_a": normalized.get("mop_a"),
                    "cfm": normalized.get("cfm"),
                    "esp_inwc": normalized.get("esp_inwc"),
                    "length_in": normalized.get("length_in"),
                    "width_in": normalized.get("width_in"),
                    "height_in": normalized.get("height_in"),
                    "weight_lb": normalized.get("weight_lb"),
                    "ahri_id": normalized.get("ahri_id"),
                }
                append_normalized(normalized_row)
                pbar.update(1)
                
                # Output progress as JSON if requested
                if progress_json:
                    progress_data = {
                        "status": "running",
                        "progress": int((pbar.n / limit) * 100),
                        "message": f"Found {pbar.n} products so far...",
                        "totalProducts": limit,
                        "currentProduct": pbar.n
                    }
                    print(json.dumps(progress_data))

            # Enqueue more links
            if depth < cfg.max_depth:
                new_links = []
                for sel in cfg.product_link_selectors:
                    anchors = page.query_selector_all(sel)
                    for a in anchors:
                        href = a.get_attribute("href")
                        if not href:
                            continue
                        full = join_url(cfg.base_url, href)
                        if full not in visited and not is_denied(full, deny_patterns):
                            new_links.append(full)
                for nl in new_links:
                    queue.append((nl, depth + 1))

            time.sleep(CRAWL_DELAY)

        browser.close()
        pbar.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", help="Path to seed JSON file")
    ap.add_argument("--url", help="Single start URL (no seed needed)")
    ap.add_argument("--manufacturer", help="Manufacturer name (required with --url)")
    ap.add_argument("--default_product_type", help="Force a product_type label for normalization")
    ap.add_argument("--limit", type=int, default=50, help="Max products to record")
    ap.add_argument("--output-dir", help="Custom output directory for job-specific results")
    ap.add_argument("--progress-json", action="store_true", help="Output progress as JSON")
    args = ap.parse_args()

    if args.url:
        if not args.manufacturer:
            raise SystemExit("--manufacturer is required when using --url")
        cfg = site_from_url(args.url, args.manufacturer)
        run(cfg, args.limit, args.default_product_type, args.output_dir, args.progress_json)
    elif args.seed:
        with open(args.seed, "r", encoding="utf-8") as f:
            cfg = SiteConfig(**json.load(f))
        run(cfg, args.limit, args.default_product_type, args.output_dir, args.progress_json)
    else:
        raise SystemExit("Provide either --url or --seed")
