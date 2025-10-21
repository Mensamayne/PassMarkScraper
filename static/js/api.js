/**
 * PassMark API Client
 * Complete client for all API endpoints
 */

class PassMarkAPI {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    async _fetch(url, options = {}) {
        try {
            const response = await fetch(this.baseURL + url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.message || error.detail || 'API Error');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Health & Info
    async getHealth() {
        return this._fetch('/health');
    }

    async getConfig() {
        return this._fetch('/config');
    }

    async updateConfig(config) {
        return this._fetch('/config', {
            method: 'PUT',
            body: JSON.stringify(config),
        });
    }

    async reloadConfig() {
        return this._fetch('/config/reload', { method: 'POST' });
    }

    // Search & Compare
    async searchComponent(name, type = null) {
        const params = new URLSearchParams({ name });
        if (type) params.append('type', type);
        return this._fetch(`/search?${params}`);
    }

    async searchEnhanced(query, componentType) {
        return this._fetch('/api/search-enhanced', {
            method: 'POST',
            body: JSON.stringify({ query, component_type: componentType }),
        });
    }

    async compareComponents(component1, component2, type = null) {
        const params = new URLSearchParams({ component1, component2 });
        if (type) params.append('type', type);
        return this._fetch(`/compare?${params}`);
    }

    async listComponents(type, limit = 10, category = null) {
        const params = new URLSearchParams({ type, limit: limit.toString() });
        if (category) params.append('category', category);
        return this._fetch(`/list?${params}`);
    }

    // Recommendation Endpoints
    async analyzePairing(cpu, gpu) {
        return this._fetch('/analyze-pairing', {
            method: 'POST',
            body: JSON.stringify({ cpu, gpu }),
        });
    }

    async recommendPairing(cpu = null, gpu = null, gameFocus = null, limit = 5) {
        const params = new URLSearchParams({ limit: limit.toString() });
        if (cpu) params.append('cpu', cpu);
        if (gpu) params.append('gpu', gpu);
        if (gameFocus) params.append('game_focus', gameFocus);
        return this._fetch(`/recommend-pairing?${params}`);
    }

    async getGamingProfile(cpu, gpu, resolution = '1440p') {
        return this._fetch('/gaming-profile', {
            method: 'POST',
            body: JSON.stringify({ cpu, gpu, resolution }),
        });
    }

    async estimatePerformance(component, type) {
        const params = new URLSearchParams({ component, type });
        return this._fetch(`/estimate-performance?${params}`);
    }

    async getGameCategories() {
        return this._fetch('/game-categories');
    }

    async powerAnalysis(cpu, gpu) {
        return this._fetch('/power-analysis', {
            method: 'POST',
            body: JSON.stringify({ cpu, gpu }),
        });
    }

    // Scraping
    async scrapeAndSave(type, limit, includeWorkstation = true, skipBackup = false) {
        const params = new URLSearchParams({
            type,
            limit: limit.toString(),
            include_workstation: includeWorkstation.toString(),
            skip_backup: skipBackup.toString(),
        });
        return this._fetch(`/scrape-and-save?${params}`, { method: 'POST' });
    }

    async getScrapeStatus() {
        return this._fetch('/scrape-status');
    }

    // Backup
    async listBackups() {
        return this._fetch('/backup/list');
    }

    async createBackup() {
        return this._fetch('/backup/create', { method: 'POST' });
    }

    async restoreBackup(filename) {
        const params = new URLSearchParams({ filename });
        return this._fetch(`/backup/restore?${params}`, { method: 'POST' });
    }

    // Scheduler
    async getSchedulerStatus() {
        return this._fetch('/scheduler/status');
    }

    async startScheduler() {
        return this._fetch('/scheduler/start', { method: 'POST' });
    }

    async stopScheduler() {
        return this._fetch('/scheduler/stop', { method: 'POST' });
    }
}

// Create global instance
window.api = new PassMarkAPI();

