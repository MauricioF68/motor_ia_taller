# 1. Usamos la imagen oficial de Python
FROM python:3.11-slim

# 2. Por seguridad en Hugging Face, creamos un usuario
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

# 3. Carpeta de trabajo
WORKDIR /app

# 4. Copiamos los requerimientos e instalamos
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 5. Copiamos el resto de tu código
COPY --chown=user . .

# 6. Exponemos el puerto 7860 (es el que pide Hugging Face)
EXPOSE 7860

# 7. Comando para encender FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]