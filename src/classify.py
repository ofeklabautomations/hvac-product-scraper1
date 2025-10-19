import re

def classify_product_type(title: str, url: str, page_text: str) -> str:
    t = f"{title} {url} {page_text}".lower()
    rules = [
        (r"rtu|rooftop", "rtu"),
        (r"chiller|air[- ]cooled chiller", "chiller_air_cooled"),
        (r"doas|dedicated outdoor air|energy recovery|erv|hrv|ahu", "ahu_doas"),
        (r"vrf|vrv|mini[- ]split", "vrf_od"),
        (r"boiler|water heater", "boiler"),
        (r"pump|circulator", "pump"),
        (r"cooling tower|evapco|closed[- ]circuit", "cooling_tower"),
        (r"fan coil|fcu", "fcu"),
        (r"ptac|vtac", "ptac"),
        (r"heat exchanger|plate|sondex", "hx"),
        (r"vfd|drive|eaton", "vfd"),
        (r"filter|iaq|ion", "filter_iaq"),
    ]
    for pat, label in rules:
        if re.search(pat, t):
            return label
    return "unknown"
