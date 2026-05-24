import json
import sys
import requests

SEASONS = [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

def test_f1_connection(season):
    base_url = f"https://api.jolpi.ca/ergast/f1/{season}/results.json"
  
    params = {"limit": 1000}
    
    print(f"Verbinding maken met de API voor seizoen {season}...")
    print(f"URL: {base_url}")
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        
        response.raise_for_status()

        data = response.json()

        total_results = data.get("MRData", {}).get("total", 0)
        print(f"✓ Succes! HTTP Status Code: {response.status_code}")
        print(f"✓ Totaal aantal resultaat-records gevonden in de API: {total_results}")
        
        output_filename = f"../../raw_results_{season}.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"✓ Bestand succesvol weggeschreven naar: ./{output_filename}")
        
    except requests.exceptions.HTTPError as http_err:
        print(f"× HTTP fout opgetreden: {http_err}", file=sys.stderr)
    except requests.exceptions.ConnectionError:
        print("× Verbindingsfout: Controleer je internetverbinding.", file=sys.stderr)
    except requests.exceptions.Timeout:
        print("× De API deed er te lang over om te antwoorden (Timeout).", file=sys.stderr)
    except Exception as err:
        print(f"× Er ging iets onverwachts mis: {err}", file=sys.stderr)

if __name__ == "__main__":
    for season in SEASONS:
        test_f1_connection(season)