// ====================== NOTIFICACIONES CON HISTORIAL ======================

// Variables globales
window.userId = null;
window.notificationHistory = [];
window.unreadCount = 0;

// Solicita permisos de notificación
async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        console.warn('⚠️ Este navegador no soporta notificaciones');
        showNotificationWarning('Tu navegador no soporta notificaciones del sistema');
        return false;
    }

    if (Notification.permission === 'granted') {
        console.log('✅ Permisos de notificación ya concedidos');
        return true;
    }

    if (Notification.permission === 'denied') {
        console.warn('❌ Permisos de notificación denegados previamente');
        showNotificationWarning('Has bloqueado las notificaciones. Actívalas en la configuración del navegador.');
        return false;
    }

    try {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            console.log('✅ Permisos de notificación concedidos');
            showSuccessMessage('Notificaciones activadas correctamente');
            return true;
        } else {
            console.warn('⚠️ Permisos de notificación denegados');
            showNotificationWarning('Has rechazado los permisos de notificación');
            return false;
        }
    } catch (error) {
        console.error('❌ Error solicitando permisos:', error);
        return false;
    }
}

// Muestra aviso de notificaciones bloqueadas
function showNotificationWarning(message) {
    const warning = document.createElement('div');
    warning.className = 'fixed top-4 right-4 bg-yellow-100 dark:bg-yellow-900 border-l-4 border-yellow-500 p-4 rounded-lg shadow-lg z-50 max-w-md';
    warning.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
            </div>
            <div class="ml-3 flex-1">
                <h3 class="text-sm font-bold text-yellow-800 dark:text-yellow-200">
                    Notificaciones
                </h3>
                <p class="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                    ${message}
                </p>
                <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                        class="mt-2 text-xs text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-200 underline">
                    Cerrar
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(warning);
    
    setTimeout(() => {
        if (warning.parentElement) warning.remove();
    }, 10000);
}

// Iconos para diferentes tipos de notificación
function getNotificationIcon(type) {
    const icons = { 
        'emails': '📧',
        'email': '📧', 
        'patents': '🔬',
        'patent': '🔬', 
        'papers': '📚',
        'paper': '📚', 
        'ayudas': '💶', 
        'test': '🧪' 
    };
    return icons[type] || '🔔';
}

// Actualiza estado en el panel
function updateNotificationStatus(userId = null) {
    console.log('🔄 Actualizando estado de notificaciones...', { userId });
    
    const statusEl = document.getElementById('notification-status');
    const swStatusEl = document.getElementById('service-worker-status');
    
    if (!statusEl) {
        console.warn('⚠️ Elemento notification-status no encontrado');
        return;
    }
    
    if (userId) {
        const permission = Notification.permission === 'granted' ? '✅' : 
                          Notification.permission === 'denied' ? '❌' : '⚠️';
        
        // CAMBIO: Mostrar ID completo truncado más claramente
        statusEl.innerHTML = `
            <strong>🆔 Usuario:</strong> ${userId.substring(0, 12)}...<br>
            <span class="text-xs">Permisos: ${permission} ${Notification.permission}</span>
        `;
        
        console.log('✅ Estado actualizado:', { 
            userId: userId.substring(0, 12), 
            permission: Notification.permission 
        });
    } else {
        statusEl.innerHTML = `
            <strong>Estado:</strong> ⏳ Iniciando...<br>
            <span class="text-xs">Esperando registro...</span>
        `;
    }
    
    // Actualizar estado del Service Worker
    if (swStatusEl) {
        if ('serviceWorker' in navigator) {
            if (navigator.serviceWorker.controller) {
                swStatusEl.textContent = 'Service Worker: ✅ Activo';
            } else {
                swStatusEl.textContent = 'Service Worker: ⏳ Registrando...';
            }
        } else {
            swStatusEl.textContent = 'Service Worker: ❌ No soportado';
        }
    }
    
    // Actualizar contador de notificaciones
    updateNotificationBadge();
}

// Actualiza el contador de notificaciones no leídas
function updateNotificationBadge() {
    const badge = document.getElementById('notification-badge');
    if (badge) {
        if (window.unreadCount > 0) {
            badge.textContent = window.unreadCount;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }
}

async function initializeNotificationSystem() {
    console.log('🔔 Inicializando sistema de notificaciones...');
    
    try {
        // 1. Actualizar UI inicial
        updateNotificationStatus();
        
        // 2. Registrar Service Worker
        if (window.registerServiceWorker) {
            console.log('📝 Registrando Service Worker...');
            await window.registerServiceWorker();
        }

        // 3. Registrar usuario en el backend
        console.log('👤 Registrando usuario...');
        const response = await fetch('/notifications/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_name: `Web-${navigator.userAgent.substring(0, 20)}...`,
                device_id: `web_${Date.now()}`
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error('Fallo en registro de usuario');
        }

        // 4. Guardar user_id globalmente
        window.userId = data.user_id;
        console.log(`✅ Usuario registrado: ${window.userId.substring(0, 12)}...`);
        
        // 5. FORZAR actualización de UI INMEDIATAMENTE con userId
        updateNotificationStatus(window.userId);
        
        // 6. Cargar historial de notificaciones
        await loadNotificationHistory();
        
        // 7. Solicitar permisos de notificación
        console.log('🔔 Solicitando permisos de notificación...');
        const hasPermission = await requestNotificationPermission();
        
        // 8. Actualizar UI después de permisos
        updateNotificationStatus(window.userId);
        
        if (hasPermission) {
            console.log('✅ Permisos concedidos');
        }

        // 9. Iniciar polling en Service Worker
        if (window.startServiceWorkerPolling && window.userId) {
            console.log('🔄 Iniciando polling en Service Worker...');
            await window.startServiceWorkerPolling(window.userId);
        }

        // 10. Iniciar polling de respaldo en el cliente
        if (window.userId) {
            console.log('🔄 Iniciando polling de respaldo en cliente...');
            startNotificationPolling();
        }

        // 11. Actualizaciones finales múltiples para asegurar
        setTimeout(() => updateNotificationStatus(window.userId), 500);
        setTimeout(() => updateNotificationStatus(window.userId), 1500);
        
        console.log('✅ Sistema de notificaciones inicializado completamente');

    } catch (error) {
        console.error("❌ Error inicializando notificaciones:", error);
        updateNotificationStatus();  // Mostrar error
        
        // Reintentar después de 5 segundos
        console.log('🔄 Reintentando en 5 segundos...');
        setTimeout(initializeNotificationSystem, 5000);
    }
}

// Carga el historial de notificaciones desde el backend
async function loadNotificationHistory() {
    if (!window.userId) {
        console.log('⏳ Esperando userId para cargar historial...');
        return;
    }
    
    try {
        const response = await fetch(`/notifications/user/${window.userId}/history`);
        
        if (response.ok) {
            const data = await response.json();
            window.notificationHistory = data.notifications || [];
            window.unreadCount = data.unread_count || 0;
            
            console.log(`📚 Historial cargado: ${window.notificationHistory.length} notificaciones, ${window.unreadCount} no leídas`);
            
            // Actualizar UI
            renderNotificationHistory();
            updateNotificationBadge();
        }
    } catch (error) {
        console.error('❌ Error cargando historial:', error);
    }
}

// Renderiza el historial de notificaciones
function renderNotificationHistory(filter = 'all') {
    const historyContainer = document.getElementById('notification-history');
    if (!historyContainer) {
        console.warn('⚠️ Contenedor de historial no encontrado');
        return;
    }
    
    let notifications = window.notificationHistory;
    
    // Aplicar filtro
    if (filter !== 'all') {
        notifications = notifications.filter(n => n.type === filter);
    }
    
    if (notifications.length === 0) {
        historyContainer.innerHTML = `
            <div class="text-center p-8 text-gray-500 dark:text-gray-400">
                <p class="text-lg">📭</p>
                <p class="mt-2">No hay notificaciones</p>
            </div>
        `;
        return;
    }
    
    historyContainer.innerHTML = notifications.map(notif => {
        const icon = getNotificationIcon(notif.type);
        const isUnread = !notif.read;
        const date = new Date(notif.created_at);
        const timeAgo = getTimeAgo(date);
        
        return `
            <div class="notification-item ${isUnread ? 'unread' : ''} p-3 mb-2 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                isUnread 
                    ? 'bg-blue-50 dark:bg-blue-900 border-blue-200 dark:border-blue-700' 
                    : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
            }" 
            onclick="openNotification(${notif.id})" 
            data-notification-id="${notif.id}">
                <div class="flex items-start">
                    <div class="flex-shrink-0 text-2xl mr-3">
                        ${icon}
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center justify-between">
                            <h4 class="font-semibold text-sm text-gray-900 dark:text-gray-100 truncate">
                                ${escapeHtml(notif.title)}
                            </h4>
                            ${isUnread ? '<span class="ml-2 w-2 h-2 bg-blue-500 rounded-full"></span>' : ''}
                        </div>
                        <p class="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                            ${escapeHtml(notif.message)}
                        </p>
                        <div class="flex items-center justify-between mt-2">
                            <span class="text-xs text-gray-500 dark:text-gray-500">${timeAgo}</span>
                            <span class="text-xs px-2 py-1 rounded ${getTypeColor(notif.type)}">
                                ${notif.type}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Abre una notificación (marca como leída y abre URL si existe)
async function openNotification(notificationId) {
    const notif = window.notificationHistory.find(n => n.id === notificationId);
    if (!notif) {
        console.warn('⚠️ Notificación no encontrada:', notificationId);
        return;
    }
    
    console.log('📬 Abriendo notificación:', notif);
    
    // Marcar como leída si no lo está
    if (!notif.read) {
        await markNotificationAsRead(notificationId);
    }
    
    // Mostrar modal con detalles
    showNotificationModal(notif);
    
    // Si tiene URL, ofrecerla para abrir
    if (notif.data && notif.data.url) {
        // La URL se manejará en el modal
    }
}

// Marca una notificación como leída
async function markNotificationAsRead(notificationId) {
    try {
        const response = await fetch(`/notifications/mark-read/${notificationId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: window.userId })
        });
        
        if (response.ok) {
            // Actualizar en el historial local
            const notif = window.notificationHistory.find(n => n.id === notificationId);
            if (notif) {
                notif.read = true;
                window.unreadCount = Math.max(0, window.unreadCount - 1);
                
                // Actualizar UI
                renderNotificationHistory();
                updateNotificationBadge();
            }
        }
    } catch (error) {
        console.error('❌ Error marcando como leída:', error);
    }
}

// Muestra modal con detalles de la notificación
function showNotificationModal(notif) {
    const icon = getNotificationIcon(notif.type);
    const date = new Date(notif.created_at);
    const formattedDate = date.toLocaleString('es-ES');
    
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50';
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
    
    const hasUrl = notif.data && notif.data.url;
    
    modal.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-hidden">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
                <div class="flex items-start">
                    <div class="text-4xl mr-4">${icon}</div>
                    <div class="flex-1">
                        <h3 class="text-xl font-bold text-gray-900 dark:text-gray-100">
                            ${escapeHtml(notif.title)}
                        </h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">${formattedDate}</p>
                    </div>
                    <button onclick="this.closest('.fixed').remove()" 
                            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
            </div>
            
            <div class="p-6 overflow-y-auto max-h-96">
                <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">${escapeHtml(notif.message)}</p>
                
                ${notif.data && Object.keys(notif.data).length > 0 ? `
                    <div class="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">📋 Información adicional:</h4>
                        <div class="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                            ${Object.entries(notif.data).map(([key, value]) => `
                                <div><span class="font-medium">${escapeHtml(key)}:</span> ${escapeHtml(String(value))}</div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
            
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex gap-3">
                ${hasUrl ? `
                    <button onclick="window.open('${escapeHtml(notif.data.url)}', '_blank'); this.closest('.fixed').remove();" 
                            class="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
                        🔗 Abrir enlace
                    </button>
                ` : ''}
                <button onclick="this.closest('.fixed').remove()" 
                        class="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg font-medium transition-colors">
                    Cerrar
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Función de polling en el cliente
function startNotificationPolling() {
    if (window.notificationCheckInterval) {
        clearInterval(window.notificationCheckInterval);
    }
    
    console.log('🔄 Iniciando polling de notificaciones en cliente');
    
    checkNotifications();
    window.notificationCheckInterval = setInterval(checkNotifications, 2 * 60 * 1000);
}

// Función para verificar notificaciones
async function checkNotifications() {
    if (!window.userId) {
        console.log('⏳ Esperando userId...');
        return;
    }
    
    try {
        const response = await fetch(`/notifications/user/${window.userId}`);
        
        if (!response.ok) {
            console.warn(`⚠️ Error al verificar notificaciones: ${response.status}`);
            return;
        }
        
        const data = await response.json();
        
        if (data.notifications && data.notifications.length > 0) {
            console.log(`📬 ${data.notifications.length} nuevas notificaciones`);
            
            // Agregar al historial
            for (const notif of data.notifications) {
                addNotificationToHistory(notif);
                showBrowserNotification(notif);
            }
            
            // Actualizar UI
            updateNotificationStatus(window.userId);
            renderNotificationHistory();
        }
    } catch (error) {
        console.error('❌ Error verificando notificaciones:', error);
    }
}

// Agrega una notificación al historial local
function addNotificationToHistory(notif) {
    // Evitar duplicados
    if (window.notificationHistory.find(n => n.id === notif.id)) {
        return;
    }
    
    // Agregar al inicio del array
    window.notificationHistory.unshift({
        ...notif,
        read: false,
        created_at: notif.created_at || new Date().toISOString()
    });
    
    window.unreadCount++;
    
    // Limitar a 100 notificaciones en el historial local
    if (window.notificationHistory.length > 100) {
        window.notificationHistory = window.notificationHistory.slice(0, 100);
    }
}

// Muestra notificación del navegador
function showBrowserNotification(notif) {
    if (Notification.permission !== 'granted') {
        console.log('⚠️ Sin permisos para mostrar notificaciones');
        return;
    }
    
    try {
        const icon = getNotificationIcon(notif.type);
        const notification = new Notification(`${icon} ${notif.title}`, {
            body: notif.message,
            icon: '/static/favicon.ico',
            badge: '/static/favicon.ico',
            tag: `${notif.type}_${notif.id}`,
            requireInteraction: false,
            silent: false,
            data: notif.data
        });
        
        notification.onclick = function(event) {
            event.preventDefault();
            window.focus();
            
            // Abrir la notificación en el modal
            openNotification(notif.id);
            
            notification.close();
        };
        
        setTimeout(() => {
            notification.close();
        }, 10000);
        
    } catch (error) {
        console.error('❌ Error mostrando notificación:', error);
    }
}

// Filtrar notificaciones por tipo
function filterNotifications(type) {
    console.log('🔍 Filtrando por:', type);
    renderNotificationHistory(type);
    
    // Actualizar botones activos
    document.querySelectorAll('.filter-button').forEach(btn => {
        btn.classList.remove('active', 'bg-blue-600', 'text-white');
        btn.classList.add('bg-gray-200', 'dark:bg-gray-700');
    });
    
    const activeBtn = document.querySelector(`.filter-button[data-filter="${type}"]`);
    if (activeBtn) {
        activeBtn.classList.remove('bg-gray-200', 'dark:bg-gray-700');
        activeBtn.classList.add('active', 'bg-blue-600', 'text-white');
    }
}

// Marcar todas como leídas
async function markAllAsRead() {
    if (!confirm('¿Marcar todas las notificaciones como leídas?')) {
        return;
    }
    
    try {
        const response = await fetch('/notifications/mark-all-read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: window.userId })
        });
        
        if (response.ok) {
            // Actualizar historial local
            window.notificationHistory.forEach(n => n.read = true);
            window.unreadCount = 0;
            
            // Actualizar UI
            renderNotificationHistory();
            updateNotificationBadge();
            
            showSuccessMessage('✅ Todas las notificaciones marcadas como leídas');
        }
    } catch (error) {
        console.error('❌ Error:', error);
    }
}

// Limpiar historial
async function clearNotificationHistory() {
    if (!confirm('¿Eliminar todo el historial de notificaciones?')) {
        return;
    }
    
    try {
        const response = await fetch('/notifications/clear-history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: window.userId })
        });
        
        if (response.ok) {
            window.notificationHistory = [];
            window.unreadCount = 0;
            
            renderNotificationHistory();
            updateNotificationBadge();
            
            showSuccessMessage('✅ Historial eliminado');
        }
    } catch (error) {
        console.error('❌ Error:', error);
    }
}

// Utilidades
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return unsafe;
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'Hace un momento';
    if (seconds < 3600) return `Hace ${Math.floor(seconds / 60)} min`;
    if (seconds < 86400) return `Hace ${Math.floor(seconds / 3600)} h`;
    if (seconds < 604800) return `Hace ${Math.floor(seconds / 86400)} días`;
    
    return date.toLocaleDateString('es-ES');
}

function getTypeColor(type) {
    const colors = {
        'papers': 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
        'patents': 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200',
        'emails': 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
        'ayudas': 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
        'test': 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
    };
    return colors[type] || colors['test'];
}

// Funciones de prueba/debug
function debugNotifications() {
    console.log('🔧 Debug de notificaciones activado');
    console.log('='.repeat(50));
    console.log('User ID:', window.userId);
    console.log('Notification permission:', Notification.permission);
    console.log('Service Worker:', navigator.serviceWorker.controller ? 'Activo' : 'Inactivo');
    console.log('Polling interval:', window.notificationCheckInterval ? 'Activo' : 'Inactivo');
    console.log('Historial:', window.notificationHistory.length, 'notificaciones');
    console.log('No leídas:', window.unreadCount);
    console.log('='.repeat(50));
    
    const message = `
📊 DEBUG INFO:
- User ID: ${window.userId ? window.userId.substring(0, 12) + '...' : 'No registrado'}
- Permisos: ${Notification.permission}
- Service Worker: ${navigator.serviceWorker.controller ? 'Activo' : 'Inactivo'}
- Polling: ${window.notificationCheckInterval ? 'Activo' : 'Inactivo'}
- Historial: ${window.notificationHistory.length} notificaciones
- No leídas: ${window.unreadCount}
    `;
    
    alert(message);
}

async function testNotifications() {
    console.log('🧪 Probando sistema de notificaciones...');
    
    if (!window.userId) {
        alert('❌ Error: Usuario no registrado. Espera un momento e intenta de nuevo.');
        return;
    }
    
    try {
        const response = await fetch(`/notifications/user/${window.userId}/test`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Notificación de prueba enviada');
            alert('✅ Notificación de prueba enviada. Deberías recibirla en unos segundos.');
            
            setTimeout(checkNotifications, 2000);
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('❌ Error enviando notificación de prueba:', error);
        alert(`❌ Error: ${error.message}`);
    }
}

function configureNotifications() {
    console.log('⚙️ Abriendo configuración de notificaciones...');
    
    if (!window.userId) {
        alert('❌ Error: Usuario no registrado. Espera un momento e intenta de nuevo.');
        return;
    }
    
    const input = document.getElementById('user_input');
    const form = document.getElementById('commandForm');
    
    if (input && form) {
        input.value = 'status';
        form.dispatchEvent(new Event('submit'));
    } else {
        alert('⚙️ Usa el comando "status" para ver tu configuración actual');
    }
}

// ===== Exportar funciones globales para HTML =====
window.requestNotificationPermission = requestNotificationPermission;
window.initializeNotificationSystem = initializeNotificationSystem;
window.debugNotifications = debugNotifications;
window.testNotifications = testNotifications;
window.configureNotifications = configureNotifications;
window.updateNotificationStatus = updateNotificationStatus;
window.getNotificationIcon = getNotificationIcon;
window.showNotificationWarning = showNotificationWarning;
window.checkNotifications = checkNotifications;
window.startNotificationPolling = startNotificationPolling;
window.showBrowserNotification = showBrowserNotification;
window.loadNotificationHistory = loadNotificationHistory;
window.renderNotificationHistory = renderNotificationHistory;
window.openNotification = openNotification;
window.markNotificationAsRead = markNotificationAsRead;
window.filterNotifications = filterNotifications;
window.markAllAsRead = markAllAsRead;
window.clearNotificationHistory = clearNotificationHistory;

// ===== Auto-inicializar cuando cargue el DOM =====
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🔔 DOM cargado, inicializando notificaciones en 1 segundo...');
        setTimeout(initializeNotificationSystem, 1000);
    });
} else {
    console.log('🔔 DOM ya cargado, inicializando notificaciones en 1 segundo...');
    setTimeout(initializeNotificationSystem, 1000);
}

console.log('🔔 Módulo de notificaciones cargado');