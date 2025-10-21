# PassMark WebUI 2.0 - Specyfikacja Designu

## 🎨 Koncepcja

Nowoczesny, responsywny dashboard z pełnym dostępem do wszystkich funkcji API:
- Analiza pairingu CPU+GPU
- Rekomendacje komponentów
- Gaming profile
- Power/TDP analysis
- Konfiguracja systemu
- Backup management

---

## 📐 Struktura UI

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  HEADER: Logo | Navigation Tabs | Dark Mode Toggle     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Tab Content Area]                                     │
│                                                         │
│  • Dashboard                                            │
│  • Analyze Pairing                                      │
│  • Recommendations                                      │
│  • Gaming Profile                                       │
│  • Power Analysis                                       │
│  • Configuration                                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  FOOTER: Status | API Version | Stats                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🏠 TAB 1: Dashboard (Overview)

### Sekcja: Quick Stats
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Components  │     CPUs     │     GPUs     │   Last Scan  │
│    28,333    │    4,255     │    2,537     │  2 days ago  │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### Sekcja: Quick Actions (Cards)
```
┌─────────────────────┐  ┌─────────────────────┐
│  🔍 Quick Compare   │  │  🎯 Analyze Build   │
│                     │  │                     │
│  [Component 1]      │  │  [Your CPU    ▼]    │
│  [Component 2]      │  │  [Your GPU    ▼]    │
│                     │  │                     │
│  [Compare Button]   │  │  [Analyze Button]   │
└─────────────────────┘  └─────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐
│  💡 Get Recommend.  │  │  ⚡ Power Check     │
│                     │  │                     │
│  I have: [CPU/GPU▼] │  │  [CPU]     [GPU]    │
│  Component: [____]  │  │                     │
│  Focus: [AAA GPU▼]  │  │  PSU: 650W          │
│                     │  │  Cost: $15/month    │
│  [Show Me Button]   │  │                     │
└─────────────────────┘  └─────────────────────┘
```

### Sekcja: Recent Analyses (History)
```
Last 5 analyses with quick re-run button
┌────────────────────────────────────────────────┐
│ 7800X3D + RTX 4070   | Balance: 98  | [↻]    │
│ i5-13400F + RTX 4060 | Balance: 82  | [↻]    │
└────────────────────────────────────────────────┘
```

---

## 🎯 TAB 2: Analyze Pairing

### Layout
```
┌─────────────────────────────────────────────┐
│  Select Components                          │
│                                             │
│  CPU: [Search or select...        ▼] 🔍    │
│  GPU: [Search or select...        ▼] 🔍    │
│                                             │
│  [Analyze Pairing Button - Full Width]     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Results (pokazuje się po kliknięciu)       │
│                                             │
│  ┌────────────┬────────────┐               │
│  │    CPU     │    GPU     │               │
│  │  7800X3D   │  RTX 4070  │               │
│  │  Score: 92 │  Score: 75 │               │
│  │  Tier: ★★★★│  Tier: ★★★ │               │
│  └────────────┴────────────┘               │
│                                             │
│  Overall Balance: [████████░░] 98/100      │
│  Verdict: 🎉 Excellent                     │
│  Bottleneck: ✅ None                       │
│                                             │
│  ── Performance by Game Type ──            │
│                                             │
│  🎮 E-sport (Valorant, CS2)                │
│     Balance: 94/100  CPU: 96%  GPU: 19%    │
│     [████████████░░] Excellent             │
│                                             │
│  🌆 AAA GPU-heavy (Cyberpunk, Starfield)   │
│     Balance: 100/100  CPU: 30%  GPU: 72%   │
│     [██████████████] Excellent             │
│     Note: Slight CPU bottleneck in RT      │
│                                             │
│  ⚖️  Balanced (GTA V, RDR2)                │
│     Balance: 100/100                       │
│     [██████████████] Excellent             │
│                                             │
│  🏗️  Simulation (Cities Skylines II)       │
│     Balance: 94/100  CPU: 100%  GPU: 10%   │
│     [████████████░░] Excellent             │
│                                             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  💡 Recommendations                         │
│                                             │
│  Upgrade Priority: None                     │
│  This pairing is well balanced!             │
│                                             │
│  Alternative GPUs:                          │
│  • RTX 4080 (100/100 match)                │
│  • RTX 4070 Ti (95/100 match)              │
└─────────────────────────────────────────────┘
```

---

## 💡 TAB 3: Recommendations

### Layout
```
┌─────────────────────────────────────────────┐
│  What do you have?                          │
│                                             │
│  ○ I have CPU, need GPU                     │
│  ○ I have GPU, need CPU                     │
│                                             │
│  Component: [Search...              ] 🔍    │
│                                             │
│  Game Focus (optional):                     │
│  [○ All  ○ E-sport  ○ AAA  ○ Balanced      │
│   ○ Simulation]                             │
│                                             │
│  [Get Recommendations Button]               │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Results                                    │
│                                             │
│  Base: AMD Ryzen 7 7800X3D (Score: 92)     │
│  Focus: AAA GPU-heavy games                 │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ 1. GeForce RTX 5090                   │ │
│  │    Match: [██████████] 100/100        │ │
│  │    Tier: ★★★★  Balance: Perfect       │ │
│  │    [View Details] [Analyze Pairing]   │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ 2. GeForce RTX 4090                   │ │
│  │    Match: [██████████] 100/100        │ │
│  │    Tier: ★★★★  Balance: Perfect       │ │
│  │    [View Details] [Analyze Pairing]   │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ 3. GeForce RTX 4080                   │ │
│  │    Match: [█████████░] 98/100         │ │
│  │    Tier: ★★★★  Balance: Excellent     │ │
│  │    [View Details] [Analyze Pairing]   │ │
│  └───────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## 🎮 TAB 4: Gaming Profile

### Layout
```
┌─────────────────────────────────────────────┐
│  Your Build                                 │
│                                             │
│  CPU: [Search or select...        ▼] 🔍    │
│  GPU: [Search or select...        ▼] 🔍    │
│                                             │
│  Target Resolution:                         │
│  [○ 1080p  ● 1440p  ○ 4K]                  │
│                                             │
│  [Generate Profile Button]                  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Performance Profile                        │
│                                             │
│  Build: Ryzen 5 7600 + RTX 4060             │
│  Resolution: 1440p                          │
│                                             │
│  Overall: [████████░░] 94/100               │
│  Verdict: 🌟 Excellent for 1440p gaming    │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ 🎯 E-sport (Valorant, CS2)          │   │
│  │ FPS: 300-500+                        │   │
│  │ Settings: Ultra                      │   │
│  │ Bottleneck: None                     │   │
│  │ [████████████████] Excellent         │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ 🌆 AAA GPU-heavy (Cyberpunk, etc)   │   │
│  │ FPS: 100-120 @ 1440p Ultra           │   │
│  │ Settings: Ultra                      │   │
│  │ Bottleneck: None                     │   │
│  │ [████████████████] Excellent         │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [+ Show All Categories]                   │
│                                             │
│  💡 Upgrade Recommendation:                │
│  Priority: None - System is well balanced  │
└─────────────────────────────────────────────┘
```

---

## ⚡ TAB 5: Power Analysis

### Layout
```
┌─────────────────────────────────────────────┐
│  System Components                          │
│                                             │
│  CPU: [Search...                  ▼] 🔍    │
│  GPU: [Search...                  ▼] 🔍    │
│                                             │
│  [Analyze Power Button]                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Power & Thermal Analysis                   │
│                                             │
│  ┌────────────┬────────────┬──────────┐    │
│  │  CPU TDP   │  GPU TDP   │  Total   │    │
│  │   120W     │   285W     │   505W   │    │
│  └────────────┴────────────┴──────────┘    │
│                                             │
│  🔌 PSU Recommendation                     │
│  ┌─────────────────────────────────────┐   │
│  │  Recommended: 850W                   │   │
│  │  Range: 750-950W                     │   │
│  │  Efficiency: 80+ Gold/Platinum       │   │
│  │                                      │   │
│  │  Popular Options:                    │   │
│  │  • Corsair RM850x (80+ Gold)         │   │
│  │  • Seasonic Focus GX-850             │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  🌡️  Thermal & Cooling                     │
│  ┌─────────────────────────────────────┐   │
│  │  Heat Class: High                    │   │
│  │  [██████████░░░░] Extreme            │   │
│  │                                      │   │
│  │  CPU Cooling:                        │   │
│  │  240-280mm AIO recommended           │   │
│  │  or high-end tower cooler            │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  💰 Operating Costs (USD)                  │
│  ┌─────────────────────────────────────┐   │
│  │  Gaming (4h/day):  $12.50/month      │   │
│  │  Idle (20h/day):   $4.62/month       │   │
│  │  ────────────────────────────────    │   │
│  │  Total Monthly:    $17.12            │   │
│  │  Total Yearly:     $205.44           │   │
│  │                                      │   │
│  │  Customize:                          │   │
│  │  Hours/day: [4] $/kWh: [0.15]       │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## ⚙️ TAB 6: Configuration

### Layout
```
┌─────────────────────────────────────────────┐
│  System Configuration                       │
│                                             │
│  [Save Changes] [Reset to Defaults]        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  📊 Database Settings                       │
│                                             │
│  Database Path: [benchmarks.db]             │
│  Components: 28,333                         │
│  Last Updated: 2 days ago                   │
│                                             │
│  [Create Backup] [Restore from Backup]     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  🎯 Recommendation Settings                 │
│                                             │
│  Min Match Score:       [40]      (0-100)   │
│  Bottleneck Threshold:  [40]      (0-100)   │
│  Max Recommendations:   [5]       (1-20)    │
│  PSU Overhead:          [30]%     (20-50)   │
│                                             │
│  ☑ Enable component suggestions on errors  │
│  Max Suggestions:       [3]       (1-10)    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  🔄 Scraping Settings                       │
│                                             │
│  ☑ Use full component lists (~28k items)   │
│  ☐ Include workstation components          │
│                                             │
│  Component Limits:                          │
│  CPU:     [-1] (unlimited)                  │
│  GPU:     [-1] (unlimited)                  │
│  RAM:     [-1] (unlimited)                  │
│  Storage: [-1] (unlimited)                  │
│                                             │
│  Delay between requests: [2000]ms           │
│  Max retries:            [3]                │
│  Timeout:                [30]s              │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  ⏰ Scheduler Settings                      │
│                                             │
│  ☐ Enable automatic scraping                │
│  Schedule: [Sunday] at [03:00] UTC          │
│                                             │
│  [Start Scheduler] [Stop Scheduler]        │
│  Next run: Not scheduled                    │
└─────────────────────────────────────────────┘
```

---

## 🎨 Design System

### Kolory (Dark Mode Support)

**Light Mode:**
```css
--bg-primary: #ffffff
--bg-secondary: #f8f9fa
--text-primary: #1a1a1a
--text-secondary: #6c757d
--accent: #667eea
--accent-secondary: #764ba2
--success: #28a745
--warning: #ffc107
--danger: #dc3545
--border: #e0e0e0
```

**Dark Mode:**
```css
--bg-primary: #1a1a1a
--bg-secondary: #2d2d2d
--text-primary: #ffffff
--text-secondary: #b0b0b0
--accent: #7c8cff
--accent-secondary: #8a5fc7
--success: #4caf50
--warning: #ffb74d
--danger: #f44336
--border: #404040
```

### Komponenty UI

**Progress Bar:**
```html
<div class="progress-bar">
  <div class="progress-fill" style="width: 94%">94</div>
</div>
```

**Score Badge:**
```html
<span class="badge badge-excellent">98/100</span>
<!-- badge-poor (0-40) -->
<!-- badge-fair (40-60) -->
<!-- badge-good (60-75) -->
<!-- badge-very-good (75-90) -->
<!-- badge-excellent (90-100) -->
```

**Tier Display:**
```html
<div class="tier-display">
  <span class="tier-stars">★★★★</span>
  <span class="tier-label">Ultra</span>
</div>
```

**Category Card:**
```html
<div class="category-card">
  <div class="category-header">
    <span class="category-icon">🎮</span>
    <h3>E-sport</h3>
  </div>
  <div class="category-stats">
    <div class="stat">
      <label>Balance</label>
      <span class="value">94/100</span>
    </div>
    <div class="stat">
      <label>CPU</label>
      <span class="value">96%</span>
    </div>
    <div class="stat">
      <label>GPU</label>
      <span class="value">19%</span>
    </div>
  </div>
  <div class="category-performance">
    <div class="progress-bar">
      <div class="fill" style="width: 94%"></div>
    </div>
    <span class="performance-label">Excellent</span>
  </div>
</div>
```

---

## 🔍 Autocomplete Search

### Component Search Box
```javascript
// Real-time search z debouncing
<input 
  type="text" 
  placeholder="Type CPU name... (e.g., 7800X3D)"
  autocomplete="off"
/>

// Dropdown z wynikami:
┌────────────────────────────────────┐
│ AMD Ryzen 7 7800X3D                │ ← Best match
│ Score: 92 | Tier: Ultra            │
├────────────────────────────────────┤
│ AMD Ryzen 9 7900X3D                │
│ Score: 88 | Tier: Ultra            │
├────────────────────────────────────┤
│ AMD Ryzen 7 7700X                  │
│ Score: 75 | Tier: High             │
└────────────────────────────────────┘
```

---

## 📱 Responsive Design

### Mobile (< 768px)
- Stack wszystkich kart pionowo
- Uproszczone tabele (scroll horizontal)
- Hamburger menu dla nawigacji
- Touch-friendly buttons (min 44px)

### Tablet (768px - 1024px)
- 2 kolumny dla quick actions
- Pełne tabele z podstawowymi danymi

### Desktop (> 1024px)
- Pełny layout z sidebar navigation
- Side-by-side comparisons
- Expanded data tables

---

## 🚀 Interaktywność

### Animacje
- Smooth scroll between tabs
- Fade in dla results
- Progress bar animations (animate width)
- Button hover effects (transform, shadow)
- Loading spinners podczas fetch

### Real-time Features
- Auto-save config changes (debounced)
- Live validation (component exists?)
- Toast notifications dla akcji
- Loading states dla wszystkich requestów

### Keyboard Shortcuts
- `Ctrl+K` - Quick search
- `Ctrl+1-6` - Switch tabs
- `Ctrl+S` - Save config
- `Escape` - Close modals

---

## 🛠️ Stack Technologiczny

### Opcja 1: Pure HTML/CSS/Vanilla JS
**Pros:** 
- Zero dependencies
- Szybki load
- Łatwy deployment

**Cons:**
- Więcej boilerplate code
- State management ręczny

### Opcja 2: Vue.js 3 (Single File)
**Pros:**
- Reactive state management
- Component reusability
- Elegant syntax

**Cons:**
- Jedna dependencja więcej

### Opcja 3: Alpine.js + Tailwind CSS (RECOMMENDED)
**Pros:**
- Minimalistyczny (15kb Alpine, inline Tailwind)
- Reactive jak Vue ale prostszy
- Utility-first CSS
- Perfect dla tego projektu

**Cons:**
- Wymaga CDN (lub inline)

---

## 📦 Implementacja

### Struktura plików
```
static/
├── index.html              # Main dashboard
├── css/
│   ├── app.css            # Custom styles
│   └── components.css     # Reusable components
├── js/
│   ├── app.js             # Main app logic
│   ├── api.js             # API client
│   ├── components.js      # UI components
│   └── config.js          # Configuration manager
└── assets/
    ├── icons/
    └── images/
```

### Core Features w JS

```javascript
// API Client
class PassMarkAPI {
  async analyzeP pairing(cpu, gpu) { ... }
  async recommendPairing(component, type, focus) { ... }
  async gamingProfile(cpu, gpu, resolution) { ... }
  async powerAnalysis(cpu, gpu) { ... }
  async getConfig() { ... }
  async updateConfig(config) { ... }
  async resetConfig() { ... }
}

// Component Search
class ComponentSearch {
  async search(query, type) {
    // Debounced search with autocomplete
  }
}

// Config Manager
class ConfigManager {
  loadConfig() { ... }
  saveConfig() { ... }
  resetToDefaults() { ... }
  validateConfig() { ... }
}

// State Management
const app = {
  state: {
    currentTab: 'dashboard',
    selectedCPU: null,
    selectedGPU: null,
    config: {},
    results: {},
  },
  methods: { ... }
}
```

---

## 🎯 User Flow Examples

### Flow 1: Nowy użytkownik chce sprawdzić swój build
1. Otwiera stronę → Dashboard
2. Widzi "Quick Actions"
3. Klika "Analyze Build"
4. Wpisuje CPU (autocomplete pomaga)
5. Wpisuje GPU (autocomplete pomaga)
6. Klika "Analyze"
7. Widzi wyniki z recommendation do upgrade

### Flow 2: Użytkownik planuje build
1. Przechodzi do "Recommendations"
2. Wybiera "I have CPU, need GPU"
3. Wpisuje swój CPU
4. Wybiera focus: "AAA GPU-heavy"
5. Klika "Get Recommendations"
6. Widzi top 5 GPU z match scores
7. Klika "Analyze Pairing" przy RTX 4080
8. Przechodzi do szczegółowej analizy

### Flow 3: Admin zmienia konfigurację
1. Przechodzi do "Configuration"
2. Widzi wszystkie settings
3. Zmienia "Min Match Score" z 40 na 50
4. Klika "Save Changes"
5. Toast: "Config saved successfully"
6. Może kliknąć "Reset to Defaults" jeśli coś pójdzie nie tak

---

## 💎 Dodatkowe Ficzery UI

### 1. Comparison Table Mode
```
┌──────────────┬──────────────┬──────────────┐
│              │   Build A    │   Build B    │
├──────────────┼──────────────┼──────────────┤
│ CPU          │  7800X3D     │  i9-14900K   │
│ GPU          │  RTX 4070    │  RTX 4080    │
│ Balance      │  98/100      │  95/100      │
│ E-sport FPS  │  300-500+    │  350-600+    │
│ AAA FPS      │  100-120     │  120-140     │
│ PSU Need     │  650W        │  850W        │
│ Cost/year    │  $180        │  $240        │
└──────────────┴──────────────┴──────────────┘
```

### 2. Build Presets
```
┌─────────────────────────────────────────────┐
│  Popular Build Presets                      │
│                                             │
│  [Budget 1080p]    [Mid-range 1440p]        │
│  [High-end 4K]     [E-sport Beast]          │
│                                             │
│  Click to load preset configuration         │
└─────────────────────────────────────────────┘
```

### 3. Export Results
```
[Export as PDF] [Share Link] [Copy JSON]
```

### 4. History/Bookmarks
```
★ Save this analysis
📋 View saved builds (5)
🕐 History (last 10)
```

---

## 🎨 Visual Mockup Kluczowych Elementów

### Balance Score Visualization
```
  Excellent (90-100)  [███████████████████░] 98/100 🎉
  Very Good (75-90)   [████████████████░░░░] 82/100 ✨
  Good (60-75)        [█████████████░░░░░░░] 67/100 ✓
  Fair (40-60)        [██████████░░░░░░░░░░] 52/100 ⚠️
  Poor (0-40)         [████░░░░░░░░░░░░░░░░] 18/100 ❌
```

### Bottleneck Indicator
```
┌─────────────────────────────────────┐
│  🔴 CPU Bottleneck Detected         │
│                                     │
│  Your GPU is 75 points stronger    │
│  than your CPU in AAA games.        │
│                                     │
│  💡 Recommended Action:             │
│  Upgrade CPU to at least 'high'    │
│  tier for optimal performance.      │
│                                     │
│  [View CPU Recommendations]         │
└─────────────────────────────────────┘
```

---

## 🔧 Funkcjonalności Specjalne

### 1. Preset Manager
- Save current analysis as preset
- Load community presets
- Share presets via link

### 2. Compare Mode
- Add multiple builds to comparison table
- Side-by-side all metrics
- Export comparison as image/PDF

### 3. Budget Calculator
- Input budget limit
- Auto-suggest best balanced build
- Show alternative options

### 4. Notification Center
```
🔔 Notifications (2)
• Config saved successfully
• New components scraped (150 added)
```

---

## 📊 Dashboard Widgets

### Widget: System Status
```
┌──────────────────────┐
│  System Health       │
│  ● Online            │
│  28,333 components   │
│  API v2.0.0          │
└──────────────────────┘
```

### Widget: Top Components
```
┌──────────────────────┐
│  Top CPUs            │
│  1. AMD 9950X        │
│  2. Intel i9-14900KS │
│  3. AMD 7800X3D      │
│  [View All]          │
└──────────────────────┘
```

### Widget: Quick Stats
```
┌──────────────────────┐
│  Today's Activity    │
│  15 analyses         │
│  8 recommendations   │
│  3 configs changed   │
└──────────────────────┘
```

---

## 🚀 Priorytet Implementacji

### Phase 1 (MVP - Must Have)
- ✅ Dashboard z quick actions
- ✅ Analyze Pairing tab (full featured)
- ✅ Basic configuration panel
- ✅ Dark mode toggle
- ✅ Responsive design

### Phase 2 (Enhanced)
- ✅ Recommendations tab
- ✅ Gaming Profile tab
- ✅ Power Analysis tab
- ✅ Autocomplete search
- ✅ History/Recent analyses

### Phase 3 (Advanced)
- ⏳ Build presets
- ⏳ Comparison mode (multiple builds)
- ⏳ Export functionality
- ⏳ Budget calculator
- ⏳ Notification system

---

## 🎯 Rekomendowany Stack

**Wybór:** Alpine.js + Tailwind CSS + Vanilla JS

**Dlaczego:**
- Single HTML file możliwy (CDN)
- Reactive state management
- Modern utility CSS
- Zero build step
- 15kb Alpine + 3kb Tailwind purged
- Perfect dla microservice

**Alternatywa:** Pure Vanilla JS + Custom CSS (jeśli zero dependencies)

---

**Mam to zaimplementować?** 🚀

