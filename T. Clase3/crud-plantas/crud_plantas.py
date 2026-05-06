"""
crud_plantas.py — Catálogo de Plantas de Interior
Taller: Construcción de Software — Mantenimiento | EPN FIS
Integración: EPN Event Manager Hub (POST /events)

Uso:
    pip install flask requests
    python crud_plantas.py

    (El Event Manager debe estar corriendo en localhost:3000)
"""

import sqlite3
import requests
import os
from datetime import datetime
from flask import Flask, request, jsonify, abort

# ─── Configuración ────────────────────────────────────────────
app = Flask(__name__)
DB_PATH = os.getenv("DB_PATH", "plantas.db")
EVENT_MANAGER_URL = os.getenv("EVENT_MANAGER_URL", "http://localhost:3000")
PORT = int(os.getenv("PORT", 4000))

# ─── Base de datos ────────────────────────────────────────────
def get_db():
    """Retorna una conexión SQLite con row_factory para dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea la tabla plantas si no existe."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plantas (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre           TEXT    NOT NULL,
                tipo             TEXT    NOT NULL,
                frecuencia_riego TEXT    NOT NULL,
                luz_requerida    TEXT    NOT NULL,
                descripcion      TEXT,
                created_at       TEXT    DEFAULT (datetime('now')),
                updated_at       TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    print("[DB] Base de datos lista: plantas.db")

# ─── Cliente del Event Manager ────────────────────────────────
def send_event(action: str, title: str, description: str, payload: dict):
    """
    Envía un evento al EPN Event Manager Hub.
    Si falla, sólo registra un warning sin bloquear el CRUD.
    """
    body = {
        "source":      "crud-plantas",
        "entity":      "plant",
        "action":      action,          # CREATE | UPDATE | DELETE | QUERY
        "title":       title,
        "description": description,
        "payload":     payload,
    }
    try:
        resp = requests.post(
            f"{EVENT_MANAGER_URL}/events",
            json=body,
            timeout=5
        )
        print(f"[EventManager] ✅ [{action}] {title} → HTTP {resp.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[EventManager] ⚠️  No se pudo registrar evento '{title}': {e}")

# ─── Helper ───────────────────────────────────────────────────
def row_to_dict(row):
    return dict(row) if row else None

# ═════════════════════════════════════════════════════════════
# ENDPOINTS CRUD
# ═════════════════════════════════════════════════════════════

# ─── GET /plantas — Listar todas ─────────────────────────────
@app.route("/plantas", methods=["GET"])
def listar_plantas():
    try:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM plantas ORDER BY created_at DESC"
            ).fetchall()
        plantas = [row_to_dict(r) for r in rows]

        send_event(
            action="QUERY",
            title="Consulta de catálogo completo",
            description=f"Se consultaron {len(plantas)} plantas del catálogo",
            payload={"count": len(plantas)},
        )
        return jsonify({"success": True, "total": len(plantas), "data": plantas})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─── GET /plantas/<id> — Obtener una ─────────────────────────
@app.route("/plantas/<int:plant_id>", methods=["GET"])
def obtener_planta(plant_id):
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM plantas WHERE id = ?", (plant_id,)
            ).fetchone()

        if not row:
            return jsonify({"success": False, "error": "Planta no encontrada"}), 404

        planta = row_to_dict(row)
        send_event(
            action="QUERY",
            title="Consulta de planta individual",
            description=f"Se consultó la planta: \"{planta['nombre']}\"",
            payload={"id": planta["id"], "nombre": planta["nombre"]},
        )
        return jsonify({"success": True, "data": planta})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─── POST /plantas — Crear ────────────────────────────────────
@app.route("/plantas", methods=["POST"])
def crear_planta():
    try:
        data = request.get_json(force=True) or {}

        # Validación de campos requeridos
        required = ["nombre", "tipo", "frecuencia_riego", "luz_requerida"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({
                "success": False,
                "error": f"Campos requeridos faltantes: {', '.join(missing)}"
            }), 400

        # Validación de longitud
        if len(data["nombre"]) > 100:
            return jsonify({"success": False, "error": "nombre máx 100 caracteres"}), 400
        if len(data["tipo"]) > 50:
            return jsonify({"success": False, "error": "tipo máx 50 caracteres"}), 400

        nombre           = data["nombre"].strip()
        tipo             = data["tipo"].strip()
        frecuencia_riego = data["frecuencia_riego"].strip()
        luz_requerida    = data["luz_requerida"].strip()
        descripcion      = data.get("descripcion", "").strip() or None

        with get_db() as conn:
            cursor = conn.execute(
                """INSERT INTO plantas (nombre, tipo, frecuencia_riego, luz_requerida, descripcion)
                   VALUES (?, ?, ?, ?, ?)""",
                (nombre, tipo, frecuencia_riego, luz_requerida, descripcion)
            )
            conn.commit()
            nueva = row_to_dict(conn.execute(
                "SELECT * FROM plantas WHERE id = ?", (cursor.lastrowid,)
            ).fetchone())

        send_event(
            action="CREATE",
            title="Planta registrada en catálogo",
            description=f"Se registró la planta \"{nombre}\" de tipo \"{tipo}\"",
            payload=nueva,
        )
        return jsonify({"success": True, "data": nueva}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─── PUT /plantas/<id> — Actualizar ──────────────────────────
@app.route("/plantas/<int:plant_id>", methods=["PUT"])
def actualizar_planta(plant_id):
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM plantas WHERE id = ?", (plant_id,)
            ).fetchone()

        if not row:
            return jsonify({"success": False, "error": "Planta no encontrada"}), 404

        antes = row_to_dict(row)
        data  = request.get_json(force=True) or {}

        nombre           = data.get("nombre",           antes["nombre"]).strip()
        tipo             = data.get("tipo",             antes["tipo"]).strip()
        frecuencia_riego = data.get("frecuencia_riego", antes["frecuencia_riego"]).strip()
        luz_requerida    = data.get("luz_requerida",    antes["luz_requerida"]).strip()
        descripcion      = data.get("descripcion",      antes["descripcion"])

        with get_db() as conn:
            conn.execute(
                """UPDATE plantas
                   SET nombre=?, tipo=?, frecuencia_riego=?,
                       luz_requerida=?, descripcion=?,
                       updated_at=datetime('now')
                   WHERE id=?""",
                (nombre, tipo, frecuencia_riego, luz_requerida, descripcion, plant_id)
            )
            conn.commit()
            despues = row_to_dict(conn.execute(
                "SELECT * FROM plantas WHERE id = ?", (plant_id,)
            ).fetchone())

        send_event(
            action="UPDATE",
            title="Planta actualizada",
            description=f"Se actualizaron los datos de la planta \"{despues['nombre']}\"",
            payload={"antes": antes, "despues": despues},
        )
        return jsonify({"success": True, "data": despues})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─── DELETE /plantas/<id> — Eliminar ─────────────────────────
@app.route("/plantas/<int:plant_id>", methods=["DELETE"])
def eliminar_planta(plant_id):
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM plantas WHERE id = ?", (plant_id,)
            ).fetchone()

        if not row:
            return jsonify({"success": False, "error": "Planta no encontrada"}), 404

        planta = row_to_dict(row)
        with get_db() as conn:
            conn.execute("DELETE FROM plantas WHERE id = ?", (plant_id,))
            conn.commit()

        send_event(
            action="DELETE",
            title="Planta eliminada del catálogo",
            description=f"Se eliminó la planta \"{planta['nombre']}\" ({planta['tipo']}) del catálogo",
            payload=planta,
        )
        return jsonify({
            "success": True,
            "message": f"Planta \"{planta['nombre']}\" eliminada correctamente"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─── GET /health ──────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":      "UP",
        "service":     "crud-plantas",
        "description": "Catálogo de Plantas de Interior",
        "timestamp":   datetime.utcnow().isoformat() + "Z",
        "version":     "1.0.0",
    })


# ─── 404 global ───────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Ruta no encontrada"}), 404


# ─── Arranque ─────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print()
    print("🌱  =========================================")
    print("🌱   CRUD — Catálogo de Plantas de Interior")
    print("🌱  =========================================")
    print(f"🌱   URL:           http://localhost:{PORT}")
    print(f"📡   Event Manager: {EVENT_MANAGER_URL}")
    print()
    print("   Endpoints:")
    print(f"   GET    /plantas")
    print(f"   GET    /plantas/<id>")
    print(f"   POST   /plantas")
    print(f"   PUT    /plantas/<id>")
    print(f"   DELETE /plantas/<id>")
    print(f"   GET    /health")
    print()
    app.run(host="0.0.0.0", port=PORT, debug=False)
