"""Exobiology species values and classification data.

Vista Genomics redemption values for complete sample sets (3 scans).
Values from Canonn Research price list (2021) and Fandom Wiki.

A species is considered "high value" when a complete set yields >= 1 000 000 CR.
A genus is considered "high value" when it reliably produces valuable species.
"""

# Per-set base CR values (no first-discovery bonus).
# Key matches Species_Localised from journal events (ScanOrganic/SellOrganicData).
# Variant names (e.g. "Bacterium Volu - Cobalt") are NOT included — the species
# key is the base name without the elemental suffix.
SPECIES_VALUE: dict[str, int] = {
    # --- 20M+ ---
    "Fonticulua Fluctus": 20_000_000,
    # --- 19M ---
    "Tussock Stigmasis": 19_010_800,
    "Stratum Tectonicas": 19_010_800,
    "Fonticulua Segmentatus": 19_010_800,
    "Concha Biconcavis": 19_010_800,
    # --- 16M ---
    "Stratum Cucumisis": 16_202_800,
    "Recepta Deltahedronix": 16_202_800,
    "Fumerola Extremus": 16_202_800,
    "Clypeus Speculumi": 16_202_800,
    "Cactoida Vermis": 16_202_800,
    # --- 14M ---
    "Tussock Virgam": 14_313_700,
    "Recepta Conditivus": 14_313_700,
    # --- 12-13M ---
    "Recepta Umbrux": 12_934_900,
    "Osseus Discus": 12_934_900,
    "Aleoida Gravis": 12_934_900,
    "Tubus Cavas": 11_873_200,
    "Clypeus Margaritus": 11_873_200,
    # --- 10M ---
    "Frutexa Flammasis": 10_326_000,
    # --- 9M ---
    "Osseus Pellebantus": 9_739_000,
    "Clypeus Lacrimam": 9_739_000,
    # --- 8M ---
    "Bacterium Informem": 8_418_000,
    "Tussock Triticum": 7_774_700,
    "Tubus Compagibus": 7_774_700,
    "Frutexa Acus": 7_774_700,
    "Concha Aureolas": 7_774_700,
    "Bacterium Volu": 7_774_700,
    "Fumerola Nitris": 7_500_900,
    "Aleoida Arcus": 7_252_500,
    # --- 6-7M ---
    "Tussock Capillum": 7_025_800,
    "Fumerola Carbosis": 6_284_600,
    "Fumerola Aquatis": 6_284_600,
    "Electricae Radialem": 6_284_600,
    "Electricae Pluma": 6_284_600,
    "Aleoida Coronamus": 6_284_600,
    "Frutexa Sponsae": 5_988_000,
    "Tussock Pennata": 5_853_800,
    "Tubus Sororibus": 5_727_600,
    "Fonticulua Upupam": 5_727_600,
    # --- 4-5M ---
    "Bacterium Nebulus": 5_289_900,
    "Bacterium Scopulum": 4_934_500,
    "Bacterium Omentum": 4_638_900,
    "Concha Renibus": 4_572_400,
    "Tussock Serrati": 4_447_100,
    "Osseus Fractus": 4_027_800,
    "Bacterium Verrata": 3_897_000,
    # --- 3-4M ---
    "Fungoida Bullarum": 3_703_200,
    "Cactoida Pullulanta": 3_667_600,
    "Cactoida Cortexum": 3_667_600,
    "Sinuous Tuber Albidum": 3_425_600,
    "Anemone Croceum": 3_399_800,
    "Tussock Caputus": 3_472_400,
    "Aleoida Spica": 3_385_200,
    "Aleoida Laminiae": 3_385_200,
    "Fungoida Gelata": 3_330_300,
    "Tussock Albata": 3_252_500,
    "Tussock Ventusa": 3_227_700,
    "Osseus Pumice": 3_156_300,
    "Fonticulua Lapida": 3_111_000,
    # --- 2-3M ---
    "Stratum Laminamus": 2_788_300,
    "Fungoida Stabitis": 2_680_300,
    "Tubus Rosarium": 2_637_500,
    "Stratum Frigus": 2_637_500,
    "Cactoida Peperatis": 2_483_600,
    "Cactoida Lapis": 2_483_600,
    "Stratum Excutitus": 2_448_900,
    "Stratum Araneamus": 2_448_900,
    "Tubus Conifer": 2_415_500,
    "Osseus Spiralis": 2_404_700,
    "Concha Labiata": 2_352_400,
    # --- 1-2M ---
    "Bacterium Tela": 1_949_000,
    "Coral Root": 1_924_600,
    "Coral Tree": 1_896_800,
    "Sinuous Tuber Viride": 1_514_500,
    "Sinuous Tuber Violaceum": 1_514_500,
    "Sinuous Tuber Roseus": 1_514_500,
    "Sinuous Tuber Prasinum": 1_514_500,
    "Sinuous Tuber Lindigoticum": 1_514_500,
    "Sinuous Tuber Caeruleum": 1_514_500,
    "Sinuous Tuber Blatteum": 1_514_500,
    "Anemone Rubeum Bioluminescent": 1_499_900,
    "Anemone Roseum Bioluminescent": 1_499_900,
    "Anemone Roseum": 1_499_900,
    "Anemone Puniceum": 1_499_900,
    "Anemone Prasinum Bioluminescent": 1_499_900,
    "Anemone Luteolum": 1_499_900,
    "Anemone Blatteum Bioluminescent": 1_499_900,
    "Tussock Ignis": 1_849_000,
    "Frutexa Flabellum": 1_808_900,
    "Fonticulua Digitos": 1_804_100,
    "Tussock Divisa": 1_766_600,
    "Tussock Cultro": 1_766_600,
    "Tussock Catena": 1_766_600,
    "Bacterium Cerbrus": 1_689_800,
    "Fungoida Setisis": 1_670_100,
    "Bacterium Alcyoneum": 1_658_500,
    "Frutexa Collum": 1_639_800,
    "Frutexa Metallicum": 1_632_500,
    "Frutexa Fera": 1_632_500,
    "Crystalline Shards": 1_628_800,
    "Amphora Plant": 1_628_800,
    "Osseus Cornibus": 1_483_000,
    "Bark Mounds": 1_471_900,
    "Stratum Paleas": 1_362_000,
    "Stratum Limaxus": 1_362_000,
    "Bacterium Bullaris": 1_152_500,
    # --- 1M ---
    "Tussock Propagito": 1_000_000,
    "Tussock Pennatis": 1_000_000,
    "Fonticulua Campestris": 1_000_000,
    "Bacterium Vesicula": 1_000_000,
    "Bacterium Aurasus": 1_000_000,
    "Bacterium Acies": 1_000_000,
    # --- below 1M ---
    "Radicoida Unica": 119_037,
}

# Genuses whose Genus_Localised in journal events indicates high-value biology.
# These match the first-word of species names *except* for multi-word genuses
# (e.g. "Amphora Plant" -> genus "Amphora Plant", not just "Amphora").
HIGH_VALUE_GENUS: set[str] = {
    "Aleoida",
    "Amphora Plant",
    "Anemone",
    "Bacterium",
    "Bark Mound",
    "Brain Tree",
    "Cactoida",
    "Clypeus",
    "Concha",
    "Coral",
    "Crystalline Shard",
    "Electricae",
    "Fonticulua",
    "Frutexa",
    "Fumerola",
    "Fungoida",
    "Osseus",
    "Recepta",
    "Sinuous Tuber",
    "Stratum",
    "Tubus",
    "Tussock",
}


def is_high_value(species_localised: str) -> bool:
    """Return True if the species is worth >= 1M CR per set.

    Checks the exact species match first, then falls back to genus-level.
    """
    val = SPECIES_VALUE.get(species_localised, 0)
    if val >= 1_000_000:
        return True
    # Fallback: check if the genus is known to produce valuable species
    for g in HIGH_VALUE_GENUS:
        if species_localised.startswith(g):
            return True
    return False


def species_value(species_localised: str) -> int | None:
    """Return per-set CR value for a species, or None if unknown."""
    return SPECIES_VALUE.get(species_localised)


def variant_base_name(variant_localised: str) -> str:
    """Strip the elemental suffix from a variant name.

    "Bacterium Volu - Cobalt" -> "Bacterium Volu"
    """
    idx = variant_localised.rfind(" - ")
    return variant_localised[:idx] if idx > 0 else variant_localised
