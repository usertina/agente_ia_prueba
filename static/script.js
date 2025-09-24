document.addEventListener('DOMContentLoaded', () => {
    // Variables globales para notificaciones
    let userId = null;
    let notificationCheckInterval = null;

    // 🌙 Configuración inicial del tema oscuro/claro
    const themeIconEl = document.getElementById('theme-icon');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && prefersDark)) {
        document.documentElement.classList.add('dark');
        if (themeIconEl) themeIconEl.textContent = '☀️';
    } else {
        document.documentElement.classList.remove('dark');
        if (themeIconEl) themeIconEl.textContent = '🌙';
    }

    const form = document.getElementById('commandForm');
    const input = document.getElementById('user_input');
    const historyDiv = document.getElementById('history');
    const loadingIndicator = document.getElementById('loading-indicator');
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const codeFilesList = document.getElementById('code-files-list');
    const guideButton = document.getElementById('guide-button');
    const guideModal = document.getElementById('guide-modal');
    const closeModalButton = document.getElementById('close-modal');

    // 🔔 Inicializar sistema de notificaciones
    initializeNotificationSystem();

    // 🌓 Cambiar entre modo claro/oscuro
    themeToggle.addEventListener('click', () => {
        if (document.documentElement.classList.contains('dark')) {
            document.documentElement.classList.remove('dark');
            localStorage.theme = 'light';
            themeIcon.textContent = '🌙';
        } else {
            document.documentElement.classList.add('dark');
            localStorage.theme = 'dark';
            themeIcon.textContent = '☀️';
        }
    });

    // 📘 Abrir/cerrar modal de la guía de uso
    if (guideButton) {
        guideButton.addEventListener('click', () => {
            guideModal.classList.remove('hidden');
        });
    }

    if (closeModalButton) {
        closeModalButton.addEventListener('click', () => {
            guideModal.classList.add('hidden');
        });
    }

    if (guideModal) {
        guideModal.addEventListener('click', (e) => {
            if (e.target === guideModal) {
                guideModal.classList.add('hidden');
            }
        });
    }

    // 📤 Envío del formulario principal
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const userInput = input.value.trim();
        if (userInput === "") return;

        showLoading(true);
        input.disabled = true;

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
                renderResult(data);

                // 🟢 Actualizar lista de archivos si está disponible
                if (data.code_files) {
                    updateCodeFiles(data.code_files);
                }

                // 📝 Actualizar información de notas
                if (data.hasOwnProperty('notes_exist')) {
                    updateNotesInfo(data.notes_exist, data.notes_count);
                }

                // 📝 Si es save_code o code_gen, recarga manualmente
                if (data.tool === "save_code" || data.tool === "code_gen") {
                    setTimeout(fetchFiles, 500);
                }

                // 📝 Si es comando de notas, actualizar info de notas
                if (data.tool === "note") {
                    setTimeout(fetchFiles, 300);
                }

                // 🔔 Si es comando de notificaciones, actualizar estado
                if (data.tool === "notifications") {
                    setTimeout(() => {
                        checkNotifications();
                        updateNotificationStatus();
                    }, 1000);
                }
            } else {
                const errorData = await response.json().catch(() => ({ detail: "Error desconocido" }));
                renderError(errorData.detail || "Ocurrió un error inesperado.");
            }

        } catch (error) {
            console.error("Error en fetch:", error);
            renderError("No se pudo conectar con el servidor.");
        } finally {
            showLoading(false);
            input.disabled = false;
            input.value = '';
        }
    });

    // 🔔 Inicializar sistema de notificaciones
    async function initializeNotificationSystem() {
        try {
            // Registrar usuario
            const response = await fetch('/notifications/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
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
                    
                    // Iniciar verificación periódica de notificaciones
                    startNotificationPolling();
                    updateNotificationStatus("✅ Conectado");
                } else {
                    console.error("Error registrando usuario:", data.error);
                    updateNotificationStatus("❌ Error");
                }
            }
        } catch (error) {
            console.error("Error inicializando notificaciones:", error);
            updateNotificationStatus("⚠️ Offline");
        }
    }

    // 🔔 Iniciar polling de notificaciones
    function startNotificationPolling() {
        if (notificationCheckInterval) {
            clearInterval(notificationCheckInterval);
        }

        // Verificar inmediatamente
        checkNotifications();

        // Verificar cada 30 segundos
        notificationCheckInterval = setInterval(checkNotifications, 30000);
    }

    // 🔔 Verificar notificaciones pendientes
    async function checkNotifications() {
        if (!userId) return;

        try {
            const response = await fetch(`/notifications/user/${userId}`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.notifications && data.notifications.length > 0) {
                    console.log(`📨 ${data.notifications.length} nuevas notificaciones`);
                    
                    // Mostrar notificaciones en el historial
                    data.notifications.forEach(notification => {
                        showNotificationInHistory(notification);
                        
                        // Mostrar notificación nativa del navegador si está soportado
                        showBrowserNotification(notification);
                    });
                }
            }
        } catch (error) {
            console.error("Error verificando notificaciones:", error);
        }
    }

    // 🔔 Mostrar notificación en el historial
    function showNotificationInHistory(notification) {
        const entry = document.createElement('div');
        entry.className = 'entry p-4 bg-blue-50 dark:bg-blue-900 rounded-lg shadow-md border-l-4 border-blue-500 cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-800 transition-colors';
        
        const icon = getNotificationIcon(notification.type);
        const timeStr = new Date(notification.timestamp).toLocaleString();
        
        // Obtener URL si está disponible
        const notifData = notification.data || {};
        const url = notifData.url || null;
        
        // Crear contenido clickeable si hay URL
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
                    <div class="text-xs text-blue-600 dark:text-blue-400 mt-2 flex justify-between items-center">
                        <span>${timeStr} • ${notification.type}</span>
                        ${url ? '<span class="text-blue-500">🔗 Click para abrir</span>' : ''}
                    </div>
                    ${createNotificationDetails(notifData)}
                </div>
            </div>
        `;
        
        // Hacer toda la notificación clickeable si hay URL
        if (url) {
            entry.addEventListener('click', (e) => {
                // Prevenir doble-click si ya clickearon el enlace
                if (e.target.tagName === 'A') return;
                
                window.open(url, '_blank', 'noopener,noreferrer');
            });
            
            // Cambiar cursor y añadir efecto hover
            entry.style.cursor = 'pointer';
        }
        
        historyDiv.prepend(entry);
        
        // Auto-scroll para mostrar la nueva notificación
        entry.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // 🔔 Crear detalles adicionales de la notificación
    function createNotificationDetails(data) {
        if (!data || Object.keys(data).length === 0) return '';
        
        let details = '';
        
        // Detalles para papers científicos
        if (data.authors && data.authors.length > 0) {
            const authors = data.authors.slice(0, 3).join(', ');
            details += `<div class="text-xs text-blue-600 dark:text-blue-400 mt-1">👥 ${authors}${data.authors.length > 3 ? '...' : ''}</div>`;
        }
        
        if (data.category) {
            details += `<div class="text-xs text-blue-600 dark:text-blue-400">📂 ${data.category}</div>`;
        }
        
        if (data.abstract) {
            details += `<div class="text-xs text-blue-600 dark:text-blue-400 mt-1 italic">${data.abstract.substring(0, 150)}...</div>`;
        }
        
        // Detalles para patentes
        if (data.app_number) {
            details += `<div class="text-xs text-blue-600 dark:text-blue-400 mt-1">🏢 ${data.app_number}</div>`;
        }
        
        if (data.inventors && data.inventors.length > 0) {
            const inventors = data.inventors.slice(0, 2).join(', ');
            details += `<div class="text-xs text-blue-600 dark:text-blue-400">👨‍🔬 ${inventors}${data.inventors.length > 2 ? '...' : ''}</div>`;
        }
        
        if (data.keyword) {
            details += `<div class="text-xs text-blue-600 dark:text-blue-400">🔍 Keyword: ${data.keyword}</div>`;
        }
        
        // Agregar enlaces alternativos para patentes
        if (data.app_number && data.app_number.startsWith('US')) {
            const appNumber = data.app_number.replace('US', '');
            details += `<div class="text-xs mt-2">
                <span class="text-blue-600 dark:text-blue-400">🔍 Enlaces alternativos: </span>
                <a href="https://patents.google.com/?q=${data.app_number}" target="_blank" class="text-blue-500 hover:underline">Google Patents</a> • 
                <a href="https://worldwide.espacenet.com/patent/search/family/simple?q=${data.app_number}" target="_blank" class="text-blue-500 hover:underline">Espacenet</a>
            </div>`;
        }
        
        // Agregar enlaces alternativos para papers
        if (data.title && (data.category || data.keyword)) {
            const searchTitle = encodeURIComponent(data.title);
            details += `<div class="text-xs mt-2">
                <span class="text-blue-600 dark:text-blue-400">🔍 Buscar también en: </span>
                <a href="https://scholar.google.com/scholar?q=${searchTitle}" target="_blank" class="text-blue-500 hover:underline">Google Scholar</a> • 
                <a href="https://www.semanticscholar.org/search?q=${searchTitle}" target="_blank" class="text-blue-500 hover:underline">Semantic Scholar</a>
            </div>`;
        }
        
        return details ? `<div class="mt-2 pt-2 border-t border-blue-200 dark:border-blue-700">${details}</div>` : '';
    }

    // 🔔 Mostrar notificación nativa del navegador (también clickeable)
    function showBrowserNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const icon = getNotificationIcon(notification.type);
            const notifData = notification.data || {};
            const url = notifData.url;
            
            const browserNotif = new Notification(notification.title, {
                body: notification.message,
                icon: '/static/favicon.ico',
                tag: `${notification.type}_${notification.id}`,
                badge: '/static/favicon.ico',
                data: { url: url } // Pasar URL en data
            });
            
            // Manejar click en notificación nativa
            if (url) {
                browserNotif.onclick = function(event) {
                    event.preventDefault();
                    window.focus();
                    window.open(url, '_blank', 'noopener,noreferrer');
                    browserNotif.close();
                };
            } else {
                browserNotif.onclick = function(event) {
                    event.preventDefault();
                    window.focus();
                    browserNotif.close();
                };
            }
        }
    }

    // 🔔 Obtener icono para tipo de notificación
    function getNotificationIcon(type) {
        const icons = {
            'email': '📧',
            'patent': '🔬',
            'paper': '📚',
            'test': '🧪'
        };
        return icons[type] || '🔔';
    }

    // 🔔 Actualizar estado de notificaciones en la UI
    function updateNotificationStatus(status = null) {
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

    // 🔔 Funciones globales para botones de notificaciones
    window.configureNotifications = function() {
        const command = `
🔔 **Comandos de Configuración de Notificaciones:**

**Para activar:**
• activar emails
• activar patentes  
• activar papers

**Para configurar búsquedas:**
• keywords patentes: AI, machine learning
• keywords papers: neural networks, deep learning
• categories: cs.AI, cs.LG, cs.CV

**Para verificar:**
• status
• debug

**Para probar (con enlaces clickeables):**
• test

**Ejemplo completo:**
1. activar papers
2. keywords papers: artificial intelligence
3. test

💡 **Las notificaciones son clickeables** - haz click para abrir enlaces
        `.trim();
        
        input.value = 'status';
        input.focus();
        
        // Mostrar ayuda en el historial
        const helpEntry = document.createElement('div');
        helpEntry.className = 'entry p-4 bg-yellow-50 dark:bg-yellow-900 rounded-lg shadow-md';
        helpEntry.innerHTML = `
            <div class="font-bold text-yellow-800 dark:text-yellow-200 mb-2">
                📋 Guía de Configuración de Notificaciones
            </div>
            <pre class="text-sm text-yellow-700 dark:text-yellow-300 whitespace-pre-wrap">${escapeHtml(command)}</pre>
        `;
        historyDiv.prepend(helpEntry);
    };

    window.testNotifications = function() {
        if (userId) {
            input.value = 'test';
            form.dispatchEvent(new Event('submit'));
        } else {
            alert('Sistema de notificaciones no inicializado');
        }
    };

    // Solicitar permisos de notificación del navegador
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            console.log(`Permisos de notificación: ${permission}`);
        });
    }

    // 📋 Mostrar el resultado en el historial
    function renderResult(data) {
        let resultHtml = '';

        switch (data.result_type) {
            case 'list':
                resultHtml = data.result_data.map(item => `
                    <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg shadow-sm">
                        <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="text-blue-600 dark:text-blue-400 font-semibold hover:underline">${item.title}</a>
                        <p class="text-sm mt-1 text-gray-600 dark:text-gray-400">${item.snippet}</p>
                    </div>
                `).join('');
                break;

            case 'open_url':
                setTimeout(() => {
                    window.open(data.url, '_blank', 'noopener,noreferrer');
                }, 500);
                resultHtml = `
                    <div class="p-4 bg-blue-50 dark:bg-blue-800 rounded-lg shadow-sm">
                        <p class="text-blue-800 dark:text-blue-200 font-semibold">${data.result_data}</p>
                        <button onclick="window.open('${data.url}', '_blank', 'noopener,noreferrer')" 
                                class="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                            🔗 Abrir ${data.url}
                        </button>
                    </div>
                `;
                break;

            case 'download_file':
                resultHtml = `
                    <div class="p-4 bg-green-50 dark:bg-green-800 rounded-lg shadow-sm">
                        <p class="text-green-800 dark:text-green-200 font-semibold">${data.result_data}</p>
                        <a href="${data.file_path}" download="${data.display_name}"
                           class="mt-2 inline-block px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">
                            📁 Descargar ${data.display_name}
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
                <span class="text-blue-600">🔧 Herramienta:</span> ${data.tool}
            </div>
            <div class="mt-4">
                <span class="font-bold text-gray-800 dark:text-gray-200">📦 Resultado:</span>
                <div class="mt-2">${resultHtml}</div>
            </div>
        `;
        historyDiv.prepend(entry);
    }

    function renderError(message) {
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
        if (loadingIndicator) {
            loadingIndicator.classList.toggle('hidden', !show);
        }
    }

    // 📁 Obtener y renderizar archivos guardados
    async function fetchFiles() {
        try {
            const response = await fetch('/files');
            const data = await response.json();
            updateCodeFiles(data.code_files || []);
            updateNotesInfo(data.notes_exist || false, data.notes_count || 0);
        } catch (error) {
            console.error("Error al cargar archivos:", error);
        }
    }

    // 📁 Actualizar lista lateral de archivos de código
    function updateCodeFiles(files) {
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

    // 👁️ Ver contenido de archivo
    async function viewFileContent(filename) {
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

    // 📄 Mostrar modal con contenido del archivo
    function showFileModal(filename, content) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50';

        modal.innerHTML = `
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg max-w-4xl w-full max-h-[90vh] flex flex-col">
                <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
                    <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200">📄 ${filename}</h3>
                    <button class="close-file-modal text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-2xl">×</button>
                </div>
                <div class="flex-1 overflow-auto p-4">
                    <pre class="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto"><code>${escapeHtml(content)}</code></pre>
                </div>
                <div class="flex justify-end space-x-2 p-4 border-t border-gray-200 dark:border-gray-700">
                    <a href="/download/code/${filename}" download="${filename}" 
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

    // 📝 Actualizar información de notas
    function updateNotesInfo(notesExist, notesCount) {
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
                <div id="notes-list" class="space-y-2"></div>
                <button onclick="createNewNote()" 
                        class="mt-2 w-full text-center p-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-lg transition-colors">
                    ➕ Crear nueva nota
                </button>
            `;
            fetchNotes();
        }
    }

    // 📝 Traer y mostrar todas las notas
    async function fetchNotes() {
        const listEl = document.getElementById('notes-list');
        if (!listEl) return;

        try {
            const response = await fetch('/view/notes');
            if (response.ok) {
                const data = await response.json();
                listEl.innerHTML = '';

                // Mostrar botones para ver y descargar todas las notas
                const notesContainer = document.createElement('div');
                notesContainer.className = "p-2 bg-gray-100 dark:bg-gray-700 rounded-lg flex justify-between items-center";
                
                notesContainer.innerHTML = `
                    <span class="text-gray-800 dark:text-gray-100 text-sm">📝 Archivo de notas (${data.notes_count} notas)</span>
                    <div class="flex space-x-1">
                        <button onclick="viewAllNotes()" class="text-gray-600 hover:text-blue-600 text-lg" title="Ver todas las notas">👁️</button>
                        <a href="/download/notes" download="mis_notas.txt" class="text-gray-600 hover:text-green-600 text-lg" title="Descargar notas">⬇️</a>
                    </div>
                `;
                
                listEl.appendChild(notesContainer);
            } else {
                listEl.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400 italic">Error al cargar notas</p>';
            }
        } catch (err) {
            console.error("Error al cargar notas:", err);
            listEl.innerHTML = '<p class="text-sm text-red-500 italic">Error de conexión</p>';
        }
    }

    // 📝 Ver todas las notas en modal
    window.viewAllNotes = async function() {
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

    // 📝 Mostrar modal con todas las notas
    function showNotesModal(content, notesCount) {
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

    // 📝 Crear nueva nota
    window.createNewNote = function() {
        const noteText = prompt("Escribe tu nota:");
        if (noteText && noteText.trim()) {
            input.value = `guardar: ${noteText.trim()}`;
            form.dispatchEvent(new Event('submit'));
        }
    }

    // 🔒 Escape para prevenir XSS
    function escapeHtml(str) {
        if (typeof str !== 'string') return str;
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
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
// Agregar estas funciones al final del archivo script.js

// ========== FUNCIONES DE GESTIÓN DE DOCUMENTOS ==========

// Variables globales para documentos
let currentDocumentFiles = {
    templates: [],
    data_files: [],
    output_files: []
};

// Función para mostrar/ocultar la sección de documentos
window.toggleDocumentSection = function() {
    const section = document.getElementById('document-section');
    const button = document.getElementById('document-toggle');
    
    if (section.classList.contains('hidden')) {
        section.classList.remove('hidden');
        button.textContent = '📄 Documentos ▼';
        loadDocumentFiles();
    } else {
        section.classList.add('hidden');
        button.textContent = '📄 Documentos ▶';
    }
};

// Cargar lista de archivos de documentos
async function loadDocumentFiles() {
    try {
        const response = await fetch('/files/documents');
        const data = await response.json();
        
        currentDocumentFiles = {
            templates: data.templates || [],
            data_files: data.data_files || [],
            output_files: data.output_files || []
        };
        
        updateDocumentFilesUI();
    } catch (error) {
        console.error('Error cargando archivos de documentos:', error);
    }
}

// Actualizar la UI con los archivos de documentos
function updateDocumentFilesUI() {
    updateTemplatesList();
    updateDataFilesList();
    updateOutputFilesList();
}

// Actualizar lista de plantillas
function updateTemplatesList() {
    const container = document.getElementById('templates-list');
    if (!container) return;
    
    if (currentDocumentFiles.templates.length === 0) {
        container.innerHTML = `
            <p class="text-sm text-gray-500 dark:text-gray-400 italic text-center p-4">
                📄 No hay plantillas. Sube una plantilla para empezar.
            </p>
        `;
        return;
    }
    
    container.innerHTML = currentDocumentFiles.templates.map(file => `
        <div class="flex justify-between items-center p-3 bg-blue-50 dark:bg-blue-900 rounded-lg mb-2 border border-blue-200 dark:border-blue-700">
            <div class="flex-1">
                <div class="font-medium text-blue-800 dark:text-blue-200">${escapeHtml(file.name)}</div>
                <div class="text-xs text-blue-600 dark:text-blue-400">
                    ${formatFileSize(file.size)} • ${formatDate(file.modified)}
                </div>
            </div>
            <div class="flex space-x-1 ml-2">
                <button onclick="analyzeTemplate('${escapeHtml(file.name)}')" 
                        class="text-blue-600 hover:text-blue-800 text-lg p-1" 
                        title="Analizar plantilla">🔍</button>
                <button onclick="createExampleData('${escapeHtml(file.name)}')" 
                        class="text-green-600 hover:text-green-800 text-lg p-1" 
                        title="Crear datos de ejemplo">📋</button>
                <a href="/download/template/${encodeURIComponent(file.name)}" 
                   class="text-gray-600 hover:text-gray-800 text-lg p-1" 
                   title="Descargar">⬇️</a>
                <button onclick="deleteTemplate('${escapeHtml(file.name)}')" 
                        class="text-red-600 hover:text-red-800 text-lg p-1" 
                        title="Eliminar">🗑️</button>
            </div>
        </div>
    `).join('');
}

// Actualizar lista de archivos de datos
function updateDataFilesList() {
    const container = document.getElementById('data-files-list');
    if (!container) return;
    
    if (currentDocumentFiles.data_files.length === 0) {
        container.innerHTML = `
            <p class="text-sm text-gray-500 dark:text-gray-400 italic text-center p-4">
                📊 No hay archivos de datos. Crea datos de ejemplo o sube un archivo.
            </p>
        `;
        return;
    }
    
    container.innerHTML = currentDocumentFiles.data_files.map(file => `
        <div class="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900 rounded-lg mb-2 border border-green-200 dark:border-green-700">
            <div class="flex-1">
                <div class="font-medium text-green-800 dark:text-green-200">${escapeHtml(file.name)}</div>
                <div class="text-xs text-green-600 dark:text-green-400">
                    ${formatFileSize(file.size)} • ${formatDate(file.modified)}
                </div>
            </div>
            <div class="flex space-x-1 ml-2">
                <button onclick="previewDataFile('${escapeHtml(file.name)}')" 
                        class="text-green-600 hover:text-green-800 text-lg p-1" 
                        title="Ver contenido">👁️</button>
                <a href="/download/data/${encodeURIComponent(file.name)}" 
                   class="text-gray-600 hover:text-gray-800 text-lg p-1" 
                   title="Descargar">⬇️</a>
                <button onclick="deleteDataFile('${escapeHtml(file.name)}')" 
                        class="text-red-600 hover:text-red-800 text-lg p-1" 
                        title="Eliminar">🗑️</button>
            </div>
        </div>
    `).join('');
}

// Actualizar lista de documentos generados
function updateOutputFilesList() {
    const container = document.getElementById('output-files-list');
    if (!container) return;
    
    if (currentDocumentFiles.output_files.length === 0) {
        container.innerHTML = `
            <p class="text-sm text-gray-500 dark:text-gray-400 italic text-center p-4">
                📁 No hay documentos generados aún.
            </p>
        `;
        return;
    }
    
    container.innerHTML = currentDocumentFiles.output_files.map(file => `
        <div class="flex justify-between items-center p-3 bg-yellow-50 dark:bg-yellow-900 rounded-lg mb-2 border border-yellow-200 dark:border-yellow-700">
            <div class="flex-1">
                <div class="font-medium text-yellow-800 dark:text-yellow-200">${escapeHtml(file.name)}</div>
                <div class="text-xs text-yellow-600 dark:text-yellow-400">
                    ${formatFileSize(file.size)} • ${formatDate(file.modified)}
                </div>
            </div>
            <div class="flex space-x-1 ml-2">
                <a href="/download/output/${encodeURIComponent(file.name)}" 
                   class="text-yellow-600 hover:text-yellow-800 text-lg p-1" 
                   title="Descargar documento generado">📥</a>
            </div>
        </div>
    `).join('');
}

// Funciones de acción para documentos
window.analyzeTemplate = function(filename) {
    input.value = `analizar: ${filename}`;
    form.dispatchEvent(new Event('submit'));
};

window.createExampleData = function(filename) {
    input.value = `crear ejemplo datos: ${filename}`;
    form.dispatchEvent(new Event('submit'));
};

window.deleteTemplate = async function(filename) {
    if (!confirm(`¿Estás seguro de que quieres eliminar la plantilla "${filename}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/delete/template/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessMessage(result.message);
            loadDocumentFiles(); // Recargar lista
        } else {
            showErrorMessage(result.error || 'Error eliminando plantilla');
        }
    } catch (error) {
        showErrorMessage(`Error eliminando plantilla: ${error.message}`);
    }
};

window.deleteDataFile = async function(filename) {
    if (!confirm(`¿Estás seguro de que quieres eliminar el archivo de datos "${filename}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/delete/data/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessMessage(result.message);
            loadDocumentFiles(); // Recargar lista
        } else {
            showErrorMessage(result.error || 'Error eliminando archivo');
        }
    } catch (error) {
        showErrorMessage(`Error eliminando archivo: ${error.message}`);
    }
};

window.previewDataFile = function(filename) {
    // Por ahora, solo mostrar comando para ver el archivo
    input.value = `listar datos`;
    showInfoMessage(`Para ver el contenido de ${filename}, edítalo manualmente o recrea los datos de ejemplo.`);
};

// Funciones de subida de archivos
window.uploadTemplate = function() {
    const fileInput = document.getElementById('template-file-input');
    if (!fileInput.files.length) {
        showErrorMessage('Selecciona un archivo de plantilla');
        return;
    }
    
    const file = fileInput.files[0];
    const allowedExtensions = ['.docx', '.txt', '.pdf'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        showErrorMessage(`Formato no soportado. Use: ${allowedExtensions.join(', ')}`);
        return;
    }
    
    uploadFile('/upload/template', file, 'Subiendo plantilla...');
};

window.uploadDataFile = function() {
    const fileInput = document.getElementById('data-file-input');
    if (!fileInput.files.length) {
        showErrorMessage('Selecciona un archivo de datos');
        return;
    }
    
    const file = fileInput.files[0];
    const allowedExtensions = ['.json', '.csv', '.xlsx', '.txt'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        showErrorMessage(`Formato no soportado. Use: ${allowedExtensions.join(', ')}`);
        return;
    }
    
    uploadFile('/upload/data', file, 'Subiendo archivo de datos...');
};

// Función genérica para subir archivos
async function uploadFile(endpoint, file, loadingMessage) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showInfoMessage(loadingMessage);
        
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessMessage(result.message);
            if (result.next_step) {
                showInfoMessage(`💡 Siguiente paso: ${result.next_step}`);
            }
            loadDocumentFiles(); // Recargar lista
            
            // Limpiar input
            if (endpoint.includes('template')) {
                document.getElementById('template-file-input').value = '';
            } else {
                document.getElementById('data-file-input').value = '';
            }
        } else {
            showErrorMessage(result.error || 'Error subiendo archivo');
        }
    } catch (error) {
        showErrorMessage(`Error subiendo archivo: ${error.message}`);
    }
}

// Funciones de utilidad para la UI de documentos
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDate(timestamp) {
    return new Date(timestamp * 1000).toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Funciones para mostrar mensajes
function showSuccessMessage(message) {
    const entry = document.createElement('div');
    entry.className = 'entry p-4 bg-green-100 dark:bg-green-800 rounded-lg shadow-md border-l-4 border-green-500';
    entry.innerHTML = `
        <div class="text-green-800 dark:text-green-200 font-bold">
            ✅ ${escapeHtml(message)}
        </div>
    `;
    historyDiv.prepend(entry);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        if (entry.parentNode) {
            entry.parentNode.removeChild(entry);
        }
    }, 5000);
}

function showErrorMessage(message) {
    const entry = document.createElement('div');
    entry.className = 'entry p-4 bg-red-100 dark:bg-red-800 rounded-lg shadow-md border-l-4 border-red-500';
    entry.innerHTML = `
        <div class="text-red-800 dark:text-red-200 font-bold">
            ❌ ${escapeHtml(message)}
        </div>
    `;
    historyDiv.prepend(entry);
}

function showInfoMessage(message) {
    const entry = document.createElement('div');
    entry.className = 'entry p-4 bg-blue-100 dark:bg-blue-800 rounded-lg shadow-md border-l-4 border-blue-500';
    entry.innerHTML = `
        <div class="text-blue-800 dark:text-blue-200 font-bold">
            💡 ${escapeHtml(message)}
        </div>
    `;
    historyDiv.prepend(entry);
    
    // Auto-remover después de 7 segundos
    setTimeout(() => {
        if (entry.parentNode) {
            entry.parentNode.removeChild(entry);
        }
    }, 7000);
}

// Funciones para comandos rápidos de documentos
window.showDocumentHelp = function() {
    input.value = 'document_filler help';
    form.dispatchEvent(new Event('submit'));
};

window.listTemplates = function() {
    input.value = 'listar plantillas';
    form.dispatchEvent(new Event('submit'));
};

window.listDataFiles = function() {
    input.value = 'listar datos';
    form.dispatchEvent(new Event('submit'));
};

// Función para crear un flujo completo de ejemplo
window.startDocumentWalkthrough = function() {
    const message = `
🚀 **TUTORIAL RÁPIDO - SISTEMA DE DOCUMENTOS**

**Pasos para tu primer documento:**

1️⃣ **Sube una plantilla**
   • Crea un archivo .docx con marcadores como {{nombre}}, {{empresa}}
   • Súbelo usando el botón "Subir Plantilla"

2️⃣ **Analiza la plantilla**
   • Comando: analizar: mi_plantilla.docx

3️⃣ **Crea datos de ejemplo**
   • Comando: crear ejemplo datos: mi_plantilla.docx

4️⃣ **Edita los datos**
   • Descarga el JSON generado
   • Edita con tus datos reales
   • Súbelo de nuevo

5️⃣ **Rellena el documento**
   • Comando: rellenar: mi_plantilla.docx con mis_datos.json

**¿Empezamos? Sube tu primera plantilla** 📄
    `;
    
    showInfoMessage(message.trim());
};

// Inicializar al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    // Solo cargar si la sección existe
    if (document.getElementById('document-section')) {
        // No cargar automáticamente, solo cuando se abra la sección
        console.log('📄 Sistema de documentos inicializado');
    }
});

// Agregar funciones para manejar comandos de documentos en el envío del formulario
const originalSubmitHandler = form.onsubmit;

// Interceptar comandos de documentos para recargar archivos después
form.addEventListener('submit', async function(e) {
    const userInput = input.value.trim().toLowerCase();
    
    // Si es un comando de documentos, recargar archivos después de la respuesta
    if (userInput.includes('rellenar:') || 
        userInput.includes('crear ejemplo datos:') || 
        userInput.includes('analizar:')) {
        
        // Esperar un poco y luego recargar
        setTimeout(() => {
            loadDocumentFiles();
        }, 2000);
    }
});

console.log('📄 Funciones de gestión de documentos cargadas');