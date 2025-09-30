// ========== REGISTRO DEL SERVICE WORKER ==========

/**
 * Registra el Service Worker para notificaciones en background
 */
async function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
        console.warn('⚠️ Service Workers no soportados en este navegador');
        return null;
    }

    try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/'
        });
        
        console.log('✅ Service Worker registrado:', registration.scope);
        
        // Esperar a que el Service Worker esté activo
        await navigator.serviceWorker.ready;
        console.log('✅ Service Worker listo');
        
        return registration;
        
    } catch (error) {
        console.error('❌ Error registrando Service Worker:', error);
        return null;
    }
}

/**
 * Verifica el estado del Service Worker
 */
function checkServiceWorkerStatus() {
    if (!('serviceWorker' in navigator)) {
        return {
            supported: false,
            registered: false,
            active: false
        };
    }

    return {
        supported: true,
        registered: !!navigator.serviceWorker.controller,
        active: navigator.serviceWorker.controller?.state === 'activated'
    };
}

/**
 * Envía mensaje al Service Worker
 */
async function sendMessageToServiceWorker(message) {
    if (!navigator.serviceWorker.controller) {
        console.warn('⚠️ No hay Service Worker activo');
        return null;
    }

    return new Promise((resolve, reject) => {
        const messageChannel = new MessageChannel();
        
        messageChannel.port1.onmessage = (event) => {
            if (event.data.error) {
                reject(event.data.error);
            } else {
                resolve(event.data);
            }
        };

        navigator.serviceWorker.controller.postMessage(message, [messageChannel.port2]);
        
        // Timeout después de 5 segundos
        setTimeout(() => {
            reject(new Error('Service Worker timeout'));
        }, 5000);
    });
}

/**
 * Actualiza el userId en el Service Worker
 */
async function updateServiceWorkerUserId(userId) {
    try {
        await sendMessageToServiceWorker({
            type: 'UPDATE_USER_ID',
            data: { userId }
        });
        console.log('✅ userId actualizado en Service Worker');
        return true;
    } catch (error) {
        console.warn('⚠️ Error actualizando userId en Service Worker:', error);
        return false;
    }
}

/**
 * Inicia el polling de notificaciones en el Service Worker
 */
async function startServiceWorkerPolling(userId) {
    try {
        await sendMessageToServiceWorker({
            type: 'START_NOTIFICATION_CHECK',
            data: { userId }
        });
        console.log('✅ Polling iniciado en Service Worker');
        return true;
    } catch (error) {
        console.warn('⚠️ Error iniciando polling en Service Worker:', error);
        return false;
    }
}

/**
 * Detiene el polling de notificaciones en el Service Worker
 */
async function stopServiceWorkerPolling() {
    try {
        await sendMessageToServiceWorker({
            type: 'STOP_NOTIFICATION_CHECK',
            data: {}
        });
        console.log('✅ Polling detenido en Service Worker');
        return true;
    } catch (error) {
        console.warn('⚠️ Error deteniendo polling en Service Worker:', error);
        return false;
    }
}

/**
 * Desregistra el Service Worker
 */
async function unregisterServiceWorker() {
    if (!('serviceWorker' in navigator)) {
        return false;
    }

    try {
        const registration = await navigator.serviceWorker.getRegistration();
        if (registration) {
            await registration.unregister();
            console.log('✅ Service Worker desregistrado');
            return true;
        }
        return false;
    } catch (error) {
        console.error('❌ Error desregistrando Service Worker:', error);
        return false;
    }
}

// Exportar funciones globalmente
window.registerServiceWorker = registerServiceWorker;
window.checkServiceWorkerStatus = checkServiceWorkerStatus;
window.updateServiceWorkerUserId = updateServiceWorkerUserId;
window.startServiceWorkerPolling = startServiceWorkerPolling;
window.stopServiceWorkerPolling = stopServiceWorkerPolling;
window.unregisterServiceWorker = unregisterServiceWorker;

// Auto-registrar al cargar el script
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', registerServiceWorker);
} else {
    registerServiceWorker();
}

console.log('🔧 Módulo de Service Worker cargado');