// MANTENIMIENTO CORRECTIVO
// Endpoint afectado: POST /events
//
// Diagnostico:
// El hub respondia ok para eventos DELETE, pero no los persistia. El codigo
// construia la entidad con deleteRepo.create(...) y retornaba antes de guardar.
//
// ANTES:
/*
if (action === 'DELETE') {
  this.deleteRepo.create({
    source: dto.source,
    entity: dto.entity,
    action: dto.action,
    title: dto.title,
    payload: payloadStr,
    createdAt: localDate,
  });
  return { ok: true };
}
*/

// DESPUES:
/*
if (action === 'DELETE') {
  const ev = this.deleteRepo.create({
    source: dto.source,
    entity: dto.entity,
    action,
    title: dto.title,
    payload: payloadStr,
    createdAt: recordedAt,
  });
  await this.deleteRepo.save(ev);
  return { ok: true, action };
}
*/

// Justificacion:
// Es correctivo porque elimina un fallo real: el sistema decia que el evento
// DELETE se registro, pero la tabla delete_events seguia vacia.
