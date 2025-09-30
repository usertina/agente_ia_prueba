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

// ========== FUNCIONES DE TOGGLE Y NAVEGACIÓN (WINDOW) ==========

window.toggleRMNSection = function() {
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
};

window.showRMNHelp = function() {
    executeRMNCommand('ayuda rmn');
};

window.showRMNMethods = function() {
    executeRMNCommand('métodos');
};

window.listSpectra = function() {
    executeRMNCommand('listar espectros');
};

window.executeRMNCommand = function(command) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = command;
    form.dispatchEvent(new Event('submit'));
};

// ========== FUNCIONES DE LIMPIEZA RÁPIDA ==========

window.quickCleanAuto = function() {
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    executeRMNCommand(`limpiar auto: ${lastSpectrum}`);
};

window.quickCleanSavgol = function() {
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    executeRMNCommand(`limpiar: ${lastSpectrum} con savgol`);
};

window.quickCleanGaussian = function() {
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    executeRMNCommand(`limpiar: ${lastSpectrum} con gaussian`);
};

window.quickCleanMedian = function() {
    const lastSpectrum = localStorage.getItem('lastSpectrum') || 'mi_espectro.csv';
    executeRMNCommand(`limpiar: ${lastSpectrum} con median`);
};

// ========== FUNCIONES DE UPLOAD ==========

window.uploadSpectrum = async function() {
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
};

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

window.analyzeSpectrum = function(filename) {
    localStorage.setItem('lastSpectrum', filename);
    executeRMNCommand(`analizar: ${filename}`);
};

window.downloadSpectrum = async function(filename) {
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
};

// ========== INICIALIZACIÓN ==========

document.addEventListener('DOMContentLoaded', function() {
    initializeRMNSection();
    loadRMNStats();
    loadSpectraList();
    console.log('✅ Sistema de espectros RMN inicializado');
});

console.log('🧪 Módulo RMN cargado');