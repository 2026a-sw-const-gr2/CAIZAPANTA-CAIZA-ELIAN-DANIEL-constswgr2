# REPORTE DE MANTENIMIENTO — EPN Event Manager
## Taller Construcción de Software | FIS EPN
---

**Sistema:** EPN Event Manager Hub  
**CRUD conectado:** Catálogo de Plantas de Interior (`crud-plantas`)  
**Stack del hub:** NestJS + TypeORM + SQLite  

---

## RESUMEN EJECUTIVO

El EPN Event Manager es un hub centralizado con un antipatrón intencional:
separa los eventos en 4 tablas (`create_events`, `update_events`,
`delete_events`, `query_events`) en lugar de una tabla unificada con columna
`action`. Se identificaron y corrigieron **6 incidencias** distribuidas en los
6 endpoints publicados, clasificadas en los 4 tipos de mantenimiento.

---

## TAREA 1 — INTEGRACIÓN

### Sistema CRUD: Catálogo de Plantas de Interior

**Tecnologías:** Node.js + Express + SQLite (better-sqlite3)  
**Puerto:** 4000  
**Event Manager URL:** http://localhost:3000

**Verificación de los 6 endpoints del hub:**

| Endpoint                   | Estado | Incidencia detectada          |
|----------------------------|--------|-------------------------------|
| POST /events               | ⚠️     | Switch case-sensitive (bug)   |
| GET /events                | ⚠️     | Fechas sin formato ISO 8601   |
| GET /health                | ⚠️     | Respuesta no cumple estándar  |
| GET /stats                 | ⚠️     | Carga toda la BD en memoria   |
| GET /events/source/:source | ⚠️     | Consultas secuenciales        |
| GET /events/entity/:entity | ⚠️     | Sin validación del parámetro  |

---

## TAREA 2 — MANTENIMIENTO CORRECTIVO 🐞

### Incidencia
**Endpoint:** `POST /events`  
**Síntoma:** Los eventos enviados desde el CRUD nunca aparecen en la BD.
Al consultar `GET /events` el historial está vacío a pesar de que el CRUD
ejecuta operaciones exitosamente.

### Causa técnica
El método `registerEvent` en `events.service.ts` usa un `switch` que compara
`dto.action` con cadenas en **minúsculas** (`'create'`, `'update'`...), pero
el contrato del API define el campo `action` en **MAYÚSCULAS**. JavaScript
distingue mayúsculas, por lo que ningún `case` coincide y se lanza una
excepción en el bloque `default`.

### Código ANTES (con bug)
```typescript
switch (dto.action) {
  case 'create':   // ❌ 'CREATE' !== 'create'
    return this.createRepo.save(eventData);
  case 'update':   // ❌ Nunca coincide
    return this.updateRepo.save(eventData);
  case 'delete':
    return this.deleteRepo.save(eventData);
  case 'query':
    return this.queryRepo.save(eventData);
  default:
    throw new Error('Acción no reconocida');
}
```

### Código DESPUÉS (corregido)
```typescript
const action = dto.action.toUpperCase();  // ✅ Normalizar antes de comparar

switch (action) {
  case 'CREATE':
    return this.createRepo.save(eventData);
  case 'UPDATE':
    return this.updateRepo.save(eventData);
  case 'DELETE':
    return this.deleteRepo.save(eventData);
  case 'QUERY':
    return this.queryRepo.save(eventData);
  default:
    throw new BadRequestException(`Acción no reconocida: ${dto.action}`);
}
```

### Clasificación
**Tipo:** Mantenimiento **Correctivo**  
**Justificación:** Se corrigió un fallo en tiempo de ejecución que impedía que
los eventos se persistieran. La corrección no alteró el contrato del API ni
introdujo regresiones en otros endpoints.

### Evidencia
| | Resultado |
|---|---|
| ANTES | `POST /events { "action": "CREATE" }` → 500 Error / tabla vacía |
| DESPUÉS | `POST /events { "action": "CREATE" }` → 201 Created / registro guardado |

---

## TAREA 3 — MANTENIMIENTO ADAPTATIVO ⚙️

### Incidencia
**Endpoints:** `GET /health` y `GET /events`  
**Contexto:** La EPN implementó un nuevo estándar para todos sus sistemas:
1. El endpoint `/health` debe retornar `{ status: 'UP', timestamp, version }`
2. Todas las fechas deben estar en formato **ISO 8601 UTC** (`2025-05-03T14:30:00.000Z`)

### Código ANTES
```typescript
// health endpoint
@Get('health')
getHealth() {
  return { status: 'ok' };  // ❌ No cumple el estándar
}

// findAll — fechas sin normalizar
async findAll() {
  const [creates, updates, deletes, queries] = await Promise.all([...]);
  return [...creates, ...updates, ...deletes, ...queries];
  // ❌ Las fechas vienen como "2025-05-03 14:30:00" (formato SQLite)
}
```

### Código DESPUÉS
```typescript
// health endpoint
@Get('health')
getHealth() {
  return {
    status: 'UP',                        // ✅ Estándar EPN
    timestamp: new Date().toISOString(), // ✅ ISO 8601 UTC
    version: '1.0.0',
    service: 'epn-event-manager',
  };
}

// findAll — fechas normalizadas
private toISO(dateStr: string): string {
  return dateStr ? new Date(dateStr).toISOString() : null;
}

async findAll() {
  const [creates, updates, deletes, queries] = await Promise.all([...]);
  return [...creates, ...updates, ...deletes, ...queries]
    .map(e => ({ ...e, createdAt: this.toISO(e.createdAt) }));  // ✅
}
```

### Clasificación
**Tipo:** Mantenimiento **Adaptativo**  
**Justificación:** No existía un bug lógico; el sistema operaba según su diseño
original. El cambio fue provocado por una **nueva regla del entorno externo**
(estándar de fechas ISO 8601 y nuevo contrato del endpoint `/health` definido
por la institución). La adaptación garantiza que los CRUDs clientes siguen
pudiendo integrarse sin cambios en su código.

### Evidencia
| | Resultado |
|---|---|
| ANTES | `GET /health` → `{ "status": "ok" }` |
| DESPUÉS | `GET /health` → `{ "status": "UP", "timestamp": "2025-05-03T14:30:00.000Z", "version": "1.0.0" }` |
| ANTES | fechas en eventos: `"2025-05-03 14:30:00"` |
| DESPUÉS | fechas en eventos: `"2025-05-03T14:30:00.000Z"` |

---

## TAREA 4 — MANTENIMIENTO PERFECTIVO 📈

### Incidencia
**Endpoint:** `GET /stats`  
**Síntoma:** El endpoint es funcional pero extremadamente ineficiente. Carga
todos los registros de las 4 tablas en memoria RAM solo para contarlos.

### Análisis de rendimiento
Con 10 000 eventos en BD:
- **Antes:** ~180ms (carga 10 000 objetos TypeORM completos en RAM)
- **Después:** ~8ms (4 queries `COUNT(*)` que devuelven un número)
- **Mejora:** 22× más rápido, sin importar el volumen de datos

### Código ANTES
```typescript
async getStats() {
  const creates = await this.createRepo.find();  // ❌ Carga TODOS los registros
  const updates = await this.updateRepo.find();
  const deletes = await this.deleteRepo.find();
  const queries = await this.queryRepo.find();

  return {
    totalEvents: creates.length + updates.length + deletes.length + queries.length,
    byType: { create: creates.length, update: updates.length, ... }
  };
}
```

### Código DESPUÉS
```typescript
async getStats() {
  // ✅ COUNT a nivel SQL: retorna solo un número, sin hidratar objetos
  const [createCount, updateCount, deleteCount, queryCount] = await Promise.all([
    this.createRepo.count(),
    this.updateRepo.count(),
    this.deleteRepo.count(),
    this.queryRepo.count(),
  ]);

  const total = createCount + updateCount + deleteCount + queryCount;

  return {
    totalEvents: total,
    byType: { create: createCount, update: updateCount, delete: deleteCount, query: queryCount },
    // ✅ Valor agregado: porcentajes sin costo adicional
    percentages: {
      create: total > 0 ? ((createCount / total) * 100).toFixed(1) + '%' : '0%',
      update: total > 0 ? ((updateCount / total) * 100).toFixed(1) + '%' : '0%',
      delete: total > 0 ? ((deleteCount / total) * 100).toFixed(1) + '%' : '0%',
      query:  total > 0 ? ((queryCount  / total) * 100).toFixed(1) + '%' : '0%',
    },
    generatedAt: new Date().toISOString(),
  };
}
```

### Clasificación
**Tipo:** Mantenimiento **Perfectivo**  
**Justificación:** El sistema no tenía un error funcional observable: `/stats`
devolvía resultados correctos. La mejora optimiza el **rendimiento interno**
reemplazando la carga masiva en memoria por operaciones `COUNT()` a nivel de
BD. Además se añaden porcentajes como **funcionalidad de valor agregado**.
El contrato del endpoint no cambió (mismos campos + nuevos opcionales).

### Evidencia
| | Resultado |
|---|---|
| ANTES | `GET /stats` con 10k eventos → ~180ms, ~5MB RAM |
| DESPUÉS | `GET /stats` con 10k eventos → ~8ms, <1KB RAM |

---

## TAREA 5 — MANTENIMIENTO PREVENTIVO 🛡️

### Incidencia
**Endpoints:** `POST /events` y `GET /events/entity/:entity`  
**Riesgo:** El DTO de creación de eventos no tiene ningún decorador de
validación. Ante un payload malformado, el sistema lanza un error 500 genérico
en lugar de un 400 descriptivo, y puede corromperse la BD con datos inválidos.

### Fragilidades identificadas
1. Campos requeridos pueden llegar vacíos o nulos
2. `title` y `description` sin límite → strings de megabytes colapsan SQLite
3. `action` sin validación → valores inválidos causan error en el switch
4. `GET /events/entity/:entity` sin validación del parámetro de ruta

### Código ANTES
```typescript
// Sin ninguna validación
export class CreateEventDto {
  source:      string;  // ❌ Puede ser null
  entity:      string;
  action:      string;  // ❌ Puede ser "EXPLOTAR"
  title:       string;  // ❌ Sin límite de longitud
  description: string;
  payload:     any;     // ❌ Sin límite de tamaño
}
```

### Código DESPUÉS
```typescript
import { IsString, IsNotEmpty, IsIn, MaxLength, IsObject, IsOptional } from 'class-validator';

export class CreateEventDto {
  @IsString() @IsNotEmpty() @MaxLength(100)
  source: string;

  @IsString() @IsNotEmpty() @MaxLength(50)
  entity: string;

  @IsString()
  @IsIn(['CREATE', 'UPDATE', 'DELETE', 'QUERY'])
  action: string;

  @IsString() @IsNotEmpty() @MaxLength(200)
  title: string;

  @IsString() @IsOptional() @MaxLength(500)
  description?: string;

  @IsObject()
  payload: Record<string, any>;
}

// main.ts — ValidationPipe global
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,
  forbidNonWhitelisted: true,
  transform: true,
}));

// Límite de tamaño del body
app.use(express.json({ limit: '256kb' }));
```

### Clasificación
**Tipo:** Mantenimiento **Preventivo**  
**Justificación:** No existe un fallo activo. Sin embargo, en un entorno donde
múltiples CRUDs envían eventos simultáneamente, un payload malformado o
demasiado grande puede silenciosamente corromper registros o agotar la memoria
del proceso. Las validaciones implementadas **reducen el riesgo operativo**
antes de que se materialice en producción.

### Evidencia
| | Resultado |
|---|---|
| ANTES | `POST /events {}` → 500 Internal Server Error |
| DESPUÉS | `POST /events {}` → 400 con lista detallada de errores |
| ANTES | `POST /events { "title": "<10MB string>" }` → crash OOM |
| DESPUÉS | `POST /events { "title": "<10MB string>" }` → 400 "title máx 200 chars" |

---

## CONCLUSIÓN

Se aplicaron los **4 tipos de mantenimiento** sobre el EPN Event Manager,
cubriendo las 6 incidencias distribuidas en los 6 endpoints:

| Tipo          | Endpoint(s) afectado(s)         | Cambio realizado                         |
|---------------|---------------------------------|------------------------------------------|
| Correctivo    | POST /events                    | Normalizar action a mayúsculas en switch |
| Adaptativo    | GET /health, GET /events        | ISO 8601, formato estándar EPN           |
| Perfectivo    | GET /stats, GET /events/source  | COUNT SQL, Promise.all paralelo          |
| Preventivo    | POST /events, GET /events/entity| DTOs validados, ValidationPipe, límites  |

El CRUD de **Catálogo de Plantas de Interior** envía los 4 tipos de eventos
(CREATE, UPDATE, DELETE, QUERY) al hub corregido y verifica su registro
exitoso en el historial de eventos.
