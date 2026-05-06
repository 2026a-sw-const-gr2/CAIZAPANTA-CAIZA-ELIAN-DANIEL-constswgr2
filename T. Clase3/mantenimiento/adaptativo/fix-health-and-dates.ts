// ============================================================
// MANTENIMIENTO ADAPTATIVO ⚙️
// Endpoint afectado: GET /health  y  GET /events
// ============================================================
//
// DIAGNÓSTICO DEL PROBLEMA
// ─────────────────────────
// La EPN adoptó el estándar ISO 8601 UTC obligatorio para todas
// las fechas de sus sistemas internos. El Event Manager:
//
//   1. GET /health devuelve { status: 'ok' } sin timestamp.
//      El nuevo estándar requiere: { status: 'UP', timestamp, version }.
//
//   2. GET /events devuelve fechas en formato local SQLite
//      (ej: "2025-05-03 14:30:00") en vez de ISO 8601 UTC
//      (ej: "2025-05-03T14:30:00.000Z").
//
//   Ambos puntos impiden la integración con el sistema de
//   monitoreo central de la EPN que espera ese formato.
//
// ============================================================

// ─── ANTES ───────────────────────────────────────────────────

// app.controller.ts  (VERSIÓN ORIGINAL)
/*
@Get('health')
getHealth() {
  return { status: 'ok' };   // ❌ No cumple el nuevo estándar
}
*/

// events.service.ts  (VERSIÓN ORIGINAL — al retornar eventos)
/*
async findAll(): Promise<any[]> {
  const [creates, updates, deletes, queries] = await Promise.all([
    this.createRepo.find(),
    this.updateRepo.find(),
    this.deleteRepo.find(),
    this.queryRepo.find(),
  ]);
  // ❌ Las fechas vienen como strings de SQLite sin conversión
  return [...creates, ...updates, ...deletes, ...queries];
}
*/

// ─── DESPUÉS (adaptado al nuevo estándar) ────────────────────

// app.controller.ts  (VERSIÓN ADAPTADA)
/*
@Get('health')
getHealth() {
  // ✅ Cumple el nuevo estándar EPN: status UP, timestamp ISO 8601, versión
  return {
    status: 'UP',
    timestamp: new Date().toISOString(),   // "2025-05-03T14:30:00.000Z"
    version: '1.0.0',
    service: 'epn-event-manager',
  };
}
*/

// events.service.ts  (VERSIÓN ADAPTADA)
/*
private toISOString(dateStr: string): string {
  // Convierte "2025-05-03 14:30:00" → "2025-05-03T14:30:00.000Z"
  if (!dateStr) return null;
  return new Date(dateStr).toISOString();
}

private normalizeEvent(event: any): any {
  return {
    ...event,
    createdAt: this.toISOString(event.createdAt),   // ✅ UTC ISO 8601
    updatedAt: this.toISOString(event.updatedAt),
  };
}

async findAll(): Promise<any[]> {
  const [creates, updates, deletes, queries] = await Promise.all([
    this.createRepo.find(),
    this.updateRepo.find(),
    this.deleteRepo.find(),
    this.queryRepo.find(),
  ]);
  return [...creates, ...updates, ...deletes, ...queries]
    .map(e => this.normalizeEvent(e));   // ✅ todas las fechas normalizadas
}
*/

// ─── CLASIFICACIÓN ───────────────────────────────────────────
//
// Tipo: MANTENIMIENTO ADAPTATIVO
//
// Justificación:
//   No existía un bug lógico previo; el sistema funcionaba
//   según su diseño original. El cambio fue motivado por una
//   nueva regla del entorno externo (estándar de fechas ISO 8601
//   y nuevo contrato del endpoint /health exigido por la EPN).
//   La adaptación garantiza que los CRUDs cliente siguen
//   pudiendo integrarse y que el sistema de monitoreo central
//   recibe la información en el formato esperado.
//
// EVIDENCIA:
//   ANTES:  GET /health → { "status": "ok" }
//   DESPUÉS: GET /health → { "status": "UP", "timestamp": "2025-05-03T14:30:00.000Z", "version": "1.0.0" }
//
//   ANTES:  GET /events → [..., { "createdAt": "2025-05-03 14:30:00" }]
//   DESPUÉS: GET /events → [..., { "createdAt": "2025-05-03T14:30:00.000Z" }]
// ─────────────────────────────────────────────────────────────
