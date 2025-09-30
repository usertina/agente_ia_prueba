import { initFormHandler } from "/static/js/form-handler.js";


document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando aplicación...');

    // Inicializar formulario
    initFormHandler();

    // Cargar archivos si existe la función
    if (window.fetchFiles) window.fetchFiles();

    // Cleanup al cerrar
    window.addEventListener('beforeunload', () => { 
        if (window.notificationCheckInterval) clearInterval(window.notificationCheckInterval); 
    });

    console.log('✅ Script principal inicializado completamente');
});
