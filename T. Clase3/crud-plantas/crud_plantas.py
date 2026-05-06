"""
CRUD: Catalogo de Plantas de Interior
Taller: Construccion de Software - Mantenimiento | EPN FIS
Integracion: EPN Event Manager Hub (POST /events)

Uso:
    pip install flask requests
    python crud_plantas.py

Abrir en navegador:
    http://localhost:4000
"""

import os
import sqlite3
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, render_template_string, request


app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "plantas.db"))
EVENT_MANAGER_URL = os.getenv("EVENT_MANAGER_URL", "http://localhost:3000")
PORT = int(os.getenv("PORT", "4000"))


INDEX_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Catalogo de Plantas de Interior</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17211b;
      --muted: #5a6a61;
      --line: #d7dfd8;
      --surface: #f7faf7;
      --accent: #2f7d4e;
      --accent-dark: #225f3b;
      --danger: #b3261e;
      --panel: #ffffff;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--surface);
      color: var(--ink);
    }
    header {
      padding: 24px clamp(16px, 4vw, 48px);
      border-bottom: 1px solid var(--line);
      background: #ffffff;
    }
    h1 { margin: 0; font-size: clamp(24px, 4vw, 38px); }
    header p { margin: 8px 0 0; color: var(--muted); }
    main {
      display: grid;
      grid-template-columns: minmax(280px, 380px) 1fr;
      gap: 20px;
      padding: 20px clamp(16px, 4vw, 48px) 40px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    h2 { margin: 0 0 14px; font-size: 18px; }
    label {
      display: block;
      margin: 10px 0 5px;
      font-size: 13px;
      font-weight: 700;
      color: var(--muted);
    }
    input, textarea {
      width: 100%;
      min-height: 40px;
      padding: 9px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      font: inherit;
      background: #fff;
      color: var(--ink);
    }
    textarea { min-height: 74px; resize: vertical; }
    .actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 14px;
    }
    button {
      min-height: 38px;
      border: 0;
      border-radius: 6px;
      padding: 0 14px;
      background: var(--accent);
      color: #fff;
      font-weight: 700;
      cursor: pointer;
    }
    button.secondary { background: #45534a; }
    button.danger { background: var(--danger); }
    button:hover { background: var(--accent-dark); }
    .toolbar {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }
    .status {
      min-height: 22px;
      color: var(--muted);
      font-size: 13px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: #fff;
      font-size: 14px;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
    }
    th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
    .row-actions { display: flex; gap: 6px; flex-wrap: wrap; }
    .row-actions button { min-height: 32px; padding: 0 10px; }
    pre {
      max-height: 220px;
      overflow: auto;
      margin: 12px 0 0;
      padding: 12px;
      background: #111a14;
      color: #e9f2ea;
      border-radius: 8px;
      font-size: 12px;
    }
    @media (max-width: 850px) {
      main { grid-template-columns: 1fr; }
      table { display: block; overflow-x: auto; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Catalogo de Plantas de Interior</h1>
    <p>CRUD personal conectado al EPN Event Manager por POST /events.</p>
  </header>

  <main>
    <section>
      <h2 id="formTitle">Registrar planta</h2>
      <form id="plantForm">
        <input type="hidden" id="plantId">

        <label for="nombre">Nombre</label>
        <input id="nombre" maxlength="100" required placeholder="Pothos Dorado">

        <label for="tipo">Tipo</label>
        <input id="tipo" maxlength="50" required placeholder="Tropical">

        <label for="frecuencia_riego">Frecuencia de riego</label>
        <input id="frecuencia_riego" maxlength="80" required placeholder="Cada 7 dias">

        <label for="luz_requerida">Luz requerida</label>
        <input id="luz_requerida" maxlength="80" required placeholder="Luz indirecta">

        <label for="descripcion">Descripcion</label>
        <textarea id="descripcion" maxlength="250" placeholder="Ideal para interiores"></textarea>

        <div class="actions">
          <button type="submit">Guardar</button>
          <button type="button" class="secondary" onclick="resetForm()">Nuevo</button>
        </div>
      </form>

      <pre id="lastResponse">Listo para registrar eventos.</pre>
    </section>

    <section>
      <div class="toolbar">
        <div>
          <h2>Plantas registradas</h2>
          <div class="status" id="status">Cargando...</div>
        </div>
        <button class="secondary" onclick="loadPlants()">Actualizar</button>
      </div>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Tipo</th>
            <th>Riego</th>
            <th>Luz</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody id="plantRows"></tbody>
      </table>
    </section>
  </main>

  <script>
    const form = document.getElementById('plantForm');
    const lastResponse = document.getElementById('lastResponse');

    function payloadFromForm() {
      return {
        nombre: document.getElementById('nombre').value.trim(),
        tipo: document.getElementById('tipo').value.trim(),
        frecuencia_riego: document.getElementById('frecuencia_riego').value.trim(),
        luz_requerida: document.getElementById('luz_requerida').value.trim(),
        descripcion: document.getElementById('descripcion').value.trim()
      };
    }

    function fillForm(plant) {
      document.getElementById('formTitle').textContent = 'Actualizar planta #' + plant.id;
      document.getElementById('plantId').value = plant.id;
      document.getElementById('nombre').value = plant.nombre || '';
      document.getElementById('tipo').value = plant.tipo || '';
      document.getElementById('frecuencia_riego').value = plant.frecuencia_riego || '';
      document.getElementById('luz_requerida').value = plant.luz_requerida || '';
      document.getElementById('descripcion').value = plant.descripcion || '';
    }

    function resetForm() {
      document.getElementById('formTitle').textContent = 'Registrar planta';
      form.reset();
      document.getElementById('plantId').value = '';
    }

    function showResponse(data) {
      lastResponse.textContent = JSON.stringify(data, null, 2);
    }

    async function loadPlants() {
      const response = await fetch('/plantas');
      const json = await response.json();
      showResponse(json);

      const rows = document.getElementById('plantRows');
      rows.innerHTML = '';
      document.getElementById('status').textContent = json.total + ' planta(s) encontradas';

      json.data.forEach((plant) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${plant.id}</td>
          <td>${plant.nombre}</td>
          <td>${plant.tipo}</td>
          <td>${plant.frecuencia_riego}</td>
          <td>${plant.luz_requerida}</td>
          <td class="row-actions">
            <button class="secondary" data-action="edit">Editar</button>
            <button class="danger" data-action="delete">Eliminar</button>
          </td>
        `;
        tr.querySelector('[data-action="edit"]').addEventListener('click', () => fillForm(plant));
        tr.querySelector('[data-action="delete"]').addEventListener('click', () => deletePlant(plant.id));
        rows.appendChild(tr);
      });
    }

    async function deletePlant(id) {
      const response = await fetch('/plantas/' + id, { method: 'DELETE' });
      const json = await response.json();
      showResponse(json);
      await loadPlants();
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const id = document.getElementById('plantId').value;
      const response = await fetch(id ? '/plantas/' + id : '/plantas', {
        method: id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadFromForm())
      });
      const json = await response.json();
      showResponse(json);
      if (json.success) {
        resetForm();
        await loadPlants();
      }
    });

    loadPlants();
  </script>
</body>
</html>
"""


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plantas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                frecuencia_riego TEXT NOT NULL,
                luz_requerida TEXT NOT NULL,
                descripcion TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    print(f"[DB] Base de datos lista: {DB_PATH}")


def row_to_dict(row):
    return dict(row) if row else None


def validate_text(data, field, max_length, required=True):
    value = data.get(field)
    if value is None:
        if required:
            return None, f"{field} es obligatorio"
        return "", None

    if not isinstance(value, str):
        return None, f"{field} debe ser texto"

    value = value.strip()
    if required and not value:
        return None, f"{field} es obligatorio"

    if len(value) > max_length:
        return None, f"{field} no puede superar {max_length} caracteres"

    return value, None


def send_event(action, title, description, payload):
    body = {
        "source": "crud-plantas",
        "entity": "plant",
        "action": action,
        "title": title,
        "description": description,
        "payload": payload,
    }

    try:
        response = requests.post(f"{EVENT_MANAGER_URL}/events", json=body, timeout=5)
        print(f"[EventManager] {action} {title} -> HTTP {response.status_code}")
    except requests.exceptions.RequestException as exc:
        print(f"[EventManager] No se pudo registrar el evento '{title}': {exc}")


@app.route("/", methods=["GET"])
def index():
    return render_template_string(INDEX_HTML)


@app.route("/plantas", methods=["GET"])
def listar_plantas():
    try:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM plantas ORDER BY id DESC").fetchall()
        plantas = [row_to_dict(row) for row in rows]

        send_event(
            "QUERY",
            "Consulta de catalogo completo",
            f"Se consultaron {len(plantas)} plantas del catalogo",
            {"count": len(plantas)},
        )
        return jsonify({"success": True, "total": len(plantas), "data": plantas})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/plantas/<int:plant_id>", methods=["GET"])
def obtener_planta(plant_id):
    try:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM plantas WHERE id = ?", (plant_id,)).fetchone()

        if not row:
            return jsonify({"success": False, "error": "Planta no encontrada"}), 404

        planta = row_to_dict(row)
        send_event(
            "QUERY",
            "Consulta de planta individual",
            f"Se consulto la planta {planta['nombre']}",
            {"id": planta["id"], "nombre": planta["nombre"]},
        )
        return jsonify({"success": True, "data": planta})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/plantas", methods=["POST"])
def crear_planta():
    try:
        data = request.get_json(force=True, silent=True) or {}
        parsed, error = parse_plant_payload(data)
        if error:
            return jsonify({"success": False, "error": error}), 400

        timestamp = now_iso()
        with get_db() as conn:
            cursor = conn.execute(
                """
                INSERT INTO plantas (
                    nombre, tipo, frecuencia_riego, luz_requerida,
                    descripcion, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    parsed["nombre"],
                    parsed["tipo"],
                    parsed["frecuencia_riego"],
                    parsed["luz_requerida"],
                    parsed["descripcion"],
                    timestamp,
                    timestamp,
                ),
            )
            conn.commit()
            nueva = row_to_dict(
                conn.execute("SELECT * FROM plantas WHERE id = ?", (cursor.lastrowid,)).fetchone()
            )

        send_event(
            "CREATE",
            "Planta registrada en catalogo",
            f"Se registro la planta {nueva['nombre']} de tipo {nueva['tipo']}",
            nueva,
        )
        return jsonify({"success": True, "data": nueva}), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/plantas/<int:plant_id>", methods=["PUT"])
def actualizar_planta(plant_id):
    try:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM plantas WHERE id = ?", (plant_id,)).fetchone()

        if not row:
            return jsonify({"success": False, "error": "Planta no encontrada"}), 404

        antes = row_to_dict(row)
        data = request.get_json(force=True, silent=True) or {}
        merged = {**antes, **data}
        parsed, error = parse_plant_payload(merged)
        if error:
            return jsonify({"success": False, "error": error}), 400

        with get_db() as conn:
            conn.execute(
                """
                UPDATE plantas
                SET nombre = ?, tipo = ?, frecuencia_riego = ?,
                    luz_requerida = ?, descripcion = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    parsed["nombre"],
                    parsed["tipo"],
                    parsed["frecuencia_riego"],
                    parsed["luz_requerida"],
                    parsed["descripcion"],
                    now_iso(),
                    plant_id,
                ),
            )
            conn.commit()
            despues = row_to_dict(
                conn.execute("SELECT * FROM plantas WHERE id = ?", (plant_id,)).fetchone()
            )

        send_event(
            "UPDATE",
            "Planta actualizada",
            f"Se actualizaron los datos de la planta {despues['nombre']}",
            {"antes": antes, "despues": despues},
        )
        return jsonify({"success": True, "data": despues})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/plantas/<int:plant_id>", methods=["DELETE"])
def eliminar_planta(plant_id):
    try:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM plantas WHERE id = ?", (plant_id,)).fetchone()

        if not row:
            return jsonify({"success": False, "error": "Planta no encontrada"}), 404

        planta = row_to_dict(row)
        with get_db() as conn:
            conn.execute("DELETE FROM plantas WHERE id = ?", (plant_id,))
            conn.commit()

        send_event(
            "DELETE",
            "Planta eliminada del catalogo",
            f"Se elimino la planta {planta['nombre']}",
            planta,
        )
        return jsonify({"success": True, "message": f"Planta {planta['nombre']} eliminada"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "UP",
            "service": "crud-plantas",
            "description": "Catalogo de Plantas de Interior",
            "timestamp": now_iso(),
            "version": "1.0.0",
        }
    )


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"success": False, "error": "Ruta no encontrada"}), 404


def parse_plant_payload(data):
    parsed = {}
    limits = {
        "nombre": 100,
        "tipo": 50,
        "frecuencia_riego": 80,
        "luz_requerida": 80,
        "descripcion": 250,
    }

    for field in ["nombre", "tipo", "frecuencia_riego", "luz_requerida"]:
        parsed[field], error = validate_text(data, field, limits[field])
        if error:
            return None, error

    parsed["descripcion"], error = validate_text(
        data, "descripcion", limits["descripcion"], required=False
    )
    if error:
        return None, error

    return parsed, None


if __name__ == "__main__":
    init_db()
    print()
    print("CRUD - Catalogo de Plantas de Interior")
    print(f"URL: http://localhost:{PORT}")
    print(f"Event Manager: {EVENT_MANAGER_URL}")
    print()
    print("Endpoints:")
    print("GET    /")
    print("GET    /plantas")
    print("GET    /plantas/<id>")
    print("POST   /plantas")
    print("PUT    /plantas/<id>")
    print("DELETE /plantas/<id>")
    print("GET    /health")
    print()
    app.run(host="0.0.0.0", port=PORT, debug=False)
