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

    // FUNCIONES DE NOTIFICACIÓN
    function getNotificationIcon(type) {
        const icons = { 'email': '📧', 'patent': '🔬', 'paper': '📚', 'ayudas': '💶', 'test': '🧪' };
        return icons[type] || '🔔';
    }

    window.updateNotificationStatus = function(status = null) {
        const statusEl = document.getElementById('notification-status');
        if (statusEl) {
            statusEl.textContent = status ? `Estado: ${status}` : 
                userId ? `Estado: ✅ Activo (${userId.substring(0, 8)}...)` : 'Estado: ⏳ Iniciando...';
        }
    };

    window.startNotificationPolling = function() {
        if (notificationCheckInterval) clearInterval(notificationCheckInterval);
        window.checkNotifications();
        notificationCheckInterval = setInterval(window.checkNotifications, 30000);
    };

    window.checkNotifications = async function() {
        if (!userId) return;
        try {
            const response = await fetch(`/notifications/user/${userId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.notifications && data.notifications.length > 0) {
                    data.notifications.forEach(notification => {
                        showNotificationInHistory(notification);
                        showBrowserNotification(notification);
                    });
                }
            }
        } catch (error) {
            console.error("❌ Error verificando notificaciones:", error);
        }
    };

    function showNotificationInHistory(notification) {
        const entry = document.createElement('div');
        entry.className = 'entry p-4 bg-blue-50 dark:bg-blue-900 rounded-lg shadow-md border-l-4 border-blue-500';
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
                    <div class="text-xs text-blue-600 dark:text-blue-400 mt-2">${new Date().toLocaleString()} • ${notification.type}</div>
                </div>
            </div>
        `;
        if (url) {
            entry.onclick = () => window.open(url, '_blank');
            entry.style.cursor = 'pointer';
        }
        historyDiv.prepend(entry);
    }

    function showBrowserNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const url = (notification.data || {}).url;
            const browserNotif = new Notification(notification.title, {
                body: notification.message,
                icon: '/static/favicon.ico',
                tag: `${notification.type}_${notification.id}`
            });
            if (url) browserNotif.onclick = () => { window.open(url, '_blank'); browserNotif.close(); };
        }
    }

    async function initializeNotificationSystem() {
        try {
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
                    console.log(`🔔 Usuario registrado: ${userId.substring(0, 12)}...`);
                    window.startNotificationPolling();
                    window.updateNotificationStatus("✅ Conectado");
                }
            }
        } catch (error) {
            console.error("❌ Error inicializando notificaciones:", error);
            window.updateNotificationStatus("⚠️ Offline");
        }
    }

    window.configureNotifications = () => { input.value = 'control configurar'; form.dispatchEvent(new Event('submit')); };
    window.testNotifications = () => { input.value = 'control test'; form.dispatchEvent(new Event('submit')); };

    // ENVÍO DEL FORMULARIO
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
                if (['save_code', 'code_gen', 'note'].includes(data.tool)) setTimeout(() => window.fetchFiles?.(), 500);
                if (data.tool === "notifications") setTimeout(() => { window.checkNotifications(); window.updateNotificationStatus(); }, 1000);
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

    // RENDERIZADO
    function renderResult(data) {
        let resultHtml = '';
        if (typeof data.result_data === 'string' && data.result_data.startsWith('OPEN_URL:')) {
            const url = data.result_data.replace('OPEN_URL:', '');
            window.open(url, '_blank');
            data.result_type = 'open_url';
            data.url = url;
        }

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

        const entry = document.createElement('div');
        entry.className = 'entry p-4 bg-white dark:bg-gray-800 rounded-lg shadow-md';
        entry.innerHTML = `
            <div class="font-bold"><span class="text-blue-600">🧠 Tú:</span> ${escapeHtml(data.input)}</div>
            <div class="mt-2"><span class="text-blue-600">🔧 Herramienta:</span> ${escapeHtml(data.tool)}</div>
            <div class="mt-4"><span class="font-bold">📦 Resultado:</span><div class="mt-2">${resultHtml}</div></div>
        `;
        historyDiv.prepend(entry);
    }

    // INICIALIZACIÓN
    initializeNotificationSystem();
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    if (window.fetchFiles) window.fetchFiles();
    window.addEventListener('beforeunload', () => { if (notificationCheckInterval) clearInterval(notificationCheckInterval); });

    console.log('🚀 Script principal inicializado');
});