import { Controller, Get } from '@nestjs/common';

@Controller('health')
export class HealthController {
  @Get()
  check() {
    return {
      status: 'UP',
      service: 'epn-event-manager',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
    };
  }
}
