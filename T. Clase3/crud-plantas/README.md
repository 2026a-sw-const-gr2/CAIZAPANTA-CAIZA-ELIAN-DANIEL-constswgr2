# Catalogo de Plantas de Interior - CRUD EPN FIS

**Taller:** Construccion de Software - Mantenimiento  
**Tema:** Gestion de Plantas de Interior  
**Framework:** Python 3 + Flask + SQLite  
**Integracion:** EPN Event Manager Hub por `POST /events`

## Instalacion rapida

```bash
pip install flask requests
python crud_plantas.py
```

El CRUD queda disponible en:

- Interfaz web: `http://localhost:4000`
- API REST: `http://localhost:4000/plantas`
- Health check: `http://localhost:4000/health`

Antes de probar la integracion completa, levantar tambien el hub:

```bash
cd ../epn-event-manager
npm install
npm run start:dev
```

## Entidad: Planta de Interior

| Campo | Tipo | Requerido | Descripcion |
| --- | --- | --- | --- |
| `id` | int | auto | Clave primaria |
| `nombre` | string | si | Nombre de la planta |
| `tipo` | string | si | Categoria, por ejemplo Tropical o Suculenta |
| `frecuencia_riego` | string | si | Frecuencia de riego |
| `luz_requerida` | string | si | Tipo de luz necesaria |
| `descripcion` | string | no | Detalle opcional |
| `created_at` | ISO date | auto | Fecha de creacion |
| `updated_at` | ISO date | auto | Ultima modificacion |

## Endpoints

### Crear planta

```powershell
curl.exe -X POST http://localhost:4000/plantas -H "Content-Type: application/json" -d "{\"nombre\":\"Pothos Dorado\",\"tipo\":\"Tropical\",\"frecuencia_riego\":\"Cada 7 dias\",\"luz_requerida\":\"Luz indirecta\",\"descripcion\":\"Ideal para interiores\"}"
```

Envia evento `CREATE` al Event Manager.

### Listar plantas

```powershell
curl.exe http://localhost:4000/plantas
```

Envia evento `QUERY` al Event Manager.

### Obtener una planta

```powershell
curl.exe http://localhost:4000/plantas/1
```

Envia evento `QUERY` al Event Manager.

### Actualizar planta

```powershell
curl.exe -X PUT http://localhost:4000/plantas/1 -H "Content-Type: application/json" -d "{\"frecuencia_riego\":\"Cada 10 dias\"}"
```

Envia evento `UPDATE` con el estado antes y despues.

### Eliminar planta

```powershell
curl.exe -X DELETE http://localhost:4000/plantas/1
```

Envia evento `DELETE` con los datos eliminados.

## Evento enviado al hub

```json
{
  "source": "crud-plantas",
  "entity": "plant",
  "action": "CREATE",
  "title": "Planta registrada en catalogo",
  "description": "Se registro la planta Pothos Dorado de tipo Tropical",
  "payload": {
    "id": 1,
    "nombre": "Pothos Dorado",
    "tipo": "Tropical"
  }
}
```

## Verificar integracion

Con ambos servidores activos:

```powershell
curl.exe http://localhost:3000/events
curl.exe http://localhost:3000/events/source/crud-plantas
curl.exe http://localhost:3000/events/entity/plant
curl.exe http://localhost:3000/stats
```
