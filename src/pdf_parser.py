import io
import pdfplumber
from typing import Dict

# Very basic: tries to read 2-column key/value tables

def extract_kv_from_pdf(pdf_bytes: bytes) -> Dict[str, str]:
    data = {}
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables()
            except Exception:
                tables = []
            for tbl in tables or []:
                for row in tbl:
                    if not row:
                        continue
                    cells = [ (c or "").strip() for c in row ]
                    if len(cells) >= 2 and len(cells[0]) > 0 and len(cells[1]) > 0:
                        k = cells[0]
                        v = cells[1]
                        if k and v and k not in data:
                            data[k] = v
    return data
