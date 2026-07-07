MATERIAL_REF = {
    "Raw": {
        "Raw Material Category 1": {1: "Carbon", 2: "Vanadium", 3: "Niobium", 4: "Yttrium"},
        "Raw Material Category 2": {1: "Phosphorus", 2: "Chromium", 3: "Molybdenum", 4: "Technetium"},
        "Raw Material Category 3": {1: "Sulphur", 2: "Manganese", 3: "Cadmium", 4: "Ruthenium"},
        "Raw Material Category 4": {1: "Iron", 2: "Zinc", 3: "Tin", 4: "Selenium"},
        "Raw Material Category 5": {1: "Nickel", 2: "Germanium", 3: "Tungsten", 4: "Tellurium"},
        "Raw Material Category 6": {1: "Rhenium", 2: "Arsenic", 3: "Mercury", 4: "Polonium"},
        "Raw Material Category 7": {1: "Lead", 2: "Zirconium", 3: "Boron", 4: "Antimony"},
    },
    "Encoded": {
        "Emission Data": {1: "Exceptional Scrambled Emission Data", 2: "Irregular Emission Data", 3: "Unexpected Emission Data", 4: "Decoded Emission Data", 5: "Abnormal Compact Emissions Data"},
        "Wake Scans": {1: "Atypical Disrupted Wake Echoes", 2: "Anomalous FSD Telemetry", 3: "Strange Wake Solutions", 4: "Eccentric Hyperspace Trajectories", 5: "Datamined Wake Exceptions"},
        "Shield Data": {1: "Distorted Shield Cycle Recordings", 2: "Inconsistent Shield Soak Analysis", 3: "Untypical Shield Scans", 4: "Aberrant Shield Pattern Analysis", 5: "Peculiar Shield Frequency Data"},
        "Encryption Files": {1: "Unusual Encrypted Files", 2: "Tagged Encryption Codes", 3: "Open Symmetric Keys", 4: "Atypical Encryption Archives", 5: "Adaptive Encryptors Capture"},
        "Data Archives": {1: "Anomalous Bulk Scan Data", 2: "Unidentified Scan Archives", 3: "Classified Scan Databanks", 4: "Divergent Scan Data", 5: "Classified Scan Fragment"},
        "Encoded Firmware": {1: "Specialised Legacy Firmware", 2: "Modified Consumer Firmware", 3: "Cracked Industrial Firmware", 4: "Security Firmware Patch", 5: "Modified Embedded Firmware"},
    },
    "Manufactured": {
        "Chemical": {1: "Chemical Storage Units", 2: "Chemical Processors", 3: "Chemical Distillery", 4: "Chemical Manipulators", 5: "Pharmaceutical Isolators"},
        "Thermic": {1: "Tempered Alloys", 2: "Heat Resistant Ceramics", 3: "Precipitated Alloys", 4: "Thermic Alloys", 5: "Military Grade Alloys"},
        "Heat": {1: "Heat Conduction Wiring", 2: "Heat Dispersion Plate", 3: "Heat Exchangers", 4: "Heat Vanes", 5: "Proto Heat Radiators"},
        "Conductive": {1: "Basic Conductors", 2: "Conductive Components", 3: "Conductive Ceramics", 4: "Conductive Polymers", 5: "Biotech Conductors"},
        "Mechanical Components": {1: "Mechanical Scrap", 2: "Mechanical Equipment", 3: "Mechanical Components", 4: "Configurable Components", 5: "Improvised Components"},
        "Capacitors": {1: "Grid Resistors", 2: "Hybrid Capacitors", 3: "Electrochemical Arrays", 4: "Polymer Capacitors", 5: "Military Supercapacitors"},
        "Shielding": {1: "Worn Shield Emitters", 2: "Shield Emitters", 3: "Shielding Sensors", 4: "Compound Shielding", 5: "Imperial Shielding"},
        "Composite": {1: "Compact Composites", 2: "Filament Composites", 3: "High Density Composites", 4: "Proprietary Composites", 5: "Core Dynamics Composites"},
        "Crystals": {1: "Crystal Shards", 2: "Flawed Focus Crystals", 3: "Focus Crystals", 4: "Refined Focus Crystals", 5: "Exquisite Focus Crystals"},
        "Alloys": {1: "Salvaged Alloys", 2: "Galvanising Alloys", 3: "Phase Alloys", 4: "Proto Light Alloys", 5: "Proto Radiolic Alloys"},
    },
}

_CATEGORY_GRADE_COUNT = {
    "Raw": 4,
    "Encoded": 5,
    "Manufactured": 5,
}

# Journal internal Name (lowercase) -> {section, grade, category, localised}
JOURNAL_LOOKUP = {
    # Raw — journal uses lowercase element names
    "carbon": {"section": "Raw Material Category 1", "grade": 1, "category": "Raw", "localised": "Carbon"},
    "vanadium": {"section": "Raw Material Category 1", "grade": 2, "category": "Raw", "localised": "Vanadium"},
    "niobium": {"section": "Raw Material Category 1", "grade": 3, "category": "Raw", "localised": "Niobium"},
    "yttrium": {"section": "Raw Material Category 1", "grade": 4, "category": "Raw", "localised": "Yttrium"},
    "phosphorus": {"section": "Raw Material Category 2", "grade": 1, "category": "Raw", "localised": "Phosphorus"},
    "chromium": {"section": "Raw Material Category 2", "grade": 2, "category": "Raw", "localised": "Chromium"},
    "molybdenum": {"section": "Raw Material Category 2", "grade": 3, "category": "Raw", "localised": "Molybdenum"},
    "technetium": {"section": "Raw Material Category 2", "grade": 4, "category": "Raw", "localised": "Technetium"},
    "sulphur": {"section": "Raw Material Category 3", "grade": 1, "category": "Raw", "localised": "Sulphur"},
    "manganese": {"section": "Raw Material Category 3", "grade": 2, "category": "Raw", "localised": "Manganese"},
    "cadmium": {"section": "Raw Material Category 3", "grade": 3, "category": "Raw", "localised": "Cadmium"},
    "ruthenium": {"section": "Raw Material Category 3", "grade": 4, "category": "Raw", "localised": "Ruthenium"},
    "iron": {"section": "Raw Material Category 4", "grade": 1, "category": "Raw", "localised": "Iron"},
    "zinc": {"section": "Raw Material Category 4", "grade": 2, "category": "Raw", "localised": "Zinc"},
    "tin": {"section": "Raw Material Category 4", "grade": 3, "category": "Raw", "localised": "Tin"},
    "selenium": {"section": "Raw Material Category 4", "grade": 4, "category": "Raw", "localised": "Selenium"},
    "nickel": {"section": "Raw Material Category 5", "grade": 1, "category": "Raw", "localised": "Nickel"},
    "germanium": {"section": "Raw Material Category 5", "grade": 2, "category": "Raw", "localised": "Germanium"},
    "tungsten": {"section": "Raw Material Category 5", "grade": 3, "category": "Raw", "localised": "Tungsten"},
    "tellurium": {"section": "Raw Material Category 5", "grade": 4, "category": "Raw", "localised": "Tellurium"},
    "rhenium": {"section": "Raw Material Category 6", "grade": 1, "category": "Raw", "localised": "Rhenium"},
    "arsenic": {"section": "Raw Material Category 6", "grade": 2, "category": "Raw", "localised": "Arsenic"},
    "mercury": {"section": "Raw Material Category 6", "grade": 3, "category": "Raw", "localised": "Mercury"},
    "polonium": {"section": "Raw Material Category 6", "grade": 4, "category": "Raw", "localised": "Polonium"},
    "lead": {"section": "Raw Material Category 7", "grade": 1, "category": "Raw", "localised": "Lead"},
    "zirconium": {"section": "Raw Material Category 7", "grade": 2, "category": "Raw", "localised": "Zirconium"},
    "boron": {"section": "Raw Material Category 7", "grade": 3, "category": "Raw", "localised": "Boron"},
    "antimony": {"section": "Raw Material Category 7", "grade": 4, "category": "Raw", "localised": "Antimony"},
    # Encoded — Emission Data
    "scrambledemissiondata": {"section": "Emission Data", "grade": 1, "category": "Encoded", "localised": "Exceptional Scrambled Emission Data"},
    "archivedemissiondata": {"section": "Emission Data", "grade": 2, "category": "Encoded", "localised": "Irregular Emission Data"},
    "emissiondata": {"section": "Emission Data", "grade": 3, "category": "Encoded", "localised": "Unexpected Emission Data"},
    "decodedemissiondata": {"section": "Emission Data", "grade": 4, "category": "Encoded", "localised": "Decoded Emission Data"},
    "compactemissionsdata": {"section": "Emission Data", "grade": 5, "category": "Encoded", "localised": "Abnormal Compact Emissions Data"},
    # Encoded — Wake Scans
    "disruptedwakeechoes": {"section": "Wake Scans", "grade": 1, "category": "Encoded", "localised": "Atypical Disrupted Wake Echoes"},
    "fsdtelemetry": {"section": "Wake Scans", "grade": 2, "category": "Encoded", "localised": "Anomalous FSD Telemetry"},
    "wakesolutions": {"section": "Wake Scans", "grade": 3, "category": "Encoded", "localised": "Strange Wake Solutions"},
    "hyperspacetrajectories": {"section": "Wake Scans", "grade": 4, "category": "Encoded", "localised": "Eccentric Hyperspace Trajectories"},
    "dataminedwake": {"section": "Wake Scans", "grade": 5, "category": "Encoded", "localised": "Datamined Wake Exceptions"},
    # Encoded — Shield Data
    "shieldcyclerecordings": {"section": "Shield Data", "grade": 1, "category": "Encoded", "localised": "Distorted Shield Cycle Recordings"},
    "shieldsoakanalysis": {"section": "Shield Data", "grade": 2, "category": "Encoded", "localised": "Inconsistent Shield Soak Analysis"},
    "shielddensityreports": {"section": "Shield Data", "grade": 3, "category": "Encoded", "localised": "Untypical Shield Scans"},
    "shieldpatternanalysis": {"section": "Shield Data", "grade": 4, "category": "Encoded", "localised": "Aberrant Shield Pattern Analysis"},
    "shieldfrequencydata": {"section": "Shield Data", "grade": 5, "category": "Encoded", "localised": "Peculiar Shield Frequency Data"},
    # Encoded — Encryption Files
    "encryptedfiles": {"section": "Encryption Files", "grade": 1, "category": "Encoded", "localised": "Unusual Encrypted Files"},
    "encryptioncodes": {"section": "Encryption Files", "grade": 2, "category": "Encoded", "localised": "Tagged Encryption Codes"},
    "symmetrickeys": {"section": "Encryption Files", "grade": 3, "category": "Encoded", "localised": "Open Symmetric Keys"},
    "encryptionarchives": {"section": "Encryption Files", "grade": 4, "category": "Encoded", "localised": "Atypical Encryption Archives"},
    "adaptiveencryptors": {"section": "Encryption Files", "grade": 5, "category": "Encoded", "localised": "Adaptive Encryptors Capture"},
    # Encoded — Data Archives
    "bulkscandata": {"section": "Data Archives", "grade": 1, "category": "Encoded", "localised": "Anomalous Bulk Scan Data"},
    "scanarchives": {"section": "Data Archives", "grade": 2, "category": "Encoded", "localised": "Unidentified Scan Archives"},
    "scandatabanks": {"section": "Data Archives", "grade": 3, "category": "Encoded", "localised": "Classified Scan Databanks"},
    "encodedscandata": {"section": "Data Archives", "grade": 4, "category": "Encoded", "localised": "Divergent Scan Data"},
    "classifiedscandata": {"section": "Data Archives", "grade": 5, "category": "Encoded", "localised": "Classified Scan Fragment"},
    # Encoded — Encoded Firmware
    "legacyfirmware": {"section": "Encoded Firmware", "grade": 1, "category": "Encoded", "localised": "Specialised Legacy Firmware"},
    "consumerfirmware": {"section": "Encoded Firmware", "grade": 2, "category": "Encoded", "localised": "Modified Consumer Firmware"},
    "industrialfirmware": {"section": "Encoded Firmware", "grade": 3, "category": "Encoded", "localised": "Cracked Industrial Firmware"},
    "securityfirmware": {"section": "Encoded Firmware", "grade": 4, "category": "Encoded", "localised": "Security Firmware Patch"},
    "embeddedfirmware": {"section": "Encoded Firmware", "grade": 5, "category": "Encoded", "localised": "Modified Embedded Firmware"},
    # Manufactured — Chemical
    "chemicalstorageunits": {"section": "Chemical", "grade": 1, "category": "Manufactured", "localised": "Chemical Storage Units"},
    "chemicalprocessors": {"section": "Chemical", "grade": 2, "category": "Manufactured", "localised": "Chemical Processors"},
    "chemicaldistillery": {"section": "Chemical", "grade": 3, "category": "Manufactured", "localised": "Chemical Distillery"},
    "chemicalmanipulators": {"section": "Chemical", "grade": 4, "category": "Manufactured", "localised": "Chemical Manipulators"},
    "pharmaceuticalisolators": {"section": "Chemical", "grade": 5, "category": "Manufactured", "localised": "Pharmaceutical Isolators"},
    # Manufactured — Thermic
    "temperedalloys": {"section": "Thermic", "grade": 1, "category": "Manufactured", "localised": "Tempered Alloys"},
    "heatresistantceramics": {"section": "Thermic", "grade": 2, "category": "Manufactured", "localised": "Heat Resistant Ceramics"},
    "precipitatedalloys": {"section": "Thermic", "grade": 3, "category": "Manufactured", "localised": "Precipitated Alloys"},
    "thermicalloys": {"section": "Thermic", "grade": 4, "category": "Manufactured", "localised": "Thermic Alloys"},
    "militarygradealloys": {"section": "Thermic", "grade": 5, "category": "Manufactured", "localised": "Military Grade Alloys"},
    # Manufactured — Heat
    "heatconductionwiring": {"section": "Heat", "grade": 1, "category": "Manufactured", "localised": "Heat Conduction Wiring"},
    "heatdispersionplate": {"section": "Heat", "grade": 2, "category": "Manufactured", "localised": "Heat Dispersion Plate"},
    "heatexchangers": {"section": "Heat", "grade": 3, "category": "Manufactured", "localised": "Heat Exchangers"},
    "heatvanes": {"section": "Heat", "grade": 4, "category": "Manufactured", "localised": "Heat Vanes"},
    "protoheatradiators": {"section": "Heat", "grade": 5, "category": "Manufactured", "localised": "Proto Heat Radiators"},
    # Manufactured — Conductive
    "basicconductors": {"section": "Conductive", "grade": 1, "category": "Manufactured", "localised": "Basic Conductors"},
    "conductivecomponents": {"section": "Conductive", "grade": 2, "category": "Manufactured", "localised": "Conductive Components"},
    "conductiveceramics": {"section": "Conductive", "grade": 3, "category": "Manufactured", "localised": "Conductive Ceramics"},
    "conductivepolymers": {"section": "Conductive", "grade": 4, "category": "Manufactured", "localised": "Conductive Polymers"},
    "biotechconductors": {"section": "Conductive", "grade": 5, "category": "Manufactured", "localised": "Biotech Conductors"},
    # Manufactured — Mechanical Components
    "mechanicalscrap": {"section": "Mechanical Components", "grade": 1, "category": "Manufactured", "localised": "Mechanical Scrap"},
    "mechanicalequipment": {"section": "Mechanical Components", "grade": 2, "category": "Manufactured", "localised": "Mechanical Equipment"},
    "mechanicalcomponents": {"section": "Mechanical Components", "grade": 3, "category": "Manufactured", "localised": "Mechanical Components"},
    "configurablecomponents": {"section": "Mechanical Components", "grade": 4, "category": "Manufactured", "localised": "Configurable Components"},
    "improvisedcomponents": {"section": "Mechanical Components", "grade": 5, "category": "Manufactured", "localised": "Improvised Components"},
    # Manufactured — Capacitors
    "gridresistors": {"section": "Capacitors", "grade": 1, "category": "Manufactured", "localised": "Grid Resistors"},
    "hybridcapacitors": {"section": "Capacitors", "grade": 2, "category": "Manufactured", "localised": "Hybrid Capacitors"},
    "electrochemicalarrays": {"section": "Capacitors", "grade": 3, "category": "Manufactured", "localised": "Electrochemical Arrays"},
    "polymercapacitors": {"section": "Capacitors", "grade": 4, "category": "Manufactured", "localised": "Polymer Capacitors"},
    "militarysupercapacitors": {"section": "Capacitors", "grade": 5, "category": "Manufactured", "localised": "Military Supercapacitors"},
    # Manufactured — Shielding
    "wornshieldemitters": {"section": "Shielding", "grade": 1, "category": "Manufactured", "localised": "Worn Shield Emitters"},
    "shieldemitters": {"section": "Shielding", "grade": 2, "category": "Manufactured", "localised": "Shield Emitters"},
    "shieldingsensors": {"section": "Shielding", "grade": 3, "category": "Manufactured", "localised": "Shielding Sensors"},
    "compoundshielding": {"section": "Shielding", "grade": 4, "category": "Manufactured", "localised": "Compound Shielding"},
    "imperialshielding": {"section": "Shielding", "grade": 5, "category": "Manufactured", "localised": "Imperial Shielding"},
    # Manufactured — Composite
    "compactcomposites": {"section": "Composite", "grade": 1, "category": "Manufactured", "localised": "Compact Composites"},
    "filamentcomposites": {"section": "Composite", "grade": 2, "category": "Manufactured", "localised": "Filament Composites"},
    "highdensitycomposites": {"section": "Composite", "grade": 3, "category": "Manufactured", "localised": "High Density Composites"},
    "fedproprietarycomposites": {"section": "Composite", "grade": 4, "category": "Manufactured", "localised": "Proprietary Composites"},
    "fedcorecomposites": {"section": "Composite", "grade": 5, "category": "Manufactured", "localised": "Core Dynamics Composites"},
    # Manufactured — Crystals
    "crystalshards": {"section": "Crystals", "grade": 1, "category": "Manufactured", "localised": "Crystal Shards"},
    "uncutfocuscrystals": {"section": "Crystals", "grade": 2, "category": "Manufactured", "localised": "Flawed Focus Crystals"},
    "focuscrystals": {"section": "Crystals", "grade": 3, "category": "Manufactured", "localised": "Focus Crystals"},
    "refinedfocuscrystals": {"section": "Crystals", "grade": 4, "category": "Manufactured", "localised": "Refined Focus Crystals"},
    "exquisitefocuscrystals": {"section": "Crystals", "grade": 5, "category": "Manufactured", "localised": "Exquisite Focus Crystals"},
    # Manufactured — Alloys
    "salvagedalloys": {"section": "Alloys", "grade": 1, "category": "Manufactured", "localised": "Salvaged Alloys"},
    "galvanisingalloys": {"section": "Alloys", "grade": 2, "category": "Manufactured", "localised": "Galvanising Alloys"},
    "phasealloys": {"section": "Alloys", "grade": 3, "category": "Manufactured", "localised": "Phase Alloys"},
    "protolightalloys": {"section": "Alloys", "grade": 4, "category": "Manufactured", "localised": "Proto Light Alloys"},
    "proradiolicalloys": {"section": "Alloys", "grade": 5, "category": "Manufactured", "localised": "Proto Radiolic Alloys"},
}

# Also build a lookup by display name (lowercase for Name_Localised fallback)
NAME_LOOKUP = {info["localised"].lower(): info for info in JOURNAL_LOOKUP.values()}

MATERIAL_TOTALS = {cat: sum(len(grades) for grades in refs.values()) for cat, refs in MATERIAL_REF.items()}
