from pydantic import BaseModel
from typing import List

class SiteConfig(BaseModel):
    manufacturer: str
    base_url: str
    start_urls: List[str]
    product_link_selectors: List[str]
    deny_patterns: List[str] = []
    pdf_keywords: List[str] = []
    max_depth: int = 2
