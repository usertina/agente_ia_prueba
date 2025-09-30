// ========== MÓDULO DE AYUDAS Y SUBVENCIONES ==========

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
// ========== INICIALIZACIÓN DE LA SECCIÓN DE AYUDAS ==========

function initializeAyudasSection() {
    const ayudasSection = document.getElementById('ayudas-section');
    if (!ayudasSection) {
        console.error('❌ Sección Ayudas no encontrada');
        return;
    }

    ayudasSection.innerHTML = `
        <!-- Estadísticas de Ayudas -->
        <div id="ayudas-stats" class="p-3 bg-green-50 dark:bg-green-900 rounded-lg text-sm mb-3">
            <strong>📊 Estado Ayudas</strong><br>
            <span class="text-sm">Sistema de monitoreo activo - 5 fuentes configuradas</span>
        </div>

        <!-- Botones de acción -->
        <div class="space-y-2 mb-3">
            <button onclick="searchAyudas()" 
                    class="w-full text-left p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors text-sm">
                🔍 Buscar Ayudas
            </button>
            <button onclick="configureAyudasRegion()" 
                    class="w-full text-left p-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors text-sm">
                🗺️ Configurar Región
            </button>
            <button onclick="activateAyudasNotifications()" 
                    class="w-full text-left p-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors text-sm">
                🔔 Activar Notificaciones
            </button>
            <button onclick="testAyudasSystem()" 
                    class="w-full text-left p-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm">
                🧪 Probar Sistema
            </button>
        </div>

        <!-- Filtros rápidos -->
        <div class="mb-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2 text-sm">⚡ Filtros Rápidos</h4>
            <div class="grid grid-cols-2 gap-2">
                <button onclick="filterAyudas('tecnología')" 
                        class="p-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-xs">
                    💻 Tecnología
                </button>
                <button onclick="filterAyudas('innovación')" 
                        class="p-2 bg-purple-500 hover:bg-purple-600 text-white rounded text-xs">
                    💡 Innovación
                </button>
                <button onclick="filterAyudas('sostenibilidad')" 
                        class="p-2 bg-green-500 hover:bg-green-600 text-white rounded text-xs">
                    🌱 Sostenible
                </button>
                <button onclick="filterAyudas('empleo')" 
                        class="p-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded text-xs">
                    👔 Empleo
                </button>
            </div>
        </div>

        <!-- Lista de ayudas recientes -->
        <div id="ayudas-list" class="mb-3">
            <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2 text-sm">📋 Ayudas Recientes</h4>
            <div class="text-xs text-gray-500 dark:text-gray-400 italic text-center">
                Busca para ver ayudas disponibles
            </div>
        </div>
    `;

    console.log('✅ Sección Ayudas inicializada');
}

// ========== FUNCIONES DE TOGGLE Y ACCIONES ==========

window.toggleAyudasSection = function() {
    const section = document.getElementById('ayudas-section');
    const toggle = document.getElementById('ayudas-toggle');
    
    if (!section) {
        console.error('❌ Sección Ayudas no encontrada');
        return;
    }
    
    if (section.classList.contains('hidden')) {
        section.classList.remove('hidden');
        if (toggle) toggle.innerHTML = '💶 Ayudas y Subvenciones ▼';
    } else {
        section.classList.add('hidden');
        if (toggle) toggle.innerHTML = '💶 Ayudas y Subvenciones ▶';
    }
};

window.searchAyudas = function() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'ayudas buscar';
    form.dispatchEvent(new Event('submit'));
};

window.filterAyudas = function(tipo) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `ayudas filtrar: ${tipo}`;
    form.dispatchEvent(new Event('submit'));
};

window.configureAyudasRegion = function() {
    const regions = ['euskadi', 'gipuzkoa', 'bizkaia', 'araba', 'nacional', 'todas'];
    const region = prompt(`Selecciona tu región:\n${regions.join(', ')}`);
    
    if (region && regions.includes(region.toLowerCase())) {
        const input = document.getElementById('user_input');
        const form = document.getElementById('commandForm');
        input.value = `ayudas region: ${region}`;
        form.dispatchEvent(new Event('submit'));
    }
};

window.activateAyudasNotifications = function() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'ayudas activar';
    form.dispatchEvent(new Event('submit'));
};

window.testAyudasSystem = function() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'ayudas test';
    form.dispatchEvent(new Event('submit'));
};

// ========== INICIALIZACIÓN ==========

document.addEventListener('DOMContentLoaded', function() {
    initializeAyudasSection();
    console.log('💶 Módulo de ayudas inicializado');
});

console.log('💶 Módulo de ayudas cargado');