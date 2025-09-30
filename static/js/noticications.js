// ====================== NOTIFICACIONES ======================

export async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        console.warn('⚠️ Este navegador no soporta notificaciones');
        return false;
    }

    if (Notification.permission === 'granted') {
        console.log('✅ Permisos de notificación ya concedidos');
        return true;
    }

    if (Notification.permission === 'denied') {
        console.warn('❌ Permisos de notificación denegados previamente');
        showNotificationWarning();
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
            showNotificationWarning();
            return false;
        }
    } catch (error) {
        console.error('❌ Error solicitando permisos:', error);
        return false;
    }
}

export function showNotificationWarning() {
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
                    Notificaciones Bloqueadas
                </h3>
                <p class="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                    Para recibir notificaciones, debes permitirlas en la configuración de tu navegador.
                </p>
                <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                        class="mt-2 text-xs text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-200">
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

export function getNotificationIcon(type) {
    const icons = { 
        'email': '📧', 
        'patent': '🔬', 
        'paper': '📚', 
        'ayudas': '💶', 
        'test': '🧪' 
    };
    return icons[type] || '🔔';
}

export function updateNotificationStatus(userId = null) {
    const statusEl = document.getElementById('notification-status');
    if (statusEl) {
        if (userId) {
            const permission = Notification.permission === 'granted' ? '✅' : '⚠️';
            statusEl.textContent = `${permission} Usuario: ${userId.substring(0, 8)}...`;
        } else {
            statusEl.textContent = 'Estado: ⏳ Iniciando...';
        }
    }
}

export async function initializeNotificationSystem() {
    try {
        if (window.registerServiceWorker) {
            await window.registerServiceWorker();
        }

        const response = await fetch('/notifications/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_name: `Web-${navigator.userAgent.substring(0, 20)}...`,
                device_id: `web_${Date.now()}`
            })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (!data.success) throw new Error('Fallo en registro de usuario');

        window.userId = data.user_id;
        updateNotificationStatus(window.userId);

        const hasPermission = await requestNotificationPermission();
        if (window.startServiceWorkerPolling) await window.startServiceWorkerPolling(window.userId);
        if (window.startNotificationPolling) window.startNotificationPolling();

        updateNotificationStatus(window.userId);

    } catch (error) {
        console.error("❌ Error inicializando notificaciones:", error);
        updateNotificationStatus();
        setTimeout(initializeNotificationSystem, 5000);
    }
}
