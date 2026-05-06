// ============================================================
// MANTENIMIENTO CORRECTIVO 🐞
// Endpoint afectado: POST /events
// ============================================================
//
// DIAGNÓSTICO DEL PROBLEMA
// ─────────────────────────
// Al enviar eventos con action = "CREATE", el sistema no los guarda.
// La causa: el switch compara action en minúsculas ('create'), pero
// el payload llega en mayúsculas ('CREATE'). TypeScript/JS distingue
// mayúsculas y minúsculas, por lo que el case nunca coincide y
// el evento cae al bloque `default` que lanza un error.
//
// PRUEBA DEL FALLO:
//   POST /events  { "action": "CREATE", ... }
//   → Error 500: "Acción no reconocida"
//   → La tabla create_events permanece vacía.
//
// ============================================================

// ─── ANTES (código con el bug) ───────────────────────────────

// events.service.ts  (VERSIÓN CON BUG)
/*
async registerEvent(dto: CreateEventDto): Promise<any> {
  const eventData = {
    source:      dto.source,
    entity:      dto.entity,
    action:      dto.action,
    title:       dto.title,
    description: dto.description,
    payload:     JSON.stringify(dto.payload),
  };

  switch (dto.action) {
    case 'create':           // ❌ BUG: minúsculas, el payload llega en MAYÚSCULAS
      return this.createRepo.save(eventData);
    case 'update':           // ❌ BUG: mismo error
      return this.updateRepo.save(eventData);
    case 'delete':           // ❌ BUG: mismo error
      return this.deleteRepo.save(eventData);
    case 'query':            // ❌ BUG: mismo error
      return this.queryRepo.save(eventData);
    default:
      throw new Error('Acción no reconocida');
  }
}
*/

// ─── DESPUÉS (código corregido) ──────────────────────────────

// events.service.ts  (VERSIÓN CORREGIDA)
/*
async registerEvent(dto: CreateEventDto): Promise<any> {
  const eventData = {
    source:      dto.source,
    entity:      dto.entity,
    action:      dto.action,
    title:       dto.title,
    description: dto.description,
    payload:     JSON.stringify(dto.payload),
  };

  // ✅ FIX: normalizar a mayúsculas antes de comparar
  const action = dto.action.toUpperCase();

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
}
*/

// ─── CLASIFICACIÓN ───────────────────────────────────────────
//
// Tipo: MANTENIMIENTO CORRECTIVO
//
// Justificación:
//   El sistema presentaba un fallo en tiempo de ejecución:
//   los eventos CREATE, UPDATE, DELETE y QUERY nunca se
//   persistían porque la comparación era case-sensitive y
//   los valores del switch usaban minúsculas mientras el
//   contrato del API esperaba mayúsculas.
//
//   Se corrigió sin cambiar el contrato externo (el payload
//   sigue llegando en mayúsculas), sin introducir regresiones
//   en los otros endpoints, y mejorando el mensaje de error
//   con BadRequestException en lugar de un genérico Error.
//
// EVIDENCIA:
//   ANTES:  POST /events { action: "CREATE" } → 500 Error
//   DESPUÉS: POST /events { action: "CREATE" } → 201 Created
// ─────────────────────────────────────────────────────────────
