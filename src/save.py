import csv
import os
from typing import Dict
from .utils import ensure_dir

PRODUCTS_CSV = "output/products.csv"
DOCS_CSV = "output/documents.csv"
NORMALIZED_CSV = "output/normalized_products.csv"

PRODUCT_HEADERS = [
    "manufacturer", "product_title", "product_url", "model_guess",
    "specs_json"
]

DOC_HEADERS = [
    "manufacturer", "product_url", "doc_type", "filename", "file_sha256", "source_url"
]

NORMALIZED_HEADERS = [
    # minimal common fields — extend to match your DB importer
    "manufacturer", "product_type", "product_title", "product_url", "model",
    "refrigerant", "capacity_ton", "eer", "ieer", "seer2",
    "power_supply", "mca_a", "mop_a",
    "cfm", "esp_inwc",
    "length_in", "width_in", "height_in", "weight_lb",
    "ahri_id"
]

def init_outputs():
    ensure_dir("output")
    ensure_dir("output/files")
    if not os.path.exists(PRODUCTS_CSV):
        with open(PRODUCTS_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(PRODUCT_HEADERS)
    if not os.path.exists(DOCS_CSV):
        with open(DOCS_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(DOC_HEADERS)
    if not os.path.exists(NORMALIZED_CSV):
        with open(NORMALIZED_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(NORMALIZED_HEADERS)


def append_row(path: str, row: Dict):
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writerow(row)


def append_normalized(row: dict):
    with open(NORMALIZED_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=NORMALIZED_HEADERS)
        writer.writerow(row)

