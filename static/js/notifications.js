// ====================== NOTIFICACIONES ======================

// Variable global para almacenar el user_id
window.userId = null;

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
    const statusEl = document.getElementById('notification-status');
    if (!statusEl) return;
    
    if (userId) {
        const permission = Notification.permission === 'granted' ? '✅' : '⚠️';
        statusEl.innerHTML = `${permission} Usuario: ${userId.substring(0, 8)}...<br>`;
        statusEl.innerHTML += `<span class="text-xs">Permisos: ${Notification.permission}</span>`;
    } else {
        statusEl.textContent = 'Estado: ⏳ Iniciando...';
    }
    
    // Actualizar estado del Service Worker
    const swStatusEl = document.getElementById('service-worker-status');
    if (swStatusEl && 'serviceWorker' in navigator) {
        if (navigator.serviceWorker.controller) {
            swStatusEl.textContent = 'Service Worker: ✅ Activo';
        } else {
            swStatusEl.textContent = 'Service Worker: ⏳ Registrando...';
        }
    }
}

// Inicializa el sistema de notificaciones
async function initializeNotificationSystem() {
    console.log('🔔 Inicializando sistema de notificaciones...');
    
    try {
        // 1. Registrar Service Worker
        if (window.registerServiceWorker) {
            console.log('📝 Registrando Service Worker...');
            await window.registerServiceWorker();
        } else {
            console.warn('⚠️ registerServiceWorker no disponible');
        }

        // 2. Registrar usuario en el backend
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

        // 3. Guardar user_id globalmente
        window.userId = data.user_id;
        console.log(`✅ Usuario registrado: ${window.userId.substring(0, 12)}...`);
        
        // 4. Actualizar UI con user_id
        updateNotificationStatus(window.userId);

        // 5. Solicitar permisos de notificación
        console.log('🔔 Solicitando permisos de notificación...');
        const hasPermission = await requestNotificationPermission();
        
        if (hasPermission) {
            console.log('✅ Permisos concedidos');
        } else {
            console.warn('⚠️ Permisos no concedidos, pero el sistema seguirá funcionando');
        }

        // 6. Iniciar polling en Service Worker (si está disponible)
        if (window.startServiceWorkerPolling && window.userId) {
            console.log('🔄 Iniciando polling en Service Worker...');
            await window.startServiceWorkerPolling(window.userId);
        }

        // 7. Iniciar polling de respaldo en el cliente
        if (window.userId) {
            console.log('🔄 Iniciando polling de respaldo en cliente...');
            startNotificationPolling();
        }

        // 8. Actualizar estado final
        updateNotificationStatus(window.userId);
        
        console.log('✅ Sistema de notificaciones inicializado completamente');

    } catch (error) {
        console.error("❌ Error inicializando notificaciones:", error);
        updateNotificationStatus();
        
        // Reintentar después de 5 segundos
        console.log('🔄 Reintentando en 5 segundos...');
        setTimeout(initializeNotificationSystem, 5000);
    }
}

// Función de polling en el cliente (respaldo si SW falla)
function startNotificationPolling() {
    // Limpiar interval anterior si existe
    if (window.notificationCheckInterval) {
        clearInterval(window.notificationCheckInterval);
    }
    
    console.log('🔄 Iniciando polling de notificaciones en cliente');
    
    // Verificar inmediatamente
    checkNotifications();
    
    // Verificar cada 2 minutos
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
            
            // Mostrar notificaciones del navegador
            for (const notif of data.notifications) {
                showBrowserNotification(notif);
            }
            
            // Actualizar UI
            if (window.updateNotificationStatus) {
                window.updateNotificationStatus(window.userId);
            }
            
            // Mostrar alerta visual en la página
            showNotificationBadge(data.notifications.length);
        }
    } catch (error) {
        console.error('❌ Error verificando notificaciones:', error);
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
        
        // Click en la notificación
        notification.onclick = function(event) {
            event.preventDefault();
            window.focus();
            
            // Si hay URL en los datos, abrirla
            if (notif.data && notif.data.url) {
                window.open(notif.data.url, '_blank');
            }
            
            notification.close();
        };
        
        // Auto-cerrar después de 10 segundos
        setTimeout(() => {
            notification.close();
        }, 10000);
        
    } catch (error) {
        console.error('❌ Error mostrando notificación:', error);
    }
}

// Muestra badge de notificaciones en la UI
function showNotificationBadge(count) {
    const statusEl = document.getElementById('notification-status');
    if (!statusEl) return;
    
    // Crear badge temporal
    const badge = document.createElement('span');
    badge.className = 'inline-block ml-2 px-2 py-1 bg-red-500 text-white text-xs rounded-full animate-pulse';
    badge.textContent = `${count} nueva${count > 1 ? 's' : ''}`;
    
    statusEl.appendChild(badge);
    
    // Quitar badge después de 5 segundos
    setTimeout(() => {
        if (badge.parentElement) {
            badge.remove();
        }
    }, 5000);
}

// Funciones de prueba/debug
function debugNotifications() {
    console.log('🔧 Debug de notificaciones activado');
    console.log('=' * 50);
    console.log('User ID:', window.userId);
    console.log('Notification permission:', Notification.permission);
    console.log('Service Worker:', navigator.serviceWorker.controller ? 'Activo' : 'Inactivo');
    console.log('Polling interval:', window.notificationCheckInterval ? 'Activo' : 'Inactivo');
    console.log('=' * 50);
    
    // Mostrar en UI también
    const message = `
📊 DEBUG INFO:
- User ID: ${window.userId ? window.userId.substring(0, 12) + '...' : 'No registrado'}
- Permisos: ${Notification.permission}
- Service Worker: ${navigator.serviceWorker.controller ? 'Activo' : 'Inactivo'}
- Polling: ${window.notificationCheckInterval ? 'Activo' : 'Inactivo'}
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
            
            // Forzar verificación inmediata
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
    
    // Ejecutar comando de status
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