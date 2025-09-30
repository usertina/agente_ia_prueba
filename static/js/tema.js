// ========== MÓDULO DE TEMA (MODO OSCURO/CLARO) ==========

/**
 * Inicializa el sistema de temas
 */
function initThemeSystem() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');

    if (!themeToggle || !themeIcon) {
        console.warn('Elementos de tema no encontrados');
        return;
    }

    // Configurar tema inicial
    setupInitialTheme(themeIcon);

    // Event listener para cambiar tema
    themeToggle.addEventListener('click', () => {
        toggleTheme(themeIcon);
    });
}

/**
 * Configura el tema inicial basado en preferencias
 */
function setupInitialTheme(themeIcon) {
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && prefersDark)) {
        document.documentElement.classList.add('dark');
        if (themeIcon) themeIcon.textContent = '☀️';
    } else {
        document.documentElement.classList.remove('dark');
        if (themeIcon) themeIcon.textContent = '🌙';
    }
}

/**
 * Alterna entre tema claro y oscuro
 */
function toggleTheme(themeIcon) {
    if (document.documentElement.classList.contains('dark')) {
        document.documentElement.classList.remove('dark');
        localStorage.theme = 'light';
        if (themeIcon) themeIcon.textContent = '🌙';
    } else {
        document.documentElement.classList.add('dark');
        localStorage.theme = 'dark';
        if (themeIcon) themeIcon.textContent = '☀️';
    }
}

/**
 * Obtiene el tema actual
 */
function getCurrentTheme() {
    return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
}

/**
 * Establece un tema específico
 */
function setTheme(theme) {
    const themeIcon = document.getElementById('theme-icon');
    
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
        localStorage.theme = 'dark';
        if (themeIcon) themeIcon.textContent = '☀️';
    } else {
        document.documentElement.classList.remove('dark');
        localStorage.theme = 'light';
        if (themeIcon) themeIcon.textContent = '🌙';
    }
}

// Exportar funciones globales
window.getCurrentTheme = getCurrentTheme;
window.setTheme = setTheme;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initThemeSystem();
    console.log('🌓 Sistema de temas inicializado');
});

console.log('🌓 Módulo de temas cargado');