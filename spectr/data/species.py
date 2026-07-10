"""Elite Dangerous exobiology species database.

This module defines every known organic species that can be sampled with
the Genetic Sampler and sold at Vista Genomics.

Base value = payout for a complete set (3 samples of the same species).
First footfall bonus: 5x total (base value × 5 because you get the base
value + 4x bonus — the formula is base + 4*base = 5*base).

Key functions used by journal.py:
  base_value(name)   — returns the payout for one set of *name*
  lookup(name)       — returns the SpeciesInfo object for *name*

Data is stored in the SPECIES dict keyed by species name, with a secondary
SPECIES_BY_NAME lookup index for case-insensitive searching.
"""

from __future__ import annotations

from typing import Optional


class SpeciesInfo:
    """Metadata for a single exobiology species.

    Attributes:
      genus        — Biological genus (e.g. "Bacterium", "Stratum")
      name         — Full display name (e.g. "Stratum Tectonicas")
      base_value   — CR payout for one complete set (3 samples)
      colony_range — Max distance from star where it appears (Ly)
      atmospheres  — Atmosphere types it can grow in
      temp_range   — Temperature range (Kelvin)
      gravity_max  — Maximum surface gravity (g)
      notes        — Player notes / identification tips
    """
    __slots__ = (
        "genus", "name", "base_value", "colony_range", "atmospheres",
        "temp_range", "gravity_max", "notes",
    )

    def __init__(
        self,
        genus: str,
        name: str,
        base_value: int,
        colony_range: int = 500,
        atmospheres: str = "",
        temp_range: str = "",
        gravity_max: float = 0.0,
        notes: str = "",
    ):
        self.genus = genus
        self.name = name
        self.base_value = base_value
        self.colony_range = colony_range
        self.atmospheres = atmospheres
        self.temp_range = temp_range
        self.gravity_max = gravity_max
        self.notes = notes


# -- Species database ------------------------------------------------
# Keyed by full name (e.g. "Aleoida Arcus").
# Values updated from Canonn Research and community sources.

SPECIES: dict[str, SpeciesInfo] = {

    # ── Aleoida ──────────────────────────────────────────────────
    "Aleoida Arcus": SpeciesInfo("Aleoida", "Aleoida Arcus", 7_252_500,
        colony_range=150, atmospheres="CO2", temp_range="175-180 K"),
    "Aleoida Coronamus": SpeciesInfo("Aleoida", "Aleoida Coronamus", 6_284_600,
        colony_range=150, atmospheres="CO2", temp_range="180-190 K"),
    "Aleoida Gravis": SpeciesInfo("Aleoida", "Aleoida Gravis", 12_934_900,
        colony_range=150, atmospheres="CO2, CO2-rich", temp_range="190-195 K"),
    "Aleoida Laminiae": SpeciesInfo("Aleoida", "Aleoida Laminiae", 3_385_200,
        colony_range=150, atmospheres="Rocky, HMC", notes="Grows in elevated areas"),
    "Aleoida Spica": SpeciesInfo("Aleoida", "Aleoida Spica", 3_385_200,
        colony_range=150, atmospheres="Rocky, HMC"),

    # ── Bacterium ────────────────────────────────────────────────
    "Bacterium Acies": SpeciesInfo("Bacterium", "Bacterium Acies", 1_000_000,
        atmospheres="Nitrogen", notes="Patch on ground, flat areas"),
    "Bacterium Alcyoneum": SpeciesInfo("Bacterium", "Bacterium Alcyoneum", 1_658_500,
        atmospheres="Rocky, HMC, CO2", notes="Teal variant common"),
    "Bacterium Aurasius": SpeciesInfo("Bacterium", "Bacterium Aurasius", 1_000_000,
        atmospheres="CO2, CO2-rich"),
    "Bacterium Bullaris": SpeciesInfo("Bacterium", "Bacterium Bullaris", 1_152_500,
        atmospheres="Nitrogen, Methane"),
    "Bacterium Cerbrus": SpeciesInfo("Bacterium", "Bacterium Cerbrus", 1_689_800,
        atmospheres="CO2", colony_range=500),
    "Bacterium Informem": SpeciesInfo("Bacterium", "Bacterium Informem", 8_418_000,
        atmospheres="Nitrogen, Oxygen", colony_range=150),
    "Bacterium Nebulas": SpeciesInfo("Bacterium", "Bacterium Nebulas", 5_262_800,
        atmospheres="Helium", colony_range=500),
    "Bacterium Omentum": SpeciesInfo("Bacterium", "Bacterium Omentum", 1_949_000,
        colony_range=500),
    "Bacterium Scopellum": SpeciesInfo("Bacterium", "Bacterium Scopellum", 4_934_500,
        atmospheres="Neon", colony_range=500),
    "Bacterium Tela": SpeciesInfo("Bacterium", "Bacterium Tela", 1_949_000,
        atmospheres="Helium", colony_range=500),
    "Bacterium Verrata": SpeciesInfo("Bacterium", "Bacterium Verrata", 3_897_000,
        atmospheres="Neon", colony_range=500),
    "Bacterium Vesicula": SpeciesInfo("Bacterium", "Bacterium Vesicula", 1_000_000,
        atmospheres="Methane", colony_range=500),
    "Bacterium Volu": SpeciesInfo("Bacterium", "Bacterium Volu", 7_774_700,
        atmospheres="Oxygen", colony_range=500),

    # ── Cactoida ─────────────────────────────────────────────────
    "Cactoida Cortex": SpeciesInfo("Cactoida", "Cactoida Cortex", 3_667_600,
        colony_range=300, atmospheres="CO2", temp_range="180-195 K",
        notes="Rugged terrain"),
    "Cactoida Lapis": SpeciesInfo("Cactoida", "Cactoida Lapis", 2_448_900,
        colony_range=300, atmospheres="Rocky", notes="Grows with Frutexa"),
    "Cactoida Peperatis": SpeciesInfo("Cactoida", "Cactoida Peperatis", 1_563_000,
        colony_range=300, atmospheres="Rocky, HMC"),
    "Cactoida Pullulanta": SpeciesInfo("Cactoida", "Cactoida Pullulanta", 3_667_600,
        colony_range=300, atmospheres="CO2", temp_range="180-195 K"),
    "Cactoida Vermis": SpeciesInfo("Cactoida", "Cactoida Vermis", 16_202_800,
        colony_range=150, atmospheres="CO2", notes="High value"),

    # ── Clypeus ──────────────────────────────────────────────────
    "Clypeus Lacrimam": SpeciesInfo("Clypeus", "Clypeus Lacrimam", 8_418_000,
        colony_range=150, atmospheres="CO2, CO2-rich", temp_range=">190 K"),
    "Clypeus Margaritus": SpeciesInfo("Clypeus", "Clypeus Margaritus", 11_873_200,
        colony_range=150, atmospheres="CO2, CO2-rich, Water-rich", temp_range=">190 K"),
    "Clypeus Speculumi": SpeciesInfo("Clypeus", "Clypeus Speculumi", 16_202_800,
        colony_range=150, atmospheres="CO2, CO2-rich", temp_range=">190 K, >2500 Ls",
        notes="High value, distant from star"),

    # ── Concha ───────────────────────────────────────────────────
    "Concha Aureola": SpeciesInfo("Concha", "Concha Aureola", 7_774_700,
        colony_range=150, atmospheres="Rocky, HMC"),
    "Concha Biconcavia": SpeciesInfo("Concha", "Concha Biconcavia", 4_572_400,
        colony_range=150, atmospheres="Nitrogen"),
    "Concha Labiata": SpeciesInfo("Concha", "Concha Labiata", 2_352_400,
        colony_range=150, atmospheres="CO2, CO2-rich"),
    "Concha Renibus": SpeciesInfo("Concha", "Concha Renibus", 4_572_400,
        colony_range=150, atmospheres="CO2", temp_range="180-195 K"),

    # ── Electricae ───────────────────────────────────────────────
    "Electricae Pluma": SpeciesInfo("Electricae", "Electricae Pluma", 6_378_200,
        colony_range=200, atmospheres="Neon-rich", notes="Star type A, lum. V+"),
    "Electricae Radialem": SpeciesInfo("Electricae", "Electricae Radialem", 6_378_200,
        colony_range=200, atmospheres="Neon-rich, Nebulae", notes="Found in nebulae"),

    # ── Fonticulua ───────────────────────────────────────────────
    "Fonticulua Campestris": SpeciesInfo("Fonticulua", "Fonticulua Campestris", 1_000_000,
        colony_range=500, notes="Icy mushroom-like, easy to spot"),
    "Fonticulua Digitos": SpeciesInfo("Fonticulua", "Fonticulua Digitos", 1_804_100,
        colony_range=500),
    "Fonticulua Fluctus": SpeciesInfo("Fonticulua", "Fonticulua Fluctus", 19_010_800,
        colony_range=500, atmospheres="Oxygen, Icy/Rocky Ice", notes="High value"),
    "Fonticulua Lapida": SpeciesInfo("Fonticulua", "Fonticulua Lapida", 3_111_000,
        colony_range=500, atmospheres="Nitrogen, Icy/Rocky Ice"),
    "Fonticulua Segmentatus": SpeciesInfo("Fonticulua", "Fonticulua Segmentatus", 19_010_800,
        colony_range=500, atmospheres="Nitrogen", notes="High value"),
    "Fonticulua Upupam": SpeciesInfo("Fonticulua", "Fonticulua Upupam", 5_853_800,
        colony_range=500),

    # ── Frutexa ──────────────────────────────────────────────────
    "Frutexa Acicularis": SpeciesInfo("Frutexa", "Frutexa Acicularis", 1_808_900,
        colony_range=150),
    "Frutexa Acus": SpeciesInfo("Frutexa", "Frutexa Acus", 7_774_700,
        colony_range=150, atmospheres="CO2, CO2-rich",
        notes="Grass-like, elevated areas. Grows with Fungoida Setisis"),
    "Frutexa Fera": SpeciesInfo("Frutexa", "Frutexa Fera", 1_808_900,
        colony_range=200, atmospheres="CO2"),
    "Frutexa Flabellum": SpeciesInfo("Frutexa", "Frutexa Flabellum", 1_808_900,
        colony_range=150, atmospheres="Rocky"),
    "Frutexa Metallicum": SpeciesInfo("Frutexa", "Frutexa Metallicum", 1_632_500,
        colony_range=150, atmospheres="HMC, CO2"),
    "Frutexa Sponsae": SpeciesInfo("Frutexa", "Frutexa Sponsae", 5_988_000,
        colony_range=150),

    # ── Fumerola ─────────────────────────────────────────────────
    "Fumerola Aquatis": SpeciesInfo("Fumerola", "Fumerola Aquatis", 3_600_000,
        colony_range=200, atmospheres="Water, Steam"),
    "Fumerola Carbosis": SpeciesInfo("Fumerola", "Fumerola Carbosis", 3_600_000,
        colony_range=200, atmospheres="Carbon/Methane"),
    "Fumerola Extremus": SpeciesInfo("Fumerola", "Fumerola Extremus", 16_202_800,
        colony_range=200, atmospheres="Silicate/Iron/Rocky",
        notes="High value, volcanic"),
    "Fumerola Nitris": SpeciesInfo("Fumerola", "Fumerola Nitris", 3_600_000,
        colony_range=200, atmospheres="Nitrogen/Ammonia"),

    # ── Fungoida ─────────────────────────────────────────────────
    "Fungoida Bullarum": SpeciesInfo("Fungoida", "Fungoida Bullarum", 3_720_200,
        colony_range=300, notes="Elevated locations, excellent visibility"),
    "Fungoida Gelata": SpeciesInfo("Fungoida", "Fungoida Gelata", 3_330_300,
        colony_range=300, atmospheres="CO2", temp_range="180-195 K"),
    "Fungoida Setisis": SpeciesInfo("Fungoida", "Fungoida Setisis", 1_670_100,
        colony_range=300, atmospheres="Rocky, HMC",
        notes="Hilly/rugged terrain, annoying to collect"),
    "Fungoida Stabitis": SpeciesInfo("Fungoida", "Fungoida Stabitis", 2_680_300,
        colony_range=300, atmospheres="CO2", temp_range="180-195 K"),

    # ── Osseus ───────────────────────────────────────────────────
    "Osseus Cornibus": SpeciesInfo("Osseus", "Osseus Cornibus", 2_448_900,
        colony_range=800, atmospheres="CO2", temp_range="180-195 K"),
    "Osseus Discus": SpeciesInfo("Osseus", "Osseus Discus", 12_934_900,
        colony_range=800, notes="High value"),
    "Osseus Fractus": SpeciesInfo("Osseus", "Osseus Fractus", 4_027_800,
        colony_range=800, atmospheres="CO2", temp_range="180-190 K"),
    "Osseus Pellebantus": SpeciesInfo("Osseus", "Osseus Pellebantus", 9_739_000,
        colony_range=800, atmospheres="CO2", temp_range="190-195 K"),
    "Osseus Pumice": SpeciesInfo("Osseus", "Osseus Pumice", 3_156_300,
        colony_range=800),
    "Osseus Spiralis": SpeciesInfo("Osseus", "Osseus Spiralis", 2_404_700,
        colony_range=800, atmospheres="Rocky, HMC"),

    # ── Recepta ──────────────────────────────────────────────────
    "Recepta Aetheris": SpeciesInfo("Recepta", "Recepta Aetheris", 6_000_000),
    "Recepta Conditivum": SpeciesInfo("Recepta", "Recepta Conditivum", 8_425_000),
    "Recepta Deltahedra": SpeciesInfo("Recepta", "Recepta Deltahedra", 12_934_900,
        notes="High value"),
    "Recepta Umbrux": SpeciesInfo("Recepta", "Recepta Umbrux", 12_934_900,
        notes="High value"),
    "Recepta Vertiginis": SpeciesInfo("Recepta", "Recepta Vertiginis", 6_000_000),

    # ── Stratum ──────────────────────────────────────────────────
    "Stratum Araneamus": SpeciesInfo("Stratum", "Stratum Araneamus", 2_448_800,
        colony_range=500, notes="Lichen-like, flat areas, easy to spot"),
    "Stratum Cucumisis": SpeciesInfo("Stratum", "Stratum Cucumisis", 16_202_800,
        colony_range=500, atmospheres="CO2, CO2-rich", temp_range=">190 K",
        notes="High value, also on Rocky planets"),
    "Stratum Excutitus": SpeciesInfo("Stratum", "Stratum Excutitus", 2_448_800,
        colony_range=500, atmospheres="CO2", temp_range="165-190 K"),
    "Stratum Laminamus": SpeciesInfo("Stratum", "Stratum Laminamus", 2_043_600,
        colony_range=500, atmospheres="Rocky, HMC", temp_range=">165 K"),
    "Stratum Paleas": SpeciesInfo("Stratum", "Stratum Paleas", 1_362_000,
        colony_range=500, atmospheres="HMC, CO2", temp_range=">165 K"),
    "Stratum Tectonicas": SpeciesInfo("Stratum", "Stratum Tectonicas", 19_010_800,
        colony_range=500, atmospheres="Rocky, HMC", temp_range=">165 K",
        notes="Highest base value in the game. Flat areas, very easy to spot"),

    # ── Tubus ────────────────────────────────────────────────────
    "Tubus Carchariae": SpeciesInfo("Tubus", "Tubus Carchariae", 3_120_000),
    "Tubus Cavas": SpeciesInfo("Tubus", "Tubus Cavas", 3_472_400,
        colony_range=800, atmospheres="CO2", temp_range="160-190 K",
        gravity_max=0.15),
    "Tubus Compagibus": SpeciesInfo("Tubus", "Tubus Compagibus", 7_774_700,
        colony_range=800, atmospheres="CO2", temp_range="160-190 K",
        gravity_max=0.15, notes="Bamboo-like, easy to spot"),
    "Tubus Conifer": SpeciesInfo("Tubus", "Tubus Conifer", 2_415_500,
        colony_range=800, atmospheres="CO2", temp_range="160-190 K",
        gravity_max=0.15),
    "Tubus Sororibus": SpeciesInfo("Tubus", "Tubus Sororibus", 5_727_600,
        colony_range=800, atmospheres="HMC, CO2", temp_range="160-190 K",
        gravity_max=0.15),

    # ── Tussock ──────────────────────────────────────────────────
    "Tussock Albata": SpeciesInfo("Tussock", "Tussock Albata", 3_252_500,
        colony_range=200, atmospheres="CO2", temp_range="175-180 K",
        notes="Grass bushes, flat areas"),
    "Tussock Capillum": SpeciesInfo("Tussock", "Tussock Capillum", 7_025_800,
        colony_range=200, notes="Rugged terrain"),
    "Tussock Caputus": SpeciesInfo("Tussock", "Tussock Caputus", 3_472_400,
        colony_range=200, atmospheres="CO2", temp_range="180-190 K"),
    "Tussock Cultro": SpeciesInfo("Tussock", "Tussock Cultro", 1_766_600,
        colony_range=200, atmospheres="Rocky"),
    "Tussock Divisa": SpeciesInfo("Tussock", "Tussock Divisa", 1_766_600,
        colony_range=200, atmospheres="Rocky"),
    "Tussock Ignis": SpeciesInfo("Tussock", "Tussock Ignis", 1_808_900,
        colony_range=200, atmospheres="CO2", temp_range="160-170 K"),
    "Tussock Pennata": SpeciesInfo("Tussock", "Tussock Pennata", 4_447_100,
        colony_range=200, atmospheres="CO2", temp_range="145-155 K"),
    "Tussock Serrati": SpeciesInfo("Tussock", "Tussock Serrati", 4_447_100,
        colony_range=200, atmospheres="CO2", temp_range="170-175 K",
        notes="Hilly regions"),
    "Tussock Stigmasis": SpeciesInfo("Tussock", "Tussock Stigmasis", 19_010_800,
        colony_range=200, notes="High value"),
    "Tussock Triticum": SpeciesInfo("Tussock", "Tussock Triticum", 7_774_700,
        colony_range=200, atmospheres="CO2", temp_range="190-195 K"),
    "Tussock Ventusa": SpeciesInfo("Tussock", "Tussock Ventusa", 3_252_500,
        colony_range=200, atmospheres="CO2", temp_range="155-160 K"),
    "Tussock Virgam": SpeciesInfo("Tussock", "Tussock Virgam", 14_313_700,
        colony_range=200, notes="High value"),
}

# -- Case-insensitive lookup index ----------------------------------
# Built once at module import so lookups are fast O(1) dict access.

SPECIES_BY_NAME: dict[str, SpeciesInfo] = {}
for s in SPECIES.values():
    key = s.name.lower()
    if key not in SPECIES_BY_NAME:
        SPECIES_BY_NAME[key] = s


# -- Public API -----------------------------------------------------

def lookup(name: str) -> Optional[SpeciesInfo]:
    """Look up a species by full name (case-insensitive)."""
    return SPECIES_BY_NAME.get(name.lower().strip())


def base_value(name: str) -> int:
    """Return the base CR value for a complete set of *name*.

    Returns 0 if the species is not in the database.
    """
    info = lookup(name)
    return info.base_value if info else 0


def total_value(name: str, first_footfall: bool = False) -> int:
    """Return the total CR value for a set, optionally with first-footfall bonus.

    First footfall bonus = 5x base value (the game pays base + 4× bonus).
    """
    bv = base_value(name)
    if first_footfall:
        return bv * 5
    return bv


def species_by_genus(genus: str) -> list[SpeciesInfo]:
    """Return all species belonging to a given genus (case-insensitive)."""
    return [s for s in SPECIES.values() if s.genus.lower() == genus.lower()]


def all_genera() -> list[str]:
    """Return a sorted list of all genus names present in the database."""
    return sorted(set(s.genus for s in SPECIES.values()))


def search(query: str) -> list[SpeciesInfo]:
    """Search species by name or genus (substring, case-insensitive)."""
    q = query.lower()
    return [
        s for s in SPECIES.values()
        if q in s.name.lower() or q in s.genus.lower()
    ]
