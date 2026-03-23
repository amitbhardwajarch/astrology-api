from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

from dasha_engine import (
    get_julian_day_local,
    calculate_sidereal_moon_longitude,
    calculate_dasha_balance,
    calculate_all_graha_positions,
    calculate_lagna,
    build_sign_chart,
    generate_mahadasha_sequence,
    get_remaining_antardashas_at_birth,
)

app = FastAPI(
    title="Astrology API",
    version="1.0.0",
    description="MVP astrology calculation API for Dasha, Lagna, Graha positions, and chart mapping."
)


class BirthInput(BaseModel):
    dob: str
    tob: str
    tz: float
    lat: float
    lon: float


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Astrology API running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/calculate")
def calculate(data: BirthInput):
    birth_dt = datetime.strptime(f"{data.dob} {data.tob}", "%Y-%m-%d %H:%M")
    jd = get_julian_day_local(data.dob, data.tob, data.tz)

    moon_longitude = calculate_sidereal_moon_longitude(jd)
    dasha_result = calculate_dasha_balance(moon_longitude)
    graha_positions = calculate_all_graha_positions(jd)
    lagna = calculate_lagna(jd, data.lat, data.lon)
    chart = build_sign_chart(lagna["sign"], graha_positions)

    mahadasha_sequence = generate_mahadasha_sequence(
        birth_dt=birth_dt,
        start_lord=dasha_result["lord"],
        balance_years_float=dasha_result["balance_years_float"],
        count=9
    )

    antardasha_sequence = get_remaining_antardashas_at_birth(
        mahadasha_lord=dasha_result["lord"],
        birth_dt=birth_dt,
        balance_years_float=dasha_result["balance_years_float"]
    )

    return {
        "input": {
            "dob": data.dob,
            "tob": data.tob,
            "tz": data.tz,
            "lat": data.lat,
            "lon": data.lon,
        },
        "core_result": {
            "moon_longitude": round(moon_longitude, 6),
            "nakshatra": dasha_result["nakshatra"],
            "dasha_lord": dasha_result["lord"],
            "balance": dasha_result["balance"],
        },
        "lagna": lagna,
        "graha_positions": graha_positions,
        "chart": chart,
        "mahadasha_sequence": [
            {
                "lord": item["lord"],
                "start": item["start"].strftime("%Y-%m-%d"),
                "end": item["end"].strftime("%Y-%m-%d"),
                "years": round(item["years"], 6) if isinstance(item["years"], float) else item["years"],
            }
            for item in mahadasha_sequence
        ],
        "remaining_antardasha_sequence": [
            {
                "lord": f'{item["mahadasha_lord"]}/{item["antardasha_lord"]}',
                "start": item["start"].strftime("%Y-%m-%d"),
                "end": item["end"].strftime("%Y-%m-%d"),
                "years": round(item["years"], 6),
            }
            for item in antardasha_sequence
        ],
    }