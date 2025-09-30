// ========== MÓDULO DE GESTIÓN DE ARCHIVOS ==========

const CODE_DIR = "code";
const NOTES_DIR = "notes";

/**
 * Función auxiliar para escapar HTML
 */
function escapeHtml(str) {
    if (typeof str !== 'string') return str;
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Obtiene la lista de archivos guardados
 */
async function fetchFiles() {
    try {
        const response = await fetch('/files');
        const data = await response.json();
        updateCodeFiles(data.code_files || []);
        window.updateNotesInfo(data.notes_exist || false, data.notes_count || 0);
    } catch (error) {
        console.error("❌ Error al cargar archivos:", error);
    }
}

/**
 * Actualiza la lista de archivos de código en el panel
 */
function updateCodeFiles(files) {
    const codeFilesList = document.getElementById('code-files-list');
    if (!codeFilesList) return;
    
    codeFilesList.innerHTML = '';

    if (files.length === 0) {
        codeFilesList.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400 italic text-center">No hay código guardado.</p>';
        return;
    }

    files.forEach(file => {
        const item = document.createElement('div');
        item.className = "flex justify-between items-center p-2 bg-gray-100 dark:bg-gray-700 rounded-lg mb-2";

        const name = document.createElement('span');
        name.textContent = file;
        name.className = "text-gray-800 dark:text-gray-100 text-sm truncate cursor-pointer hover:text-blue-600";
        name.title = "Click para ver contenido";
        name.addEventListener('click', () => viewFileContent(file));

        const actions = document.createElement('div');
        actions.className = "flex space-x-1";

        const viewBtn = document.createElement('button');
        viewBtn.innerHTML = '👁️';
        viewBtn.className = "text-gray-600 hover:text-blue-600 text-lg";
        viewBtn.title = "Ver contenido";
        viewBtn.addEventListener('click', () => viewFileContent(file));

        const downloadBtn = document.createElement('a');
        downloadBtn.href = `/download/code/${file}`;
        downloadBtn.innerHTML = '⬇️';
        downloadBtn.className = "text-gray-600 hover:text-green-600 text-lg";
        downloadBtn.title = "Descargar archivo";
        downloadBtn.setAttribute('download', file);

        actions.appendChild(viewBtn);
        actions.appendChild(downloadBtn);

        item.appendChild(name);
        item.appendChild(actions);
        codeFilesList.appendChild(item);
    });
}

/**
 * Visualiza el contenido de un archivo de código
 */
async function viewFileContent(filename) {
    try {
        const response = await fetch(`/view/code/${filename}`);
        if (response.ok) {
            const data = await response.json();
            showFileModal(data.filename, data.content);
        } else {
            renderError(`No se pudo cargar el archivo ${filename}`);
        }
    } catch (error) {
        renderError(`Error al cargar el archivo: ${error.message}`);
    }
}

/**
 * Muestra modal con el contenido del archivo
 */
function showFileModal(filename, content) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50';

    modal.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg max-w-4xl w-full max-h-[90vh] flex flex-col">
            <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200">📄 ${escapeHtml(filename)}</h3>
                <button class="close-file-modal text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-2xl">×</button>
            </div>
            <div class="flex-1 overflow-auto p-4">
                <pre class="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto"><code>${escapeHtml(content)}</code></pre>
            </div>
            <div class="flex justify-end space-x-2 p-4 border-t border-gray-200 dark:border-gray-700">
                <a href="/download/code/${encodeURIComponent(filename)}" download="${escapeHtml(filename)}" 
                   class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">
                    ⬇️ Descargar
                </a>
                <button class="close-file-modal px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors">
                    Cerrar
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    modal.querySelectorAll('.close-file-modal').forEach(btn => {
        btn.addEventListener('click', () => {
            document.body.removeChild(modal);
        });
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

/**
 * Función auxiliar para escapar HTML
 */
function escapeHtml(str) {
    if (typeof str !== 'string') return str;
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Renderiza un error en el historial
 */
function renderError(message) {
    const historyDiv = document.getElementById('history');
    if (!historyDiv) return;
    
    const entry = document.createElement('div');
    entry.className = 'entry p-4 bg-red-100 dark:bg-red-800 rounded-lg shadow-md';
    entry.innerHTML = `
        <div class="text-red-800 dark:text-red-200 font-bold">
            ❌ Error: ${escapeHtml(message)}
        </div>
    `;
    historyDiv.prepend(entry);
}

// Exportar funciones para uso global
window.fetchFiles = fetchFiles;
window.viewFileContent = viewFileContent;

console.log('📁 Módulo de archivos cargado');