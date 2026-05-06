// MANTENIMIENTO PERFECTIVO
// Endpoint afectado: GET /stats
//
// Diagnostico:
// Las estadisticas no incluian query_events y las consultas no aprovechaban
// paralelismo. El endpoint funcionaba, pero entregaba menos valor.
//
// ANTES:
/*
const createCount = await this.createRepo.count();
const updateCount = await this.updateRepo.count();
const deleteCount = await this.deleteRepo.count();

return {
  create: createCount,
  update: updateCount,
  delete: deleteCount,
  total: createCount + updateCount + deleteCount,
};
*/

// DESPUES:
/*
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
  percentages: {
    create: this.percent(createCount, total),
    update: this.percent(updateCount, total),
    delete: this.percent(deleteCount, total),
    query: this.percent(queryCount, total),
  },
  generatedAt: new Date().toISOString(),
};
*/

// Justificacion:
// Es perfectivo porque mejora rendimiento y utilidad de una funcion existente
// sin cambiar el objetivo del endpoint.
