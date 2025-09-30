// ========== MÓDULO DE GUÍA Y AYUDA ==========

/**
 * Inicializa el sistema de guía y ayuda
 */
function initGuideSystem() {
    const guideKeywordsModal = document.getElementById("guide-keywords-modal");
    const guideButton = document.getElementById("guide-button");
    const closeGuideKeywordsButton = document.getElementById("close-guide-keywords-modal");

    if (!guideKeywordsModal || !guideButton || !closeGuideKeywordsButton) {
        console.warn('Elementos de guía no encontrados');
        return;
    }

    // Abrir modal
    guideButton.addEventListener("click", () => {
        guideKeywordsModal.classList.remove("hidden");
    });

    // Cerrar modal
    closeGuideKeywordsButton.addEventListener("click", () => {
        guideKeywordsModal.classList.add("hidden");
    });

    // Cerrar al hacer click fuera
    guideKeywordsModal.addEventListener("click", (e) => {
        if (e.target === guideKeywordsModal) {
            guideKeywordsModal.classList.add("hidden");
        }
    });

    // Inicializar sistema de tabs
    initTabSystem();
}

/**
 * Inicializa el sistema de pestañas
 */
function initTabSystem() {
    const tabButtons = document.querySelectorAll(".tab-button");

    if (tabButtons.length === 0) return;

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.dataset.tab;
            switchTab(targetTab);
        });
    });

    // Activar primera pestaña por defecto
    switchTab('tools');
}

/**
 * Cambia entre pestañas
 */
function switchTab(targetTab) {
    const tabContents = document.querySelectorAll(".tab-content");
    const tabButtons = document.querySelectorAll(".tab-button");

    // Ocultar todos los contenidos
    tabContents.forEach(tc => tc.classList.add("hidden"));
    
    // Resetear estilos de botones
    tabButtons.forEach(b => {
        b.classList.remove("active", "bg-blue-100", "dark:bg-blue-700");
        b.classList.add("bg-gray-100", "dark:bg-gray-600");
    });
    
    // Mostrar contenido seleccionado
    const targetContent = document.getElementById("tab-" + targetTab);
    if (targetContent) {
        targetContent.classList.remove("hidden");
    }
    
    // Activar botón seleccionado
    const activeBtn = document.querySelector(`.tab-button[data-tab="${targetTab}"]`);
    if (activeBtn) {
        activeBtn.classList.remove("bg-gray-100", "dark:bg-gray-600");
        activeBtn.classList.add("active", "bg-blue-100", "dark:bg-blue-700");
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initGuideSystem();
    console.log('📘 Sistema de guía inicializado');
});

console.log('📘 Módulo de guía cargado');