// ========== MÓDULO DE GUÍA Y AYUDA ==========

function initGuideSystem() {
    const guideKeywordsModal = document.getElementById("guide-keywords-modal");
    const guideButton = document.getElementById("guide-button");
    const closeGuideKeywordsButton = document.getElementById("close-guide-keywords-modal");

    if (!guideKeywordsModal || !guideButton || !closeGuideKeywordsButton) {
        console.warn('Elementos de guía no encontrados');
        return;
    }

    // Generar contenido de las pestañas
    generateTabContent();

    // Abrir modal
    guideButton.addEventListener("click", () => {
        guideKeywordsModal.classList.remove("hidden");
    });

    // Cerrar modal
    closeGuideKeywordsButton.addEventListener("click", () => {
        guideKeywordsModal.classList.add("hidden");
    });

    // Cerrar al hacer click fuera
    guideKeywordsModal.addEventListener("click", (e) => {
        if (e.target === guideKeywordsModal) {
            guideKeywordsModal.classList.add("hidden");
        }
    });

    // Inicializar sistema de tabs
    initTabSystem();
}

function generateTabContent() {
    const toolsTab = document.getElementById('tab-tools');
    const keywordsTab = document.getElementById('tab-keywords');

    if (toolsTab) {
        toolsTab.innerHTML = `
            <div class="space-y-6">
                <div class="bg-blue-50 dark:bg-blue-900 p-4 rounded-lg">
                    <h3 class="font-bold text-blue-800 dark:text-blue-200 mb-2">📝 Notas</h3>
                    <ul class="space-y-1 text-sm">
                        <li><code>guardar: tu nota</code> - Guardar una nota</li>
                        <li><code>leer</code> - Ver todas las notas</li>
                        <li><code>buscar: término</code> - Buscar en notas</li>
                        <li><code>borrar</code> - Eliminar todas las notas</li>
                    </ul>
                </div>

                <div class="bg-green-50 dark:bg-green-900 p-4 rounded-lg">
                    <h3 class="font-bold text-green-800 dark:text-green-200 mb-2">💻 Guardar Código</h3>
                    <ul class="space-y-1 text-sm">
                        <li><code>archivo.py||código</code> - Guardar código</li>
                        <li><code>generar: descripción</code> - Generar código con IA</li>
                    </ul>
                </div>

                <div class="bg-purple-50 dark:bg-purple-900 p-4 rounded-lg">
                    <h3 class="font-bold text-purple-800 dark:text-purple-200 mb-2">🔍 Búsqueda Web</h3>
                    <p class="text-sm">Escribe cualquier pregunta y el sistema buscará en la web automáticamente.</p>
                </div>

                <div class="bg-orange-50 dark:bg-orange-900 p-4 rounded-lg">
                    <h3 class="font-bold text-orange-800 dark:text-orange-200 mb-2">🧮 Calculadora</h3>
                    <p class="text-sm">Escribe operaciones matemáticas: <code>2 + 2 * 5</code></p>
                </div>

                <div class="bg-teal-50 dark:bg-teal-900 p-4 rounded-lg">
                    <h3 class="font-bold text-teal-800 dark:text-teal-200 mb-2">🧪 Espectros RMN</h3>
                    <ul class="space-y-1 text-sm">
                        <li><code>analizar: espectro.csv</code> - Analizar espectro</li>
                        <li><code>limpiar auto: espectro.csv</code> - Limpiar ruido</li>
                        <li><code>comparar: espectro.csv</code> - Comparar versiones</li>
                    </ul>
                </div>

                <div class="bg-yellow-50 dark:bg-yellow-900 p-4 rounded-lg">
                    <h3 class="font-bold text-yellow-800 dark:text-yellow-200 mb-2">📄 Documentos</h3>
                    <ul class="space-y-1 text-sm">
                        <li><code>analizar: plantilla.docx</code> - Analizar plantilla</li>
                        <li><code>crear ejemplo datos: plantilla.docx</code> - Crear datos</li>
                        <li><code>rellenar: plantilla.docx con datos.json</code> - Rellenar</li>
                    </ul>
                </div>

                <div class="bg-red-50 dark:bg-red-900 p-4 rounded-lg">
                    <h3 class="font-bold text-red-800 dark:text-red-200 mb-2">🔔 Notificaciones</h3>
                    <ul class="space-y-1 text-sm">
                        <li><code>status</code> - Ver estado</li>
                        <li><code>activar emails</code> - Activar notificaciones</li>
                        <li><code>keywords patentes: AI, robotics</code> - Configurar</li>
                    </ul>
                </div>

                <div class="bg-emerald-50 dark:bg-emerald-900 p-4 rounded-lg">
                    <h3 class="font-bold text-emerald-800 dark:text-emerald-200 mb-2">💶 Ayudas y Subvenciones</h3>
                    <ul class="space-y-1 text-sm">
                        <li><code>ayudas buscar</code> - Buscar ayudas</li>
                        <li><code>ayudas filtrar: tecnología</code> - Filtrar por tipo</li>
                        <li><code>ayudas activar</code> - Activar notificaciones</li>
                    </ul>
                </div>
            </div>
        `;
    }

    if (keywordsTab) {
        keywordsTab.innerHTML = `
            <div class="space-y-4">
                <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <h3 class="font-bold text-gray-800 dark:text-gray-200 mb-3">🔑 Palabras Clave del Sistema</h3>
                    
                    <div class="mb-4">
                        <h4 class="font-semibold text-blue-600 dark:text-blue-400 mb-2">📝 Notas:</h4>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-1 bg-blue-100 dark:bg-blue-800 rounded text-xs">guardar:</span>
                            <span class="px-2 py-1 bg-blue-100 dark:bg-blue-800 rounded text-xs">leer</span>
                            <span class="px-2 py-1 bg-blue-100 dark:bg-blue-800 rounded text-xs">borrar</span>
                            <span class="px-2 py-1 bg-blue-100 dark:bg-blue-800 rounded text-xs">buscar:</span>
                        </div>
                    </div>

                    <div class="mb-4">
                        <h4 class="font-semibold text-green-600 dark:text-green-400 mb-2">💻 Código:</h4>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-1 bg-green-100 dark:bg-green-800 rounded text-xs">||</span>
                            <span class="px-2 py-1 bg-green-100 dark:bg-green-800 rounded text-xs">generar:</span>
                            <span class="px-2 py-1 bg-green-100 dark:bg-green-800 rounded text-xs">crear</span>
                        </div>
                    </div>

                    <div class="mb-4">
                        <h4 class="font-semibold text-teal-600 dark:text-teal-400 mb-2">🧪 Espectros RMN:</h4>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-1 bg-teal-100 dark:bg-teal-800 rounded text-xs">analizar:</span>
                            <span class="px-2 py-1 bg-teal-100 dark:bg-teal-800 rounded text-xs">limpiar auto:</span>
                            <span class="px-2 py-1 bg-teal-100 dark:bg-teal-800 rounded text-xs">comparar:</span>
                            <span class="px-2 py-1 bg-teal-100 dark:bg-teal-800 rounded text-xs">exportar:</span>
                        </div>
                    </div>

                    <div class="mb-4">
                        <h4 class="font-semibold text-orange-600 dark:text-orange-400 mb-2">📄 Documentos:</h4>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-1 bg-orange-100 dark:bg-orange-800 rounded text-xs">rellenar:</span>
                            <span class="px-2 py-1 bg-orange-100 dark:bg-orange-800 rounded text-xs">crear ejemplo datos:</span>
                            <span class="px-2 py-1 bg-orange-100 dark:bg-orange-800 rounded text-xs">listar plantillas</span>
                        </div>
                    </div>

                    <div class="mb-4">
                        <h4 class="font-semibold text-red-600 dark:text-red-400 mb-2">🔔 Notificaciones:</h4>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-1 bg-red-100 dark:bg-red-800 rounded text-xs">status</span>
                            <span class="px-2 py-1 bg-red-100 dark:bg-red-800 rounded text-xs">activar</span>
                            <span class="px-2 py-1 bg-red-100 dark:bg-red-800 rounded text-xs">keywords</span>
                            <span class="px-2 py-1 bg-red-100 dark:bg-red-800 rounded text-xs">test</span>
                        </div>
                    </div>

                    <div class="mb-4">
                        <h4 class="font-semibold text-emerald-600 dark:text-emerald-400 mb-2">💶 Ayudas:</h4>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-1 bg-emerald-100 dark:bg-emerald-800 rounded text-xs">ayudas buscar</span>
                            <span class="px-2 py-1 bg-emerald-100 dark:bg-emerald-800 rounded text-xs">ayudas filtrar:</span>
                            <span class="px-2 py-1 bg-emerald-100 dark:bg-emerald-800 rounded text-xs">ayudas region:</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

function initTabSystem() {
    const tabButtons = document.querySelectorAll(".tab-button");

    if (tabButtons.length === 0) return;

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.dataset.tab;
            switchTab(targetTab);
        });
    });

    // Activar primera pestaña por defecto
    switchTab('tools');
}

function switchTab(targetTab) {
    const tabContents = document.querySelectorAll(".tab-content");
    const tabButtons = document.querySelectorAll(".tab-button");

    // Ocultar todos los contenidos
    tabContents.forEach(tc => tc.classList.add("hidden"));
    
    // Resetear estilos de botones
    tabButtons.forEach(b => {
        b.classList.remove("active", "bg-blue-100", "dark:bg-blue-700");
        b.classList.add("bg-gray-100", "dark:bg-gray-600");
    });
    
    // Mostrar contenido seleccionado
    const targetContent = document.getElementById("tab-" + targetTab);
    if (targetContent) {
        targetContent.classList.remove("hidden");
    }
    
    // Activar botón seleccionado
    const activeBtn = document.querySelector(`.tab-button[data-tab="${targetTab}"]`);
    if (activeBtn) {
        activeBtn.classList.remove("bg-gray-100", "dark:bg-gray-600");
        activeBtn.classList.add("active", "bg-blue-100", "dark:bg-blue-700");
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initGuideSystem();
    console.log('📘 Sistema de guía inicializado');
});

console.log('📘 Módulo de guía cargado');