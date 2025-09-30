// ========== INICIALIZACIÓN DE LA SECCIÓN RMN ==========

function initializeRMNSection() {
    const rmnSection = document.getElementById('rmn-section');
    if (!rmnSection) {
        console.error('❌ Sección RMN no encontrada');
        return;
    }

    rmnSection.innerHTML = `
        <!-- Estadísticas RMN -->
        <div id="rmn-stats" class="p-3 bg-teal-50 dark:bg-teal-900 rounded-lg text-sm mb-3">
            <strong>📊 Estado RMN</strong><br>
            <span class="text-sm">Espectros: 0 | Limpios: 0 | Gráficos: 0</span>
        </div>

        <!-- Botones de acción rápida -->
        <div class="space-y-2 mb-3">
            <button onclick="showRMNHelp()" 
                    class="w-full text-left p-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors text-sm">
                ❓ Ayuda RMN
            </button>
            <button onclick="showRMNMethods()" 
                    class="w-full text-left p-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors text-sm">
                🔬 Ver Métodos
            </button>
            <button onclick="listSpectra()" 
                    class="w-full text-left p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors text-sm">
                📋 Listar Espectros
            </button>
        </div>

        <!-- Upload de espectro -->
        <div class="mb-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2 text-sm">📤 Subir Espectro</h4>
            <input type="file" id="spectrum-file-input" 
                   accept=".csv,.txt,.dat,.asc,.json" 
                   class="hidden">
            <button onclick="document.getElementById('spectrum-file-input').click()" 
                    class="w-full p-2 bg-teal-500 hover:bg-teal-600 text-white rounded-lg transition-colors text-sm mb-2">
                📁 Seleccionar Archivo
            </button>
            <button onclick="uploadSpectrum()" 
                    class="w-full p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors text-sm">
                ⬆️ Subir Espectro
            </button>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Formatos: CSV, TXT, DAT, ASC, JSON
            </p>
        </div>

        <!-- Lista de espectros -->
        <div class="mb-3">
            <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2 text-sm">🧪 Espectros Disponibles</h4>
            <div id="spectra-list" class="space-y-2 max-h-60 overflow-y-auto">
                <p class="text-xs text-gray-500 dark:text-gray-400 italic text-center">No hay espectros subidos</p>
            </div>
        </div>

        <!-- Limpieza rápida -->
        <div class="mb-3 p-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900 dark:to-purple-900 rounded-lg">
            <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2 text-sm">⚡ Limpieza Rápida</h4>
            <div class="grid grid-cols-2 gap-2">
                <button onclick="quickCleanAuto()" 
                        class="p-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-xs">
                    🤖 Auto
                </button>
                <button onclick="quickCleanSavgol()" 
                        class="p-2 bg-purple-500 hover:bg-purple-600 text-white rounded text-xs">
                    📈 Savgol
                </button>
                <button onclick="quickCleanGaussian()" 
                        class="p-2 bg-green-500 hover:bg-green-600 text-white rounded text-xs">
                    🌊 Gaussian
                </button>
                <button onclick="quickCleanMedian()" 
                        class="p-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded text-xs">
                    🎯 Median
                </button>
            </div>
        </div>

        <!-- Espectros limpios -->
        <div id="cleaned-spectra" class="mb-3">
            <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2 text-sm">✨ Espectros Limpios</h4>
            <div class="text-xs text-gray-500 dark:text-gray-400 italic text-center">
                Todavía no hay espectros limpios
            </div>
        </div>
    `;

    const fileInput = document.getElementById('spectrum-file-input');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                console.log('📁 Archivo seleccionado:', this.files[0].name);
            }
        });
    }

    console.log('✅ Sección RMN inicializada');
}

// ========== FUNCIONES DE TOGGLE Y NAVEGACIÓN ==========

function toggleRMNSection() {
    const section = document.getElementById('rmn-section');
    const toggle = document.getElementById('rmn-toggle');
    
    if (!section) {
        console.error('❌ Sección RMN no encontrada');
        return;
    }
    
    if (section.classList.contains('hidden')) {
        section.classList.remove('hidden');
        if (toggle) toggle.innerHTML = '🧪 Espectros RMN ▼';
        loadRMNStats();
        loadSpectraList();
    } else {
        section.classList.add('hidden');
        if (toggle) toggle.innerHTML = '🧪 Espectros RMN ▶';
    }
}

function showRMNHelp() {
    executeRMNCommand('ayuda rmn');
}

function showRMNMethods() {
    executeRMNCommand('métodos');
}

function listSpectra() {
    executeRMNCommand('listar espectros');
}

function executeRMNCommand(command) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = command;
    form.dispatchEvent(new Event('submit'));
}

// ========== FUNCIONES DE LIMPIEZA RÁPIDA ==========

function quickCleanAuto() {
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    executeRMNCommand(`limpiar auto: ${lastSpectrum}`);
}

function quickCleanSavgol() {
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    executeRMNCommand(`limpiar: ${lastSpectrum} con savgol`);
}

function quickCleanGaussian() {
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    executeRMNCommand(`limpiar: ${lastSpectrum} con gaussian`);
}

function quickCleanMedian() {
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    executeRMNCommand(`limpiar: ${lastSpectrum} con median`);
}

// ========== FUNCIONES DE UPLOAD ==========

async function uploadSpectrum() {
    const fileInput = document.getElementById('spectrum-file-input');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Por favor selecciona un archivo de espectro');
        return;
    }

    const allowedExtensions = ['.csv', '.txt', '.dat', '.asc', '.json'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        alert(`Formato no soportado. Use: ${allowedExtensions.join(', ')}`);
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload/spectrum', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (result.success) {
            alert(`✅ ${result.message}\n💡 ${result.next_step}`);
            localStorage.setItem('lastSpectrum', result.filename);
            fileInput.value = '';
            loadSpectraList();
            loadRMNStats();
        } else {
            alert(`❌ Error: ${result.error}`);
        }
    } catch (error) {
        alert(`❌ Error subiendo espectro: ${error.message}`);
    }
}

// ========== FUNCIONES DE CARGA DE DATOS ==========

async function loadSpectraList() {
    try {
        const response = await fetch('/files/spectra');
        const data = await response.json();
        
        const spectraList = document.getElementById('spectra-list');
        if (!spectraList) return;
        
        if (data.spectra && data.spectra.length > 0) {
            spectraList.innerHTML = data.spectra.map(spectrum => `
                <div class="flex items-center justify-between p-2 bg-white dark:bg-gray-700 rounded border text-xs">
                    <div class="flex-1">
                        <div class="font-semibold text-blue-800 dark:text-blue-200">${spectrum.name}</div>
                        <div class="text-gray-600 dark:text-gray-400">${(spectrum.size / 1024).toFixed(1)} KB</div>
                    </div>
                    <div class="flex gap-1">
                        <button onclick="analyzeSpectrum('${spectrum.name}')" 
                                class="px-2 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-xs">
                            🔍 Analizar
                        </button>
                        <button onclick="downloadSpectrum('${spectrum.name}')" 
                                class="px-2 py-1 bg-green-500 hover:bg-green-600 text-white rounded text-xs">
                            📥
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            spectraList.innerHTML = '<div class="text-xs text-gray-500 dark:text-gray-400 italic text-center">No hay espectros subidos</div>';
        }
    } catch (error) {
        console.error('Error cargando espectros:', error);
    }
}

async function loadRMNStats() {
    try {
        const response = await fetch('/files/spectra');
        const data = await response.json();
        
        const statsElement = document.getElementById('rmn-stats');
        if (statsElement) {
            const spectraCount = data.spectra ? data.spectra.length : 0;
            const cleanedCount = data.cleaned ? data.cleaned.length : 0;
            const plotsCount = data.plots ? data.plots.length : 0;
            
            statsElement.innerHTML = `
                <strong>📊 Estado RMN</strong><br>
                <span class="text-sm">Espectros: ${spectraCount} | Limpios: ${cleanedCount} | Gráficos: ${plotsCount}</span>
            `;
        }
    } catch (error) {
        console.error('Error cargando estadísticas RMN:', error);
    }
}

// ========== FUNCIONES DE ANÁLISIS Y DESCARGA ==========

function analyzeSpectrum(filename) {
    localStorage.setItem('lastSpectrum', filename);
    executeRMNCommand(`analizar: ${filename}`);
}

async function downloadSpectrum(filename) {
    try {
        const response = await fetch(`/download/spectrum/${filename}`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Error descargando el espectro');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// ========== FUNCIONES DE VISUALIZACIÓN DE RESULTADOS ==========

function showCleanResult(result) {
    const containerId = 'cleaned-spectra';
    let container = document.getElementById(containerId);

    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.className = 'mt-4 space-y-4';
        const rmnSection = document.getElementById('rmn-section');
        rmnSection.appendChild(container);
    }

    const emptyMsg = container.querySelector('div.text-xs.italic');
    if (emptyMsg) emptyMsg.remove();

    const cleanFileName = result.cleaned_file.split('/').pop();
    const plotFileName = result.plot_file ? result.plot_file.split('/').pop() : 'grafico_comparativo.png';
    const paramsStr = result.params ? 
        Object.entries(result.params).map(([key, value]) => `${key}: ${value}`).join(', ') : 
        'Parámetros automáticos';

    const entry = document.createElement('div');
    entry.className = 'p-4 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900 dark:to-blue-900 rounded-lg shadow-md border-l-4 border-green-500';
    entry.innerHTML = `
        <div class="flex justify-between items-start mb-3">
            <div class="flex items-center space-x-3">
                <div class="text-2xl">🧪</div>
                <div>
                    <div class="text-green-800 dark:text-green-200 font-bold text-lg">ESPECTRO LIMPIADO</div>
                    <div class="text-xs text-green-600 dark:text-green-400">
                        ${new Date().toLocaleString('es-ES')}
                    </div>
                </div>
            </div>
            <div class="flex space-x-1">
                <button onclick="analyzeCleanSpectrum('${cleanFileName}')" 
                        class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-xs">
                    🔍 Analizar
                </button>
                <button onclick="compareWithOriginal('${result.original_file}', '${cleanFileName}')" 
                        class="px-3 py-1 bg-purple-500 hover:bg-purple-600 text-white rounded text-xs">
                    📊 Comparar
                </button>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-4">
            <div class="space-y-1">
                <div class="flex justify-between">
                    <span class="text-gray-600 dark:text-gray-400">Archivo original:</span>
                    <span class="font-mono text-gray-800 dark:text-gray-200">${result.original_file}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600 dark:text-gray-400">Archivo limpio:</span>
                    <span class="font-mono text-green-700 dark:text-green-300">${cleanFileName}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600 dark:text-gray-400">Método:</span>
                    <span class="font-semibold text-blue-600 dark:text-blue-400">${result.method}</span>
                </div>
            </div>
            <div class="space-y-1">
                <div class="flex justify-between">
                    <span class="text-gray-600 dark:text-gray-400">Mejora SNR:</span>
                    <span class="font-semibold text-green-600 dark:text-green-400">+${result.snr_improvement || '0'} dB</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600 dark:text-gray-400">Parámetros:</span>
                    <span class="text-xs text-gray-700 dark:text-gray-300">${paramsStr}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600 dark:text-gray-400">Estado:</span>
                    <span class="text-green-600 dark:text-green-400 font-semibold">✅ Listo</span>
                </div>
            </div>
        </div>

        <div class="flex flex-wrap gap-2 pt-3 border-t border-green-200 dark:border-green-700">
            <a href="/download/cleaned/${encodeURIComponent(cleanFileName)}" download
               class="flex items-center px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors">
                📥 Descargar CSV Limpio
            </a>
            
            ${result.plot_file ? `
            <a href="/download/plot/${encodeURIComponent(plotFileName)}" download
               class="flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors">
                📊 Descargar Gráfico
            </a>
            ` : ''}

            <button onclick="exportSpectrum('${cleanFileName}', 'json')" 
                    class="flex items-center px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors">
                📁 Exportar JSON
            </button>

            <button onclick="showSpectrumDetails('${cleanFileName}')" 
                    class="flex items-center px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors">
                ℹ️ Detalles
            </button>
        </div>

        <div class="mt-3 text-xs text-gray-500 dark:text-gray-400 flex justify-between">
            <span>💡 Haz clic en "Analizar" para ver estadísticas detalladas</span>
            <span>🕒 Procesado en ${result.processing_time || '0'}s</span>
        </div>
    `;

    container.prepend(entry);
    loadRMNStats();
    showNotification('success', `Espectro limpiado: ${cleanFileName}`, 'El archivo está listo para descargar');
}

function analyzeCleanSpectrum(filename) {
    executeRMNCommand(`analizar: ${filename}`);
}

function compareWithOriginal(originalFile, cleanFile) {
    executeRMNCommand(`comparar: ${originalFile} con ${cleanFile}`);
}

function exportSpectrum(filename, format) {
    executeRMNCommand(`exportar: ${filename} formato ${format}`);
}

function showSpectrumDetails(filename) {
    executeRMNCommand(`detalles: ${filename}`);
}

// ========== SISTEMA DE NOTIFICACIONES ==========

function showNotification(type, title, message) {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transform transition-transform duration-300 ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 'bg-blue-500'
    } text-white`;
    
    notification.innerHTML = `
        <div class="flex items-center space-x-3">
            <span class="text-xl">${type === 'success' ? '✅' : type === 'error' ? '❌' : '💡'}</span>
            <div>
                <div class="font-semibold">${title}</div>
                <div class="text-sm opacity-90">${message}</div>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="text-white hover:text-gray-200">
                ×
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// ========== INICIALIZACIÓN AL CARGAR LA PÁGINA ==========

document.addEventListener('DOMContentLoaded', function() {
    initializeRMNSection();
    loadRMNStats();
    loadSpectraList();
    console.log('✅ Sistema de espectros RMN inicializado');
});

console.log('🧪 Módulo RMN cargado');