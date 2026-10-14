/**
 * app.js — Utilitários globais, formatação, toasts, navegação e alternador de tema.
 */

// Timestamp final de referência da base sintética do PoC (~22/09/2026)
const POC_FIM_MS = 1790121300000;

function formatDateTime(timestampMs) {
    if (!timestampMs) return "--";
    const date = new Date(timestampMs);
    return date.toLocaleString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function formatDateOnly(timestampMs) {
    if (!timestampMs) return "--";
    const date = new Date(timestampMs);
    return date.toLocaleDateString("pt-BR");
}

function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) return "--";
    return Number(num).toFixed(decimals);
}

function showToast(message, type = "info") {
    let container = document.getElementById("toastContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "toastContainer";
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-msg">${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Destacar estritamente a página atual na navegação
function setupNavigation() {
    let currentPath = window.location.pathname.toLowerCase();
    if (currentPath === "" || currentPath === "/" || currentPath.endsWith("/index.html")) {
        currentPath = "/";
    } else {
        currentPath = currentPath.replace(/\.html$/, "").replace(/\/$/, "");
    }

    const navLinks = document.querySelectorAll(".nav-link");

    navLinks.forEach((link) => {
        let linkHref = (link.getAttribute("href") || "").toLowerCase();
        if (linkHref === "" || linkHref === "/" || linkHref.endsWith("/index.html")) {
            linkHref = "/";
        } else {
            linkHref = linkHref.replace(/\.html$/, "").replace(/\/$/, "");
        }

        if (currentPath === linkHref) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
}

// Relógio em tempo real no header
function setupLiveClock() {
    const clockEl = document.getElementById("liveClock");
    if (!clockEl) return;

    function update() {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });
    }
    update();
    setInterval(update, 1000);
}

// ============================================================
// Gerenciamento de Tema (Escuro / Claro)
// ============================================================

const ICONS = {
    sun: `<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`,
    moon: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`
};

function getSavedTheme() {
    return localStorage.getItem("ninfa_theme") || "dark";
}

function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("ninfa_theme", theme);

    const btn = document.getElementById("themeToggleBtn");
    if (btn) {
        // Se o tema ativo for dark, exibe o sol para mudar para claro; se for light, exibe a lua
        btn.innerHTML = theme === "dark" ? ICONS.sun : ICONS.moon;
        btn.setAttribute("title", theme === "dark" ? "Alternar para Tema Claro" : "Alternar para Tema Escuro");
    }

    // Disparar evento para componentes que dependem do tema (ex: ApexCharts)
    window.dispatchEvent(new CustomEvent("themeChanged", { detail: { theme } }));
}

function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    applyTheme(next);
}

// Inicializar antes da renderização para evitar flickering
(function initThemeEarly() {
    const saved = getSavedTheme();
    document.documentElement.setAttribute("data-theme", saved);
})();

document.addEventListener("DOMContentLoaded", () => {
    setupNavigation();
    setupLiveClock();

    // Configurar botão de tema
    const btn = document.getElementById("themeToggleBtn");
    if (btn) {
        btn.addEventListener("click", toggleTheme);
        const current = getSavedTheme();
        btn.innerHTML = current === "dark" ? ICONS.sun : ICONS.moon;
        btn.setAttribute("title", current === "dark" ? "Alternar para Tema Claro" : "Alternar para Tema Escuro");
    }
});
