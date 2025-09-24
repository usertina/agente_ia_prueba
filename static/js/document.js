// ========== FUNCIONES DE GESTIÓN DE DOCUMENTOS ==========

// Variables que necesita document.js
const input = document.getElementById('user-input') || document.querySelector('input[type="text"]');
const form = document.getElementById('chat-form') || document.querySelector('form');
let historyDiv = document.getElementById('chat-history') || document.querySelector('.chat-history');

// Si no existe el contenedor de historial, crearlo dinámicamente
if (!historyDiv) {
    historyDiv = document.createElement('div');
    historyDiv.id = 'chat-history';
    historyDiv.className = 'chat-history';
    document.body.prepend(historyDiv);
}

// Variables globales para documentos
let currentDocumentFiles = {
    templates: [],
    data_files: [],
    output_files: []
};

function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}


// Función para mostrar/ocultar la sección de documentos
window.toggleDocumentSection = function() {
    const section = document.getElementById('document-section');
    const button = document.getElementById('document-toggle');
    
    if (section.classList.contains('hidden')) {
        section.classList.remove('hidden');
        button.textContent = '📄 Documentos ▼';
        loadDocumentFiles();
    } else {
        section.classList.add('hidden');
        button.textContent = '📄 Documentos ▶';
    }
};

// Cargar lista de archivos de documentos
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

// Actualizar la UI con los archivos de documentos
function updateDocumentFilesUI() {
    updateTemplatesList();
    updateDataFilesList();
    updateOutputFilesList();
}

// Actualizar lista de plantillas
function updateTemplatesList() {
    const container = document.getElementById('templates-list');
    if (!container) return;
    
    if (currentDocumentFiles.templates.length === 0) {
        container.innerHTML = `
            <p class="text-sm text-gray-500 dark:text-gray-400 italic text-center p-4">
                📄 No hay plantillas. Sube una plantilla para empezar.
            </p>
        `;
        return;
    }
    
    container.innerHTML = currentDocumentFiles.templates.map(file => `
        <div class="flex justify-between items-center p-3 bg-blue-50 dark:bg-blue-900 rounded-lg mb-2 border border-blue-200 dark:border-blue-700">
            <div class="flex-1">
                <div class="font-medium text-blue-800 dark:text-blue-200">${escapeHtml(file.name)}</div>
                <div class="text-xs text-blue-600 dark:text-blue-400">
                    ${formatFileSize(file.size)} • ${formatDate(file.modified)}
                </div>
            </div>
            <div class="flex space-x-1 ml-2">
                <button onclick="analyzeTemplate('${escapeHtml(file.name)}')" 
                        class="text-blue-600 hover:text-blue-800 text-lg p-1" 
                        title="Analizar plantilla">🔍</button>
                <button onclick="createExampleData('${escapeHtml(file.name)}')" 
                        class="text-green-600 hover:text-green-800 text-lg p-1" 
                        title="Crear datos de ejemplo">📋</button>
                <a href="/download/template/${encodeURIComponent(file.name)}" 
                   class="text-gray-600 hover:text-gray-800 text-lg p-1" 
                   title="Descargar">⬇️</a>
                <button onclick="deleteTemplate('${escapeHtml(file.name)}')" 
                        class="text-red-600 hover:text-red-800 text-lg p-1" 
                        title="Eliminar">🗑️</button>
            </div>
        </div>
    `).join('');
}

// Actualizar lista de archivos de datos
function updateDataFilesList() {
    const container = document.getElementById('data-files-list');
    if (!container) return;
    
    if (currentDocumentFiles.data_files.length === 0) {
        container.innerHTML = `
            <p class="text-sm text-gray-500 dark:text-gray-400 italic text-center p-4">
                📊 No hay archivos de datos. Crea datos de ejemplo o sube un archivo.
            </p>
        `;
        return;
    }
    
    container.innerHTML = currentDocumentFiles.data_files.map(file => `
        <div class="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900 rounded-lg mb-2 border border-green-200 dark:border-green-700">
            <div class="flex-1">
                <div class="font-medium text-green-800 dark:text-green-200">${escapeHtml(file.name)}</div>
                <div class="text-xs text-green-600 dark:text-green-400">
                    ${formatFileSize(file.size)} • ${formatDate(file.modified)}
                </div>
            </div>
            <div class="flex space-x-1 ml-2">
                <button onclick="previewDataFile('${escapeHtml(file.name)}')" 
                        class="text-green-600 hover:text-green-800 text-lg p-1" 
                        title="Ver contenido">👁️</button>
                <a href="/download/data/${encodeURIComponent(file.name)}" 
                   class="text-gray-600 hover:text-gray-800 text-lg p-1" 
                   title="Descargar">⬇️</a>
                <button onclick="deleteDataFile('${escapeHtml(file.name)}')" 
                        class="text-red-600 hover:text-red-800 text-lg p-1" 
                        title="Eliminar">🗑️</button>
            </div>
        </div>
    `).join('');
}

// Actualizar lista de documentos generados
function updateOutputFilesList() {
    const container = document.getElementById('output-files-list');
    if (!container) return;
    
    if (currentDocumentFiles.output_files.length === 0) {
        container.innerHTML = `
            <p class="text-sm text-gray-500 dark:text-gray-400 italic text-center p-4">
                📁 No hay documentos generados aún.
            </p>
        `;
        return;
    }
    
    container.innerHTML = currentDocumentFiles.output_files.map(file => `
        <div class="flex justify-between items-center p-3 bg-yellow-50 dark:bg-yellow-900 rounded-lg mb-2 border border-yellow-200 dark:border-yellow-700">
            <div class="flex-1">
                <div class="font-medium text-yellow-800 dark:text-yellow-200">${escapeHtml(file.name)}</div>
                <div class="text-xs text-yellow-600 dark:text-yellow-400">
                    ${formatFileSize(file.size)} • ${formatDate(file.modified)}
                </div>
            </div>
            <div class="flex space-x-1 ml-2">
                <a href="/download/output/${encodeURIComponent(file.name)}" 
                   class="text-yellow-600 hover:text-yellow-800 text-lg p-1" 
                   title="Descargar documento generado">📥</a>
                <button onclick="deleteOutputFile('${escapeHtml(file.name)}')"
                        class="text-red-600 hover:text-red-800 text-lg p-1
                        title="Eliminar documento generado">🗑️</button> 
            </div>
        </div>
    `).join('');
}

// Función para eliminar documentos generados
window.deleteOutputFile = async function(filename) {
    if (!confirm(`¿Quieres eliminar el documento generado "${filename}"?`)) return;

    try {
        const response = await fetch(`/delete/output/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        const result = await response.json();

        if (result.success) {
            showSuccessMessage(result.message);
            loadDocumentFiles(); // recarga la lista
        } else {
            showErrorMessage(result.error || 'Error eliminando documento');
        }
    } catch (error) {
        showErrorMessage(`Error eliminando documento: ${error.message}`);
    }
};

// Funciones de acción para documentos
window.analyzeTemplate = function(filename) {
    input.value = `analizar: ${filename}`;
    form.dispatchEvent(new Event('submit'));
};

window.createExampleData = function(filename) {
    input.value = `crear ejemplo datos: ${filename}`;
    form.dispatchEvent(new Event('submit'));
};

window.deleteTemplate = async function(filename) {
    if (!confirm(`¿Estás seguro de que quieres eliminar la plantilla "${filename}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/delete/template/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessMessage(result.message);
            loadDocumentFiles(); // Recargar lista
        } else {
            showErrorMessage(result.error || 'Error eliminando plantilla');
        }
    } catch (error) {
        showErrorMessage(`Error eliminando plantilla: ${error.message}`);
    }
};

window.deleteDataFile = async function(filename) {
    if (!confirm(`¿Estás seguro de que quieres eliminar el archivo de datos "${filename}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/delete/data/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessMessage(result.message);
            loadDocumentFiles(); // Recargar lista
        } else {
            showErrorMessage(result.error || 'Error eliminando archivo');
        }
    } catch (error) {
        showErrorMessage(`Error eliminando archivo: ${error.message}`);
    }
};

window.previewDataFile = function(filename) {
    input.value = `listar datos`;
    showInfoMessage(`Para ver el contenido de ${filename}, edítalo manualmente o recrea los datos de ejemplo.`);
};

// Funciones de subida de archivos
window.uploadTemplate = function() {
    const fileInput = document.getElementById('template-file-input');
    if (!fileInput.files.length) {
        showErrorMessage('Selecciona un archivo de plantilla');
        return;
    }
    
    const file = fileInput.files[0];
    const allowedExtensions = ['.docx', '.txt', '.pdf'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        showErrorMessage(`Formato no soportado. Use: ${allowedExtensions.join(', ')}`);
        return;
    }
    
    uploadFile('/upload/template', file, 'Subiendo plantilla...');
};

window.uploadDataFile = function() {
    const fileInput = document.getElementById('data-file-input');
    if (!fileInput.files.length) {
        showErrorMessage('Selecciona un archivo de datos');
        return;
    }
    
    const file = fileInput.files[0];
    const allowedExtensions = ['.json', '.csv', '.xlsx', '.txt'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        showErrorMessage(`Formato no soportado. Use: ${allowedExtensions.join(', ')}`);
        return;
    }
    
    uploadFile('/upload/data', file, 'Subiendo archivo de datos...');
};

// Función genérica para subir archivos
async function uploadFile(endpoint, file, loadingMessage) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showInfoMessage(loadingMessage);
        
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessMessage(result.message);
            if (result.next_step) {
                showInfoMessage(`💡 Siguiente paso: ${result.next_step}`);
            }
            loadDocumentFiles(); // Recargar lista
            
            // Limpiar input
            if (endpoint.includes('template')) {
                document.getElementById('template-file-input').value = '';
            } else {
                document.getElementById('data-file-input').value = '';
            }
        } else {
            showErrorMessage(result.error || 'Error subiendo archivo');
        }
    } catch (error) {
        showErrorMessage(`Error subiendo archivo: ${error.message}`);
    }
}

// Funciones de utilidad para la UI de documentos
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDate(timestamp) {
    return new Date(timestamp * 1000).toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Funciones para mostrar mensajes
function showSuccessMessage(message) {
    if (!historyDiv) return;
    const entry = document.createElement('div');
    entry.className = 'entry p-4 bg-green-100 dark:bg-green-800 rounded-lg shadow-md border-l-4 border-green-500';
    entry.innerHTML = `
        <div class="text-green-800 dark:text-green-200 font-bold">
            ✅ ${escapeHtml(message)}
        </div>
    `;
    historyDiv.prepend(entry);
    
    setTimeout(() => entry.remove(), 5000);
}

function showErrorMessage(message) {
    if (!historyDiv) return;
    const entry = document.createElement('div');
    entry.className = 'entry p-4 bg-red-100 dark:bg-red-800 rounded-lg shadow-md border-l-4 border-red-500';
    entry.innerHTML = `
        <div class="text-red-800 dark:text-red-200 font-bold">
            ❌ ${escapeHtml(message)}
        </div>
    `;
    historyDiv.prepend(entry);
}

function showInfoMessage(message) {
    if (!historyDiv) return;
    const entry = document.createElement('div');
    entry.className = 'entry p-4 bg-blue-100 dark:bg-blue-800 rounded-lg shadow-md border-l-4 border-blue-500';
    entry.innerHTML = `
        <div class="text-blue-800 dark:text-blue-200 font-bold">
            💡 ${escapeHtml(message)}
        </div>
    `;
    historyDiv.prepend(entry);
    
    setTimeout(() => entry.remove(), 7000);
}




// Funciones para comandos rápidos de documentos
window.showDocumentHelp = function() {
    input.value = 'document_filler help';
    form.dispatchEvent(new Event('submit'));
};

window.listTemplates = function() {
    input.value = 'listar plantillas';
    form.dispatchEvent(new Event('submit'));
};

window.listDataFiles = function() {
    input.value = 'listar datos';
    form.dispatchEvent(new Event('submit'));
};

// Función para crear un flujo completo de ejemplo
window.startDocumentWalkthrough = function() {
    const message = `
🚀 **TUTORIAL RÁPIDO - SISTEMA DE DOCUMENTOS**

1️⃣ **Sube una plantilla**
   • Archivo .docx con marcadores {{nombre}}, {{empresa}}
   • Botón "Subir Plantilla"

2️⃣ **Analiza la plantilla**
   • Comando: analizar: mi_plantilla.docx

3️⃣ **Crea datos de ejemplo**
   • Comando: crear ejemplo datos: mi_plantilla.docx

4️⃣ **Edita los datos**
   • Descarga el JSON generado
   • Edita con tus datos reales
   • Súbelo de nuevo

5️⃣ **Rellena el documento**
   • Comando: rellenar: mi_plantilla.docx con mis_datos.json

📄 ¡Empieza subiendo tu primera plantilla!
    `;
    
    showInfoMessage(message.trim());
};

// Inicializar al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('document-section')) {
        console.log('📄 Sistema de documentos inicializado');
    }
});

// Interceptar comandos de documentos en el envío del formulario
form.addEventListener('submit', async function(e) {
    const userInput = input.value.trim().toLowerCase();
    if (userInput.includes('rellenar:') || 
        userInput.includes('crear ejemplo datos:') || 
        userInput.includes('analizar:')) {
        setTimeout(() => loadDocumentFiles(), 2000);
    }
});

// Función para actualizar estadísticas de documentos
function updateDocumentStats() {
    const statsElement = document.getElementById('document-stats');
    if (statsElement && currentDocumentFiles) {
        const templatesCount = currentDocumentFiles.templates.length;
        const dataCount = currentDocumentFiles.data_files.length;
        const outputCount = currentDocumentFiles.output_files.length;
        statsElement.textContent = `Plantillas: ${templatesCount} | Datos: ${dataCount} | Generados: ${outputCount}`;
    }
}

// Extender updateDocumentFilesUI para actualizar estadísticas
const originalUpdateDocumentFilesUI = updateDocumentFilesUI;
updateDocumentFilesUI = function() {
    originalUpdateDocumentFilesUI();
    updateDocumentStats();
};

console.log('📄 Funciones de gestión de documentos cargadas');
