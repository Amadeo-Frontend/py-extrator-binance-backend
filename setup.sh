#!/usr/bin/env bash
set -e

echo ">>> Instalando UV..."
pip install uv

echo ">>> Garantindo que o Python correto está selecionado..."
uv python install 3.10

echo ">>> Fixando Python 3.10 como versão do projeto..."
uv python pin 3.10

echo ">>> Sincronizando dependências..."
uv sync --frozen || {
    echo ">>> uv sync falhou. Tentando novamente sem --frozen..."
    uv sync
}

echo ">>> Build finalizado com sucesso!"
