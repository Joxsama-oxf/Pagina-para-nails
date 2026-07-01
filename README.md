# Laura Nails - Sistema de Gestion

Proyecto Flask dockerizado para gestion de citas y clientes de un salon de unas.

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- Git instalado

## Instalacion y ejecucion (para el profesor)

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/Joxsama-oxf/Pagina-para-nails.git
   cd Pagina-para-nails
   ```

2. **Crear el archivo de variables de entorno:**
   ```bash
   cp .env.example .env
   ```
   *(Opcional: Edita `.env` y cambia las claves si lo deseas. Si no, las variables por defecto funcionan.)*

3. **Levantar el proyecto:**
   ```bash
   docker compose up --build
   ```
   La primera vez descargara las imagenes e instalara dependencias. Toma 3-5 minutos.

4. **Abrir en el navegador:**
   ```
   http://localhost:8001
   ```

5. **Configurar el sistema (primera vez):**
   Ve a `http://localhost:8001/configurar-sistema` para crear los usuarios y datos de demostracion.

   Usuarios creados por defecto:
   | Rol | Correo | Contrasena |
   |-----|--------|------------|
   | Admin | admin@lauranails.com | admin123 |
   | Manicurista 1 | mani1@lauranails.com | manicurista1 |
   | Manicurista 2 | mani2@lauranails.com | manicurista2 |
   | Manicurista 3 | mani3@lauranails.com | manicurista3 |

## Detener el proyecto

Presiona `Ctrl + C` en la terminal donde corre, o en otra terminal dentro de la carpeta:
```bash
docker compose down
```

## Reiniciar despues de cambios

Si modificas codigo y quieres ver los cambios:
```bash
docker compose up --build
```

## Estructura de archivos importantes

- `app.py` - Aplicacion principal Flask
- `docker-compose.yml` - Configuracion de Docker
- `Dockerfile` - Instrucciones para construir la imagen
- `.env.example` - Plantilla de variables de entorno (copiar a `.env`)
- `instance/` - Carpeta donde se guarda la base de datos SQLite (se crea automaticamente)

## Notas

- La base de datos SQLite se guarda en la carpeta `instance/` de tu maquina local (persiste entre reinicios).
- Si borras la carpeta `instance/`, perderas todos los datos y deberas volver a ejecutar `/configurar-sistema`.
- El puerto expuesto es el `8001`. Si esta ocupado, cambia `"8001:8000"` por `"8080:8000"` en `docker-compose.yml` y accede a `http://localhost:8080`.
- Si `/configurar-sistema` da "Forbidden", significa que ya hay usuarios en la base de datos. Usa los datos de login de la tabla de arriba.
