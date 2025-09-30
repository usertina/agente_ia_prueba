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

/**
 * Alterna la visibilidad de la sección de ayudas
 */
window.toggleAyudasSection = function() {
    const section = document.getElementById('ayudas-section');
    const toggle = document.getElementById('ayudas-toggle');
    
    if (section.classList.contains('hidden')) {
        section.classList.remove('hidden');
        toggle.innerHTML = '💶 Ayudas y Subvenciones ▼';
        loadAyudasStats();
    } else {
        section.classList.add('hidden');
        toggle.innerHTML = '💶 Ayudas y Subvenciones ▶';
    }
};

/**
 * Busca ayudas actuales
 */
window.searchAyudas = function() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'ayudas buscar';
    form.dispatchEvent(new Event('submit'));
};

/**
 * Filtra ayudas por tipo
 */
window.filterAyudas = function(tipo) {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = `ayudas filtrar: ${tipo}`;
    form.dispatchEvent(new Event('submit'));
};

/**
 * Configura la región para las ayudas
 */
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

/**
 * Activa las notificaciones de ayudas
 */
window.activateAyudasNotifications = function() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'ayudas activar';
    form.dispatchEvent(new Event('submit'));
};

/**
 * Prueba el sistema de ayudas
 */
window.testAyudasSystem = function() {
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    input.value = 'ayudas test';
    form.dispatchEvent(new Event('submit'));
};

/**
 * Carga las estadísticas de ayudas
 */
async function loadAyudasStats() {
    const statsEl = document.getElementById('ayudas-stats');
    if (statsEl) {
        statsEl.textContent = 'Sistema de monitoreo activo - 5 fuentes configuradas';
    }
}

/**
 * Muestra notificación de ayuda en el navegador
 */
function showAyudaNotification(ayuda) {
    // Notificación del navegador
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification(ayuda.title, {
            body: ayuda.message,
            icon: '💶',
            tag: `ayuda_${ayuda.data.id}`,
            data: ayuda.data
        });
        
        notification.onclick = function() {
            window.open(ayuda.data.url, '_blank');
            notification.close();
        };
    }
    
    // Actualizar lista de ayudas en el panel
    updateAyudasList(ayuda);
}

/**
 * Actualiza la lista de ayudas en el panel
 */
function updateAyudasList(ayuda) {
    const listEl = document.getElementById('ayudas-list');
    if (!listEl) return;
    
    const ayudaEl = document.createElement('div');
    ayudaEl.className = 'p-2 bg-green-50 dark:bg-green-800 rounded text-xs cursor-pointer hover:bg-green-100 dark:hover:bg-green-700';
    ayudaEl.innerHTML = `
        <div class="font-semibold text-green-800 dark:text-green-200">${escapeHtml(ayuda.title)}</div>
        <div class="text-green-600 dark:text-green-300">${escapeHtml(ayuda.message)}</div>
        <div class="text-xs text-green-500 dark:text-green-400 mt-1">
            ${ayuda.data.fecha_limite ? `Límite: ${ayuda.data.fecha_limite}` : 'Sin fecha límite'}
        </div>
    `;
    ayudaEl.onclick = () => window.open(ayuda.data.url, '_blank');
    
    // Insertar al principio de la lista
    listEl.insertBefore(ayudaEl, listEl.firstChild);
    
    // Limitar a 10 elementos
    while (listEl.children.length > 10) {
        listEl.removeChild(listEl.lastChild);
    }
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

// Escuchar eventos de ayudas
window.addEventListener('ayudasNotification', function(event) {
    if (event.detail) {
        showAyudaNotification(event.detail);
    }
});

// Inicializar al cargar
document.addEventListener('DOMContentLoaded', function() {
    console.log('💶 Módulo de ayudas inicializado');
});

console.log('💶 Módulo de ayudas cargado');