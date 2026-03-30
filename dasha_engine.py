import swisseph as swe
from datetime import datetime, timezone, timedelta

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
    ("Revati", "Mercury"),
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
    "Mercury": 17,
}

DASHA_ORDER = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]

KP_LORD_SEQUENCE = DASHA_ORDER[:]  # same Vimshottari order
TOTAL_DASHA_YEARS = 120.0
NAKSHATRA_SPAN = 13.333333333333334  # 13°20'

def get_kp_division_lord(offset_in_span: float, span_length: float, start_lord: str):
    """
    Given an offset inside a span and the starting Vimshottari lord,
    return which lord owns that subdivision using proportional KP division.
    """
    start_index = KP_LORD_SEQUENCE.index(start_lord)
    running = 0.0

    for i in range(9):
        lord = KP_LORD_SEQUENCE[(start_index + i) % 9]
        lord_span = span_length * (DASHA_YEARS[lord] / TOTAL_DASHA_YEARS)
        if running <= offset_in_span < running + lord_span:
            return lord, running, lord_span
        running += lord_span

    # fallback for floating-point edge
    lord = KP_LORD_SEQUENCE[(start_index + 8) % 9]
    lord_span = span_length * (DASHA_YEARS[lord] / TOTAL_DASHA_YEARS)
    return lord, running - lord_span, lord_span


def get_kp_details(longitude: float):
    """
    Returns Nakshatra, Nakshatra Lord, Sub-Lord, and Sub-Sub-Lord
    for a given longitude using KP-style Vimshottari subdivision.
    """
    nakshatra, nak_lord = get_nakshatra_info(longitude)

    position_in_nak = longitude % NAKSHATRA_SPAN

    sub_lord, sub_start, sub_span = get_kp_division_lord(
        position_in_nak,
        NAKSHATRA_SPAN,
        nak_lord
    )

    position_in_sub = position_in_nak - sub_start

    sub_sub_lord, _, _ = get_kp_division_lord(
        position_in_sub,
        sub_span,
        sub_lord
    )

    return {
        "nakshatra": nakshatra,
        "nakshatra_lord": nak_lord,
        "sub_lord": sub_lord,
        "sub_sub_lord": sub_sub_lord,
    }

RASHIS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
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


def setup_sidereal():
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def get_julian_day_local(dob: str, tob: str, tz_offset_hours: float) -> float:
    local_dt = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
    offset = timedelta(hours=tz_offset_hours)
    utc_dt = local_dt.replace(tzinfo=timezone(offset)).astimezone(timezone.utc)
    return swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
    )


def add_years_approx(start_date: datetime, years_float: float) -> datetime:
    return start_date + timedelta(days=int(years_float * 365.25))


def zodiac_from_longitude(longitude: float):
    sign_index = int(longitude // 30) % 12
    degree_in_sign = longitude % 30
    return RASHIS[sign_index], round(degree_in_sign, 6)


def get_nakshatra_info(longitude: float):
    nak_degree = 13.333333333333334
    nak_index = int(longitude // nak_degree) % 27
    return NAKSHATRAS[nak_index]


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
        nakshatra, nak_lord = get_nakshatra_info(lon)
        positions[name] = {
            "longitude": round(lon, 6),
            "sign": sign,
            "degree_in_sign": deg,
            "nakshatra": nakshatra,
            "nakshatra_lord": nak_lord,
        }

    ketu_lon = (positions["Rahu"]["longitude"] + 180.0) % 360.0
    ketu_sign, ketu_deg = zodiac_from_longitude(ketu_lon)
    ketu_nak, ketu_lord = get_nakshatra_info(ketu_lon)
    positions["Ketu"] = {
        "longitude": round(ketu_lon, 6),
        "sign": ketu_sign,
        "degree_in_sign": ketu_deg,
        "nakshatra": ketu_nak,
        "nakshatra_lord": ketu_lord,
    }

    return positions


def calculate_lagna(jd: float, lat: float, lon: float):
    setup_sidereal()
    houses = swe.houses_ex(jd, lat, lon, b"P", swe.FLG_SIDEREAL)
    asc = houses[0][0]
    sign, deg = zodiac_from_longitude(asc)
    kp = get_kp_details(asc)

    return {
        "longitude": round(asc, 6),
        "sign": sign,
        "degree_in_sign": deg,
        "nakshatra": kp["nakshatra"],
        "nakshatra_lord": kp["nakshatra_lord"],
        "sub_lord": kp["sub_lord"],
        "sub_sub_lord": kp["sub_sub_lord"],
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
            "days": days,
        },
    }


def generate_mahadasha_sequence(birth_dt: datetime, start_lord: str, balance_years_float: float, count: int = 9):
    sequence = []

    current_start = birth_dt
    current_end = add_years_approx(current_start, balance_years_float)
    sequence.append({
        "lord": start_lord,
        "start": current_start,
        "end": current_end,
        "years": balance_years_float,
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
            "years": years,
        })
        current_end = next_end
        next_index = (next_index + 1) % len(DASHA_ORDER)

    return sequence


def get_current_dasha(mahadasha_sequence, now=None):
    now = now or datetime.now()
    for item in mahadasha_sequence:
        if item["start"] <= now <= item["end"]:
            return item
    if mahadasha_sequence and now < mahadasha_sequence[0]["start"]:
        return mahadasha_sequence[0]
    return mahadasha_sequence[-1] if mahadasha_sequence else None


def build_sign_chart(lagna_sign: str, graha_positions: dict) -> dict:
    chart = {sign: [] for sign in RASHIS}
    chart[lagna_sign].append("Lagna")
    for graha, data in graha_positions.items():
        chart[data["sign"]].append(graha)
    return chart


def navamsa_sign_from_longitude(longitude: float) -> str:
    navamsa_index = int((longitude * 9) // 30) % 12
    return RASHIS[navamsa_index]


def build_navamsa_chart(lagna_longitude: float, graha_positions: dict) -> dict:
    chart = {sign: [] for sign in RASHIS}
    lagna_navamsa = navamsa_sign_from_longitude(lagna_longitude)
    chart[lagna_navamsa].append("Lagna")
    for graha, data in graha_positions.items():
        nav_sign = navamsa_sign_from_longitude(data["longitude"])
        chart[nav_sign].append(graha)
    return chart
