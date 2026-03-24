import json
import urllib.request
from pathlib import Path

SOURCE_URL = "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/master/json/countries+states+cities.json"
OUTPUT_FILE = Path("india_locations.js")

def normalize_name(name: str) -> str:
    return " ".join(name.strip().upper().split())

def main():
    with urllib.request.urlopen(SOURCE_URL) as response:
        data = json.load(response)

    india = next((c for c in data if c.get("name") == "India"), None)
    if not india:
        raise RuntimeError("India not found in source dataset")

    result = {}

    for state in india.get("states", []):
        state_name = normalize_name(state.get("name", ""))
        if not state_name:
            continue

        cities = []
        for city in state.get("cities", []):
            city_name = normalize_name(city.get("name", ""))
            if city_name:
                cities.append(city_name)

        cities = sorted(set(cities))
        result[state_name] = cities

    js = "const INDIA_LOCATIONS = " + json.dumps(result, ensure_ascii=False, indent=2) + ";"
    OUTPUT_FILE.write_text(js, encoding="utf-8")

    print(f"Wrote {OUTPUT_FILE} with {len(result)} states/UTs.")

if __name__ == "__main__":
    main()