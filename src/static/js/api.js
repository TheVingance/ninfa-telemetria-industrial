/**
 * api.js — Cliente de requisições HTTP para a API Ninfa Telemetria.
 */

const API_BASE = "";

const api = {
    async request(endpoint, options = {}) {
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                headers: {
                    "Content-Type": "application/json",
                    ...options.headers,
                },
                ...options,
            });

            if (!res.ok) {
                const errBody = await res.json().catch(() => ({}));
                const msg = errBody.detail || `Erro HTTP ${res.status}: ${res.statusText}`;
                throw new Error(msg);
            }

            return await res.json();
        } catch (err) {
            console.error(`Falha na requisição [${endpoint}]:`, err);
            throw err;
        }
    },

    // Equipamentos
    async getEquipments() {
        return this.request("/api/equipments");
    },

    async getFactoryOverview() {
        return this.request("/api/equipments/overview");
    },

    async getEquipment(id) {
        return this.request(`/api/equipments/${id}`);
    },

    // Telemetria & Séries Temporais
    async getSeries(noId, startMs = null, endMs = null, bucket = "auto") {
        const params = new URLSearchParams({ no_id: noId, bucket });
        if (startMs) params.append("start_ms", startMs);
        if (endMs) params.append("end_ms", endMs);
        return this.request(`/api/telemetry/series?${params.toString()}`);
    },

    async getPredictive(noId, windowHours = 72, endMs = null) {
        const params = new URLSearchParams({ no_id: noId, window_hours: windowHours });
        if (endMs) params.append("end_ms", endMs);
        return this.request(`/api/telemetry/predictive?${params.toString()}`);
    },

    async getQuality(noId, startMs = null, endMs = null) {
        const params = new URLSearchParams({ no_id: noId });
        if (startMs) params.append("start_ms", startMs);
        if (endMs) params.append("end_ms", endMs);
        return this.request(`/api/telemetry/quality?${params.toString()}`);
    },

    // Tags & Limites Operacionais
    async getTags(equipamentoId = null) {
        const params = new URLSearchParams();
        if (equipamentoId) params.append("equipamento_id", equipamentoId);
        return this.request(`/api/tags?${params.toString()}`);
    },

    async getTag(noId) {
        return this.request(`/api/tags/${noId}`);
    },

    async updateTagLimits(noId, limiteAtencao, limiteCritico) {
        return this.request(`/api/tags/${noId}/limits`, {
            method: "PUT",
            body: JSON.stringify({
                limite_atencao: parseFloat(limiteAtencao),
                limite_critico: parseFloat(limiteCritico),
            }),
        });
    },

    // Alarmes
    async getAlarms(filters = {}) {
        const params = new URLSearchParams();
        if (filters.equipamentoId) params.append("equipamento_id", filters.equipamentoId);
        if (filters.startMs) params.append("start_ms", filters.startMs);
        if (filters.endMs) params.append("end_ms", filters.endMs);
        if (filters.severidade) params.append("severidade", filters.severidade);
        if (filters.tipoAlarme) params.append("tipo_alarme", filters.tipoAlarme);
        if (filters.limit) params.append("limit", filters.limit);
        return this.request(`/api/alarms?${params.toString()}`);
    },

    async getAlarmsSummary() {
        return this.request("/api/alarms/summary");
    },

    async getHealth() {
        return this.request("/api/health");
    },
};
