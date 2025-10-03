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

        

        <!-- Listas -->
        <div id="templates-list" class="mb-2"></div>
    
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
    input.value = `analizar plantilla ${filename}`;
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

// EN document.js

// =============================================================
// REEMPLAZA TU FUNCIÓN autoFillQuick POR TODO ESTE BLOQUE
// =============================================================

// Función principal que inicia el proceso de autorellenado
window.autoFillQuick = async function() {
    const templates = currentDocumentFiles.templates;
    
    if (templates.length === 0) {
        alert('⚠️ No hay plantillas. Sube una primero.');
        return;
    }
    
    let templateName;
    if (templates.length === 1) {
        templateName = templates[0].name;
    } else {
        const opciones = templates.map((t, i) => `${i+1}. ${t.name}`).join('\n');
        const selected = prompt(`🎯 Elige una plantilla para rellenar:\n\n${opciones}\n\nEscribe el nombre completo o el número:`);
        
        if (!selected) return; // El usuario canceló
        
        // Permite seleccionar por número o por nombre
        const index = parseInt(selected, 10) - 1;
        if (!isNaN(index) && templates[index]) {
            templateName = templates[index].name;
        } else if (templates.some(t => t.name === selected)) {
            templateName = selected;
        } else {
            alert('❌ Plantilla no válida.');
            return;
        }
    }
    
    // En lugar de llamar directamente a la API, muestra la modal
    showDocTypeModal(templateName);
};

// Nueva función para mostrar la modal
function showDocTypeModal(templateName) {
    const modal = document.getElementById('doc-type-modal');
    if (modal) {
        // Almacena el nombre de la plantilla en la modal para usarlo después
        modal.dataset.templateName = templateName;
        modal.classList.remove('hidden');
    }
}

// Nueva función para ocultar la modal
function hideDocTypeModal() {
    const modal = document.getElementById('doc-type-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Nueva función que contiene la lógica de la llamada a la API
async function runAutoFill(templateName, docType) {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'autofill-loading';
    loadingDiv.className = 'fixed top-4 right-4 bg-purple-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    loadingDiv.innerHTML = `<div class="flex items-center"><svg class="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg><span>⚡ Generando documento...</span></div>`;
    document.body.appendChild(loadingDiv);
    
    try {
        // Llamada a tu endpoint de Python
        // Se añade el 'doc_type' al cuerpo de la petición
        const response = await fetch('/fill/auto', { // Asegúrate que el endpoint sea el correcto
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                template_filename: templateName,
                doc_type: docType
            })
        });
        
        const result = await response.json();
        
        if (loadingDiv.parentElement) loadingDiv.remove();
        
        if (result.success) {
            showSuccessNotification(result, templateName);
            await loadDocumentFiles();
            setTimeout(() => {
                const outputSection = document.getElementById('output-files-list');
                if (outputSection) {
                    outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 500);
        } else {
            alert(`❌ Error:\n${result.message || result.error || 'Error desconocido'}`);
        }
    } catch (error) {
        console.error('Error en runAutoFill:', error);
        if (loadingDiv.parentElement) loadingDiv.remove();
        alert(`❌ Error de conexión: ${error.message}`);
    }
}

// Lógica para manejar los clics en los botones de la modal
// Se añade al final de tu archivo, dentro del evento DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('doc-type-modal');
    if (modal) {
        modal.addEventListener('click', function(event) {
            const button = event.target.closest('button');
            if (!button) return;

            const docType = button.dataset.docType;
            if (docType) {
                // Si se hizo clic en un botón de tipo
                const templateName = modal.dataset.templateName;
                hideDocTypeModal();
                runAutoFill(templateName, docType);
            } else if (button.id === 'cancel-doc-type-modal') {
                // Si se hizo clic en cancelar
                hideDocTypeModal();
            }
        });
    }
});
// ✅ NUEVA FUNCIÓN: Mostrar notificación de éxito elegante
function showSuccessNotification(result, templateName) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-4 rounded-lg shadow-2xl z-50 animate-slide-in max-w-md';
    
    const stats = result.statistics || {};
    // Limpiar el nombre del archivo de asteriscos y espacios extra
    let outputFile = result.output_file;
    if (outputFile) {
        outputFile = outputFile.replace(/^\*+\s*/, '').trim();
    }
    
    notification.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
            </div>
            <div class="ml-3 flex-1">
                <h3 class="text-sm font-bold">✅ Documento Generado</h3>
                <p class="mt-1 text-xs">${outputFile || templateName}</p>
                ${stats.total_fields ? `
                    <p class="mt-2 text-xs opacity-90">
                        📊 ${stats.total_fields} campos | 
                        🗄️ ${stats.from_database} de BD | 
                        🤖 ${stats.from_ai} de IA
                    </p>
                ` : ''}
                ${result.download_url ? `
                    <a href="${result.download_url}" 
                       class="mt-2 inline-block text-xs bg-white text-green-600 px-3 py-1 rounded hover:bg-green-50 transition-colors">
                        📥 Descargar
                    </a>
                ` : ''}
            </div>
            <button onclick="this.parentElement.parentElement.remove()" 
                    class="ml-4 text-white hover:text-gray-200">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remover después de 10 segundos
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            notification.style.transition = 'all 0.5s ease';
            setTimeout(() => notification.remove(), 500);
        }
    }, 10000);
}

// ✅ CSS para la animación
const style = document.createElement('style');
style.textContent = `
@keyframes slide-in {
    from {
        opacity: 0;
        transform: translateX(100%);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.animate-slide-in {
    animation: slide-in 0.5s ease-out;
}
`;
document.head.appendChild(style);

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

// ========== FUNCIONES DE UPLOAD ==========

window.uploadTemplate = async function() {
    const fileInput = document.getElementById('template-file-input');
    if (!fileInput || !fileInput.files.length) {
        alert('Selecciona un archivo de plantilla');
        return;
    }
    
    await uploadFile('/upload/template', fileInput.files[0], fileInput);
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


// ========== FUNCIÓN DE AUTORELLENADO MEJORADA ==========



// Actualizar cuando se detecte un documento generado
window.addEventListener('documentGenerated', function() {
    loadDocumentFiles();
});

console.log('📄 Módulo de documentos cargado');