#!/usr/bin/env bash
set -e

echo "🚀 Iniciando setup do ambiente para Render..."

# 1. Conferir versão do Python
echo "➡️ Verificando Python..."
python --version

# 2. Instalar UV caso não exista
echo "➡️ Garantindo UV instalado..."
pip install uv

# 3. Gerar requirements.txt limpo
echo "➡️ Gerando requirements.txt a partir do pyproject.toml..."
uv pip compile pyproject.toml -o requirements.txt --upgrade

# 4. Instalar dependências
echo "➡️ Instalando dependências..."
uv pip install -r requirements.txt

echo "✅ Setup finalizado!"
