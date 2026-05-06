import {
  IsIn,
  IsNotEmpty,
  IsObject,
  IsOptional,
  IsString,
  MaxLength,
} from 'class-validator';

export class CreateEventDto {
  @IsString()
  @IsNotEmpty({ message: 'source es obligatorio' })
  @MaxLength(100, { message: 'source no puede superar 100 caracteres' })
  source: string;

  @IsString()
  @IsNotEmpty({ message: 'entity es obligatorio' })
  @MaxLength(50, { message: 'entity no puede superar 50 caracteres' })
  entity: string;

  @IsString()
  @IsNotEmpty({ message: 'action es obligatorio' })
  @IsIn(['CREATE', 'UPDATE', 'DELETE', 'QUERY'], {
    message: 'action debe ser CREATE, UPDATE, DELETE o QUERY',
  })
  action: string;

  @IsString()
  @IsNotEmpty({ message: 'title es obligatorio' })
  @MaxLength(200, { message: 'title no puede superar 200 caracteres' })
  title: string;

  @IsString()
  @IsOptional()
  @MaxLength(500, { message: 'description no puede superar 500 caracteres' })
  description?: string;

  @IsObject({ message: 'payload debe ser un objeto JSON' })
  payload: Record<string, unknown>;
}
