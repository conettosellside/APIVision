# Usa una imagen oficial de Python como imagen base.
FROM python:3.12-slim

# Establece el directorio de trabajo en el contenedor.
WORKDIR /app

# Actualiza e instala dependencias del sistema necesarias para OpenCV.
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requisitos y lo instala. Asume que tienes Daphne, Django y OpenCV en el archivo.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de tu aplicación Django al contenedor.
COPY . .

# Ejecuta migraciones. Si tu aplicación no necesita migraciones, puedes omitir este paso.
RUN python manage.py migrate

# Define el comando para iniciar el servidor Daphne. Asegúrate de usar la variable de entorno $PORT.
CMD daphne -b 0.0.0.0 -p $PORT mysite.asgi:application
