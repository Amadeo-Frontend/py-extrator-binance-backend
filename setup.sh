#!/usr/bin/env bash
set -e

echo "🚀 Iniciando setup do backend..."

# 1️⃣ Garantir Python 3.10 no Render
echo "🔧 Instalando Python 3.10..."
PYTHON_VERSION=3.10

# Render já fornece vários Python, este comando ajusta o path
export PATH="/opt/python/$PYTHON_VERSION/bin:$PATH"

python3 --version

# 2️⃣ Instalar UV (gerenciador de pacotes)
echo "📦 Instalando uv..."
pip install uv

# 3️⃣ Instalar dependências do projeto
echo "📚 Instalando dependências com uv..."
uv sync --no-dev

# 4️⃣ Criar diretório para logs (evita erros em produção)
mkdir -p logs

echo "✅ Setup concluído com sucesso!"
