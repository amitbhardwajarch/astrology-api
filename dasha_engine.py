import swisseph as swe
from datetime import datetime, timezone, timedelta

# =========================
# CONSTANTS
# =========================

NAKSHATRAS = [
    ("Ashwini", "Ketu"),
    ("Bharani", "Venus"),
    ("Krittika", "Sun"),
    ("Rohini", "Moon"),
    ("Mrigashira", "Mars"),
    ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"),
    ("Pushya", "Saturn"),
    ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"),
    ("Purva Phalguni", "Venus"),
    ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"),
    ("Chitra", "Mars"),
    ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"),
    ("Anuradha", "Saturn"),
    ("Jyeshtha", "Mercury"),
    ("Moola", "Ketu"),
    ("Purva Ashadha", "Venus"),
    ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"),
    ("Dhanishta", "Mars"),
    ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"),
    ("Uttara Bhadrapada", "Saturn"),
    ("Revati", "Mercury")
]

DASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17
}

DASHA_ORDER = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury"
]

RASHIS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}

# =========================
# UTILITY
# =========================

def get_julian_day_local(dob: str, tob: str, tz_offset_hours: float) -> float:
    local_dt = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
    offset = timedelta(hours=tz_offset_hours)
    utc_dt = local_dt.replace(tzinfo=timezone(offset)).astimezone(timezone.utc)

    return swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    )

def add_years_approx(start_date: datetime, years_float: float) -> datetime:
    days = int(years_float * 365.25)
    return start_date + timedelta(days=days)

def zodiac_from_longitude(longitude: float):
    sign_index = int(longitude // 30) % 12
    degree_in_sign = longitude % 30
    return RASHIS[sign_index], round(degree_in_sign, 6)

# =========================
# CORE ASTROLOGY
# =========================

def setup_sidereal():
    swe.set_sid_mode(swe.SIDM_LAHIRI)

def calculate_sidereal_longitude(jd: float, planet_code: int) -> float:
    setup_sidereal()
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    data = swe.calc_ut(jd, planet_code, flags)[0]
    return data[0]

def calculate_all_graha_positions(jd: float) -> dict:
    positions = {}

    for name, code in PLANETS.items():
        lon = calculate_sidereal_longitude(jd, code)
        sign, deg = zodiac_from_longitude(lon)
        positions[name] = {
            "longitude": round(lon, 6),
            "sign": sign,
            "degree_in_sign": deg
        }

    ketu_lon = (positions["Rahu"]["longitude"] + 180.0) % 360.0
    ketu_sign, ketu_deg = zodiac_from_longitude(ketu_lon)
    positions["Ketu"] = {
        "longitude": round(ketu_lon, 6),
        "sign": ketu_sign,
        "degree_in_sign": ketu_deg
    }

    return positions

def calculate_lagna(jd: float, lat: float, lon: float):
    setup_sidereal()
    houses = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
    asc = houses[0][0]
    sign, deg = zodiac_from_longitude(asc)
    return {
        "longitude": round(asc, 6),
        "sign": sign,
        "degree_in_sign": deg
    }

def calculate_sidereal_moon_longitude(jd: float) -> float:
    return calculate_sidereal_longitude(jd, swe.MOON)

def calculate_dasha_balance(moon_longitude: float) -> dict:
    nak_degree = 13.333333333333334
    nak_index = int(moon_longitude // nak_degree) % 27
    nak_name, lord = NAKSHATRAS[nak_index]

    position_in_nak = moon_longitude % nak_degree
    remaining = nak_degree - position_in_nak
    fraction_remaining = remaining / nak_degree

    total_years = DASHA_YEARS[lord]
    balance_years_float = total_years * fraction_remaining

    years = int(balance_years_float)
    months_float = (balance_years_float - years) * 12
    months = int(months_float)
    days = int((months_float - months) * 30)

    return {
        "nakshatra": nak_name,
        "lord": lord,
        "balance_years_float": balance_years_float,
        "balance": {
            "years": years,
            "months": months,
            "days": days
        }
    }

# =========================
# DASHA
# =========================

def generate_mahadasha_sequence(
    birth_dt: datetime,
    start_lord: str,
    balance_years_float: float,
    count: int = 9
):
    sequence = []

    current_start = birth_dt
    current_end = add_years_approx(current_start, balance_years_float)

    sequence.append({
        "lord": start_lord,
        "start": current_start,
        "end": current_end,
        "years": balance_years_float
    })

    start_index = DASHA_ORDER.index(start_lord)
    next_index = (start_index + 1) % len(DASHA_ORDER)

    for _ in range(count - 1):
        lord = DASHA_ORDER[next_index]
        years = DASHA_YEARS[lord]
        next_start = current_end
        next_end = add_years_approx(next_start, years)

        sequence.append({
            "lord": lord,
            "start": next_start,
            "end": next_end,
            "years": years
        })

        current_end = next_end
        next_index = (next_index + 1) % len(DASHA_ORDER)

    return sequence

def generate_full_antardasha_sequence(mahadasha_lord: str, mahadasha_start: datetime):
    mahadasha_years = DASHA_YEARS[mahadasha_lord]
    start_index = DASHA_ORDER.index(mahadasha_lord)

    sequence = []
    current_start = mahadasha_start

    for i in range(9):
        antardasha_lord = DASHA_ORDER[(start_index + i) % len(DASHA_ORDER)]
        antardasha_years = (mahadasha_years * DASHA_YEARS[antardasha_lord]) / 120.0
        current_end = add_years_approx(current_start, antardasha_years)

        sequence.append({
            "mahadasha_lord": mahadasha_lord,
            "antardasha_lord": antardasha_lord,
            "start": current_start,
            "end": current_end,
            "years": antardasha_years
        })

        current_start = current_end

    return sequence

def get_remaining_antardashas_at_birth(
    mahadasha_lord: str,
    birth_dt: datetime,
    balance_years_float: float
):
    total_mahadasha_years = DASHA_YEARS[mahadasha_lord]
    elapsed_years_before_birth = total_mahadasha_years - balance_years_float

    full_mahadasha_start = birth_dt - timedelta(days=int(elapsed_years_before_birth * 365.25))
    full_sequence = generate_full_antardasha_sequence(mahadasha_lord, full_mahadasha_start)

    remaining = []
    for item in full_sequence:
        if item["end"] > birth_dt:
            clipped_start = max(item["start"], birth_dt)
            remaining.append({
                "mahadasha_lord": item["mahadasha_lord"],
                "antardasha_lord": item["antardasha_lord"],
                "start": clipped_start,
                "end": item["end"],
                "years": item["years"]
            })

    return remaining

# =========================
# CHART LAYOUT
# =========================

def build_sign_chart(lagna_sign: str, graha_positions: dict) -> dict:
    chart = {sign: [] for sign in RASHIS}

    chart[lagna_sign].append("Lagna")

    for graha, data in graha_positions.items():
        chart[data["sign"]].append(graha)

    return chart

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    dob = input("Enter DOB (YYYY-MM-DD): ").strip()
    tob = input("Enter Time of Birth (HH:MM, 24-hour): ").strip()
    tz = float(input("Enter Timezone offset from UTC (e.g. 5.5 for India): ").strip())
    lat = float(input("Enter Latitude (e.g. 28.6139): ").strip())
    lon = float(input("Enter Longitude (e.g. 77.2090): ").strip())

    birth_dt = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
    jd = get_julian_day_local(dob, tob, tz)

    moon_longitude = calculate_sidereal_moon_longitude(jd)
    dasha_result = calculate_dasha_balance(moon_longitude)
    graha_positions = calculate_all_graha_positions(jd)
    lagna = calculate_lagna(jd, lat, lon)
    chart = build_sign_chart(lagna["sign"], graha_positions)

    print("\n--- Core Result ---")
    print("Sidereal Moon Longitude:", round(moon_longitude, 6))
    print("Nakshatra:", dasha_result["nakshatra"])
    print("Dasha Lord:", dasha_result["lord"])
    print(
        "Balance:",
        f'{dasha_result["balance"]["years"]} years, '
        f'{dasha_result["balance"]["months"]} months, '
        f'{dasha_result["balance"]["days"]} days'
    )

    print("\n--- Lagna ---")
    print(
        f'Lagna: {lagna["sign"]} {lagna["degree_in_sign"]:.6f}° '
        f'(absolute {lagna["longitude"]:.6f}°)'
    )

    print("\n--- Graha Positions ---")
    for graha, data in graha_positions.items():
        print(
            f'{graha}: {data["sign"]} {data["degree_in_sign"]:.6f}° '
            f'(absolute {data["longitude"]:.6f}°)'
        )

    mahadasha_sequence = generate_mahadasha_sequence(
        birth_dt=birth_dt,
        start_lord=dasha_result["lord"],
        balance_years_float=dasha_result["balance_years_float"],
        count=9
    )

    print("\n--- Mahadasha Sequence ---")
    for item in mahadasha_sequence:
        print(
            f'{item["lord"]}: '
            f'{item["start"].strftime("%Y-%m-%d")} to '
            f'{item["end"].strftime("%Y-%m-%d")}'
        )

    print("\n--- Remaining Antardasha Sequence At Birth ---")
    antardasha_sequence = get_remaining_antardashas_at_birth(
        mahadasha_lord=dasha_result["lord"],
        birth_dt=birth_dt,
        balance_years_float=dasha_result["balance_years_float"]
    )

    for item in antardasha_sequence:
        print(
            f'{item["mahadasha_lord"]}/{item["antardasha_lord"]}: '
            f'{item["start"].strftime("%Y-%m-%d")} to '
            f'{item["end"].strftime("%Y-%m-%d")}'
        )

    print("\n--- Sign-wise Chart Placement ---")
    for sign in RASHIS:
        print(f"{sign}: {', '.join(chart[sign]) if chart[sign] else '-'}")