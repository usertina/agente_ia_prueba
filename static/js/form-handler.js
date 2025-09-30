import { abrirWeb } from "/static/js/abrir_web.js";
import { renderResult } from "/static/js/rendering.js";

export function initFormHandler() {
    const form = document.getElementById('commandForm');
    const input = document.getElementById('user_input');

    if (!form || !input) {
        console.error('❌ Elementos críticos del formulario no encontrados');
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userInput = input.value.trim();
        if (!userInput) return;

        showLoading(true);
        input.disabled = true;

        try {
            // Abrir URLs directamente
            if (userInput.match(/^(https?:\/\/)?(www\.)?\w+\.\w+/i)) {
                abrirWeb(userInput);
                input.value = '';
                showLoading(false);
                input.disabled = false;
                return;
            }

            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ 'user_input': userInput })
            });

            if (response.ok) {
                const data = await response.json();
                renderResult(data);

                // Actualizar archivos si es código
                if (['save_code', 'code_gen', 'note'].includes(data.tool)) {
                    setTimeout(() => window.fetchFiles?.(), 500);
                }

                // Si es herramienta de notificaciones
                if (data.tool === "notifications") {
                    setTimeout(() => {
                        window.checkNotifications?.();
                        window.updateNotificationStatus?.();
                    }, 1000);
                }

                // RMN Spectrum Cleaner
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
}
