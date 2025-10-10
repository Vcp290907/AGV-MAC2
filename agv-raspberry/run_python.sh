#!/bin/bash
# Wrapper para executar scripts Python com ambiente virtual
# Uso: ./run_python.sh script.py [args]

if [ -z "$1" ]; then
    echo "Uso: $0 <script.py> [argumentos]"
    exit 1
fi

# Ativar ambiente virtual
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Executar script Python
python3 "$@"