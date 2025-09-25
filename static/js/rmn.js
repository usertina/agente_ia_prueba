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

// Cargar estadísticas al inicio
document.addEventListener('DOMContentLoaded', function() {
    loadRMNStats();
});