// ========== INICIALIZACIÓN DE LA SECCIÓN DE DOCUMENTOS ==========

function initializeDocumentSection() {
    const docSection = document.getElementById('document-section');
    if (!docSection) {
        console.error('❌ Sección Documentos no encontrada');
        return;
    }

    docSection.innerHTML = `
        <!-- Estadísticas -->
        <div id="document-stats" class="p-3 bg-orange-50 dark:bg-orange-900 rounded-lg text-sm mb-3">
            <strong>📊 Estado Documentos</strong><br>
            <span class="text-sm">Plantillas: 0 | Datos: 0 | Generados: 0</span>
        </div>

                <!-- Botones de ayuda -->
        <div class="space-y-2 mb-3">
            <button onclick="autoFillQuick()" 
                    class="w-full text-left p-3 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-lg hover:from-purple-600 hover:to-indigo-700 transition-all duration-300 font-bold shadow-lg">
                ⚡ RELLENAR AUTOMÁTICO
            </button>
            <button onclick="showUserDatabase()" 
                    class="w-full text-left p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors text-sm">
                🗄️ Ver Mi Base de Datos
            </button>
            <button onclick="configureDatabase()" 
                    class="w-full text-left p-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors text-sm">
                ⚙️ Configurar Mis Datos
            </button>
            <button onclick="showDocumentHelp()" 
                    class="w-full text-left p-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm">
                ❓ Ayuda
            </button>
        </div>

        <!-- Upload plantilla -->
        <div class="mb-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2 text-sm">📤 Subir Plantilla</h4>
            <input type="file" id="template-file-input" accept=".docx,.txt,.pdf" class="hidden">
            <button onclick="document.getElementById('template-file-input').click()" 
                    class="w-full p-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg text-sm mb-2">
                📁 Seleccionar Plantilla
            </button>
            <button onclick="uploadTemplate()" 
                    class="w-full p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm">
                ⬆️ Subir Plantilla
            </button>
        </div>

        <!-- Upload datos -->
        <div class="mb-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2 text-sm">📤 Subir Datos</h4>
            <input type="file" id="data-file-input" accept=".json,.csv,.xlsx,.txt" class="hidden">
            <button onclick="document.getElementById('data-file-input').click()" 
                    class="w-full p-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg text-sm mb-2">
                📁 Seleccionar Datos
            </button>
            <button onclick="uploadDataFile()" 
                    class="w-full p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm">
                ⬆️ Subir Datos
            </button>
        </div>

        <!-- Listas -->
        <div id="templates-list" class="mb-2"></div>
        <div id="data-files-list" class="mb-2"></div>
        <div id="output-files-list"></div>
    `;

    console.log('✅ Sección Documentos inicializada');
}

// ========== VARIABLES GLOBALES ==========

let currentDocumentFiles = {
    templates: [],
    data_files: [],
    output_files: []
};

// ========== FUNCIONES DE TOGGLE ==========

window.toggleDocumentSection = function() {
    const section = document.getElementById('document-section');
    const button = document.getElementById('document-toggle');
    
    if (!section) {
        console.error('❌ Sección Documentos no encontrada');
        return;
    }
    
    if (section.classList.contains('hidden')) {
        section.classList.remove('hidden');
        if (button) button.innerHTML = '📄 Documentos ▼';
        loadDocumentFiles();
    } else {
        section.classList.add('hidden');
        if (button) button.innerHTML = '📄 Documentos ▶';
    }
};

// ========== FUNCIONES DE CARGA ==========

async function loadDocumentFiles() {
    try {
        const response = await fetch('/files/documents');
        const data = await response.json();
        
        currentDocumentFiles = {
            templates: data.templates || [],
            data_files: data.data_files || [],
            output_files: data.output_files || []
        };
        
        updateDocumentFilesUI();
    } catch (error) {
        console.error('Error cargando archivos de documentos:', error);
    }
}

function updateDocumentFilesUI() {
    updateTemplatesList();
    updateDataFilesList();
    updateOutputFilesList();
    updateDocumentStats();
}

// ========== ACTUALIZAR LISTAS ==========

function updateTemplatesList() {
    const container = document.getElementById('templates-list');
    if (!container) return;
    
    if (currentDocumentFiles.templates.length === 0) {
        container.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400 italic text-center p-4">📄 No hay plantillas</p>';
        return;
    }
    
    container.innerHTML = currentDocumentFiles.templates.map(file => `
        <div class="flex justify-between items-center p-3 bg-blue-50 dark:bg-blue-900 rounded-lg mb-2">
            <div class="flex-1">
                <div class="font-medium text-blue-800 dark:text-blue-200">${escapeHtml(file.name)}</div>
                <div class="text-xs text-blue-600 dark:text-blue-400">${formatFileSize(file.size)}</div>
            </div>
            <div class="flex space-x-1">
                <button onclick="analyzeTemplate('${escapeHtml(file.name)}')" class="text-lg p-1" title="Analizar">🔍</button>
                <button onclick="deleteTemplate('${escapeHtml(file.name)}')" class="text-lg p-1" title="Eliminar">🗑️</button>
            </div>
        </div>
    `).join('');
}

function updateDataFilesList() {
    const container = document.getElementById('data-files-list');
    if (!container) return;
    
    if (currentDocumentFiles.data_files.length === 0) {
        container.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400 italic text-center p-4">📊 No hay datos</p>';
        return;
    }
    
    container.innerHTML = currentDocumentFiles.data_files.map(file => `
        <div class="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900 rounded-lg mb-2">
            <div class="flex-1">
                <div class="font-medium text-green-800 dark:text-green-200">${escapeHtml(file.name)}</div>
                <div class="text-xs text-green-600 dark:text-green-400">${formatFileSize(file.size)}</div>
            </div>
            <div class="flex space-x-1">
                <a href="/download/data/${encodeURIComponent(file.name)}" class="text-lg p-1" title="Descargar">⬇️</a>
                <button onclick="deleteDataFile('${escapeHtml(file.name)}')" class="text-lg p-1" title="Eliminar">🗑️</button>
            </div>
        </div>
    `).join('');
}

function updateOutputFilesList() {
    const container = document.getElementById('output-files-list');
    if (!container) return;
    
    if (currentDocumentFiles.output_files.length === 0) {
        container.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400 italic text-center p-4">📁 No hay documentos generados</p>';
        return;
    }
    
    container.innerHTML = currentDocumentFiles.output_files.map(file => `
        <div class="flex justify-between items-center p-3 bg-yellow-50 dark:bg-yellow-900 rounded-lg mb-2">
            <div class="flex-1">
                <div class="font-medium text-yellow-800 dark:text-yellow-200">${escapeHtml(file.name)}</div>
                <div class="text-xs text-yellow-600 dark:text-yellow-400">${formatFileSize(file.size)}</div>
            </div>
            <div class="flex space-x-1">
                <a href="/download/output/${encodeURIComponent(file.name)}" class="text-lg p-1" title="Descargar">📥</a>
                <button onclick="deleteOutputFile('${escapeHtml(file.name)}')" class="text-lg p-1" title="Eliminar">🗑️</button>
            </div>
        </div>
    `).join('');
}

function updateDocumentStats() {
    const statsElement = document.getElementById('document-stats');
    if (statsElement && currentDocumentFiles) {
        const templatesCount = currentDocumentFiles.templates.length;
        const dataCount = currentDocumentFiles.data_files.length;
        const outputCount = currentDocumentFiles.output_files.length;
        
        statsElement.innerHTML = `
            <strong>📊 Estado Documentos</strong><br>
            <span class="text-sm">Plantillas: ${templatesCount} | Datos: ${dataCount} | Generados: ${outputCount}</span>
        `;
    }
}

// ========== FUNCIONES DE ACCIÓN ==========

window.analyzeTemplate = function(filename) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `analizar: ${filename}`;
    form.dispatchEvent(new Event('submit'));
};

window.showDocumentHelp = function() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'document_filler help';
    form.dispatchEvent(new Event('submit'));
};

window.listTemplates = function() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'listar plantillas';
    form.dispatchEvent(new Event('submit'));
};

window.listDataFiles = function() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'listar datos';
    form.dispatchEvent(new Event('submit'));
};

// ========== FUNCIONES DE UPLOAD ==========

window.uploadTemplate = async function() {
    const fileInput = document.getElementById('template-file-input');
    if (!fileInput || !fileInput.files.length) {
        alert('Selecciona un archivo de plantilla');
        return;
    }
    
    await uploadFile('/upload/template', fileInput.files[0], fileInput);
};

window.uploadDataFile = async function() {
    const fileInput = document.getElementById('data-file-input');
    if (!fileInput || !fileInput.files.length) {
        alert('Selecciona un archivo de datos');
        return;
    }
    
    await uploadFile('/upload/data', fileInput.files[0], fileInput);
};

async function uploadFile(endpoint, file, fileInput) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(endpoint, { method: 'POST', body: formData });
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ ${result.message}`);
            fileInput.value = '';
            loadDocumentFiles();
        } else {
            alert(`❌ Error: ${result.error}`);
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

// ========== FUNCIONES DE ELIMINACIÓN ==========

window.deleteTemplate = async function(filename) {
    if (!confirm(`¿Eliminar plantilla "${filename}"?`)) return;
    await deleteFile(`/delete/template/${encodeURIComponent(filename)}`);
};

window.deleteDataFile = async function(filename) {
    if (!confirm(`¿Eliminar datos "${filename}"?`)) return;
    await deleteFile(`/delete/data/${encodeURIComponent(filename)}`);
};

window.deleteOutputFile = async function(filename) {
    if (!confirm(`¿Eliminar documento "${filename}"?`)) return;
    await deleteFile(`/delete/output/${encodeURIComponent(filename)}`);
};

async function deleteFile(url) {
    try {
        const response = await fetch(url, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ ${result.message}`);
            loadDocumentFiles();
        } else {
            alert(`❌ ${result.error}`);
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

// ========== UTILIDADES ==========

function escapeHtml(unsafe) {
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDate(timestamp) {
    return new Date(timestamp * 1000).toLocaleString('es-ES');
}

// ========== INICIALIZACIÓN ==========

document.addEventListener('DOMContentLoaded', function() {
    initializeDocumentSection();
    console.log('📄 Sistema de documentos inicializado');
});

// ========== NUEVAS FUNCIONES DE AUTORELLENADO ==========

window.autoFillQuick = function() {
    const templates = currentDocumentFiles.templates;
    
    if (templates.length === 0) {
        alert('⚠️ No hay plantillas disponibles.\n\n1. Sube una plantilla primero\n2. Luego usa este botón');
        return;
    }
    
    let templateName;
    
    if (templates.length === 1) {
        templateName = templates[0].name;
    } else {
        const opciones = templates.map((t, i) => `${i+1}. ${t.name}`).join('\n');
        templateName = prompt(`🎯 Selecciona plantilla para rellenar:\n\n${opciones}\n\nEscribe el nombre completo:`);
        
        if (!templateName) return;
    }
    
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `rellenar auto: ${templateName}`;
    form.dispatchEvent(new Event('submit'));
    
    // Mostrar mensaje de carga
    const loading = document.createElement('div');
    loading.className = 'fixed top-4 right-4 bg-purple-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-pulse';
    loading.innerHTML = `
        <div class="flex items-center">
            <svg class="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>⚡ Generando documento automáticamente...</span>
        </div>
    `;
    document.body.appendChild(loading);
    
    setTimeout(() => {
        if (loading.parentElement) loading.remove();
    }, 5000);
};

window.showUserDatabase = function() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'ver datos';
    form.dispatchEvent(new Event('submit'));
};

window.configureDatabase = function() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'configurar datos';
    form.dispatchEvent(new Event('submit'));
};

// Actualizar cuando se detecte un documento generado
window.addEventListener('documentGenerated', function() {
    loadDocumentFiles();
});

console.log('📄 Módulo de documentos cargado');