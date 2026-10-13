/**
 * app.js — Utilitários globais, formatação, toasts e navegação.
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
    toast.innerHTML = `
        <span class="toast-msg">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Destacar página atual na navegação
function setupNavigation() {
    const path = window.location.pathname.replace(/\/$/, "") || "/";
    const navLinks = document.querySelectorAll(".nav-link");

    navLinks.forEach((link) => {
        const href = link.getAttribute("href").replace(/\/$/, "");
        if (
            (path === "" || path === "/" || path === "/index.html") &&
            (href === "/" || href === "/index.html")
        ) {
            link.classList.add("active");
        } else if (href !== "/" && path.includes(href)) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
}

// Iniciar relógio no header
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

document.addEventListener("DOMContentLoaded", () => {
    setupNavigation();
    setupLiveClock();
});
