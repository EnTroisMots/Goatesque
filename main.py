import sqlite3
import datetime
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE L'APPLICATION ET DE LA BASE DE DONNÉES
# ------------------------------------------------------------------------------

DB_FILE = "pyrosentinel.db"
app = FastAPI(title="PyroSentinel Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """Crée et retourne une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise la table unifiée 'mesures' et ses index."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mesures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            temperature_sol REAL,
            temperature_air REAL,
            humidite REAL,
            co REAL,
            wind_speed REAL,
            battery_level REAL,
            timestamp TEXT NOT NULL,
            criticite TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON mesures(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_unit_id ON mesures(unit_id)")
    conn.commit()
    conn.close()

init_db()


# ------------------------------------------------------------------------------
# 2. MODÈLES DE DONNÉES (Pydantic)
# ------------------------------------------------------------------------------

class MeasureInput(BaseModel):
    unit_id: str
    mode: str  # "Balise" ou "Sonde"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    temperature_sol: Optional[float] = None
    temperature_air: Optional[float] = None
    humidite: Optional[float] = None
    co: Optional[float] = None
    wind_speed: Optional[float] = None
    battery_level: Optional[float] = None
    timestamp: Optional[str] = None  # Format ISO 8601 (YYYY-MM-DDTHH:MM:SS)


# ------------------------------------------------------------------------------
# 3. MOTEUR DE RÈGLES MÉTIER ET GESTION DE LA RÉTENTION
# ------------------------------------------------------------------------------

def evaluer_criticite(measure: MeasureInput) -> str:
    """
    Évalue le niveau de criticité (VERT, JAUNE, ROUGE) de manière déterministe.
    Les seuils sont basés sur le taux de CO et la température de l'air.
    """
    co = measure.co if measure.co is not None else 0.0
    temp_air = measure.temperature_air if measure.temperature_air is not None else 0.0
    temp_sol = measure.temperature_sol if measure.temperature_sol is not None else 0.0

    if co >= 50.0 or temp_air >= 55.0 or temp_sol >= 70.0:
        return "ROUGE"
    
    if co >= 20.0 or temp_air >= 40.0 or temp_sol >= 50.0:
        return "JAUNE"

    return "VERT"

def purger_donnees_anciennes():
    """Supprime automatiquement les mesures de plus de 7 jours."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mesures WHERE timestamp < datetime('now', '-7 days')")
    conn.commit()
    conn.close()


# ------------------------------------------------------------------------------
# 4. GESTIONNAIRE DE WEBSOCKETS
# ------------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Diffuse un message JSON à tous les clients connectés."""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()


# ------------------------------------------------------------------------------
# 5. ENDPOINTS DE L'API REST & WEBSOCKET
# ------------------------------------------------------------------------------

@app.post("/api/measures", status_code=201)
async def ingest_measure(measure: MeasureInput, background_tasks: BackgroundTasks):
    """
    Ingère une trame JSON, calcule la criticité, l'enregistre dans SQLite
    et diffuse l'événement via WebSocket pour la mise à jour temps réel.
    """
    current_time = measure.timestamp or datetime.datetime.now().isoformat()
    criticite = evaluer_criticite(measure)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mesures (
            unit_id, mode, latitude, longitude, temperature_sol, 
            temperature_air, humidite, co, wind_speed, battery_level, 
            timestamp, criticite
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        measure.unit_id, measure.mode, measure.latitude, measure.longitude,
        measure.temperature_sol, measure.temperature_air, measure.humidite,
        measure.co, measure.wind_speed, measure.battery_level,
        current_time, criticite
    ))
    conn.commit()
    conn.close()

    background_tasks.add_task(purger_donnees_anciennes)

    record = measure.dict()
    record["timestamp"] = current_time
    record["criticite"] = criticite

    # Diffusion systématique à toutes les cartes en temps réel
    await manager.broadcast({
        "type": "MEASURE_UPDATE",
        "data": record
    })

    return {"status": "success", "criticite": criticite, "data": record}


@app.get("/api/measures/latest")
def get_latest_measures():
    """Récupère la dernière mesure connue pour chaque unité active."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.* FROM mesures m
        INNER JOIN (
            SELECT unit_id, MAX(timestamp) as max_time
            FROM mesures
            GROUP BY unit_id
        ) latest ON m.unit_id = latest.unit_id AND m.timestamp = latest.max_time
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/units/{unit_id}/history")
def get_unit_history(unit_id: str, limit: int = 50):
    """Récupère l'historique récent d'une unité spécifique."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM mesures 
        WHERE unit_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (unit_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail="Unité non trouvée ou aucune donnée disponible")
        
    return [dict(row) for row in rows]


@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    """Canal WebSocket pour l'interface PyroMap."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/measures/history")
def get_measures_history(
    unit_id: Optional[str] = None, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM mesures WHERE 1=1"
    params = []

    if start_date:
        query += " AND REPLACE(timestamp, 'T', ' ') >= ?"
        params.append(start_date)

    if unit_id:
        query += " AND unit_id = ?"
        params.append(unit_id)
        
    if end_date:
        query += " AND REPLACE(timestamp, 'T', ' ') <= ?"
        params.append(end_date)
        
    query += " ORDER BY timestamp DESC LIMIT 200"
    
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows