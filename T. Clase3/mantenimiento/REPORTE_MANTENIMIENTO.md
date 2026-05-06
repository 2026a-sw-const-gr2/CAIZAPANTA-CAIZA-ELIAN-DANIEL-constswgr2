# Reporte de Mantenimiento - EPN Event Manager

**Materia:** Construccion y Evolucion de Software  
**Sistema intervenido:** EPN Event Manager  
**CRUD conectado:** Catalogo de Plantas de Interior (`crud-plantas`)  
**Stack del hub:** NestJS + TypeORM + SQLite  
**Stack del CRUD:** Python + Flask + SQLite

## Diagnostico general

El EPN Event Manager centraliza eventos de CRUD externos, pero mantiene una deuda tecnica intencional: separa eventos en cuatro tablas (`create_events`, `update_events`, `delete_events`, `query_events`) y expone endpoints que originalmente no validaban correctamente los datos ni respondian con formatos estandar.

El CRUD de plantas envia eventos `CREATE`, `QUERY`, `UPDATE` y `DELETE` al hub usando `POST /events`.

## 1. Mantenimiento correctivo

**Endpoint afectado:** `POST /events`

### Incidencia tecnica

Los eventos `DELETE` respondian como exitosos, pero no se guardaban en la base de datos. En `events.service.ts`, el codigo construia la entidad con `this.deleteRepo.create(...)`, pero retornaba `{ ok: true }` antes de ejecutar `save`.

### Antes

```ts
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
```

### Despues

```ts
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
```

### Justificacion

Es mantenimiento correctivo porque corrige un fallo real de ejecucion: el sistema reportaba exito, pero perdia eventos `DELETE`. La intervencion estabiliza el comportamiento sin cambiar el contrato externo del API.

## 2. Mantenimiento adaptativo

**Endpoints afectados:** `GET /health`, `GET /events`, `POST /events`

### Incidencia tecnica

El entorno institucional exige fechas ISO 8601 UTC y respuesta de salud con `status: "UP"`, `timestamp`, `version` y `service`. El hub devolvia `status: "ok"` y guardaba fechas locales con `toLocaleString()`.

### Antes

```ts
return { status: 'ok', timestamp: new Date().toLocaleString() };
```

```ts
const localDate = new Date().toLocaleString();
```

### Despues

```ts
return {
  status: 'UP',
  service: 'epn-event-manager',
  version: '1.0.0',
  timestamp: new Date().toISOString(),
};
```

```ts
const recordedAt = new Date().toISOString();
```

### Justificacion

Es mantenimiento adaptativo porque el sistema se ajusta a una nueva regla externa del entorno: formato UTC ISO 8601 y contrato estandar para monitoreo. No nace de un bug funcional interno, sino de compatibilidad con el nuevo contexto.

## 3. Mantenimiento perfectivo

**Endpoints afectados:** `GET /stats`, `GET /events/source/:source`, `GET /events/entity/:entity`

### Incidencia tecnica

`GET /stats` no contaba la tabla `query_events`, por lo que la metrica total quedaba incompleta. Ademas, algunas consultas a las cuatro tablas se ejecutaban de forma secuencial, aumentando la latencia.

### Antes

```ts
const createCount = await this.createRepo.count();
const updateCount = await this.updateRepo.count();
const deleteCount = await this.deleteRepo.count();

return {
  create: createCount,
  update: updateCount,
  delete: deleteCount,
  total: createCount + updateCount + deleteCount,
};
```

### Despues

```ts
const [createCount, updateCount, deleteCount, queryCount] = await Promise.all([
  this.createRepo.count(),
  this.updateRepo.count(),
  this.deleteRepo.count(),
  this.queryRepo.count(),
]);

const total = createCount + updateCount + deleteCount + queryCount;
```

Tambien se agregaron:

```ts
totalEvents: total,
byType: { create: createCount, update: updateCount, delete: deleteCount, query: queryCount },
percentages: {
  create: this.percent(createCount, total),
  update: this.percent(updateCount, total),
  delete: this.percent(deleteCount, total),
  query: this.percent(queryCount, total),
},
generatedAt: new Date().toISOString(),
```

### Justificacion

Es mantenimiento perfectivo porque mejora una funcion existente: las estadisticas ahora son mas completas, mas utiles y se calculan en paralelo. El endpoint sigue cumpliendo su objetivo original, pero aporta mas valor y mejor rendimiento.

## 4. Mantenimiento preventivo

**Endpoints afectados:** `POST /events`, `GET /events/entity/:entity`

### Incidencia tecnica

El DTO de eventos no validaba campos requeridos, longitudes ni acciones permitidas. Un payload vacio, un `action` invalido o textos demasiado largos podian generar errores 500 o registros inconsistentes.

### Antes

```ts
export class CreateEventDto {
  source: string;
  entity: string;
  action: string;
  title: string;
  description: string;
  payload: any;
}
```

### Despues

```ts
export class CreateEventDto {
  @IsString()
  @IsNotEmpty()
  @MaxLength(100)
  source: string;

  @IsString()
  @IsIn(['CREATE', 'UPDATE', 'DELETE', 'QUERY'])
  action: string;

  @IsString()
  @IsNotEmpty()
  @MaxLength(200)
  title: string;

  @IsObject()
  payload: Record<string, unknown>;
}
```

En `main.ts`:

```ts
app.use(json({ limit: '256kb' }));
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,
    forbidNonWhitelisted: true,
    transform: true,
  }),
);
```

En `events.controller.ts`:

```ts
if (!normalizedEntity) {
  throw new BadRequestException('entity no puede estar vacio');
}

if (normalizedEntity.length > 50) {
  throw new BadRequestException('entity no puede superar 50 caracteres');
}
```

### Justificacion

Es mantenimiento preventivo porque reduce riesgos futuros antes de que el sistema falle en produccion. Las validaciones evitan datos corruptos, campos gigantes y errores 500 dificiles de diagnosticar.

## Prueba de vida

1. Levantar el hub:

```bash
cd epn-event-manager
npm run start:dev
```

2. Levantar el CRUD:

```bash
cd crud-plantas
python crud_plantas.py
```

3. Abrir `http://localhost:4000` y ejecutar:

- Crear una planta.
- Listar plantas.
- Actualizar una planta.
- Eliminar una planta.

4. Verificar en el hub:

```bash
curl http://localhost:3000/events/source/crud-plantas
curl http://localhost:3000/stats
curl http://localhost:3000/health
```

## Conclusion

Se implementaron los cuatro tipos de mantenimiento solicitados. El CRUD de plantas demuestra integracion real con el hub y el Event Manager queda mas estable, compatible, util y robusto frente a entradas invalidas.
