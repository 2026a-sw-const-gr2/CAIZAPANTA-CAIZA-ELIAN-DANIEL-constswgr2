# 🌱 Catálogo de Plantas de Interior — CRUD EPN FIS

**Taller:** Construcción de Software — Mantenimiento  
**Tema:** Gestión de Plantas de Interior  
**Framework:** Python 3 + Flask + SQLite (built-in)  
**Integración:** EPN Event Manager Hub

---

## Instalación rápida

```bash
# 1. Instalar dependencias (solo 2 paquetes)
pip install flask requests

# 2. Levantar el Event Manager primero en otro terminal
#    (clonar el repo del profesor → seguir sus instrucciones)

# 3. Iniciar el CRUD
python crud_plantas.py
```

El CRUD queda en: **http://localhost:4000**

> **Variables de entorno opcionales:**
> ```bash
> PORT=4000 EVENT_MANAGER_URL=http://localhost:3000 python crud_plantas.py
> ```

---

## Entidad: Planta de Interior

| Campo            | Tipo   | Req | Descripción                             |
|------------------|--------|-----|-----------------------------------------|
| id               | int    | auto| Clave primaria                          |
| nombre           | string | ✅  | Nombre de la planta (ej: "Pothos")      |
| tipo             | string | ✅  | Categoría (Tropical, Suculenta, etc)    |
| frecuencia_riego | string | ✅  | Frecuencia de riego (ej: "Cada 7 días") |
| luz_requerida    | string | ✅  | Luz necesaria (ej: "Luz indirecta")     |
| descripcion      | string | ❌  | Descripción opcional                    |
| created_at       | date   | auto| Fecha de creación                       |
| updated_at       | date   | auto| Última modificación                     |

---

## Endpoints

### `POST /plantas` — Crear planta
```bash
curl -X POST http://localhost:4000/plantas \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Pothos Dorado",
    "tipo": "Tropical",
    "frecuencia_riego": "Cada 7 días",
    "luz_requerida": "Luz indirecta media",
    "descripcion": "Muy resistente, ideal para interiores"
  }'
```
→ Envía evento **CREATE** al hub

---

### `GET /plantas` — Listar todas
```bash
curl http://localhost:4000/plantas
```
→ Envía evento **QUERY** al hub

---

### `GET /plantas/<id>` — Obtener una
```bash
curl http://localhost:4000/plantas/1
```
→ Envía evento **QUERY** al hub

---

### `PUT /plantas/<id>` — Actualizar
```bash
curl -X PUT http://localhost:4000/plantas/1 \
  -H "Content-Type: application/json" \
  -d '{"frecuencia_riego": "Cada 10 días"}'
```
→ Envía evento **UPDATE** al hub (incluye estado antes/después)

---

### `DELETE /plantas/<id>` — Eliminar
```bash
curl -X DELETE http://localhost:4000/plantas/1
```
→ Envía evento **DELETE** al hub

---

### `GET /health` — Estado del servicio
```bash
curl http://localhost:4000/health
```
```json
{ "status": "UP", "service": "crud-plantas", "version": "1.0.0", "timestamp": "..." }
```

---

## Evento enviado al hub (ejemplo)

```json
{
  "source": "crud-plantas",
  "entity": "plant",
  "action": "CREATE",
  "title": "Planta registrada en catálogo",
  "description": "Se registró la planta \"Pothos Dorado\" de tipo \"Tropical\"",
  "payload": {
    "id": 1,
    "nombre": "Pothos Dorado",
    "tipo": "Tropical",
    "frecuencia_riego": "Cada 7 días",
    "luz_requerida": "Luz indirecta media",
    "descripcion": "Muy resistente"
  }
}
```

---

## Verificar integración

Con el Event Manager corriendo, después de operar el CRUD:

```bash
# Ver todos los eventos registrados
curl http://localhost:3000/events

# Ver solo eventos de este CRUD
curl http://localhost:3000/events/source/crud-plantas

# Ver solo eventos de la entidad plant
curl http://localhost:3000/events/entity/plant

# Estadísticas generales
curl http://localhost:3000/stats
```
