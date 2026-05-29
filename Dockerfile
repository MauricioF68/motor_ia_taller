# 1. Usamos una imagen de Python oficial
FROM python:3.11-slim

# 2. Creamos un usuario para que no corra como root (por seguridad en la nube)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

# 3. Establecemos la carpeta de trabajo
WORKDIR /app

# 4. Copiamos el archivo de librerías e instalamos
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 5. Copiamos todo el resto del código
COPY --chown=user . .

# 6. Exponemos el puerto que usa Hugging Face por defecto
EXPOSE 7860

# 7. Comando para arrancar FastAPI (usando el puerto 7860)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]