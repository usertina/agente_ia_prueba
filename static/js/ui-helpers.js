// ========== FUNCIONES AUXILIARES DE UI ==========

/**
 * Escapa HTML para prevenir XSS
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
 * Crea un mensaje de entrada en el historial
 */
function createMessageEntry(type, icon, message) {
    const historyDiv = document.getElementById('history');
    if (!historyDiv) return;

    const entry = document.createElement('div');
    const colorClasses = {
        'success': 'bg-green-100 dark:bg-green-800 border-green-500 text-green-800 dark:text-green-200',
        'error': 'bg-red-100 dark:bg-red-800 border-red-500 text-red-800 dark:text-red-200',
        'info': 'bg-blue-100 dark:bg-blue-800 border-blue-500 text-blue-800 dark:text-blue-200'
    };

    entry.className = `entry p-4 rounded-lg shadow-md border-l-4 mb-4 ${colorClasses[type] || colorClasses['info']}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'font-bold';
    contentDiv.textContent = `${icon} ${message}`;
    
    entry.appendChild(contentDiv);
    historyDiv.prepend(entry);
    
    setTimeout(() => {
        if (entry.parentNode) {
            entry.remove();
        }
    }, 7000);
}

/**
 * Muestra mensaje de éxito
 */
window.showSuccessMessage = function(message) {
    createMessageEntry('success', '✅', message);
};

/**
 * Muestra mensaje de error
 */
window.showErrorMessage = function(message) {
    createMessageEntry('error', '❌', message);
};

/**
 * Muestra mensaje informativo
 */
window.showInfoMessage = function(message) {
    createMessageEntry('info', '💡', message);
};

/**
 * Muestra/oculta indicador de carga
 */
function showLoading(show) {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.classList.toggle('hidden', !show);
    }
}

/**
 * Formatea el tamaño de archivo
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * Formatea fecha desde timestamp
 */
function formatDate(timestamp) {
    return new Date(timestamp * 1000).toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Renderiza error en el historial
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

// Exportar funciones globales
window.escapeHtml = escapeHtml;
window.showLoading = showLoading;
window.formatFileSize = formatFileSize;
window.formatDate = formatDate;
window.renderError = renderError;

console.log('🎨 Módulo de UI helpers cargado');