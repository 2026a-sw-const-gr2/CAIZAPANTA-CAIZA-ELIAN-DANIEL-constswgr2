import { BadRequestException, Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { CreateEventDto } from './dto/create-event.dto';
import { CreateEventEntity } from '../../database/entities/create-event.entity';
import { UpdateEventEntity } from '../../database/entities/update-event.entity';
import { DeleteEventEntity } from '../../database/entities/delete-event.entity';
import { QueryEventEntity } from '../../database/entities/query-event.entity';

@Injectable()
export class EventsService {
  constructor(
    @InjectRepository(CreateEventEntity)
    private readonly createRepo: Repository<CreateEventEntity>,
    @InjectRepository(UpdateEventEntity)
    private readonly updateRepo: Repository<UpdateEventEntity>,
    @InjectRepository(DeleteEventEntity)
    private readonly deleteRepo: Repository<DeleteEventEntity>,
    @InjectRepository(QueryEventEntity)
    private readonly queryRepo: Repository<QueryEventEntity>,
  ) {}

  async registerEvent(dto: CreateEventDto): Promise<{ ok: boolean; action: string }> {
    const action = (dto.action ?? '').toUpperCase();
    const payloadStr = JSON.stringify(dto.payload ?? {});
    const recordedAt = new Date().toISOString();

    if (action === 'CREATE') {
      const ev = this.createRepo.create({
        source: dto.source,
        entity: dto.entity,
        action,
        title: dto.title,
        description: dto.description ?? '',
        payload: payloadStr,
        recorded_at: recordedAt,
      });
      await this.createRepo.save(ev);
      return { ok: true, action };
    }

    if (action === 'UPDATE') {
      const ev = this.updateRepo.create({
        source: dto.source,
        entity: dto.entity,
        action,
        title: dto.title,
        description: dto.description ?? '',
        payload: payloadStr,
        timestamp: recordedAt,
      });
      await this.updateRepo.save(ev);
      return { ok: true, action };
    }

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

    if (action === 'QUERY') {
      const ev = this.queryRepo.create({
        source: dto.source,
        entity: dto.entity,
        action,
        title: dto.title,
        description: dto.description ?? '',
        payload: payloadStr,
        event_date: recordedAt,
      });
      await this.queryRepo.save(ev);
      return { ok: true, action };
    }

    throw new BadRequestException(`Accion no reconocida: ${dto.action}`);
  }

  async findAll(): Promise<object[]> {
    const [creates, updates, deletes, queries] = await Promise.all([
      this.createRepo.find(),
      this.updateRepo.find(),
      this.deleteRepo.find(),
      this.queryRepo.find(),
    ]);

    const merged = [
      ...creates.map((e) => this.normalizeEvent(e, 'create_events', e.recorded_at)),
      ...updates.map((e) => this.normalizeEvent(e, 'update_events', e.timestamp)),
      ...deletes.map((e) => this.normalizeEvent(e, 'delete_events', e.createdAt)),
      ...queries.map((e) => this.normalizeEvent(e, 'query_events', e.event_date)),
    ];

    return this.sortByTimestampDesc(merged);
  }

  async findBySource(source: string): Promise<object[]> {
    const [creates, updates, deletes, queries] = await Promise.all([
      this.createRepo.findBy({ source }),
      this.updateRepo.findBy({ source }),
      this.deleteRepo.findBy({ source }),
      this.queryRepo.findBy({ source }),
    ]);

    return this.sortByTimestampDesc([
      ...creates.map((e) => this.normalizeEvent(e, 'create_events', e.recorded_at)),
      ...updates.map((e) => this.normalizeEvent(e, 'update_events', e.timestamp)),
      ...deletes.map((e) => this.normalizeEvent(e, 'delete_events', e.createdAt)),
      ...queries.map((e) => this.normalizeEvent(e, 'query_events', e.event_date)),
    ]);
  }

  async findByEntity(entity: string): Promise<object[]> {
    const [creates, updates, deletes, queries] = await Promise.all([
      this.createRepo.findBy({ entity }),
      this.updateRepo.findBy({ entity }),
      this.deleteRepo.findBy({ entity }),
      this.queryRepo.findBy({ entity }),
    ]);

    return this.sortByTimestampDesc([
      ...creates.map((e) => this.normalizeEvent(e, 'create_events', e.recorded_at)),
      ...updates.map((e) => this.normalizeEvent(e, 'update_events', e.timestamp)),
      ...deletes.map((e) => this.normalizeEvent(e, 'delete_events', e.createdAt)),
      ...queries.map((e) => this.normalizeEvent(e, 'query_events', e.event_date)),
    ]);
  }

  async getStats(): Promise<object> {
    const [createCount, updateCount, deleteCount, queryCount] = await Promise.all([
      this.createRepo.count(),
      this.updateRepo.count(),
      this.deleteRepo.count(),
      this.queryRepo.count(),
    ]);
    const total = createCount + updateCount + deleteCount + queryCount;

    return {
      create: createCount,
      update: updateCount,
      delete: deleteCount,
      query: queryCount,
      total,
      totalEvents: total,
      byType: {
        create: createCount,
        update: updateCount,
        delete: deleteCount,
        query: queryCount,
      },
      percentages: {
        create: this.percent(createCount, total),
        update: this.percent(updateCount, total),
        delete: this.percent(deleteCount, total),
        query: this.percent(queryCount, total),
      },
      generatedAt: new Date().toISOString(),
    };
  }

  private normalizeEvent(
    event: object,
    table: string,
    rawTimestamp?: string | null,
  ): object {
    const row = event as Record<string, unknown>;
    const payload = typeof row.payload === 'string' ? this.parsePayload(row.payload) : row.payload;

    return {
      ...row,
      payload,
      _table: table,
      timestamp: this.toISO(rawTimestamp),
    };
  }

  private parsePayload(payload: string): unknown {
    try {
      return JSON.parse(payload);
    } catch {
      return payload;
    }
  }

  private toISO(value?: string | null): string | null {
    if (!value) {
      return null;
    }

    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toISOString();
  }

  private sortByTimestampDesc(events: object[]): object[] {
    return events.sort((a, b) => {
      const left = (a as Record<string, string>).timestamp ?? '';
      const right = (b as Record<string, string>).timestamp ?? '';
      return right.localeCompare(left);
    });
  }

  private percent(value: number, total: number): string {
    return total > 0 ? `${((value / total) * 100).toFixed(1)}%` : '0%';
  }
}
