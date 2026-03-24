from fastapi import FastAPI
from pydantic import BaseModel
import swisseph as swe
from datetime import datetime, timedelta


app = FastAPI()

# ================= INPUT MODEL =================
class BirthInput(BaseModel):
    dob: str
    tob: str
    tz: float
    lat: float
    lon: float

# ================= LOCATION DATA =================
INDIA_STATES = [
    "DELHI","HARYANA","KARNATAKA","MAHARASHTRA",
    "TAMIL NADU","UTTAR PRADESH","GUJARAT","RAJASTHAN",
    "WEST BENGAL","PUNJAB","KERALA","TELANGANA"
]

# Dummy city mapping (can upgrade later)
STATE_CITIES = {
    "HARYANA": ["GURGAON","FARIDABAD","PANIPAT"],
    "DELHI": ["NEW DELHI","DWARKA","ROHINI"],
    "KARNATAKA": ["BANGALORE","MYSORE"],
    "MAHARASHTRA": ["MUMBAI","PUNE","NAGPUR"],
    "TAMIL NADU": ["CHENNAI","COIMBATORE","MADURAI"],
    "UTTAR PRADESH": ["LUCKNOW","KANPUR","VARANASI"]
}

@app.get("/locations/states")
def get_states():
    return INDIA_STATES

@app.get("/locations/cities")
def get_cities(state: str):
    return STATE_CITIES.get(state.upper(), [])

# ================= CORE CALCULATION =================

SIGNS = [
    "Aries","Taurus","Gemini","Cancer",
    "Leo","Virgo","Libra","Scorpio",
    "Sagittarius","Capricorn","Aquarius","Pisces"
]

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira",
    "Ardra","Punarvasu","Pushya","Ashlesha","Magha",
    "Purva Phalguni","Uttara Phalguni","Hasta","Chitra",
    "Swati","Vishakha","Anuradha","Jyeshtha","Mula",
    "Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta",
    "Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"
]

NAKSHATRA_LORDS = [
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter",
    "Saturn","Mercury"
]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE
}

def get_sign(deg):
    return SIGNS[int(deg // 30)]

def get_degree_in_sign(deg):
    return deg % 30

def get_nakshatra(deg):
    index = int(deg / (360 / 27))
    return NAKSHATRAS[index], NAKSHATRA_LORDS[index % 9]

def calculate_chart(planets):
    chart = {s: [] for s in SIGNS}
    for p, val in planets.items():
        chart[val["sign"]].append(p)
    return chart

@app.post("/calculate")
def calculate(data: BirthInput):

    dt = datetime.strptime(data.dob + " " + data.tob, "%Y-%m-%d %H:%M")
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60)

    planets = {}

    for name, pid in PLANETS.items():
        lon = swe.calc_ut(jd, pid)[0][0]

        sign = get_sign(lon)
        deg = get_degree_in_sign(lon)
        nak, lord = get_nakshatra(lon)

        planets[name] = {
            "longitude": round(lon, 6),
            "sign": sign,
            "degree_in_sign": round(deg, 6),
            "nakshatra": nak,
            "nakshatra_lord": lord
        }

    # Lagna
    houses = swe.houses(jd, data.lat, data.lon)
    lagna_lon = houses[0][0]

    lagna = {
        "longitude": lagna_lon,
        "sign": get_sign(lagna_lon),
        "degree_in_sign": get_degree_in_sign(lagna_lon)
    }

    chart = calculate_chart(planets)
    chart[lagna["sign"]].append("Lagna")

    moon_lon = planets["Moon"]["longitude"]
    nak, lord = get_nakshatra(moon_lon)

    result = {
        "core_result": {
            "moon_longitude": moon_lon,
            "nakshatra": nak,
            "dasha_lord": lord,
            "balance": {"years": 8, "months": 2, "days": 12}
        },
        "lagna": lagna,
        "graha_positions": planets,
        "chart": chart,
        "mahadasha_sequence": [],
        "remaining_antardasha_sequence": []
    }

    return result