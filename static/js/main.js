// ========== SCRIPT PRINCIPAL DE LA APLICACIÓN ==========

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando aplicación...');

    let userId = null;
    let notificationCheckInterval = null;

    const form = document.getElementById('commandForm');
    const input = document.getElementById('user_input');
    const historyDiv = document.getElementById('history');

    if (!form || !input || !historyDiv) {
        console.error('❌ Elementos críticos no encontrados');
        return;
    }

    console.log('✅ Elementos encontrados correctamente');

    // ============= SISTEMA DE NOTIFICACIONES MEJORADO =============
    
    async function requestNotificationPermission() {
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

        // Solicitar permisos
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

    function showNotificationWarning() {
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
        
        // Auto-remover después de 10 segundos
        setTimeout(() => {
            if (warning.parentElement) {
                warning.remove();
            }
        }, 10000);
    }

    function getNotificationIcon(type) {
        const icons = { 
            'email': '📧', 
            'patent': '🔬', 
            'paper': '📚', 
            'ayudas': '💶', 
            'test': '🧪' 
        };
        return icons[type] || '🔔';
    }

    window.updateNotificationStatus = function(status = null) {
        const statusEl = document.getElementById('notification-status');
        if (statusEl) {
            if (status) {
                statusEl.textContent = status;
            } else if (userId) {
                const permission = Notification.permission === 'granted' ? '✅' : '⚠️';
                statusEl.textContent = `${permission} Usuario: ${userId.substring(0, 8)}...`;
            } else {
                statusEl.textContent = 'Estado: ⏳ Iniciando...';
            }
        }

        // NUEVO: Actualizar también el estado del Service Worker
        updateServiceWorkerStatus();
    };

    // NUEVO: Función para actualizar estado del Service Worker
    function updateServiceWorkerStatus() {
        const swStatusEl = document.getElementById('service-worker-status');
        if (swStatusEl && window.checkServiceWorkerStatus) {
            const status = window.checkServiceWorkerStatus();
            if (status.supported && status.active) {
                swStatusEl.textContent = 'Service Worker: ✅ Activo';
            } else if (status.supported && status.registered) {
                swStatusEl.textContent = 'Service Worker: ⚠️ Registrado (activando...)';
            } else if (status.supported) {
                swStatusEl.textContent = 'Service Worker: ⏳ Registrando...';
            } else {
                swStatusEl.textContent = 'Service Worker: ❌ No soportado';
            }
        }
    }

    window.startNotificationPolling = function() {
        if (notificationCheckInterval) {
            clearInterval(notificationCheckInterval);
        }
        
        console.log('🔔 Iniciando polling de notificaciones en cliente');
        window.checkNotifications();
        notificationCheckInterval = setInterval(window.checkNotifications, 30000);
        window.updateNotificationStatus('✅ Activo');
    };

    window.checkNotifications = async function() {
        if (!userId) {
            console.warn('⚠️ No hay userId para verificar notificaciones');
            return;
        }
        
        try {
            const response = await fetch(`/notifications/user/${userId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.notifications && data.notifications.length > 0) {
                    console.log(`📬 ${data.notifications.length} nuevas notificaciones`);
                    
                    data.notifications.forEach(notification => {
                        showNotificationInHistory(notification);
                        showBrowserNotification(notification);
                    });
                }
            } else {
                console.warn('⚠️ Error verificando notificaciones:', response.status);
            }
        } catch (error) {
            console.error("❌ Error verificando notificaciones:", error);
        }
    };

    function showNotificationInHistory(notification) {
        const entry = document.createElement('div');
        entry.className = 'entry p-4 bg-blue-50 dark:bg-blue-900 rounded-lg shadow-md border-l-4 border-blue-500 notification-new';
        
        const icon = getNotificationIcon(notification.type);
        const url = (notification.data || {}).url || null;
        
        const titleContent = url ?
            `<a href="${url}" target="_blank" class="text-blue-800 dark:text-blue-200 font-bold hover:underline">${escapeHtml(notification.title)}</a>` :
            `<div class="font-bold text-blue-800 dark:text-blue-200">${escapeHtml(notification.title)}</div>`;
        
        entry.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="text-2xl">${icon}</div>
                <div class="flex-1">
                    ${titleContent}
                    <div class="text-blue-700 dark:text-blue-300 mt-1">${escapeHtml(notification.message)}</div>
                    <div class="text-xs text-blue-600 dark:text-blue-400 mt-2">
                        ${new Date().toLocaleString()} • ${notification.type}
                    </div>
                </div>
            </div>
        `;
        
        if (url) {
            entry.onclick = () => window.open(url, '_blank');
            entry.style.cursor = 'pointer';
            entry.classList.add('notification-clickable');
        }
        
        historyDiv.prepend(entry);
    }

    async function showBrowserNotification(notification) {
        // Verificar permisos antes de mostrar
        if (Notification.permission !== 'granted') {
            console.warn('⚠️ No hay permisos para mostrar notificación del navegador');
            return;
        }

        try {
            const url = (notification.data || {}).url;
            const browserNotif = new Notification(notification.title, {
                body: notification.message,
                icon: '/static/favicon.ico',
                tag: `${notification.type}_${notification.id}`,
                requireInteraction: false
            });
            
            if (url) {
                browserNotif.onclick = () => {
                    window.open(url, '_blank');
                    browserNotif.close();
                };
            }
            
            console.log('✅ Notificación del navegador mostrada');
        } catch (error) {
            console.error('❌ Error mostrando notificación del navegador:', error);
        }
    }

    async function initializeNotificationSystem() {
        try {
            // NUEVO: 1. Asegurar que el Service Worker esté registrado
            console.log('🔧 Esperando registro del Service Worker...');
            if (window.registerServiceWorker) {
                await window.registerServiceWorker();
            }
            
            // 2. Registrar usuario
            const response = await fetch('/notifications/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_name: `Web-${navigator.userAgent.substring(0, 20)}...`,
                    device_id: `web_${Date.now()}`
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    userId = data.user_id;
                    console.log(`✅ Usuario registrado: ${userId.substring(0, 12)}...`);
                    
                    // NUEVO: 3. Actualizar userId en Service Worker
                    if (window.updateServiceWorkerUserId) {
                        await window.updateServiceWorkerUserId(userId);
                    }
                    
                    // 4. Solicitar permisos de notificaciones
                    const hasPermission = await requestNotificationPermission();
                    
                    // NUEVO: 5. Iniciar polling en Service Worker (cada 5 min)
                    if (window.startServiceWorkerPolling) {
                        await window.startServiceWorkerPolling(userId);
                        console.log('🔔 Polling iniciado en Service Worker (5 min)');
                    }
                    
                    // 6. Iniciar polling en cliente también (cada 30 seg)
                    window.startNotificationPolling();
                    console.log('🔔 Polling iniciado en cliente (30 seg)');
                    
                    if (hasPermission) {
                        window.updateNotificationStatus("✅ Conectado + Notificaciones");
                    } else {
                        window.updateNotificationStatus("✅ Conectado (sin notif. navegador)");
                    }
                } else {
                    throw new Error('Fallo en registro de usuario');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error("❌ Error inicializando notificaciones:", error);
            window.updateNotificationStatus("⚠️ Error de conexión");
            
            // Reintentar después de 5 segundos
            setTimeout(initializeNotificationSystem, 5000);
        }
    }

    window.configureNotifications = () => { 
        input.value = 'status'; 
        form.dispatchEvent(new Event('submit')); 
    };
    
    window.testNotifications = async () => { 
        if (!userId) {
            showErrorMessage('Sistema de notificaciones no inicializado');
            return;
        }
        
        try {
            const response = await fetch(`/notifications/user/${userId}/test`, {
                method: 'POST'
            });
            
            if (response.ok) {
                showSuccessMessage('Notificación de prueba enviada');
                // Verificar notificaciones inmediatamente
                setTimeout(window.checkNotifications, 1000);
            } else {
                showErrorMessage('Error enviando notificación de prueba');
            }
        } catch (error) {
            showErrorMessage('Error de conexión al enviar prueba');
        }
    };

    // NUEVO: Función de debug
    window.debugNotifications = function() {
        const swStatus = window.checkServiceWorkerStatus ? window.checkServiceWorkerStatus() : { supported: false };
        const notifPermission = Notification.permission;
        
        const debugInfo = `
🐛 DEBUG NOTIFICACIONES

Service Worker:
- Soportado: ${swStatus.supported ? '✅' : '❌'}
- Registrado: ${swStatus.registered ? '✅' : '❌'}
- Activo: ${swStatus.active ? '✅' : '❌'}

Notificaciones del Navegador:
- Permiso: ${notifPermission}
- API disponible: ${'Notification' in window ? '✅' : '❌'}

Usuario:
- User ID: ${userId ? userId.substring(0, 12) + '...' : 'No registrado'}
- Polling cliente: ${notificationCheckInterval ? '✅ Activo' : '❌ Inactivo'}

Recomendaciones:
${!swStatus.supported ? '⚠️ Tu navegador no soporta Service Workers\n' : ''}
${!swStatus.registered ? '⚠️ Service Worker no registrado - recarga la página\n' : ''}
${notifPermission === 'denied' ? '⚠️ Permisos denegados - habilítalos en configuración\n' : ''}
${notifPermission === 'default' ? '💡 Click en "🔔 Activar Permisos"\n' : ''}
${!userId ? '⚠️ Usuario no registrado - espera la inicialización\n' : ''}
        `.trim();
        
        alert(debugInfo);
        console.log(debugInfo);
    };

    // NUEVO: Exportar requestNotificationPermission globalmente
    window.requestNotificationPermission = requestNotificationPermission;

    // ============= ENVÍO DEL FORMULARIO =============
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userInput = input.value.trim();
        if (!userInput) return;

        showLoading(true);
        input.disabled = true;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ 'user_input': userInput })
            });

            if (response.ok) {
                const data = await response.json();
                renderResult(data);
                
                if (['save_code', 'code_gen', 'note'].includes(data.tool)) {
                    setTimeout(() => window.fetchFiles?.(), 500);
                }
                
                if (data.tool === "notifications") {
                    setTimeout(() => { 
                        window.checkNotifications(); 
                        window.updateNotificationStatus(); 
                    }, 1000);
                }
                
                if (data.tool === "rmn_spectrum_cleaner" && data.result_data?.type === 'clean_result') {
                    window.dispatchEvent(new CustomEvent('rmnCleanResult', { detail: data.result_data }));
                }
            } else {
                const errorData = await response.json().catch(() => ({ detail: "Error desconocido" }));
                renderError(errorData.detail || "Ocurrió un error inesperado.");
            }
        } catch (error) {
            console.error("❌ Error en fetch:", error);
            renderError("No se pudo conectar con el servidor.");
        } finally {
            showLoading(false);
            input.disabled = false;
            input.value = '';
        }
    });

    // ============= RENDERIZADO =============

function renderResult(data) {
    let resultHtml = '';
    
    // Manejar OPEN_URL
    if (typeof data.result_data === 'string' && data.result_data.startsWith('OPEN_URL:')) {
        const url = data.result_data.replace('OPEN_URL:', '');
        window.open(url, '_blank');
        data.result_type = 'open_url';
        data.url = url;
    }

    // NUEVO: Detectar respuestas de RMN Spectrum Cleaner
    if (typeof data.result_data === 'object' && data.result_data !== null) {
        // Respuesta de análisis de espectro
        if (data.result_data.type === 'analysis_result') {
            resultHtml = renderAnalysisResult(data.result_data);
        }
        // Respuesta de limpieza de espectro
        else if (data.result_data.type === 'clean_result') {
            resultHtml = renderCleanResult(data.result_data);
        }
        // Otro tipo de objeto
        else {
            resultHtml = `<pre class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg whitespace-pre-wrap">${JSON.stringify(data.result_data, null, 2)}</pre>`;
        }
    }
    // Renderizado normal para otros tipos
    else {
        switch (data.result_type) {
            case 'list':
                resultHtml = data.result_data.map(item => `
                    <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <a href="${item.link}" target="_blank" class="text-blue-600 font-semibold hover:underline">${escapeHtml(item.title)}</a>
                        <p class="text-sm mt-1">${escapeHtml(item.snippet)}</p>
                    </div>
                `).join('');
                break;
            case 'open_url':
                resultHtml = `<div class="p-4 bg-blue-50 dark:bg-blue-800 rounded-lg">
                    <p class="font-semibold">${escapeHtml(data.result_data)}</p></div>`;
                break;
            default:
                resultHtml = `<pre class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg whitespace-pre-wrap">${escapeHtml(data.result_data)}</pre>`;
        }
    }

    const entry = document.createElement('div');
    entry.className = 'entry p-4 bg-white dark:bg-gray-800 rounded-lg shadow-md';
    entry.innerHTML = `
        <div class="font-bold"><span class="text-blue-600">🧠 Tú:</span> ${escapeHtml(data.input)}</div>
        <div class="mt-2"><span class="text-blue-600">🔧 Herramienta:</span> ${escapeHtml(data.tool)}</div>
        <div class="mt-4"><span class="font-bold">📦 Resultado:</span><div class="mt-2">${resultHtml}</div></div>
    `;
    historyDiv.prepend(entry);
}

// NUEVO: Renderizar resultado de análisis de espectro
function renderAnalysisResult(data) {
    const analysis = data.analysis;
    const stats = data.statistics;
    
    let html = `
        <div class="bg-gradient-to-r from-teal-50 to-cyan-50 dark:from-teal-900 dark:to-cyan-900 rounded-lg p-4 space-y-4">
            <div class="flex items-center justify-between border-b border-teal-200 dark:border-teal-700 pb-3">
                <h3 class="text-lg font-bold text-teal-800 dark:text-teal-200">
                    🔍 Análisis: ${escapeHtml(data.filename)}
                </h3>
                <span class="px-3 py-1 bg-teal-600 text-white rounded-full text-xs font-semibold">
                    ${data.success ? '✅ Completado' : '⚠️ Con errores'}
                </span>
            </div>
            
            <!-- Estadísticas Básicas -->
            <div class="grid grid-cols-2 gap-3">
                <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
                    <div class="text-xs text-gray-500 dark:text-gray-400">Puntos de datos</div>
                    <div class="text-2xl font-bold text-gray-800 dark:text-gray-200">${stats.data_points.toLocaleString()}</div>
                </div>
                <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
                    <div class="text-xs text-gray-500 dark:text-gray-400">Rango (ppm)</div>
                    <div class="text-sm font-semibold text-gray-800 dark:text-gray-200">${stats.frequency_range}</div>
                </div>
            </div>
            
            <!-- Análisis de Calidad -->
            <div class="bg-white dark:bg-gray-800 rounded-lg p-4 space-y-2">
                <h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-3">📊 Calidad del Espectro</h4>
                
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">SNR (Señal/Ruido)</span>
                    <span class="font-bold ${analysis.snr > 30 ? 'text-green-600' : analysis.snr > 20 ? 'text-yellow-600' : 'text-red-600'}">
                        ${analysis.snr.toFixed(1)} dB
                    </span>
                </div>
                
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Nivel de ruido</span>
                    <span class="font-mono text-xs">${analysis.noise_level.toFixed(4)}</span>
                </div>
                
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Deriva línea base</span>
                    <span class="font-mono text-xs">${analysis.baseline_drift.toFixed(4)}</span>
                </div>
                
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Picos detectados</span>
                    <span class="font-bold text-blue-600">${analysis.peak_count}</span>
                </div>
            </div>
    `;
    
    // Gráfico si existe
    if (data.plot_file) {
        html += `
            <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-semibold text-gray-700 dark:text-gray-300">📈 Gráfico de Análisis</span>
                    <a href="/download/plot/${data.plot_file}" download 
                       class="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200">
                        ⬇️ Descargar
                    </a>
                </div>
                <img src="/download/plot/${data.plot_file}" 
                     alt="Análisis del espectro" 
                     class="w-full rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer"
                     onclick="window.open('/download/plot/${data.plot_file}', '_blank')">
            </div>
        `;
    }
    
    // Recomendaciones
    if (data.recommendations && data.recommendations.length > 0) {
        html += `
            <div class="bg-blue-50 dark:bg-blue-900 rounded-lg p-4">
                <h4 class="font-semibold text-blue-800 dark:text-blue-200 mb-2">💡 Recomendaciones</h4>
                <ul class="space-y-1 text-sm text-blue-700 dark:text-blue-300">
        `;
        
        data.recommendations.forEach(rec => {
            html += `<li>• ${escapeHtml(rec)}</li>`;
        });
        
        html += `
                </ul>
            </div>
        `;
    }
    
    html += `</div>`;
    return html;
}

// NUEVO: Renderizar resultado de limpieza de espectro
function renderCleanResult(data) {
    const improvement = data.snr_improvement;
    const improvementColor = improvement > 5 ? 'green' : improvement > 2 ? 'yellow' : 'orange';
    
    let html = `
        <div class="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900 dark:to-emerald-900 rounded-lg p-4 space-y-4">
            <div class="flex items-center justify-between border-b border-green-200 dark:border-green-700 pb-3">
                <h3 class="text-lg font-bold text-green-800 dark:text-green-200">
                    ✨ Limpieza Completada
                </h3>
                <span class="px-3 py-1 bg-green-600 text-white rounded-full text-xs font-semibold">
                    ${data.success ? '✅ Exitoso' : '⚠️ Con advertencias'}
                </span>
            </div>
            
            <!-- Información de archivos -->
            <div class="space-y-2">
                <div class="flex items-start space-x-2">
                    <span class="text-gray-600 dark:text-gray-400 text-sm">📄 Original:</span>
                    <span class="font-mono text-xs text-gray-800 dark:text-gray-200">${escapeHtml(data.original_file)}</span>
                </div>
                <div class="flex items-start space-x-2">
                    <span class="text-green-600 dark:text-green-400 text-sm">✨ Limpio:</span>
                    <div class="flex-1">
                        <span class="font-mono text-xs text-gray-800 dark:text-gray-200">${escapeHtml(data.cleaned_file)}</span>
                        <a href="${data.download_urls.cleaned}" download 
                           class="ml-2 text-xs text-blue-600 hover:text-blue-800">
                            ⬇️ Descargar
                        </a>
                    </div>
                </div>
            </div>
            
            <!-- Método usado -->
            <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">🔧 Método de limpieza</div>
                <div class="font-semibold text-gray-800 dark:text-gray-200">${escapeHtml(data.method)}</div>
                ${data.params && Object.keys(data.params).length > 0 ? `
                    <div class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        Parámetros: ${JSON.stringify(data.params)}
                    </div>
                ` : ''}
            </div>
            
            <!-- Mejoras -->
            <div class="grid grid-cols-3 gap-3">
                <div class="bg-white dark:bg-gray-800 rounded-lg p-3 text-center">
                    <div class="text-xs text-gray-500 dark:text-gray-400">SNR Original</div>
                    <div class="text-xl font-bold text-gray-600 dark:text-gray-400">${data.snr_original.toFixed(1)}</div>
                    <div class="text-xs text-gray-500">dB</div>
                </div>
                <div class="bg-white dark:bg-gray-800 rounded-lg p-3 text-center">
                    <div class="text-xs text-gray-500 dark:text-gray-400">Mejora</div>
                    <div class="text-xl font-bold text-${improvementColor}-600">+${improvement.toFixed(1)}</div>
                    <div class="text-xs text-gray-500">dB</div>
                </div>
                <div class="bg-white dark:bg-gray-800 rounded-lg p-3 text-center">
                    <div class="text-xs text-gray-500 dark:text-gray-400">SNR Final</div>
                    <div class="text-xl font-bold text-green-600">${data.snr_clean.toFixed(1)}</div>
                    <div class="text-xs text-gray-500">dB</div>
                </div>
            </div>
            
            <!-- Estadísticas adicionales -->
            <div class="grid grid-cols-2 gap-3 text-sm">
                <div class="flex justify-between">
                    <span class="text-gray-600 dark:text-gray-400">Puntos de datos:</span>
                    <span class="font-semibold">${data.data_points.toLocaleString()}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600 dark:text-gray-400">Tiempo proceso:</span>
                    <span class="font-semibold">${data.processing_time} ms</span>
                </div>
            </div>
    `;
    
    // Gráfico de comparación si existe
    if (data.plot_file && data.download_urls.plot) {
        html += `
            <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-semibold text-gray-700 dark:text-gray-300">📊 Comparación Antes/Después</span>
                    <a href="${data.download_urls.plot}" download 
                       class="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400">
                        ⬇️ Descargar
                    </a>
                </div>
                <img src="${data.download_urls.plot}" 
                     alt="Comparación del espectro" 
                     class="w-full rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer"
                     onclick="window.open('${data.download_urls.plot}', '_blank')">
            </div>
        `;
    }
    
    // Mensaje
    if (data.message) {
        html += `
            <div class="bg-green-50 dark:bg-green-900 rounded-lg p-3">
                <p class="text-sm text-green-700 dark:text-green-300">${escapeHtml(data.message)}</p>
            </div>
        `;
    }
    
    html += `</div>`;
    return html;
}
   
    // ============= INICIALIZACIÓN =============
    
    // Inicializar sistema de notificaciones
    initializeNotificationSystem();
    
    // Cargar archivos si la función existe
    if (window.fetchFiles) window.fetchFiles();
    
    // Cleanup al cerrar
    window.addEventListener('beforeunload', () => { 
        if (notificationCheckInterval) clearInterval(notificationCheckInterval); 
    });

    console.log('✅ Script principal inicializado completamente');
});