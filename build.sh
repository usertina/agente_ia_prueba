#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Iniciando build..."

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p notes code templates_docs data_docs output_docs
mkdir -p rmn_spectra/input rmn_spectra/output rmn_spectra/plots
mkdir -p cache static templates

# Crear directorio para templates por defecto
mkdir -p templates_docs/defaults

# Inicializar base de datos
echo "💾 Inicializando base de datos..."
python -c "from multi_user_notification_system import multi_user_system; multi_user_system.init_database()"

# Verificar que los archivos estáticos existen
echo "✅ Verificando archivos estáticos..."
if [ -d "static" ]; then
    echo "   ✓ Directorio static encontrado"
    ls -la static/ | head -10
else
    echo "   ⚠️ Directorio static no encontrado"
fi

if [ -d "templates" ]; then
    echo "   ✓ Directorio templates encontrado"
    ls -la templates/
else
    echo "   ⚠️ Directorio templates no encontrado"
fi

echo "✅ Build completado exitosamente"