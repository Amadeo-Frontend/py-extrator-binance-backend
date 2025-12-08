#!/usr/bin/env bash
set -e

echo ">>> Instalando UV..."
pip install uv

echo ">>> Instalando dependências do projeto..."
uv sync || {
    echo ">>> Falha ao instalar dependências com --frozen. Tentando novamente sem restrições..."
    uv sync --no-lock
}

echo ">>> Build concluído com sucesso!"
