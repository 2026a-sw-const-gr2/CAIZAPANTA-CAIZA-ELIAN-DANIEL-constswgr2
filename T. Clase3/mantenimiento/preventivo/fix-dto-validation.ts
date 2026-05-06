// MANTENIMIENTO PREVENTIVO
// Endpoints afectados: POST /events, GET /events/entity/:entity
//
// Diagnostico:
// El DTO no validaba campos requeridos, longitudes ni acciones permitidas.
// Esto podia generar registros inconsistentes, payloads gigantes o errores 500.
//
// ANTES:
/*
export class CreateEventDto {
  source: string;
  entity: string;
  action: string;
  title: string;
  description: string;
  payload: any;
}
*/

// DESPUES:
/*
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
*/

// main.ts:
/*
app.use(json({ limit: '256kb' }));
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,
  forbidNonWhitelisted: true,
  transform: true,
}));
*/

// Justificacion:
// Es preventivo porque reduce riesgos antes de que se materialicen: entradas
// invalidas, campos enormes y parametros de ruta inseguros.
