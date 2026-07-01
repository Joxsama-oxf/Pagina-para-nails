# Laura Nails - Sistema de Gestion

Proyecto Flask dockerizado para gestion de citas y clientes de un salon de unas.

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- Git instalado

## Instalacion y ejecucion (para el profesor)

1. Crear el archivo de variables de entorno:
Bash
cp .env.example .env
(Opcional: Edita .env y cambia las claves si lo deseas. Si no, las variables por defecto funcionan.)

2. Levantar el proyecto:
Bash
docker compose up --build
La primera vez descargará las imágenes e instalará dependencias. Toma 3-5 minutos.

3. Abrir en el navegador:
http://localhost:8001

4. Configurar el sistema (primera vez):
Para inicializar la base de datos con los roles, permisos y usuarios de demostración, cargue la siguiente URL en el navegador:
http://localhost:8001/configurar-sistema?token=token-setup-laura-nails-2026
Nota: Es obligatorio que aparezca el mensaje de confirmación antes de intentar el ingreso.

Usuarios creados por defecto:
Rol                 Correo                      Contraseña
Admin Principal     lauranadmin@gmail.com       admin123
Manicurista 1       lauranails01@gmail.com      manicurista1
Manicurista 2       lauranails02@gmail.com      manicurista2
Manicurista 3       lauranails03@gmail.com      manicurista3

5. Detener el proyecto
Presiona Ctrl + C en la terminal donde corre, o en otra terminal dentro de la carpeta:
Bash
docker compose down

6. Reiniciar después de cambios
Si modifica el código o las variables de entorno y requiere reconstruir la imagen limpia:
Bash
docker compose down
docker compose up --build -d

7. Diagnóstico y Restablecimiento Seguro
Errores 500 / IntegrityError / Bloqueos de SQLite
Si el proceso de configuración falla con un error interno (IntegrityError por registros huérfanos o colisión de IDs únicos) o lanza un ERR_TIMED_OUT debido a problemas de permisos de escritura en el volumen, no elimine manualmente la carpeta instance/ con sudo, ya que esto altera los privilegios del propietario asignándolos a root e impide que el contenedor Docker escriba en el archivo.

Para destruir el estado corrupto de la base de datos y reconstruir el entorno de forma segura, ejecute:
Bash
docker compose down -v
rm -rf instance/*
docker compose up --build -d
Posteriormente, ejecute de nuevo la configuración con el parámetro de token correspondiente.

8. Estructura de archivos importantes
app.py - Aplicación principal Flask
docker-compose.yml - Configuración de Docker
Dockerfile - Instrucciones para construir la imagen
.env.example - Plantilla de variables de entorno (copiar a .env)
instance/ - Carpeta donde se guarda la base de datos SQLite (se crea automáticamente)