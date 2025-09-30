// ========== MÓDULO DE GESTIÓN DE NOTAS ==========

/**
 * Función auxiliar para escapar HTML (por si no está cargado ui-helpers)
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
 * Visualiza todas las notas guardadas
 */
window.viewAllNotes = async function() {
    try {
        const response = await fetch('/view/notes');
        if (response.ok) {
            const data = await response.json();
            showNotesModal(data.content, data.notes_count);
        } else {
            alert("No se pudieron cargar las notas");
        }
    } catch (error) {
        alert("Error al cargar las notas: " + error.message);
    }
};

/**
 * Muestra modal con todas las notas
 */
function showNotesModal(content, notesCount) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50';
    
    modal.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg max-w-4xl w-full max-h-[90vh] flex flex-col">
            <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200">📝 Todas las Notas (${notesCount})</h3>
                <button class="close-notes-modal text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-2xl">×</button>
            </div>
            <div class="flex-1 overflow-auto p-4">
                <pre class="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">${escapeHtml(content)}</pre>
            </div>
            <div class="flex justify-end space-x-2 p-4 border-t border-gray-200 dark:border-gray-700">
                <a href="/download/notes" download="mis_notas.txt" 
                   class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">
                    ⬇️ Descargar
                </a>
                <button class="close-notes-modal px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors">
                    Cerrar
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    modal.querySelectorAll('.close-notes-modal').forEach(btn => {
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
 * Crea una nueva nota
 */
window.createNewNote = function() {
    const noteText = prompt("Escribe tu nota:");
    if (noteText && noteText.trim()) {
        const input = document.getElementById('user_input');
        const form = document.getElementById('commandForm');
        input.value = `guardar: ${noteText.trim()}`;
        form.dispatchEvent(new Event('submit'));
    }
};

/**
 * Actualiza la información de notas en el panel lateral
 */
window.updateNotesInfo = function(notesExist, notesCount) {
    const notesSection = document.getElementById('notes-section');
    if (!notesSection) return;

    if (!notesExist || notesCount === 0) {
        notesSection.innerHTML = `
            <h3 class="font-semibold text-lg text-gray-700 dark:text-gray-300 mb-2">📝 Notas</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 italic text-center mb-2">No hay notas guardadas</p>
            <div class="space-y-2">
                <button onclick="createNewNote()" 
                        class="block w-full text-center p-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-lg transition-colors">
                    ➕ Crear primera nota
                </button>
            </div>
        `;
    } else {
        notesSection.innerHTML = `
            <h3 class="font-semibold text-lg text-gray-700 dark:text-gray-300 mb-2">📝 Notas (${notesCount})</h3>
            <div class="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg flex justify-between items-center">
                <span class="text-gray-800 dark:text-gray-100 text-sm">📝 Archivo de notas (${notesCount} notas)</span>
                <div class="flex space-x-1">
                    <button onclick="viewAllNotes()" class="text-gray-600 hover:text-blue-600 text-lg" title="Ver todas las notas">👁️</button>
                    <a href="/download/notes" download="mis_notas.txt" class="text-gray-600 hover:text-green-600 text-lg" title="Descargar notas">⬇️</a>
                </div>
            </div>
            <button onclick="createNewNote()" 
                    class="mt-2 w-full text-center p-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-lg transition-colors">
                ➕ Crear nueva nota
            </button>
        `;
    }
};

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

console.log('📝 Módulo de notas cargado');