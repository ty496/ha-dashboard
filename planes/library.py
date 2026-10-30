# The plane-art library: which airline + type combinations get a poster drawing.
# Picked 2026-10-30 from a live ADS-B sample (adsb.lol, 110 aircraft within 40 nm of the house)
# plus the airlines' known Denver fleets. Key = "<airline ICAO>-<type ICAO>"; GEN = plain white
# fallback by type. UAX = United Express (SkyWest/Republic flights out of DEN mostly wear it).
COMBOS = [
    ("UAL", "B738", "United Airlines", "Boeing 737-800"),
    ("UAL", "B739", "United Airlines", "Boeing 737-900"),
    ("UAL", "B38M", "United Airlines", "Boeing 737 MAX 8"),
    ("UAL", "B39M", "United Airlines", "Boeing 737 MAX 9"),
    ("UAL", "A319", "United Airlines", "Airbus A319"),
    ("UAL", "A320", "United Airlines", "Airbus A320"),
    ("UAL", "A21N", "United Airlines", "Airbus A321neo"),
    ("UAL", "B752", "United Airlines", "Boeing 757-200"),
    ("UAL", "B772", "United Airlines", "Boeing 777-200"),
    ("UAL", "B789", "United Airlines", "Boeing 787-9"),
    ("UAX", "E75L", "United Express", "Embraer 175"),
    ("UAX", "CRJ7", "United Express", "CRJ-700"),
    ("UAX", "CRJ2", "United Express", "CRJ-200"),
    ("SWA", "B737", "Southwest Airlines", "Boeing 737-700"),
    ("SWA", "B738", "Southwest Airlines", "Boeing 737-800"),
    ("SWA", "B38M", "Southwest Airlines", "Boeing 737 MAX 8"),
    ("FFT", "A20N", "Frontier Airlines", "Airbus A320neo"),
    ("FFT", "A21N", "Frontier Airlines", "Airbus A321neo"),
    ("AAL", "A321", "American Airlines", "Airbus A321"),
    ("AAL", "B738", "American Airlines", "Boeing 737-800"),
    ("AAL", "A319", "American Airlines", "Airbus A319"),
    ("DAL", "A321", "Delta Air Lines", "Airbus A321"),
    ("DAL", "B739", "Delta Air Lines", "Boeing 737-900"),
    ("DAL", "A320", "Delta Air Lines", "Airbus A320"),
    ("DAL", "BCS3", "Delta Air Lines", "Airbus A220-300"),
    ("ASA", "B39M", "Alaska Airlines", "Boeing 737 MAX 9"),
    ("ASA", "B739", "Alaska Airlines", "Boeing 737-900"),
    ("ACA", "BCS3", "Air Canada", "Airbus A220-300"),
    ("BAW", "A35K", "British Airways", "Airbus A350-1000"),
    ("SCX", "B738", "Sun Country Airlines", "Boeing 737-800"),
    ("AAY", "A320", "Allegiant Air", "Airbus A320"),
    ("GEN", "C172", "", "Cessna 172"),
    ("GEN", "PA44", "", "Piper PA-44 Seminole"),
    ("GEN", "P28A", "", "Piper PA-28"),
    ("GEN", "SR22", "", "Cirrus SR22"),
    ("GEN", "PC12", "", "Pilatus PC-12"),
    ("GEN", "C56X", "", "Cessna Citation Excel"),
    ("GEN", "CL35", "", "Bombardier Challenger 350"),
    ("GEN", "GLEX", "", "Bombardier Global Express"),
    ("GEN", "HELI", "", "Airbus Helicopters H125"),
    ("GEN", "NARROW", "", "Boeing 737-800"),
    ("GEN", "REGIONAL", "", "Embraer 175"),
    ("GEN", "WIDE", "", "Boeing 787-9"),
]


def key(c):
    return f"{c[0]}-{c[1]}"
