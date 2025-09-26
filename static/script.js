document.addEventListener('DOMContentLoaded', () => {
    // Variables globales para notificaciones
    // NOTA: 'let' a nivel de window es mejor, pero aquí lo mantengo dentro de DOMContentLoaded
    // para mantener el patrón original. Expondré solo las funciones.
    let userId = null;
    let notificationCheckInterval = null;

    // Elementos del DOM
    const form = document.getElementById('commandForm');
    const input = document.getElementById('user_input');
    const historyDiv = document.getElementById('history');
    const loadingIndicator = document.getElementById('loading-indicator');
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const codeFilesList = document.getElementById('code-files-list');

    // Verificar elementos críticos
    if (!form || !input || !historyDiv) {
        console.error('❌ Elementos críticos no encontrados:', {
            form: !!form,
            input: !!input, 
            historyDiv: !!historyDiv
        });
        return;
    }

    console.log('✅ Elementos encontrados correctamente');

    // 🔒 Escape para prevenir XSS (Mantenida en el scope para ser usada internamente)
    function escapeHtml(str) {
        if (typeof str !== 'string') return str;
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // =========================================================================
    // 🔔 FUNCIONES DE NOTIFICACIÓN (Expuestas a Window)
    // =========================================================================

    function getNotificationIcon(type) {
        const icons = {
            'email': '📧',
            'patent': '🔬',
            'paper': '📚',
            'test': '🧪'
        };
        return icons[type] || '🔔';
    }

    // Expuesta a window para que el HTML pueda llamar a los botones
    window.updateNotificationStatus = function(status = null) {
        const statusEl = document.getElementById('notification-status');
        if (statusEl) {
            if (status) {
                statusEl.textContent = `Estado: ${status}`;
            } else {
                statusEl.textContent = userId ? 
                    `Estado: ✅ Activo (${userId.substring(0, 8)}...)` : 
                    'Estado: ⏳ Iniciando...';
            }
        }
    }

    window.startNotificationPolling = function() {
        if (notificationCheckInterval) {
            clearInterval(notificationCheckInterval);
        }
        window.checkNotifications();
        notificationCheckInterval = setInterval(window.checkNotifications, 30000);
    }
    
    // Función central para verificar notificaciones (Expuesta a window)
    window.checkNotifications = async function() {
        if (!userId) return;

        try {
            const response = await fetch(`/notifications/user/${userId}`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.notifications && data.notifications.length > 0) {
                    console.log(`📨 ${data.notifications.length} nuevas notificaciones`);
                    
                    data.notifications.forEach(notification => {
                        showNotificationInHistory(notification);
                        showBrowserNotification(notification);
                    });
                }
            }
        } catch (error) {
            console.error("❌ Error verificando notificaciones:", error);
        }
    }

    // Lógica para mostrar en el historial (Mantenida como función interna)
    function showNotificationInHistory(notification) {
        const entry = document.createElement('div');
        entry.className = 'entry p-4 bg-blue-50 dark:bg-blue-900 rounded-lg shadow-md border-l-4 border-blue-500';
        
        const icon = getNotificationIcon(notification.type);
        const timeStr = new Date().toLocaleString();
        
        const notifData = notification.data || {};
        const url = notifData.url || null;
        
        const clickableClass = url ? 'cursor-pointer hover:underline' : '';
        const titleContent = url ? 
            `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-800 dark:text-blue-200 font-bold hover:underline">${escapeHtml(notification.title)}</a>` :
            `<div class="font-bold text-blue-800 dark:text-blue-200">${escapeHtml(notification.title)}</div>`;
        
        entry.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="text-2xl flex-shrink-0">${icon}</div>
                <div class="flex-1 min-w-0">
                    ${titleContent}
                    <div class="text-blue-700 dark:text-blue-300 mt-1 ${clickableClass}">
                        ${escapeHtml(notification.message)}
                    </div>
                    <div class="text-xs text-blue-600 dark:text-blue-400 mt-2">
                        ${timeStr} • ${notification.type}
                    </div>
                </div>
            </div>
        `;
        
        if (url) {
            entry.addEventListener('click', (e) => {
                if (e.target.tagName === 'A') return;
                window.open(url, '_blank', 'noopener,noreferrer');
            });
            entry.style.cursor = 'pointer';
        }
        
        historyDiv.prepend(entry);
        entry.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    // Lógica de notificación del navegador (Mantenida como función interna)
    function showBrowserNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const notifData = notification.data || {};
            const url = notifData.url;
            
            const browserNotif = new Notification(notification.title, {
                body: notification.message,
                icon: '/static/favicon.ico',
                tag: `${notification.type}_${notification.id}`,
                data: { url: url }
            });
            
            if (url) {
                browserNotif.onclick = function(event) {
                    event.preventDefault();
                    window.focus();
                    window.open(url, '_blank', 'noopener,noreferrer');
                    browserNotif.close();
                };
            }
        }
    }
    
    // Lógica de inicialización (Mantenida como función interna)
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

    // =========================================================================
    // FUNCIONES GLOBALES PARA BOTONES DE NOTIFICACIÓN
    // Estas funciones deben estar en el ámbito de Window, al igual que los demás 
    // controladores de botones del panel lateral que te proporcioné antes.
    // =========================================================================

    // Nueva función expuesta a Window para el botón "⚙️ Configurar"
    window.configureNotifications = function() {
        // Asume que el comando 'configurar' es manejado por el backend
        input.value = 'control configurar';
        form.dispatchEvent(new Event('submit'));
    }

    // Nueva función expuesta a Window para el botón "🧪 Probar"
    window.testNotifications = function() {
        // Asume que el comando 'test' es manejado por el backend
        input.value = 'control test';
        form.dispatchEvent(new Event('submit'));
    }


    // 🌙 Configuración inicial del tema
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && prefersDark)) {
        document.documentElement.classList.add('dark');
        if (themeIcon) themeIcon.textContent = '☀️';
    } else {
        document.documentElement.classList.remove('dark');
        if (themeIcon) themeIcon.textContent = '🌙';
    }

    // 🌓 Cambiar tema
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            if (document.documentElement.classList.contains('dark')) {
                document.documentElement.classList.remove('dark');
                localStorage.theme = 'light';
                if (themeIcon) themeIcon.textContent = '🌙';
            } else {
                document.documentElement.classList.add('dark');
                localStorage.theme = 'dark';
                if (themeIcon) themeIcon.textContent = '☀️';
            }
        });
    }

    // 🔔 Inicializar sistema de notificaciones
    initializeNotificationSystem();

    // 📤 Envío del formulario principal
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const userInput = input.value.trim();
        if (userInput === "") return;

        console.log('📤 Enviando comando:', userInput);

        showLoading(true);
        input.disabled = true;

        // Ocultar guía inicial (El div 'guide-section' no existe, lo mantengo comentado)
        /*
        const guideSection = document.getElementById('guide-section');
        if (guideSection && guideSection.style.display !== 'none') {
            guideSection.style.display = 'none';
        }
        */

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({ 'user_input': userInput })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('📦 Respuesta recibida:', data);
                
                renderResult(data);

                // Actualizar archivos si es necesario
                if (data.tool === "save_code" || data.tool === "code_gen" || data.tool === "note") {
                    setTimeout(fetchFiles, 500);
                }

                // Si es comando de notificaciones, actualizar estado
                if (data.tool === "notifications") {
                    setTimeout(() => {
                        window.checkNotifications();
                        window.updateNotificationStatus();
                    }, 1000);
                }
                
                // Disparar evento para que el JS en el HTML maneje el resultado RMN
                if (data.tool === "rmn_spectrum_cleaner" && data.result_data && typeof data.result_data === 'object' && data.result_data.type === 'clean_result') {
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

    // 📋 Renderizar resultados
    function renderResult(data) {
        // ... (Tu función renderResult se mantiene igual, ya que está correcta)
        let resultHtml = '';

        if (typeof data.result_data === 'string' && data.result_data.startsWith('OPEN_URL:')) {
            const url = data.result_data.replace('OPEN_URL:', '');
            window.open(url, '_blank', 'noopener,noreferrer');
            data.result_type = 'open_url';
            data.url = url;
        }

        switch (data.result_type) {
            case 'list':
                resultHtml = data.result_data.map(item => `
                    <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg shadow-sm">
                        <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="text-blue-600 dark:text-blue-400 font-semibold hover:underline">${escapeHtml(item.title)}</a>
                        <p class="text-sm mt-1 text-gray-600 dark:text-gray-400">${escapeHtml(item.snippet)}</p>
                    </div>
                `).join('');
                break;

            case 'open_url':
                {
                    let url = data.url;
                    if (url && url.startsWith('OPEN_URL:')) {
                        url = url.replace('OPEN_URL:', '');
                    }

                    if (url) {
                        window.open(url, '_blank', 'noopener,noreferrer');
                    }

                    resultHtml = `
                        <div class="p-4 bg-blue-50 dark:bg-blue-800 rounded-lg shadow-sm">
                            <p class="text-blue-800 dark:text-blue-200 font-semibold">${escapeHtml(data.result_data)}</p>
                            ${url ? `<button onclick="window.open('${url}', '_blank', 'noopener,noreferrer')" 
                                class="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                                🔗 Abrir ${url}
                            </button>` : ''}
                        </div>
                    `;
                }
                break;

            case 'download_file':
                resultHtml = `
                    <div class="p-4 bg-green-50 dark:bg-green-800 rounded-lg shadow-sm">
                        <p class="text-green-800 dark:text-green-200 font-semibold">${escapeHtml(data.result_data)}</p>
                        <a href="${data.file_path}" download="${escapeHtml(data.display_name)}"
                           class="mt-2 inline-block px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">
                            📁 Descargar ${escapeHtml(data.display_name)}
                        </a>
                    </div>
                `;
                break;

            default:
                resultHtml = `<pre class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg shadow-sm whitespace-pre-wrap">${escapeHtml(data.result_data)}</pre>`;
        }

        const entry = document.createElement('div');
        entry.className = 'entry p-4 bg-white dark:bg-gray-800 rounded-lg shadow-md';
        entry.innerHTML = `
            <div class="font-bold text-gray-800 dark:text-gray-200">
                <span class="text-blue-600">🧠 Tú:</span> ${escapeHtml(data.input)}
            </div>
            <div class="mt-2 text-gray-600 dark:text-gray-400">
                <span class="text-blue-600">🔧 Herramienta:</span> ${escapeHtml(data.tool)}
            </div>
            <div class="mt-4">
                <span class="font-bold text-gray-800 dark:text-gray-200">📦 Resultado:</span>
                <div class="mt-2">${resultHtml}</div>
            </div>
        `;
        historyDiv.prepend(entry);
    }

    function renderError(message) {
        // ... (Tu función renderError se mantiene igual)
        const entry = document.createElement('div');
        entry.className = 'entry p-4 bg-red-100 dark:bg-red-800 rounded-lg shadow-md';
        entry.innerHTML = `
            <div class="text-red-800 dark:text-red-200 font-bold">
                ❌ Error: ${escapeHtml(message)}
            </div>
        `;
        historyDiv.prepend(entry);
    }

    function showLoading(show) {
        // ... (Tu función showLoading se mantiene igual)
        if (loadingIndicator) {
            loadingIndicator.classList.toggle('hidden', !show);
        }
    }

    // 📁 Gestión de archivos
    async function fetchFiles() {
        // ... (Tu función fetchFiles se mantiene igual)
        try {
            const response = await fetch('/files');
            const data = await response.json();
            updateCodeFiles(data.code_files || []);
            updateNotesInfo(data.notes_exist || false, data.notes_count || 0);
        } catch (error) {
            console.error("❌ Error al cargar archivos:", error);
        }
    }

    function updateCodeFiles(files) {
        // ... (Tu función updateCodeFiles se mantiene igual)
        if (!codeFilesList) return;
        
        codeFilesList.innerHTML = '';

        if (files.length === 0) {
            codeFilesList.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400 italic text-center">No hay código guardado.</p>';
            return;
        }

        files.forEach(file => {
            const item = document.createElement('div');
            item.className = "flex justify-between items-center p-2 bg-gray-100 dark:bg-gray-700 rounded-lg mb-2";

            const name = document.createElement('span');
            name.textContent = file;
            name.className = "text-gray-800 dark:text-gray-100 text-sm truncate cursor-pointer hover:text-blue-600";
            name.title = "Click para ver contenido";
            name.addEventListener('click', () => viewFileContent(file));

            const actions = document.createElement('div');
            actions.className = "flex space-x-1";

            const viewBtn = document.createElement('button');
            viewBtn.innerHTML = '👁️';
            viewBtn.className = "text-gray-600 hover:text-blue-600 text-lg";
            viewBtn.title = "Ver contenido";
            viewBtn.addEventListener('click', () => viewFileContent(file));

            const downloadBtn = document.createElement('a');
            downloadBtn.href = `/download/code/${file}`;
            downloadBtn.innerHTML = '⬇️';
            downloadBtn.className = "text-gray-600 hover:text-green-600 text-lg";
            downloadBtn.title = "Descargar archivo";
            downloadBtn.setAttribute('download', file);

            actions.appendChild(viewBtn);
            actions.appendChild(downloadBtn);

            item.appendChild(name);
            item.appendChild(actions);
            codeFilesList.appendChild(item);
        });
    }

    async function viewFileContent(filename) {
        // ... (Tu función viewFileContent se mantiene igual)
        try {
            const response = await fetch(`/view/code/${filename}`);
            if (response.ok) {
                const data = await response.json();
                showFileModal(data.filename, data.content);
            } else {
                renderError(`No se pudo cargar el archivo ${filename}`);
            }
        } catch (error) {
            renderError(`Error al cargar el archivo: ${error.message}`);
        }
    }

    function showFileModal(filename, content) {
        // ... (Tu función showFileModal se mantiene igual)
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50';

        modal.innerHTML = `
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg max-w-4xl w-full max-h-[90vh] flex flex-col">
                <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
                    <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200">📄 ${escapeHtml(filename)}</h3>
                    <button class="close-file-modal text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-2xl">×</button>
                </div>
                <div class="flex-1 overflow-auto p-4">
                    <pre class="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto"><code>${escapeHtml(content)}</code></pre>
                </div>
                <div class="flex justify-end space-x-2 p-4 border-t border-gray-200 dark:border-gray-700">
                    <a href="/download/code/${encodeURIComponent(filename)}" download="${escapeHtml(filename)}" 
                       class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">
                        ⬇️ Descargar
                    </a>
                    <button class="close-file-modal px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors">
                        Cerrar
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelectorAll('.close-file-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                document.body.removeChild(modal);
            });
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }

    function updateNotesInfo(notesExist, notesCount) {
        // ... (Tu función updateNotesInfo se mantiene igual, las funciones de nota se exponen globalmente)
        const notesSection = document.getElementById('notes-section');
        if (!notesSection) return;

        if (!notesExist || notesCount === 0) {
            notesSection.innerHTML = `
                <h3 class="font-semibold text-lg text-gray-700 dark:text-gray-300 mb-2">📝 Notas</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 italic text-center mb-2">No hay notas guardadas</p>
                <div class="space-y-2">
                    <button onclick="createNewNote()" 
                            class="block w-full text-center p-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-lg transition-colors">
                        ➕ Crear primera nota
                    </button>
                </div>
            `;
        } else {
            notesSection.innerHTML = `
                <h3 class="font-semibold text-lg text-gray-700 dark:text-gray-300 mb-2">📝 Notas (${notesCount})</h3>
                <div class="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg flex justify-between items-center">
                    <span class="text-gray-800 dark:text-gray-100 text-sm">📝 Archivo de notas (${notesCount} notas)</span>
                    <div class="flex space-x-1">
                        <button onclick="viewAllNotes()" class="text-gray-600 hover:text-blue-600 text-lg" title="Ver todas las notas">👁️</button>
                        <a href="/download/notes" download="mis_notas.txt" class="text-gray-600 hover:text-green-600 text-lg" title="Descargar notas">⬇️</a>
                    </div>
                </div>
                <button onclick="createNewNote()" 
                        class="mt-2 w-full text-center p-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-lg transition-colors">
                    ➕ Crear nueva nota
                </button>
            `;
        }
    }

    // Funciones globales para notas (Mantenidas y expuestas a window)
    window.viewAllNotes = async function() {
        // ... (Tu función viewAllNotes se mantiene igual)
        try {
            const response = await fetch('/view/notes');
            if (response.ok) {
                const data = await response.json();
                showNotesModal(data.content, data.notes_count);
            } else {
                alert("No se pudieron cargar las notas");
            }
        } catch (error) {
            alert("Error al cargar las notas: " + error.message);
        }
    }

    function showNotesModal(content, notesCount) {
        // ... (Tu función showNotesModal se mantiene igual)
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50';
        
        modal.innerHTML = `
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg max-w-4xl w-full max-h-[90vh] flex flex-col">
                <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
                    <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200">📝 Todas las Notas (${notesCount})</h3>
                    <button class="close-notes-modal text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-2xl">×</button>
                </div>
                <div class="flex-1 overflow-auto p-4">
                    <pre class="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">${escapeHtml(content)}</pre>
                </div>
                <div class="flex justify-end space-x-2 p-4 border-t border-gray-200 dark:border-gray-700">
                    <a href="/download/notes" download="mis_notas.txt" 
                       class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">
                        ⬇️ Descargar
                    </a>
                    <button class="close-notes-modal px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors">
                        Cerrar
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.querySelectorAll('.close-notes-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                document.body.removeChild(modal);
            });
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }

    window.createNewNote = function() {
        // ... (Tu función createNewNote se mantiene igual)
        const noteText = prompt("Escribe tu nota:");
        if (noteText && noteText.trim()) {
            input.value = `guardar: ${noteText.trim()}`;
            form.dispatchEvent(new Event('submit'));
        }
    }

    // Función para mostrar resultado de limpieza RMN
    // Mantenida como interna, ya que el evento 'rmnCleanResult' la disparará desde el HTML.
    function showCleanResult(result) {
        // ... (Tu función showCleanResult se mantiene igual)
        console.log("Result recibido:", result);
        
        const containerId = 'cleaned-spectra';
        let container = document.getElementById(containerId);

        if (!container) {
            container = document.createElement('div');
            container.id = containerId;
            container.className = 'mt-4 space-y-4';
            const rmnSection = document.getElementById('rmn-section');
            if (rmnSection) {
                rmnSection.appendChild(container);
            }
        }
        
        // CORRECCIÓN: Eliminar el mensaje de 'no hay espectros limpios' si existe
        const emptyMsg = container.querySelector('div.text-xs.italic');
        if (emptyMsg) emptyMsg.remove();


        const cleanFileName = result.cleaned_file.split('/').pop();
        const plotFileName = result.plot_file ? result.plot_file.split('/').pop() : 'grafico_comparativo.png';

        const paramsStr = result.params ? 
            Object.entries(result.params).map(([key, value]) => `${key}: ${value}`).join(', ') : 
            'Parámetros automáticos';

        const entry = document.createElement('div');
        entry.className = 'p-4 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900 dark:to-blue-900 rounded-lg shadow-md border-l-4 border-green-500';
        entry.innerHTML = `
            <div class="flex justify-between items-start mb-3">
                <div class="flex items-center space-x-3">
                    <div class="text-2xl">🧪</div>
                    <div>
                        <div class="text-green-800 dark:text-green-200 font-bold text-lg">ESPECTRO LIMPIADO</div>
                        <div class="text-xs text-green-600 dark:text-green-400">
                            ${new Date().toLocaleString('es-ES')}
                        </div>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-4">
                <div class="space-y-1">
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Archivo original:</span>
                        <span class="font-mono text-gray-800 dark:text-gray-200">${escapeHtml(result.original_file)}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Archivo limpio:</span>
                        <span class="font-mono text-green-700 dark:text-green-300">${escapeHtml(cleanFileName)}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Método:</span>
                        <span class="font-semibold text-blue-600 dark:text-blue-400">${escapeHtml(result.method)}</span>
                    </div>
                </div>
                <div class="space-y-1">
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Mejora SNR:</span>
                        <span class="font-semibold text-green-600 dark:text-green-400">+${result.snr_improvement || '0'} dB</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Parámetros:</span>
                        <span class="text-xs text-gray-700 dark:text-gray-300">${escapeHtml(paramsStr)}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600 dark:text-gray-400">Estado:</span>
                        <span class="text-green-600 dark:text-green-400 font-semibold">✅ Listo</span>
                    </div>
                </div>
            </div>

            <div class="flex flex-wrap gap-2 pt-3 border-t border-green-200 dark:border-green-700">
                <a href="/download/cleaned/${encodeURIComponent(cleanFileName)}" download
                   class="flex items-center px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors">
                    📥 Descargar CSV Limpio
                </a>
                
                ${result.plot_file ? `
                <a href="/download/plot/${encodeURIComponent(plotFileName)}" download
                   class="flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors">
                    📊 Descargar Gráfico
                </a>
                ` : ''}
            </div>

            <div class="mt-3 text-xs text-gray-500 dark:text-gray-400 flex justify-between">
                <span>💡 Haz clic en "Analizar" para ver estadísticas detalladas</span>
                <span>🕒 Procesado en ${result.processing_time || '0'}s</span>
            </div>
        `;

        container.prepend(entry);
    }
    
    // Solicitar permisos de notificación
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            console.log(`Permisos de notificación: ${permission}`);
        });
    }

    // 📂 Inicializar archivos y notas al cargar
    fetchFiles();

    // 🔔 Cleanup al cerrar la página
    window.addEventListener('beforeunload', () => {
        if (notificationCheckInterval) {
            clearInterval(notificationCheckInterval);
        }
    });

    console.log('🚀 Script inicializado correctamente');
    console.log('🔔 Sistema de notificaciones:', userId ? 'Activo' : 'Iniciando...');
});