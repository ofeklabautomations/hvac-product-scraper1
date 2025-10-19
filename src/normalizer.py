import json
import re
from typing import Dict, Any
from pathlib import Path
from pint import UnitRegistry

ureg = UnitRegistry()
Q_ = ureg.Quantity

# Load the spec catalog once
_catalog_cache = None

def load_catalog(path: str = "specs/spec_catalog.json") -> Dict[str, Any]:
    global _catalog_cache
    if _catalog_cache is None:
        _catalog_cache = json.loads(Path(path).read_text(encoding="utf-8"))
    return _catalog_cache

_num_re = re.compile(r"([-+]?[0-9]*\.?[0-9]+)")
_unit_re = re.compile(r"([A-Za-z\/()°\-]+)")

_alias_map_cache: Dict[str, Dict[str, str]] = {}

def _build_alias_map(cat: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    amap = {}
    for ptype, conf in cat.items():
        fields = conf.get("fields", {})
        amap[ptype] = {}
        for canon, meta in fields.items():
            aliases = [canon] + [a for a in meta.get("aliases", [])]
            for a in aliases:
                amap[ptype][a.strip().lower()] = canon
    return amap


def _parse_number_with_unit(val: str):
    s = (val or "").strip()
    # Try a simple "number unit" parse
    try:
        # allow like "20 ton", "70 kW", "460V", "208/230V"
        # normalize some common units first
        s = s.replace("°", " ")
        # If it looks like volts (e.g., 460V), separate
        s = s.replace("V", " V").replace("v", " V")
        parts = s.split()
        if len(parts) >= 2 and _num_re.search(parts[0]):
            q = Q_(float(_num_re.search(parts[0]).group(1)), parts[1])
            return q
    except Exception:
        pass
    # Fallback: extract first number only
    m = _num_re.search(s)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            return None
    return None


def normalize_specs(raw: Dict[str, str], product_type: str, catalog_path: str = "specs/spec_catalog.json") -> Dict[str, Any]:
    cat = load_catalog(catalog_path)
    amap = _alias_map_cache.get("map")
    if amap is None:
        amap = _build_alias_map(cat)
        _alias_map_cache["map"] = amap

    conf = cat.get(product_type) or {}
    fields = conf.get("fields", {})

    out: Dict[str, Any] = {k: None for k in fields.keys()}

    # 1) Map aliases → canonical keys
    for k_raw, v_raw in (raw or {}).items():
        k_l = (k_raw or "").strip().lower()
        # try match inside this product_type first, otherwise global by best effort
        canon = amap.get(product_type, {}).get(k_l)
        if not canon:
            # try any product type alias map
            for p, amapP in amap.items():
                if k_l in amapP:
                    canon = amapP[k_l]
                    break
        if not canon:
            continue
        meta = fields.get(canon, {})
        v = (v_raw or "").strip()
        vtype = meta.get("value_type", "string")
        if vtype == "number":
            canonical_unit = meta.get("canonical_unit")
            parsed = _parse_number_with_unit(v)
            if parsed is None:
                continue
            if canonical_unit and hasattr(parsed, "to"):
                try:
                    v_norm = parsed.to(canonical_unit).magnitude
                except Exception:
                    # if incompatible units (e.g., unitless) just take float
                    v_norm = float(parsed.magnitude if hasattr(parsed, "magnitude") else parsed)
            else:
                v_norm = float(parsed.magnitude if hasattr(parsed, "magnitude") else parsed)
            out[canon] = v_norm
        elif vtype == "enum":
            allowed = [str(x).lower() for x in meta.get("allowed", [])]
            vv = v.lower()
            # simple cleanup of refrigerant strings like "R410A"
            vv = vv.replace("r ", "r").replace(" ", "-")
            if allowed:
                # try direct or contains
                for a in allowed:
                    if vv == a.lower() or a.lower() in vv:
                        out[canon] = a
                        break
                if out.get(canon) is None:
                    out[canon] = vv  # keep as-is if not matched
            else:
                out[canon] = vv
        elif vtype == "bool":
            out[canon] = v.lower() in ("yes", "true", "1", "y")
        else:
            out[canon] = v

    return out
