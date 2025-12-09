#!/usr/bin/env bash
set -e

echo "🚀 Iniciando setup de ambiente para Render..."

# -------------------------------
# 1️⃣ Garantir que Python está ok
# -------------------------------

echo "🧪 Verificando versão do Python..."
python3 --version

# Render já vem com Python 3.10.x
# (compatível com psycopg2, numpy 1.26, etc)

# -------------------------------
# 2️⃣ Instalar UV se necessário
# -------------------------------

if ! command -v uv &> /dev/null
then
    echo "📦 Instalando UV..."
    pip install uv
else
    echo "✔ UV já instalado"
fi


# -------------------------------
# 3️⃣ Instalar dependências
# -------------------------------

echo "📦 Instalando dependências do requirements.txt..."
uv pip install -r requirements.txt --system --no-cache


# -------------------------------
# 4️⃣ Criar diretórios necessários
# -------------------------------

echo "📁 Garantindo que pastas existem..."
mkdir -p logs
mkdir -p tmp


# -------------------------------
# 5️⃣ Testes de integridade
# -------------------------------

echo "🔍 Testando importação de módulos essenciais..."

python3 - << 'EOF'
import psycopg2
import asyncpg
import fastapi
import uvicorn
import numpy
import pandas
print("✔ Todos módulos importados com sucesso.")
EOF


# -------------------------------
# 6️⃣ Conclusão
# -------------------------------

echo "🎉 Setup concluído com sucesso!"
