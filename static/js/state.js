/**
 * Alpine.js Global State Store
 * Centralized reactive state management
 */

document.addEventListener('alpine:init', () => {
    Alpine.store('app', {
        // UI State
        currentTab: 'dashboard',
        darkMode: localStorage.getItem('darkMode') === 'true',
        loading: false,
        
        // Component Selection
        selectedCPU: null,
        selectedGPU: null,
        searchResults: {
            cpu: [],
            gpu: [],
        },
        
        // Compare Components
        compareComponent1: null,
        compareComponent2: null,
        compareType1: null,
        compareType2: null,
        compareResult: null,
        
        // Analysis Results
        pairingAnalysis: null,
        recommendations: null,
        gamingProfile: null,
        powerAnalysis: null,
        
        // Configuration
        config: null,
        defaultConfig: null,
        
        // Stats
        stats: {
            dbCount: 0,
            cpuCount: 0,
            gpuCount: 0,
            lastScrape: null,
        },
        
        // History (from localStorage)
        history: [],
        
        // UI Helpers
        toast: null,
        
        // Methods
        init() {
            this.loadHistory();
            this.loadStats();
            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            }
        },
        
        setTab(tab) {
            this.currentTab = tab;
            // Clear results when switching tabs
            if (tab !== this.currentTab) {
                this.clearResults();
            }
        },
        
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            localStorage.setItem('darkMode', this.darkMode);
            document.documentElement.classList.toggle('dark');
        },
        
        async loadStats() {
            try {
                const health = await api.getHealth();
                this.stats.dbCount = health.db_count;
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        },
        
        setSelectedCPU(cpu) {
            this.selectedCPU = cpu;
        },
        
        setSelectedGPU(gpu) {
            this.selectedGPU = gpu;
        },
        
        async searchComponents(query, type) {
            if (!query || query.length < 2) {
                this.searchResults[type.toLowerCase()] = [];
                return;
            }
            
            try {
                const result = await api.searchEnhanced(query, type);
                this.searchResults[type.toLowerCase()] = result.matches || [];
            } catch (error) {
                console.error('Search error:', error);
                this.searchResults[type.toLowerCase()] = [];
            }
        },
        
        async analyzePairing() {
            if (!this.selectedCPU || !this.selectedGPU) {
                this.showToast('Please select both CPU and GPU', 'warning');
                return;
            }
            
            this.loading = true;
            try {
                const result = await api.analyzePairing(this.selectedCPU, this.selectedGPU);
                this.pairingAnalysis = result;
                this.addToHistory('pairing', this.selectedCPU, this.selectedGPU, result);
                this.showToast('Analysis complete!', 'success');
            } catch (error) {
                this.showToast(error.message, 'error');
            } finally {
                this.loading = false;
            }
        },
        
        async getRecommendations(component, type, gameFocus, limit = 5) {
            this.loading = true;
            try {
                const cpu = type === 'CPU' ? component : null;
                const gpu = type === 'GPU' ? component : null;
                const result = await api.recommendPairing(cpu, gpu, gameFocus, limit);
                this.recommendations = result;
                this.showToast(`Found ${result.recommendations.length} recommendations`, 'success');
            } catch (error) {
                this.showToast(error.message, 'error');
            } finally {
                this.loading = false;
            }
        },
        
        async getGamingProfile(resolution = '1440p') {
            if (!this.selectedCPU || !this.selectedGPU) {
                this.showToast('Please select both CPU and GPU', 'warning');
                return;
            }
            
            this.loading = true;
            try {
                const result = await api.getGamingProfile(this.selectedCPU, this.selectedGPU, resolution);
                this.gamingProfile = result;
                this.showToast('Profile generated!', 'success');
            } catch (error) {
                this.showToast(error.message, 'error');
            } finally {
                this.loading = false;
            }
        },
        
        async getPowerAnalysis() {
            if (!this.selectedCPU || !this.selectedGPU) {
                this.showToast('Please select both CPU and GPU', 'warning');
                return;
            }
            
            this.loading = true;
            try {
                const result = await api.powerAnalysis(this.selectedCPU, this.selectedGPU);
                this.powerAnalysis = result;
                this.showToast('Power analysis complete!', 'success');
            } catch (error) {
                this.showToast(error.message, 'error');
            } finally {
                this.loading = false;
            }
        },
        
        async loadConfig() {
            try {
                const config = await api.getConfig();
                this.config = JSON.parse(JSON.stringify(config)); // Deep copy
                if (!this.defaultConfig) {
                    this.defaultConfig = JSON.parse(JSON.stringify(config));
                }
            } catch (error) {
                this.showToast('Failed to load config', 'error');
            }
        },
        
        async saveConfig() {
            this.loading = true;
            try {
                await api.updateConfig(this.config);
                await api.reloadConfig();
                this.showToast('Configuration saved!', 'success');
            } catch (error) {
                this.showToast('Failed to save config', 'error');
            } finally {
                this.loading = false;
            }
        },
        
        resetConfig() {
            if (confirm('Reset all settings to defaults?')) {
                this.config = JSON.parse(JSON.stringify(this.defaultConfig));
                this.showToast('Config reset to defaults (not saved yet)', 'info');
            }
        },
        
        async compareComponents() {
            if (!this.compareComponent1 || !this.compareComponent2) {
                this.showToast('Please select both components', 'warning');
                return;
            }
            
            this.loading = true;
            try {
                const result = await api.compareComponents(
                    this.compareComponent1, 
                    this.compareComponent2, 
                    this.compareType1 === this.compareType2 ? this.compareType1 : null
                );
                this.compareResult = result;
                this.showToast('Comparison complete!', 'success');
            } catch (error) {
                this.showToast(error.message, 'error');
            } finally {
                this.loading = false;
            }
        },
        
        clearResults() {
            this.pairingAnalysis = null;
            this.recommendations = null;
            this.gamingProfile = null;
            this.powerAnalysis = null;
            this.compareResult = null;
        },
        
        // History Management
        addToHistory(type, cpu, gpu, result) {
            const entry = {
                type,
                cpu,
                gpu,
                result,
                timestamp: new Date().toISOString(),
            };
            
            this.history.unshift(entry);
            if (this.history.length > 10) {
                this.history = this.history.slice(0, 10);
            }
            
            this.saveHistory();
        },
        
        loadHistory() {
            const saved = localStorage.getItem('analysisHistory');
            if (saved) {
                try {
                    this.history = JSON.parse(saved);
                } catch (e) {
                    this.history = [];
                }
            }
        },
        
        saveHistory() {
            localStorage.setItem('analysisHistory', JSON.stringify(this.history));
        },
        
        clearHistory() {
            if (confirm('Clear all history?')) {
                this.history = [];
                localStorage.removeItem('analysisHistory');
                this.showToast('History cleared', 'info');
            }
        },
        
        loadFromHistory(entry) {
            this.selectedCPU = entry.cpu;
            this.selectedGPU = entry.gpu;
            this.pairingAnalysis = entry.result;
            this.setTab('analyze');
        },
        
        // Toast Notifications
        showToast(message, type = 'info') {
            this.toast = { message, type };
            setTimeout(() => {
                this.toast = null;
            }, 3000);
        },
        
        // Utilities
        getBalanceClass(score) {
            if (score >= 90) return 'excellent';
            if (score >= 75) return 'very-good';
            if (score >= 60) return 'good';
            if (score >= 40) return 'fair';
            return 'poor';
        },
        
        getTierStars(tier) {
            const stars = {
                'low': '★☆☆☆',
                'mid': '★★☆☆',
                'high': '★★★☆',
                'ultra': '★★★★',
            };
            return stars[tier] || '★☆☆☆';
        },
        
        formatDate(isoString) {
            const date = new Date(isoString);
            return date.toLocaleString('pl-PL', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
        },
    });
});

