// Funciones para la sección de Espectros RMN

function toggleRMNSection() {
    const section = document.getElementById('rmn-section');
    const toggle = document.getElementById('rmn-toggle');
    
    if (section.classList.contains('hidden')) {
        section.classList.remove('hidden');
        toggle.innerHTML = '🧪 Espectros RMN ▼';
        loadRMNStats();
    } else {
        section.classList.add('hidden');
        toggle.innerHTML = '🧪 Espectros RMN ▶';
    }
}

function showRMNHelp() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'ayuda rmn';
    form.dispatchEvent(new Event('submit'));
}

function showRMNMethods() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'métodos';
    form.dispatchEvent(new Event('submit'));
}

function listSpectra() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'listar espectros';
    form.dispatchEvent(new Event('submit'));
}

function executeRMNCommand(command) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = command;
    form.dispatchEvent(new Event('submit'));
}

function quickCleanAuto() {
    // Obtener el último espectro mencionado o pedir al usuario
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `limpiar auto: ${lastSpectrum}`;
    form.dispatchEvent(new Event('submit'));
}

function quickCleanSavgol() {
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `limpiar: ${lastSpectrum} con savgol`;
    form.dispatchEvent(new Event('submit'));
}

function quickCleanGaussian() {
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `limpiar: ${lastSpectrum} con gaussian`;
    form.dispatchEvent(new Event('submit'));
}

function quickCleanMedian() {
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `limpiar: ${lastSpectrum} con median`;
    form.dispatchEvent(new Event('submit'));
}

async function uploadSpectrum() {
    const fileInput = document.getElementById('spectrum-file-input');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Por favor selecciona un archivo de espectro');
        return;
    }

    // Validar formato
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
            // Mostrar mensaje de éxito
            alert(`✅ ${result.message}\n💡 ${result.next_step}`);
            
            // Guardar último espectro para comandos rápidos
            localStorage.setItem('lastSpectrum', result.filename);
            
            // Limpiar input
            fileInput.value = '';
            
            // Actualizar lista de espectros
            loadSpectraList();
            loadRMNStats();
        } else {
            alert(`❌ Error: ${result.error}`);
        }
    } catch (error) {
        alert(`❌ Error subiendo espectro: ${error.message}`);
    }
}

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

function analyzeSpectrum(filename) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `analizar: ${filename}`;
    localStorage.setItem('lastSpectrum', filename);
    form.dispatchEvent(new Event('submit'));
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

async function loadRMNStats() {
    try {
        const response = await fetch('/files/spectra');
        const data = await response.json();
        
        const statsElement = document.getElementById('rmn-stats');
        if (statsElement) {
            const spectraCount = data.spectra ? data.spectra.length : 0;
            const cleanedCount = data.cleaned ? data.cleaned.length : 0;
            const plotsCount = data.plots ? data.plots.length : 0;
            
            statsElement.textContent = `Espectros: ${spectraCount} | Limpios: ${cleanedCount} | Gráficos: ${plotsCount}`;
        }
    } catch (error) {
        console.error('Error cargando estadísticas RMN:', error);
    }
}
console.log("Result recibido:", result);

// -----------------------------
// Mostrar espectro limpio con descarga
function showCleanResult(result) {
    const containerId = 'cleaned-spectra';
    let container = document.getElementById(containerId);

    // Si no existe el contenedor, lo creamos
    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.className = 'mt-4 space-y-4';
        const rmnSection = document.getElementById('rmn-section');
        rmnSection.appendChild(container);
    }

    // Eliminar mensaje de "Todavía no hay espectros limpios"
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

    updateRMNStats();
    showNotification('success', `Espectro limpiado: ${cleanFileName}`, 'El archivo está listo para descargar');
}

// -----------------------------
// Funciones auxiliares para espectros limpios
// -----------------------------

function analyzeCleanSpectrum(filename) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `analizar: ${filename}`;
    form.dispatchEvent(new Event('submit'));
}

function compareWithOriginal(originalFile, cleanFile) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `comparar: ${originalFile} con ${cleanFile}`;
    form.dispatchEvent(new Event('submit'));
}

function exportSpectrum(filename, format) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `exportar: ${filename} formato ${format}`;
    form.dispatchEvent(new Event('submit'));
}

function showSpectrumDetails(filename) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `detalles: ${filename}`;
    form.dispatchEvent(new Event('submit'));
}

// -----------------------------
// Actualizar estadísticas RMN
// -----------------------------
async function updateRMNStats() {
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
        console.error('Error actualizando estadísticas RMN:', error);
    }
}

// -----------------------------
// Sistema de notificaciones para espectros
// -----------------------------
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
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}
// Añadir estas funciones al archivo static/js/rmn.js o al script principal

// Función para detectar y manejar resultados de limpieza de espectros
function handleSpectrumCleaningResult(result, input, tool) {
    console.log("Procesando resultado de limpieza:", result);
    
    // Verificar si es un resultado de limpieza de espectro
    if (typeof result === 'object' && result.type === 'clean_result') {
        showCleanSpectrumResult(result);
        return true;
    }
    
    // También verificar si es un string que contiene información de limpieza
    if (typeof result === 'string' && result.includes('ESPECTRO LIMPIADO')) {
        // Intentar extraer información del texto
        const cleanFileName = extractFileNameFromText(result);
        if (cleanFileName) {
            showSimpleCleanResult(cleanFileName, result);
            return true;
        }
    }
    
    return false;
}

// Función para mostrar resultado completo de limpieza
function showCleanSpectrumResult(result) {
    console.log("Mostrando resultado completo:", result);
    
    const responseDiv = document.getElementById('response');
    if (!responseDiv) return;
    
    const cleanFileName = result.cleaned_file.split('/').pop();
    const plotFileName = result.plot_file ? result.plot_file.split('/').pop() : null;
    
    const resultHTML = `
        <div class="spectrum-clean-result bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900 dark:to-blue-900 rounded-lg shadow-md border-l-4 border-green-500 p-4 mb-4">
            <div class="flex justify-between items-start mb-3">
                <div class="flex items-center space-x-3">
                    <div class="text-2xl">🧪</div>
                    <div>
                        <div class="text-green-800 dark:text-green-200 font-bold text-lg">ESPECTRO LIMPIADO EXITOSAMENTE</div>
                        <div class="text-xs text-green-600 dark:text-green-400">
                            ${new Date().toLocaleString('es-ES')}
                        </div>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-4">
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Archivo original:</span>
                        <span class="font-mono text-gray-800 dark:text-gray-200 text-xs">${result.original_file}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Archivo limpio:</span>
                        <span class="font-mono text-green-700 dark:text-green-300 text-xs">${cleanFileName}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Método usado:</span>
                        <span class="font-semibold text-blue-600 dark:text-blue-400">${result.method}</span>
                    </div>
                </div>
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Mejora SNR:</span>
                        <span class="font-semibold text-green-600 dark:text-green-400">+${result.snr_improvement} dB</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Puntos de datos:</span>
                        <span class="text-gray-700 dark:text-gray-300">${result.data_points.toLocaleString()}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Tiempo procesado:</span>
                        <span class="text-gray-700 dark:text-gray-300">${result.processing_time}s</span>
                    </div>
                </div>
            </div>

            <div class="flex flex-wrap gap-2 pt-3 border-t border-green-200 dark:border-green-700">
                <button onclick="downloadCleanedFile('${cleanFileName}')" 
                        class="flex items-center px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors">
                    📥 Descargar CSV Limpio
                </button>
                
                ${plotFileName ? `
                <button onclick="downloadPlotFile('${plotFileName}')" 
                        class="flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors">
                    📊 Descargar Gráfico
                </button>
                ` : ''}

                <button onclick="analyzeCleanSpectrum('${cleanFileName}')" 
                        class="flex items-center px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors">
                    🔍 Analizar Limpio
                </button>

                <button onclick="compareSpectra('${result.original_file}')" 
                        class="flex items-center px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg transition-colors">
                    📊 Comparar Versiones
                </button>
            </div>

            <div class="mt-3 text-xs text-gray-500 dark:text-gray-400">
                💡 El archivo está guardado y listo para descargar. Usa "analizar: ${cleanFileName}" para ver estadísticas detalladas.
            </div>
        </div>
    `;
    
    // Insertar al inicio del response div
    responseDiv.insertAdjacentHTML('afterbegin', resultHTML);
    
    // Actualizar estadísticas
    updateRMNStats();
    
    // Mostrar notificación
    showNotification('success', 'Espectro Limpiado', `${cleanFileName} está listo para descargar`);
    
    // Guardar último espectro para comandos rápidos
    localStorage.setItem('lastSpectrum', result.original_file);
    localStorage.setItem('lastCleanedSpectrum', cleanFileName);
}

// Función para resultado simple (cuando solo tenemos texto)
function showSimpleCleanResult(fileName, resultText) {
    const responseDiv = document.getElementById('response');
    if (!responseDiv) return;
    
    const resultHTML = `
        <div class="spectrum-clean-simple bg-green-50 dark:bg-green-900 rounded-lg border-l-4 border-green-500 p-4 mb-4">
            <div class="flex items-center space-x-3 mb-3">
                <div class="text-2xl">🧪</div>
                <div>
                    <div class="text-green-800 dark:text-green-200 font-bold">ESPECTRO PROCESADO</div>
                    <div class="text-xs text-green-600 dark:text-green-400">
                        ${new Date().toLocaleString('es-ES')}
                    </div>
                </div>
            </div>
            
            <div class="text-sm mb-4 whitespace-pre-wrap">${resultText}</div>
            
            <div class="flex flex-wrap gap-2">
                <button onclick="listCleanedSpectra()" 
                        class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg">
                    📋 Ver Espectros Limpios
                </button>
                
                <button onclick="executeRMNCommand('listar espectros')" 
                        class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg">
                    🔄 Actualizar Lista
                </button>
            </div>
        </div>
    `;
    
    responseDiv.insertAdjacentHTML('afterbegin', resultHTML);
    updateRMNStats();
}

// Funciones de descarga
async function downloadCleanedFile(filename) {
    try {
        console.log(`Descargando archivo limpio: ${filename}`);
        const response = await fetch(`/download/cleaned/${encodeURIComponent(filename)}`);
        
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
            
            showNotification('success', 'Descarga iniciada', `${filename} descargándose`);
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error descargando archivo limpio:', error);
        showNotification('error', 'Error de descarga', `No se pudo descargar ${filename}: ${error.message}`);
    }
}

async function downloadPlotFile(filename) {
    try {
        console.log(`Descargando gráfico: ${filename}`);
        const response = await fetch(`/download/plot/${encodeURIComponent(filename)}`);
        
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
            
            showNotification('success', 'Gráfico descargado', filename);
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error descargando gráfico:', error);
        showNotification('error', 'Error de descarga', `No se pudo descargar el gráfico: ${error.message}`);
    }
}

// Función para listar espectros limpios disponibles
async function listCleanedSpectra() {
    try {
        const response = await fetch('/list/cleaned');
        const data = await response.json();
        
        if (data.success && data.cleaned.length > 0) {
            let listHTML = '<div class="cleaned-spectra-list mt-4"><h4 class="font-bold mb-2">📋 Espectros Limpios Disponibles:</h4>';
            
            data.cleaned.forEach((spectrum, index) => {
                listHTML += `
                    <div class="flex items-center justify-between p-2 bg-white dark:bg-gray-700 rounded border text-xs mb-1">
                        <div class="flex-1">
                            <div class="font-semibold text-green-800 dark:text-green-200">${spectrum.name}</div>
                            <div class="text-gray-600 dark:text-gray-400">${(spectrum.size / 1024).toFixed(1)} KB</div>
                        </div>
                        <div class="flex gap-1">
                            <button onclick="downloadCleanedFile('${spectrum.name}')" 
                                    class="px-2 py-1 bg-green-500 hover:bg-green-600 text-white rounded text-xs">
                                📥 Descargar
                            </button>
                            <button onclick="analyzeCleanSpectrum('${spectrum.name}')" 
                                    class="px-2 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-xs">
                                🔍 Analizar
                            </button>
                        </div>
                    </div>
                `;
            });
            
            listHTML += '</div>';
            
            const responseDiv = document.getElementById('response');
            if (responseDiv) {
                responseDiv.insertAdjacentHTML('afterbegin', listHTML);
            }
        } else {
            showNotification('info', 'Sin espectros', 'No hay espectros limpios disponibles');
        }
    } catch (error) {
        console.error('Error listando espectros limpios:', error);
        showNotification('error', 'Error', 'No se pudo obtener la lista de espectros limpios');
    }
}

// Función para extraer nombre de archivo del texto de respuesta
function extractFileNameFromText(text) {
    const matches = text.match(/([^\/\s]+_clean_\d+\.csv)|([^\/\s]+_[a-zA-Z]+_\d+\.csv)/);
    return matches ? matches[0] : null;
}

// Función para comparar espectros (llamada desde botón)
function compareSpectra(originalFile) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `comparar: ${originalFile}`;
    form.dispatchEvent(new Event('submit'));
}

// MODIFICACIÓN IMPORTANTE: Integrar con el sistema de respuestas existente
// Esta función debe ser llamada desde el manejador principal de respuestas

function integrateSpectrumHandling() {
    // Interceptar las respuestas del formulario principal
    const originalHandleResponse = window.handleFormResponse || function() {};
    
    window.handleFormResponse = function(data) {
        console.log("Interceptando respuesta:", data);
        
        // Verificar si es una respuesta de limpieza de espectro
        if (data.result_type === 'text' && typeof data.result_data === 'object' && data.result_data.type === 'clean_result') {
            handleSpectrumCleaningResult(data.result_data, data.input, data.tool);
            return;
        } else if (data.result_type === 'text' && typeof data.result_data === 'string') {
            // Verificar si el texto indica limpieza de espectro
            if (handleSpectrumCleaningResult(data.result_data, data.input, data.tool)) {
                return;
            }
        }
        
        // Si no es un resultado de espectro, usar el manejador original
        originalHandleResponse(data);
    };
}

// Inicializar la integración cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    integrateSpectrumHandling();
    console.log("Sistema de manejo de espectros RMN integrado");
});