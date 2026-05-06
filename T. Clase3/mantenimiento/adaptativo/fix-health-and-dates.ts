// MANTENIMIENTO ADAPTATIVO
// Endpoints afectados: GET /health, POST /events, GET /events
//
// Diagnostico:
// El nuevo estandar EPN exige status UP y fechas ISO 8601 UTC. El hub
// respondia status ok y guardaba fechas locales con toLocaleString().
//
// ANTES:
/*
return { status: 'ok', timestamp: new Date().toLocaleString() };

const localDate = new Date().toLocaleString();
*/

// DESPUES:
/*
return {
  status: 'UP',
  service: 'epn-event-manager',
  version: '1.0.0',
  timestamp: new Date().toISOString(),
};

const recordedAt = new Date().toISOString();
*/

// Justificacion:
// Es adaptativo porque el cambio responde a una regla externa del entorno,
// no a un defecto funcional interno.
