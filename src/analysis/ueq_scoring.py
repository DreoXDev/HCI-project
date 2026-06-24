from __future__ import annotations

import math


UEQ_SCALE_ITEMS = {
    "Attrattività": ["Q01", "Q12", "Q14", "Q16", "Q24", "Q25"],
    "Apprendibilità": ["Q02", "Q04", "Q13", "Q21"],
    "Efficienza": ["Q09", "Q20", "Q22", "Q23"],
    "Controllabilità": ["Q08", "Q11", "Q17", "Q19"],
    "Stimolazione": ["Q05", "Q06", "Q07", "Q18"],
    "Originalità": ["Q03", "Q10", "Q15", "Q26"],
}

UEQ_POSITIVE_SIDE = {
    "Q01": "right",
    "Q02": "right",
    "Q03": "left",
    "Q04": "left",
    "Q05": "left",
    "Q06": "right",
    "Q07": "right",
    "Q08": "right",
    "Q09": "left",
    "Q10": "left",
    "Q11": "right",
    "Q12": "left",
    "Q13": "right",
    "Q14": "right",
    "Q15": "right",
    "Q16": "right",
    "Q17": "left",
    "Q18": "left",
    "Q19": "left",
    "Q20": "right",
    "Q21": "left",
    "Q22": "right",
    "Q23": "left",
    "Q24": "left",
    "Q25": "left",
    "Q26": "right",
}


def transform_ueq_value(raw_value: float, positive_side: str) -> float:
    if raw_value is None or (isinstance(raw_value, float) and math.isnan(raw_value)):
        return math.nan
    raw = float(raw_value)
    if raw < 1 or raw > 7:
        raise ValueError(f"UEQ raw value outside 1..7: {raw_value}")
    side = str(positive_side).strip().lower()
    if side == "right":
        return raw - 4.0
    if side == "left":
        return 4.0 - raw
    raise ValueError(f"Unknown UEQ positive side: {positive_side!r}")


def transform_ueq_item(raw_value: float, item_id: str) -> float:
    item_key = str(item_id).strip().upper()
    if item_key not in UEQ_POSITIVE_SIDE:
        raise KeyError(f"Unknown UEQ item id: {item_id!r}")
    return transform_ueq_value(raw_value, UEQ_POSITIVE_SIDE[item_key])
