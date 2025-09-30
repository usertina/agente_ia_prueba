// Service Worker para notificaciones en background
const CACHE_NAME = 'agente-gemini-v2';
const CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutos
let checkTimer = null;
let userId = null;

// Instalar Service Worker
self.addEventListener('install', event => {
    console.log('🔧 Service Worker instalando...');
    
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll([
                '/',
                '/static/script.js'
            ]).catch(err => {
                console.log('⚠️ Error caching files:', err);
                return Promise.resolve();
            });
        })
    );
    
    self.skipWaiting();
});

// Activar Service Worker
self.addEventListener('activate', event => {
    console.log('✅ Service Worker activado');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    return self.clients.claim();
});

// Manejar mensajes del cliente
self.addEventListener('message', event => {
    const { type, data } = event.data;
    
    switch (type) {
        case 'START_NOTIFICATION_CHECK':
            userId = data.userId;
            startNotificationPolling();
            event.ports[0].postMessage({ success: true });
            break;

        case 'STOP_NOTIFICATION_CHECK':
            stopNotificationPolling();
            event.ports[0].postMessage({ success: true });
            break;
            
        case 'UPDATE_USER_ID':
            userId = data.userId;
            event.ports[0].postMessage({ success: true });
            break;
    }
});

// Iniciar polling de notificaciones
function startNotificationPolling() {
    if (checkTimer) return;
    
    console.log('🔔 Iniciando verificación de notificaciones en background');
    
    // Verificar inmediatamente
    checkNotifications();
    
    // Configurar timer
    checkTimer = setInterval(checkNotifications, CHECK_INTERVAL);
}

// Detener polling
function stopNotificationPolling() {
    if (checkTimer) {
        clearInterval(checkTimer);
        checkTimer = null;
        console.log('⏹️ Deteniendo verificación de notificaciones');
    }
}

// Verificar notificaciones
async function checkNotifications() {
    if (!userId) return;
    
    try {
        const response = await fetch(`/notifications/user/${userId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.notifications && data.notifications.length > 0) {
                console.log(`📨 ${data.notifications.length} nuevas notificaciones`);
                data.notifications.forEach(notification => {
                    showNotification(notification);
                });
            }
        }
    } catch (error) {
        console.error('Error verificando notificaciones:', error);
    }
}

// Mostrar notificación
function showNotification(notification) {
    const options = {
        body: notification.message,
        icon: getNotificationIcon(notification.type),
        badge: '/static/favicon.ico',
        tag: `${notification.type}_${notification.id}`,
        timestamp: Date.now(),
        requireInteraction: false,
        silent: false,
        data: {
            notificationId: notification.id,
            type: notification.type,
            timestamp: notification.timestamp,
            data: notification.data
        },
        actions: [
            {
                action: 'view',
                title: 'Ver'
            },
            {
                action: 'dismiss',
                title: 'Cerrar'
            }
        ]
    };
    
    self.registration.showNotification(notification.title, options);
}

// Manejar clicks en notificaciones
self.addEventListener('notificationclick', event => {
    const notification = event.notification;
    const action = event.action;
    
    event.notification.close();
    
    if (action === 'view' || !action) {
        // Abrir o enfocar la app
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then(clientList => {
                // Si hay una ventana abierta, enfocarla
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Si no hay ventana abierta, abrir una nueva
                if (clients.openWindow) {
                    return clients.openWindow('/');
                }
            })
        );
    }
    
    // Enviar mensaje a los clientes conectados
    event.waitUntil(
        clients.matchAll().then(clientList => {
            clientList.forEach(client => {
                client.postMessage({
                    type: 'NOTIFICATION_CLICKED',
                    data: {
                        action: action,
                        notificationData: notification.data
                    }
                });
            });
        })
    );
});

// Obtener icono de notificación
function getNotificationIcon(type) {
    // Usar emoji como iconos (funciona en todos los navegadores)
    const icons = {
        'email': '📧',
        'patent': '🔬',
        'paper': '📚',
        'test': '🧪'
    };
    return icons[type] || '🔔';
}

// Manejar requests (funcionalidad offline básica)
self.addEventListener('fetch', event => {
    // Solo cachear requests GET
    if (event.request.method !== 'GET') return;
    
    // No interferir con requests de API
    if (event.request.url.includes('/notifications/') ||
        event.request.url.includes('/ask')) return;
    
    event.respondWith(
        caches.match(event.request).then(response => {
            // Devolver desde cache si existe
            if (response) {
                return response;
            }
            
            // Hacer fetch normal
            return fetch(event.request).then(response => {
                if (!response || response.status !== 200 || response.type !== 'basic') {
                    return response;
                }
                
                // Solo cachear recursos estáticos
                if (event.request.url.includes('/static/')) {
                    const responseToCache = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, responseToCache);
                    });
                }
                
                return response;
            }).catch(error => {
                console.log('Fetch failed:', error);
                return new Response('Sin conexión', { status: 503 });
            });
        })
    );
});

console.log('🔧 Service Worker cargado correctamente');