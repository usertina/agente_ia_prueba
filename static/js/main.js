import { initFormHandler } from "/static/js/form-handler.js";


document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando aplicación...');

    // Inicializar formulario
    initFormHandler();

    // Cargar archivos si existe la función
    if (window.fetchFiles) window.fetchFiles();

    // Cleanup al cerrar
    window.addEventListener('beforeunload', () => { 
        if (window.notificationCheckInterval) clearInterval(window.notificationCheckInterval); 
    });

    console.log('✅ Script principal inicializado completamente');
});
// ========== INICIALIZACIÓN DE NOTAS ==========
// Agregar este código al archivo main.js

/**
 * Verifica el estado de las notas al cargar la página
 */
async function initializeNotesSection() {
    try {
        console.log('📝 Inicializando sección de notas...');
        
        // Verificar si existe el archivo de notas
        const response = await fetch('/check/notes');
        
        if (response.ok) {
            const data = await response.json();
            
            // Actualizar la interfaz con el estado actual
            if (window.updateNotesInfo) {
                window.updateNotesInfo(data.exists, data.count || 0);
                console.log(`✅ Notas cargadas: ${data.exists ? data.count + ' notas' : 'sin notas'}`);
            }
        } else if (response.status === 404) {
            // No hay archivo de notas
            if (window.updateNotesInfo) {
                window.updateNotesInfo(false, 0);
                console.log('📝 No hay notas guardadas');
            }
        } else {
            throw new Error(`Error del servidor: ${response.status}`);
        }
    } catch (error) {
        console.error('❌ Error cargando estado de notas:', error);
        
        // En caso de error, mostrar interfaz vacía
        const notesSection = document.getElementById('notes-section');
        if (notesSection) {
            notesSection.innerHTML = `
                <h3 class="font-semibold text-lg text-gray-700 dark:text-gray-300 mb-2">📝 Notas</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 italic text-center mb-2">
                    Error al cargar notas
                </p>
                <div class="space-y-2">
                    <button onclick="initializeNotesSection()" 
                            class="block w-full text-center p-2 bg-yellow-500 hover:bg-yellow-600 text-white font-semibold rounded-lg transition-colors">
                        🔄 Reintentar
                    </button>
                    <button onclick="createNewNote()" 
                            class="block w-full text-center p-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-lg transition-colors">
                        ➕ Crear nueva nota
                    </button>
                </div>
            `;
        }
    }
}

/**
 * Actualiza las notas después de guardar una nueva
 */
async function refreshNotesSection() {
    await initializeNotesSection();
}

// Hacer las funciones disponibles globalmente
window.initializeNotesSection = initializeNotesSection;
window.refreshNotesSection = refreshNotesSection;

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Esperar un momento para asegurar que todos los módulos estén cargados
        setTimeout(initializeNotesSection, 100);
    });
} else {
    // Si el DOM ya está cargado, inicializar después de un breve delay
    setTimeout(initializeNotesSection, 100);
}