import requests
import time

# URL de votre API FastAPI locale
URL = "http://127.0.0.1:8000/api/measures"

print("Démarrage du simulateur de PyroUnits (Terrain)...")

# Liste de scénarios de test pour voir réagir le moteur de règles et le stockage SQLite
scenarios_test = [
    {
        "nom": "Situation normale (VERT)",
        "data": {
            "unit_id": "BALISE-WIFI-01",
            "mode": "Balise",
            "latitude": 45.1885,
            "longitude": 5.7245,
            "temperature_sol": 20.0,
            "temperature_air": 25.0,
            "humidite": 50.0,
            "co": 5.0,
            "wind_speed": 10.0,
            "battery_level": 95.0
        }
    },
    {
        "nom": "Situation de vigilance (JAUNE)",
        "data": {
            "unit_id": "BALISE-WIFI-01",
            "mode": "Balise",
            "latitude": 45.1885,
            "longitude": 5.7245,
            "temperature_sol": 45.0,
            "temperature_air": 42.0,
            "humidite": 30.0,
            "co": 25.0,
            "wind_speed": 15.0,
            "battery_level": 94.0
        }
    },
    {
        "nom": "Alerte critique d'incendie (ROUGE) -> Déclenche le WebSocket !",
        "data": {
            "unit_id": "BALISE-WIFI-01",
            "mode": "Balise",
            "latitude": 45.1885,
            "longitude": 5.7245,
            "temperature_sol": 75.0,
            "temperature_air": 60.0,
            "humidite": 15.0,
            "co": 65.0,
            "wind_speed": 25.0,
            "battery_level": 92.0
        }
    }
]

for scenario in scenarios_test:
    print(f"\n--- Envoi : {scenario['nom']} ---")
    try:
        response = requests.post(URL, json=scenario["data"])
        if response.status_code == 201:
            resultat = response.json()
            print(f"Succès ! Criticité évaluée par le serveur : {resultat['criticite']}")
        else:
            print(f"Erreur HTTP : {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Impossible de joindre le serveur : {e}")
    
    # Petite pause de 2 secondes entre chaque envoi
    time.sleep(2)

print("\nSimulation terminée avec succès !")