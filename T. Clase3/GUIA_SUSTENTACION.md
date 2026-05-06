# Guia de sustentacion

## Como ejecutar

Abrir dos terminales en la carpeta `T. Clase3`.

Terminal 1 - Event Manager:

```bash
cd epn-event-manager
npm install
npm run start:dev
```

Terminal 2 - CRUD:

```bash
cd crud-plantas
pip install flask requests
python crud_plantas.py
```

Abrir en el navegador:

```text
http://localhost:4000
```

## Demo visual

1. En la pagina web crear una planta.
2. Presionar Actualizar para listar.
3. Editar la planta y guardar.
4. Eliminar la planta.
5. Abrir estos enlaces para mostrar que el hub recibio eventos:

```text
http://localhost:3000/events/source/crud-plantas
http://localhost:3000/events/entity/plant
http://localhost:3000/stats
http://localhost:3000/health
```

## Speech corto

Buenas tardes. Mi proyecto CRUD es un Catalogo de Plantas de Interior. Lo construi en Python con Flask y SQLite. Cada vez que creo, consulto, actualizo o elimino una planta, el CRUD envia automaticamente un evento al EPN Event Manager mediante `POST /events`.

Para la prueba de vida, aqui se ve la interfaz web del CRUD en `localhost:4000`. Al crear una planta se envia un evento `CREATE`; al listar o consultar se envia `QUERY`; al editar se envia `UPDATE`; y al eliminar se envia `DELETE`. Luego verifico en el hub con `localhost:3000/events/source/crud-plantas`, donde aparecen los eventos registrados por mi aplicacion.

En mantenimiento correctivo corregi un error real: los eventos `DELETE` respondian como exitosos, pero no se guardaban porque el codigo creaba la entidad y retornaba antes de hacer `save`. La solucion fue guardar la entidad con `await this.deleteRepo.save(ev)`.

En mantenimiento adaptativo ajuste el sistema al nuevo estandar de entorno: `/health` ahora responde con `status: "UP"`, version, servicio y timestamp ISO 8601 UTC. Tambien las fechas de eventos se guardan con `toISOString()`.

En mantenimiento perfectivo mejore las estadisticas. Antes no se contaban los eventos `QUERY`; ahora `GET /stats` cuenta las cuatro tablas en paralelo con `Promise.all` y agrega porcentajes por tipo de evento.

En mantenimiento preventivo agregue validaciones con `class-validator`, `ValidationPipe`, limite de body de 256 KB y validacion del parametro `entity`. Esto evita payloads invalidos, campos vacios, acciones no permitidas y errores 500 innecesarios.

Con esto se cumplen los cuatro tipos de mantenimiento: correctivo porque arregla un fallo, adaptativo porque responde a una nueva regla externa, perfectivo porque mejora una funcion existente y preventivo porque reduce riesgos futuros.

## Si solo se ve la terminal

La terminal solo demuestra que el servidor esta corriendo. Para que la sustentacion sea visual, abre `http://localhost:4000` en el navegador. Esa pantalla permite operar el CRUD sin escribir comandos. La terminal queda como evidencia tecnica: muestra que Flask recibio las peticiones y que se intento registrar cada evento en el Event Manager.
