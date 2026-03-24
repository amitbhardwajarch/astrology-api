from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from dasha_engine import (
    build_navamsa_chart,
    build_sign_chart,
    calculate_all_graha_positions,
    calculate_dasha_balance,
    calculate_lagna,
    calculate_sidereal_moon_longitude,
    generate_mahadasha_sequence,
    get_current_dasha,
    get_julian_day_local,
)

app = FastAPI(title="Astroguruji API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BirthInput(BaseModel):
    dob: str
    tob: str
    tz: float
    lat: float
    lon: float
    country: str = "India"
    state: str = ""
    city: str = ""


@app.get("/")
def home():
    return FileResponse("index.html")


@app.get("/india_locations.js")
def india_locations():
    return FileResponse("india_locations.js", media_type="application/javascript")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/calculate")
def calculate(data: BirthInput):
    jd = get_julian_day_local(data.dob, data.tob, data.tz)
    birth_dt = datetime.strptime(f"{data.dob} {data.tob}", "%Y-%m-%d %H:%M")

    graha_positions = calculate_all_graha_positions(jd)
    lagna = calculate_lagna(jd, data.lat, data.lon)
    moon_longitude = calculate_sidereal_moon_longitude(jd)
    dasha = calculate_dasha_balance(moon_longitude)

    mahadasha = generate_mahadasha_sequence(
        birth_dt=birth_dt,
        start_lord=dasha["lord"],
        balance_years_float=dasha["balance_years_float"],
        count=9,
    )
    current_dasha = get_current_dasha(mahadasha)

    rasi_chart = build_sign_chart(lagna["sign"], graha_positions)
    navamsa_chart = build_navamsa_chart(lagna["longitude"], graha_positions)

    return {
        "input": {
            "dob": data.dob,
            "tob": data.tob,
            "tz": data.tz,
            "lat": data.lat,
            "lon": data.lon,
            "country": data.country,
            "state": data.state,
            "city": data.city,
        },
        "core_result": {
            "moon_nakshatra": dasha["nakshatra"],
            "dasha_lord": dasha["lord"],
            "balance": dasha["balance"],
            "current_dasha": {
                "lord": current_dasha["lord"] if current_dasha else dasha["lord"],
                "start": current_dasha["start"].strftime("%Y-%m-%d") if current_dasha else data.dob,
                "end": current_dasha["end"].strftime("%Y-%m-%d") if current_dasha else data.dob,
            },
        },
        "lagna": lagna,
        "graha_positions": graha_positions,
        "rasi_chart": rasi_chart,
        "navamsa_chart": navamsa_chart,
        "mahadasha": [
            {
                "lord": item["lord"],
                "start": item["start"].strftime("%Y-%m-%d"),
                "end": item["end"].strftime("%Y-%m-%d"),
                "years": round(item["years"], 4),
            }
            for item in mahadasha
        ],
    }