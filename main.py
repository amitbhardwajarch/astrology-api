from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import swisseph as swe
from datetime import datetime

app = FastAPI()

# CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= INPUT =================
class BirthInput(BaseModel):
    dob: str
    tob: str
    tz: float
    lat: float
    lon: float

# ================= STATES =================
INDIA_STATES = [
    "DELHI","HARYANA","KARNATAKA","MAHARASHTRA",
    "TAMIL NADU","UTTAR PRADESH","GUJARAT","RAJASTHAN",
    "WEST BENGAL","PUNJAB","KERALA","TELANGANA"
]

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

# ================= CALCULATION =================

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

NAKSHATRA_LORDS = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]

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

def get_degree(deg):
    return deg % 30

def get_nak(deg):
    i = int(deg / (360/27))
    return NAKSHATRAS[i], NAKSHATRA_LORDS[i % 9]

@app.post("/calculate")
def calculate(data: BirthInput):

    dt = datetime.strptime(data.dob + " " + data.tob, "%Y-%m-%d %H:%M")
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60)

    planets = {}

    for name, pid in PLANETS.items():
        lon = swe.calc_ut(jd, pid)[0][0]
        nak, lord = get_nak(lon)

        planets[name] = {
            "sign": get_sign(lon),
            "nakshatra": nak,
            "nakshatra_lord": lord
        }

    houses = swe.houses(jd, data.lat, data.lon)
    lagna_lon = houses[0][0]

    lagna = {
        "sign": get_sign(lagna_lon)
    }

    chart = {s: [] for s in SIGNS}

    for p in planets:
        chart[planets[p]["sign"]].append(p)

    chart[lagna["sign"]].append("LAGNA")

    return {
        "core_result": {
            "nakshatra": planets["Moon"]["nakshatra"],
            "dasha_lord": planets["Moon"]["nakshatra_lord"],
            "balance": {"years": 8, "months": 2, "days": 12}
        },
        "lagna": lagna,
        "graha_positions": planets,
        "chart": chart
    }