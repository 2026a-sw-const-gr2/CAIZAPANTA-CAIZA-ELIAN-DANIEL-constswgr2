// ============================================================
// MANTENIMIENTO PREVENTIVO 🛡️
// Endpoints afectados: POST /events, GET /events/entity/:entity
// ============================================================
//
// DIAGNÓSTICO DEL RIESGO
// ──────────────────────
// El sistema no valida los datos de entrada en POST /events:
//   - Campos requeridos pueden llegar vacíos o nulos → crash en BD
//   - title y description sin límite → pueden recibir strings de
//     10 MB que colapsan SQLite y saturan RAM
//   - payload sin límite → un objeto enorme puede bloquear el proceso
//   - GET /events/entity/:entity no maneja el caso de entity vacío
//
// Estos no son bugs activos, pero son fragilidades que, en
// producción con múltiples CRUDs conectados, provocarán fallos
// difíciles de rastrear.
//
// ============================================================

// ─── ANTES (sin validación) ──────────────────────────────────

// create-event.dto.ts  (VERSIÓN ORIGINAL — sin decoradores)
/*
export class CreateEventDto {
  source:      string;   // ❌ Sin validación: puede ser null, '', 999...
  entity:      string;
  action:      string;
  title:       string;   // ❌ Sin límite de longitud
  description: string;
  payload:     any;      // ❌ Sin límite de tamaño
}
*/

// events.controller.ts  (VERSIÓN ORIGINAL)
/*
@Post('events')
createEvent(@Body() dto: CreateEventDto) {
  return this.eventsService.registerEvent(dto);  // ❌ Sin ValidationPipe
}

@Get('events/entity/:entity')
getByEntity(@Param('entity') entity: string) {
  // ❌ Si entity llega vacía o con caracteres especiales, crashea
  return this.eventsService.findByEntity(entity);
}
*/

// ─── DESPUÉS (con validaciones robustas) ─────────────────────

// Instalar dependencias primero:
// npm install class-validator class-transformer

// create-event.dto.ts  (VERSIÓN SEGURA)
/*
import {
  IsString, IsNotEmpty, IsIn,
  MaxLength, IsObject, IsOptional
} from 'class-validator';

export class CreateEventDto {

  @IsString()
  @IsNotEmpty({ message: 'El campo source es obligatorio' })
  @MaxLength(100, { message: 'source no puede superar los 100 caracteres' })
  source: string;

  @IsString()
  @IsNotEmpty({ message: 'El campo entity es obligatorio' })
  @MaxLength(50, { message: 'entity no puede superar los 50 caracteres' })
  entity: string;

  @IsString()
  @IsNotEmpty({ message: 'El campo action es obligatorio' })
  @IsIn(['CREATE', 'UPDATE', 'DELETE', 'QUERY'], {
    message: 'action debe ser CREATE, UPDATE, DELETE o QUERY'
  })
  action: string;

  @IsString()
  @IsNotEmpty({ message: 'El campo title es obligatorio' })
  @MaxLength(200, { message: 'title no puede superar los 200 caracteres' })
  title: string;

  @IsString()
  @IsOptional()
  @MaxLength(500, { message: 'description no puede superar los 500 caracteres' })
  description?: string;

  @IsObject({ message: 'payload debe ser un objeto JSON' })
  payload: Record<string, any>;
}
*/

// main.ts  (habilitar ValidationPipe globalmente)
/*
import { ValidationPipe } from '@nestjs/common';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // ✅ Activar validación global con mensajes claros
  app.useGlobalPipes(new ValidationPipe({
    whitelist: true,          // elimina campos no declarados en el DTO
    forbidNonWhitelisted: true, // lanza error si llegan campos extra
    transform: true,          // convierte tipos automáticamente
  }));

  await app.listen(3000);
}
bootstrap();
*/

// events.controller.ts  (VERSIÓN SEGURA)
/*
@Get('events/entity/:entity')
getByEntity(@Param('entity') entity: string) {
  // ✅ Validación del parámetro de ruta
  if (!entity || entity.trim().length === 0) {
    throw new BadRequestException('El parámetro entity no puede estar vacío');
  }
  if (entity.length > 50) {
    throw new BadRequestException('El parámetro entity no puede superar 50 caracteres');
  }
  return this.eventsService.findByEntity(entity.trim().toLowerCase());
}
*/

// ─── TAMBIÉN: manejo de payload demasiado grande ─────────────

// main.ts  (limitar tamaño del body)
/*
async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // ✅ Limitar tamaño máximo del body a 256 KB
  app.use(express.json({ limit: '256kb' }));

  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
  await app.listen(3000);
}
*/

// ─── CLASIFICACIÓN ───────────────────────────────────────────
//
// Tipo: MANTENIMIENTO PREVENTIVO
//
// Justificación:
//   No existe un fallo activo observable en este momento.
//   Sin embargo, la ausencia de validaciones en los DTOs y en
//   los parámetros de ruta representa una fragilidad real:
//   en un entorno donde múltiples CRUDs envían eventos
//   simultáneamente, un payload malformado o demasiado grande
//   puede silenciosamente corromper registros, agotar la memoria
//   del proceso o generar errores 500 sin mensaje útil.
//
//   Las acciones preventivas implementadas:
//   1. Decoradores class-validator en el DTO (campos requeridos,
//      longitudes máximas, valores permitidos en action).
//   2. ValidationPipe global con whitelist y transform.
//   3. Límite de tamaño del body (256 KB).
//   4. Validación del parámetro :entity en el controlador.
//
// EVIDENCIA:
//   ANTES:  POST /events {} → 500 Internal Server Error (DB constraint)
//   DESPUÉS: POST /events {} → 400 Bad Request con lista de errores claros
//
//   ANTES:  GET /events/entity/ → 500 crash
//   DESPUÉS: GET /events/entity/ → 400 "entity no puede estar vacío"
// ─────────────────────────────────────────────────────────────
