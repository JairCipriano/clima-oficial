# 1. Usa a mesma imagem leve do AgendaCloud
FROM python:3.11-slim

# 2. Define o diretório de trabalho dentro do container
WORKDIR /app

# 3. Impede geração de arquivos .pyc e garante logs em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 5. Instala as bibliotecas Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copia todo o código-fonte
COPY . .

# 7. Porta 3000 conforme exigido pela proposta N703
EXPOSE 3000

# 8. Inicia a API na porta 3000 (o 0.0.0.0 é necessário para funcionar em containers)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000"]
