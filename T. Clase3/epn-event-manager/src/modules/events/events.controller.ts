import {
  BadRequestException,
  Body,
  Controller,
  Get,
  Param,
  Post,
} from '@nestjs/common';
import { EventsService } from './events.service';
import { CreateEventDto } from './dto/create-event.dto';

@Controller('events')
export class EventsController {
  constructor(private readonly eventsService: EventsService) {}

  @Post()
  registerEvent(@Body() dto: CreateEventDto) {
    return this.eventsService.registerEvent(dto);
  }

  @Get()
  findAll() {
    return this.eventsService.findAll();
  }

  @Get('source/:source')
  findBySource(@Param('source') source: string) {
    return this.eventsService.findBySource(source);
  }

  @Get('entity/:entity')
  findByEntity(@Param('entity') entity: string) {
    const normalizedEntity = entity.trim();

    if (!normalizedEntity) {
      throw new BadRequestException('entity no puede estar vacio');
    }

    if (normalizedEntity.length > 50) {
      throw new BadRequestException('entity no puede superar 50 caracteres');
    }

    return this.eventsService.findByEntity(normalizedEntity);
  }
}
