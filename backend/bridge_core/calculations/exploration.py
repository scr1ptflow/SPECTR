"""Exploration value calculations for Elite Dangerous.

Computes estimated payouts for stellar body scans based on
FDev's exploration payout formulas.
"""

from __future__ import annotations

import math

# Surface scanning values by body class (approximate)
_BODY_BASE_VALUES: dict[str, int] = {
    "Star": 1_200,
    "Gas giant with water based life": 4_200,
    "Gas giant with ammonia based life": 3_900,
    "Gas giant (other)": 3_500,
    "Earthlike body": 25_000,
    "Water world": 14_000,
    "Ammonia world": 18_000,
    "Water giant": 2_500,
    "Water giant with life": 4_000,
    "Sudarsky class I gas giant": 3_500,
    "Sudarsky class II gas giant": 3_500,
    "Sudarsky class III gas giant": 3_500,
    "Sudarsky class IV gas giant": 3_500,
    "Sudarsky class V gas giant": 3_500,
    "Rocky body": 1_000,
    "Rocky ice body": 1_000,
    "Ice body": 1_000,
    "High metal content body": 1_000,
    "Metal rich body": 1_000,
    "Metal body": 1_000,
}

# Biological values (base value for a complete set of 3 samples)
_BIO_BASE_VALUES: dict[str, int] = {
    "Aleoida Arcus": 7_252_500,
    "Aleoida Coronamus": 6_284_600,
    "Aleoida Gravis": 12_934_900,
    "Aleoida Laminiae": 3_385_200,
    "Aleoida Spica": 3_385_200,
    "Bacterium Acies": 1_000_000,
    "Bacterium Albus": 1_000_000,
    "Bacterium Aurata": 1_000_000,
    "Bacterium Caesin": 1_000_000,
    "Bacterium Cerberus": 1_000_000,
    "Bacterium Chryseum": 1_000_000,
    "Bacterium Descendens": 1_000_000,
    "Bacterium Epaticus": 1_000_000,
    "Bacterium Gascticus": 1_000_000,
    "Bacterium Helium": 1_000_000,
    "Bacterium Hydrogenus": 1_000_000,
    "Bacterium Iceus": 1_000_000,
    "Bacterium Kappa": 1_000_000,
    "Bacterium Liquidum": 1_000_000,
    "Bacterium Muscosa": 1_000_000,
    "Bacterium Nitrus": 1_000_000,
    "Bacterium Ochrous": 1_000_000,
    "Bacterium Olea": 1_000_000,
    "Bacterium Pelliculosa": 1_000_000,
    "Bacterium Pyriticus": 1_000_000,
    "Bacterium Scopulorum": 1_000_000,
    "Bacterium Vesicula": 1_000_000,
    "Bacterium Volaticus": 1_000_000,
    "Clypeus Lacertae": 14_828_700,
    "Clypeus Marginatus": 14_828_700,
    "Clypeus Specus": 14_828_700,
    "Concha Renibus": 16_432_500,
    "Concha Spirabilis": 16_432_500,
    "Concha Suprema": 16_432_500,
    "Frutexa Acus": 4_709_500,
    "Frutexa Collum": 4_709_500,
    "Frutexa Fera": 4_709_500,
    "Frutexa Flammasis": 4_709_500,
    "Frutexa Medusa": 4_709_500,
    "Frutexa Metallicum": 4_709_500,
    "Frutexa Rubicundus": 4_709_500,
    "Fungoida Setosa": 7_774_500,
    "Fungoida Stiria": 7_774_500,
    "Fungoida Ustulata": 7_774_500,
    "Galea Bullosa": 14_644_500,
    "Galea Reclusa": 14_644_500,
    "Galea Spiralis": 14_644_500,
    "Osseus Cornibus": 13_959_000,
    "Osseus Fractalus": 13_959_000,
    "Osseus Pellebis": 13_959_000,
    "Osseus Ramulis": 13_959_000,
    "Recepta Dolium": 15_360_000,
    "Recepta Nabatis": 15_360_000,
    "Recepta Umbrax": 15_360_000,
    "Stratum Araneae": 4_848_500,
    "Stratum Excutitus": 4_848_500,
    "Stratum Limaxus": 4_848_500,
    "Stratum Laminamus": 4_848_500,
    "Stratum Paleas": 4_848_500,
    "Stratum Tectonicas": 4_848_500,
    "Tubus Cavas": 12_321_000,
    "Tubus Compagibus": 12_321_000,
    "Tubus Constrictus": 12_321_000,
    "Tubus Cyathium": 12_321_000,
    "Tubus Rosarium": 12_321_000,
    "Tubus Sinuatus": 12_321_000,
    "Tussock Avellanus": 5_211_000,
    "Tussock Capillus": 5_211_000,
    "Tussock Caputus": 5_211_000,
    "Tussock Cornucopia": 5_211_000,
    "Tussock Divisa": 5_211_000,
    "Tussock Ignis": 5_211_000,
    "Tussock Pennata": 5_211_000,
    "Tussock Pennatae": 5_211_000,
    "Tussock Propagito": 5_211_000,
    "Tussock Rotundata": 5_211_000,
    "Tussock Serrata": 5_211_000,
    "Tussock Spicula": 5_211_000,
    "Tussock Tigris": 5_211_000,
    "Tussock Viride": 5_211_000,
}


def predict_scan_value(body_class: str, distance_ls: float = 0.0, is_mapped: bool = True) -> int:
    """Estimate the scan value for a stellar body.

    Args:
        body_class: The body class string from the journal.
        distance_ls: Distance from star in light seconds (affects value slightly).
        is_mapped: Whether a detailed surface scan was performed (5x multiplier).

    Returns:
        Estimated CR value.
    """
    base = _BODY_BASE_VALUES.get(body_class, 1_000)

    # First discovery bonus: 50%
    # Mapped bonus: varies by body type
    multiplier = 1.0
    if is_mapped:
        multiplier = 3.0  # approximate DSS multiplier

    # Distance bonus (log scale)
    if distance_ls > 0:
        dist_bonus = 1.0 + math.log10(max(distance_ls, 1.0)) * 0.05
    else:
        dist_bonus = 1.0

    return int(base * multiplier * dist_bonus)


def predict_biological_value(species: str, count: int = 1) -> int:
    """Estimate the CR value for biological samples.

    Args:
        species: Species name (e.g., "Stratum Tectonicas").
        count: Number of complete sets (3 samples each).

    Returns:
        Estimated CR value.
    """
    base = _BIO_BASE_VALUES.get(species, 0)
    return base * count


def predict_total_organic_pending(
    scans: dict, sold: dict
) -> tuple[int, int]:
    """Compute total pending organic value.

    Args:
        scans: Dict of (species, variant, body, system) -> {count, ...}
        sold: Dict of "species|variant" -> {value, count}

    Returns:
        (total_sellable_sets, total_pending_value)
    """
    total_sets = 0
    total_value = 0

    for key, info in scans.items():
        species = key[0] if isinstance(key, tuple) else info.get("species", "")
        count = info.get("count", 0)
        sellable = count // 3
        if sellable > 0:
            total_sets += sellable
            total_value += predict_biological_value(species, sellable)

    return total_sets, total_value
