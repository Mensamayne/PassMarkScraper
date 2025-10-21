# System Rekomendacji i Analizy Bottlenecków - Specyfikacja

## 🎯 Cel projektu

Rozszerzenie PassMark Scraper API o inteligentny system rekomendacji pairingu CPU+GPU z uwzględnieniem różnych typów gier i rzeczywistych scenariuszy użytkowania.

---

## 📊 Model kategorii gier

System analizuje kompatybilność komponentów w kontekście 4 kategorii gier:

| Typ gry | Przykłady | Co testuje | Waga w modelu | CPU/GPU split |
|---------|-----------|------------|---------------|---------------|
| **E-sport / lekkie CPU-heavy** | Valorant, CS2, LoL, Fortnite | pojedynczy wątek CPU, latency, RAM | 25% | 80% CPU / 20% GPU |
| **AAA GPU-heavy (open world)** | Cyberpunk 2077, Hogwarts Legacy, Starfield | GPU ray tracing, VRAM, CPU drugi plan | 35% | 25% CPU / 75% GPU |
| **Zbalansowane / silnik CPU+GPU** | GTA V, RDR2, AC Mirage, Horizon FW | synergy CPU/GPU, cache, RAM | 25% | 50% CPU / 50% GPU |
| **CPU-intensive symulatory** | Cities Skylines II, MSFS 2024, Total War | czysty CPU load, single-thread | 15% | 90% CPU / 10% GPU |

---

## 🔌 Nowe endpointy API

### 1. `POST /analyze-pairing`

Analizuje konkretną parę CPU+GPU i zwraca szczegółową ocenę dla każdej kategorii gier.

**Request:**
```json
{
  "cpu": "Ryzen 7 7800X3D",
  "gpu": "RTX 4070"
}
```

**Response:**
```json
{
  "cpu": {
    "name": "AMD Ryzen 7 7800X3D",
    "passmark_score": 35821,
    "single_thread": 4508,
    "cores": 8,
    "threads": 16
  },
  "gpu": {
    "name": "GeForce RTX 4070",
    "g3d_mark": 28161,
    "memory_size": 12
  },
  "analysis": {
    "overall_balance": "excellent",
    "bottleneck": null,
    "balance_score": 95,
    "by_category": {
      "esport": {
        "performance": "excellent",
        "bottleneck": null,
        "cpu_utilization": 85,
        "gpu_utilization": 60,
        "fps_estimate": "300+"
      },
      "aaa_gpu": {
        "performance": "very_good",
        "bottleneck": "slight_cpu",
        "cpu_utilization": 95,
        "gpu_utilization": 98,
        "fps_estimate": "100-120 @ 1440p Ultra"
      },
      "balanced": {
        "performance": "excellent",
        "bottleneck": null,
        "synergy": "optimal"
      },
      "simulation": {
        "performance": "excellent",
        "bottleneck": null,
        "cpu_utilization": 80
      }
    }
  },
  "recommendations": {
    "verdict": "Excellent pairing for all game types",
    "notes": [
      "Optimal for 1440p gaming",
      "CPU cache excellent for AAA games",
      "No bottleneck in any category"
    ]
  }
}
```

---

### 2. `GET /recommend-pairing`

Rekomenduje optymalne komponenty na podstawie jednego komponentu i typu gier.

**Request:**
```http
GET /recommend-pairing?cpu=7800X3D&game_focus=aaa_gpu
```

**Response:**
```json
{
  "cpu": "AMD Ryzen 7 7800X3D",
  "game_focus": "aaa_gpu",
  "recommended_gpus": [
    {
      "name": "RTX 4080",
      "match_score": 98,
      "balance": "perfect",
      "expected_performance": "4K 60+ FPS Ultra"
    },
    {
      "name": "RTX 4070 Ti",
      "match_score": 95,
      "balance": "excellent",
      "expected_performance": "1440p 120+ FPS Ultra"
    },
    {
      "name": "RX 7900 XT",
      "match_score": 93,
      "balance": "very_good",
      "expected_performance": "1440p 100+ FPS Ultra"
    }
  ]
}
```

**Odwrotnie - rekomendacja CPU:**
```http
GET /recommend-pairing?gpu=RTX4090&game_focus=simulation
```

---

### 3. `GET /gaming-profile`

Kompleksowy profil wydajności systemu w różnych rozdzielczościach i typach gier.

**Request:**
```http
GET /gaming-profile?components=7800X3D,RTX4070&resolution=1440p
```

**Response:**
```json
{
  "system": {
    "cpu": "Ryzen 7 7800X3D",
    "gpu": "RTX 4070"
  },
  "performance_by_game_type": {
    "esport": {
      "games": ["Valorant", "CS2", "LoL"],
      "fps_range": "300-500+",
      "settings": "Max everything",
      "bottleneck": "none",
      "cpu_utilization": "60-70%",
      "gpu_utilization": "40-50%"
    },
    "aaa_gpu": {
      "games": ["Cyberpunk", "Starfield"],
      "fps_range": "100-120",
      "settings": "Ultra + RT Medium",
      "bottleneck": "slight_cpu_in_rt",
      "cpu_utilization": "90-95%",
      "gpu_utilization": "95-100%"
    },
    "balanced": {
      "games": ["RDR2", "GTA V"],
      "fps_range": "120-140",
      "settings": "Ultra",
      "bottleneck": "none",
      "synergy": "excellent"
    },
    "simulation": {
      "games": ["MSFS 2024", "Cities II"],
      "fps_range": "60-90",
      "settings": "High-Ultra",
      "bottleneck": "none",
      "cpu_utilization": "70-85%"
    }
  },
  "overall_verdict": "Excellent 1440p gaming build",
  "upgrade_path": {
    "current_balance": 95,
    "next_cpu": null,
    "next_gpu": "RTX 4080 for 4K gaming"
  }
}
```

---

### 4. `GET /estimate-performance`

Estymacja wydajności komponentu w różnych rozdzielczościach.

**Request:**
```http
GET /estimate-performance?component=RTX4070&type=gpu
```

**Response:**
```json
{
  "component": "RTX 4070",
  "passmark_score": 28161,
  "estimated_performance": {
    "1080p_low": "300+ FPS",
    "1080p_high": "200+ FPS",
    "1080p_ultra": "150+ FPS",
    "1440p_high": "120+ FPS",
    "1440p_ultra": "100+ FPS",
    "4K_high": "70+ FPS",
    "4K_ultra": "50-60 FPS"
  },
  "category": "high-end",
  "gaming_tier": {
    "1080p": "ultra (144+ FPS)",
    "1440p": "ultra (100+ FPS)",
    "4K": "high (60+ FPS)"
  },
  "note": "Estimates based on synthetic benchmarks and real-world correlations"
}
```

---

## 🧮 Algorytm balansowania

### WAŻNE: Wagi ≠ Możliwość ignorowania komponentu!

**Wagi 80% CPU / 20% GPU** oznaczają **relatywną ważność dla bottlenecku**, ale **NIE** oznaczają że można wcisnąć GTX 1030 do Threadrippera!

Każdy komponent musi spełniać:
1. ✅ **Minimalny próg wydajności** dla danej kategorii
2. ✅ **Maksymalną różnicę tierów** (nie więcej niż 1-2 "oczka")
3. ✅ **Maksymalną różnicę score** (nie więcej niż 30-60 punktów)

---

### 1. Minimalne progi dla każdej kategorii:

```python
category_minimum_requirements = {
    "esport": {
        "min_cpu_score": 15,  # normalized 0-100
        "min_gpu_score": 10,
        "min_cpu_single_thread": 2000,
        "min_gpu_memory": 4  # GB VRAM
    },
    "aaa_gpu": {
        "min_cpu_score": 30,
        "min_gpu_score": 40,
        "min_cpu_cores": 6,
        "min_gpu_memory": 8
    },
    "balanced": {
        "min_cpu_score": 35,
        "min_gpu_score": 35,
        "min_cpu_cores": 6,
        "min_gpu_memory": 6
    },
    "simulation": {
        "min_cpu_score": 40,
        "min_gpu_score": 15,  # Nawet 10% wagi wymaga minimum!
        "min_cpu_cores": 8,
        "min_cpu_threads": 12
    }
}
```

**Przykład:** Cities Skylines II (90% CPU) nadal wymaga minimum GTX 1650, nie GTX 1030!

---

### 2. Maximum tier difference (system "oczek"):

```python
def check_tier_compatibility(cpu, gpu, category):
    """
    Sprawdza czy różnica tier nie jest za duża.
    Jeśli jest - podciąga słabszy komponent "oczko wyżej"
    """
    tier_values = {
        "low": 1,
        "mid": 2, 
        "high": 3,
        "ultra": 4
    }
    
    cpu_tier = tier_values[cpu['tier']]
    gpu_tier = tier_values[gpu['tier']]
    
    # Maksymalna różnica tierów
    max_tier_diff = {
        "esport": 1,      # CPU ultra + GPU high = OK
        "aaa_gpu": 1,     # GPU ultra + CPU high = OK
        "balanced": 1,    # Oba podobne (max 1 tier różnicy)
        "simulation": 2   # CPU ultra + GPU mid = OK (ale nie low!)
    }
    
    tier_diff = abs(cpu_tier - gpu_tier)
    
    if tier_diff > max_tier_diff[category['name']]:
        # Znajdź słabszy komponent i podciągnij go wyżej
        if cpu_tier < gpu_tier:
            target_tier = gpu_tier - max_tier_diff[category['name']]
            return {
                "compatible": False,
                "issue": "cpu_too_weak",
                "recommendation": f"Upgrade CPU to at least '{get_tier_name(target_tier)}' tier"
            }
        else:
            target_tier = cpu_tier - max_tier_diff[category['name']]
            return {
                "compatible": False,
                "issue": "gpu_too_weak",
                "recommendation": f"Upgrade GPU to at least '{get_tier_name(target_tier)}' tier"
            }
    
    return {"compatible": True}
```

---

### 3. Maximum score difference:

```python
def check_score_balance(cpu, gpu, category):
    """
    Nawet z wagami, różnica score nie może być zbyt duża
    """
    cpu_score = cpu['normalized_score']
    gpu_score = gpu['normalized_score']
    
    # Maksymalna dozwolona różnica (punkty)
    max_score_diff = {
        "esport": 50,      # CPU może być 50pkt lepsze od GPU
        "aaa_gpu": 50,     # GPU może być 50pkt lepsze od CPU
        "balanced": 30,    # Max 30pkt różnicy
        "simulation": 60   # CPU może być 60pkt lepsze
    }
    
    diff = abs(cpu_score - gpu_score)
    
    if diff > max_score_diff[category['name']]:
        if cpu_score < gpu_score:
            needed_score = gpu_score - max_score_diff[category['name']]
            return {
                "balanced": False,
                "weak_component": "cpu",
                "current_score": cpu_score,
                "recommended_min_score": needed_score,
                "action": "upgrade_cpu"
            }
        else:
            needed_score = cpu_score - max_score_diff[category['name']]
            return {
                "balanced": False,
                "weak_component": "gpu",
                "current_score": gpu_score,
                "recommended_min_score": needed_score,
                "action": "upgrade_gpu"
            }
    
    return {"balanced": True}
```

---

### 4. Wzór na balance score (z limitami):

```python
def calculate_balance_score(cpu, gpu, category):
    """
    Oblicza score dopasowania CPU+GPU dla danej kategorii gier
    Zwraca: 0-100 (100 = perfect balance)
    
    UWAGA: Sprawdza najpierw minimalne progi i tier compatibility!
    """
    # 1. Check minimum requirements
    min_reqs = category_minimum_requirements[category['name']]
    
    if cpu['normalized_score'] < min_reqs['min_cpu_score']:
        return 0  # Instant fail
    if gpu['normalized_score'] < min_reqs['min_gpu_score']:
        return 0  # Instant fail
    
    # 2. Check tier compatibility
    tier_check = check_tier_compatibility(cpu, gpu, category)
    if not tier_check['compatible']:
        return max(0, 30 - (tier_diff * 10))  # Penalty za złe tiery
    
    # 3. Check score balance
    balance_check = check_score_balance(cpu, gpu, category)
    if not balance_check['balanced']:
        penalty = abs(cpu['normalized_score'] - gpu['normalized_score']) / 2
        return max(0, 70 - penalty)
    
    # 4. Calculate weighted balance
    cpu_norm = cpu['normalized_score']
    gpu_norm = gpu['normalized_score']
    
    cpu_weight = category['cpu_importance']
    gpu_weight = category['gpu_importance']
    
    cpu_weighted = cpu_norm * cpu_weight
    gpu_weighted = gpu_norm * gpu_weight
    
    balance_diff = abs(cpu_weighted - gpu_weighted)
    balance_score = max(0, 100 - (balance_diff * 2))
    
    return balance_score
```

### Detekcja bottlenecku:

```python
def detect_bottleneck(cpu, gpu, category):
    """
    Wykrywa bottleneck w danej kategorii
    """
    ratio = (gpu['g3d_mark'] / cpu['passmark_score']) * 1000
    
    if category['cpu_importance'] > 0.6:  # CPU-heavy games
        if ratio > 1.2:
            return "cpu_bottleneck"
            
    elif category['gpu_importance'] > 0.6:  # GPU-heavy games
        if ratio < 0.8:
            return "gpu_bottleneck"
            
    else:  # Balanced games
        if ratio > 1.3:
            return "slight_cpu_bottleneck"
        elif ratio < 0.7:
            return "slight_gpu_bottleneck"
    
    return None  # No bottleneck
```

### Estymacja FPS:

```python
def estimate_fps(component, resolution, settings, game_category):
    """
    Estymuje FPS na podstawie PassMark score
    """
    base_score = component['passmark_score']
    
    # Scaling factors per category
    scaling = {
        'esport': 3.5,      # Lekkie gry
        'aaa_gpu': 1.2,     # Ciężkie AAA
        'balanced': 2.0,    # Średnie
        'simulation': 2.5   # CPU-bound
    }
    
    # Resolution penalty
    res_penalty = {
        '1080p': 1.0,
        '1440p': 0.65,
        '4K': 0.35
    }
    
    # Settings penalty
    settings_penalty = {
        'low': 1.2,
        'medium': 1.0,
        'high': 0.85,
        'ultra': 0.70
    }
    
    fps = (base_score / 1000) * scaling[game_category] * \
          res_penalty[resolution] * settings_penalty[settings]
    
    return round(fps)
```

---

## 📐 Korelacja PassMark ↔ FPS

### Założenia:

1. **PassMark ratio ≈ FPS ratio** (z tolerancją ±20%)
   ```
   GPU A: 10,000 PassMark
   GPU B: 20,000 PassMark
   → GPU B jest ~1.8-2.2x szybsze w grach
   ```

2. **Nie jest liniowe** - zależy od:
   - Typu gry (CPU/GPU bound)
   - Rozdzielczości
   - Architektury (RT, DLSS, FSR)
   - Optymalizacji silnika

3. **Bezpieczne użycie:**
   - ✅ Względne porównania ("GPU B jest 70% szybsze")
   - ✅ Kategorie wydajności ("Nadaje się do 1440p ultra")
   - ⚠️ Konkretne FPS (tylko jako estymacje z disclaimerem)

### Przykład walidacji:

| GPU | PassMark G3D | FPS Cyberpunk 1080p | FPS CS2 1080p | Ratio check |
|-----|-------------|---------------------|---------------|-------------|
| RTX 3060 | 17,048 | ~60 FPS | ~250 FPS | - |
| RTX 4070 | 28,161 | ~110 FPS | ~450 FPS | - |
| **Ratio** | **1.65x** | **1.83x** | **1.8x** | ✅ Korelacja |

---

## 🗂️ Struktura plików

```
app/
├── recommendation.py      # Logika rekomendacji i balansowania
├── gaming_profiles.py     # Profile gier i estymacje FPS
├── bottleneck_analyzer.py # Analiza bottlenecków
└── models.py              # Nowe modele Pydantic

Nowe modele:
- PairingAnalysisRequest
- PairingAnalysisResponse
- RecommendationRequest
- RecommendationResponse
- GamingProfileResponse
- PerformanceEstimate
```

---

## 📋 Przykłady działania limitów

### Przykład 1: Threadripper + GTX 1030 + Cities Skylines II ❌

```python
cpu = {
    "name": "Threadripper 5995WX",
    "normalized_score": 100,
    "tier": "ultra"
}

gpu = {
    "name": "GTX 1030",
    "normalized_score": 8,
    "tier": "low"
}

category = "simulation"  # 90% CPU / 10% GPU

# Check 1: Minimum requirements
✗ gpu_score (8) < min_gpu_score (15)

# Check 2: Tier difference
✗ tier_diff (3) > max_tier_diff (2)

# Check 3: Score difference  
✗ score_diff (92) > max_score_diff (60)
```

**Response:**
```json
{
  "compatible": false,
  "balance_score": 0,
  "issues": [
    "GPU below minimum requirements for simulation games",
    "GPU tier too low (low vs ultra CPU) - difference: 3 tiers",
    "Massive imbalance - GPU is 92 points behind"
  ],
  "recommendations": {
    "immediate": "Upgrade GPU to at least 'mid' tier (normalized score 25+)",
    "suggested_gpus": [
      {"name": "GTX 1650", "score": 25, "reason": "Minimum for simulation rendering"},
      {"name": "RX 6400", "score": 28, "reason": "Better value, modern"},
      {"name": "RTX 3050", "score": 35, "reason": "More future-proof"}
    ],
    "reason": "Even CPU-heavy games need minimum GPU performance for rendering"
  }
}
```

---

### Przykład 2: i3-12100F + RTX 4090 + Cyberpunk 2077 ❌

```python
cpu = {
    "name": "Intel i3-12100F",
    "normalized_score": 25,
    "tier": "low",
    "cores": 4
}

gpu = {
    "name": "RTX 4090",
    "normalized_score": 100,
    "tier": "ultra"
}

category = "aaa_gpu"  # 25% CPU / 75% GPU

# Check 1: Minimum requirements
✗ cpu_score (25) < min_cpu_score (30)
✗ cpu_cores (4) < min_cpu_cores (6)

# Check 2: Tier difference
✗ tier_diff (3) > max_tier_diff (1)

# Check 3: Score difference
✗ score_diff (75) > max_score_diff (50)
```

**Response:**
```json
{
  "compatible": false,
  "balance_score": 5,
  "issues": [
    "CPU below minimum for AAA games (25 vs required 30)",
    "CPU has only 4 cores, AAA games need 6+",
    "Massive CPU bottleneck - tier difference: 3",
    "RTX 4090 will be severely underutilized (~40% usage)"
  ],
  "performance_estimate": {
    "expected_fps": "70-90 @ 4K Ultra",
    "max_potential_fps": "120+ @ 4K Ultra",
    "performance_loss": "~40% of GPU potential wasted"
  },
  "recommendations": {
    "immediate": "Upgrade CPU to 'high' or 'ultra' tier",
    "suggested_cpus": [
      {"name": "Ryzen 7 7800X3D", "score": 75, "reason": "Best for gaming"},
      {"name": "Intel i7-14700K", "score": 80, "reason": "Great all-rounder"},
      {"name": "Ryzen 9 7900X", "score": 85, "reason": "Future-proof"}
    ],
    "reason": "Even GPU-heavy games need strong CPU for game logic, physics, AI"
  }
}
```

---

### Przykład 3: Ryzen 5 7600 + RTX 4060 + E-sport ✅

```python
cpu = {
    "name": "Ryzen 5 7600",
    "normalized_score": 45,
    "tier": "mid"
}

gpu = {
    "name": "RTX 4060",
    "normalized_score": 40,
    "tier": "mid"
}

category = "esport"  # 80% CPU / 20% GPU

# Check 1: Minimum requirements
✓ cpu_score (45) > min_cpu_score (15)
✓ gpu_score (40) > min_gpu_score (10)

# Check 2: Tier difference
✓ tier_diff (0) <= max_tier_diff (1)

# Check 3: Score difference
✓ score_diff (5) <= max_score_diff (50)
```

**Response:**
```json
{
  "compatible": true,
  "balance_score": 95,
  "performance": {
    "esport": {
      "fps_estimate": "300+ FPS in Valorant/CS2",
      "cpu_utilization": "70%",
      "gpu_utilization": "50%",
      "bottleneck": "none"
    }
  },
  "verdict": "Perfect pairing for competitive gaming",
  "notes": [
    "Excellent balance for e-sport titles",
    "CPU strong enough to push high FPS",
    "GPU won't bottleneck at 1080p competitive settings",
    "Upgrade not needed for this use case"
  ]
}
```

---

### Przykład 4: Ryzen 9 7950X + RTX 4070 Ti + Balanced ✅

```python
cpu = {
    "name": "Ryzen 9 7950X",
    "normalized_score": 85,
    "tier": "ultra"
}

gpu = {
    "name": "RTX 4070 Ti",
    "normalized_score": 75,
    "tier": "high"
}

category = "balanced"  # 50% CPU / 50% GPU

# Check 1: Minimum requirements
✓ Both way above minimums

# Check 2: Tier difference
✓ tier_diff (1) <= max_tier_diff (1)

# Check 3: Score difference
✓ score_diff (10) <= max_score_diff (30)
```

**Response:**
```json
{
  "compatible": true,
  "balance_score": 92,
  "performance": {
    "balanced_games": {
      "fps_estimate": "120+ FPS @ 1440p Ultra",
      "cpu_utilization": "65%",
      "gpu_utilization": "90%",
      "bottleneck": "slight_gpu (optimal)",
      "synergy": "excellent"
    }
  },
  "verdict": "Excellent pairing for AAA gaming",
  "notes": [
    "Slight GPU bottleneck is GOOD - means GPU is fully utilized",
    "CPU has headroom for background tasks",
    "Great for streaming while gaming",
    "Next upgrade: RTX 4080 for 4K gaming"
  ]
}
```

---

## 🎮 Przykłady użycia API

### Use Case 1: Użytkownik ma CPU, chce kupić GPU

```bash
curl "http://localhost:9091/recommend-pairing?cpu=7800X3D&game_focus=aaa_gpu&budget_max=800"
```

Dostaje listę najlepiej zbilansowanych GPU w budżecie.

### Use Case 2: Sprawdzenie istniejącego buildu

```bash
curl -X POST http://localhost:9091/analyze-pairing \
  -H "Content-Type: application/json" \
  -d '{"cpu": "i5-13400F", "gpu": "RTX 4090"}'
```

Response: "MASSIVE CPU bottleneck w AAA grach - wymień CPU na 7800X3D/14700K"

### Use Case 3: Planowanie buildu pod konkretne gry

```bash
curl "http://localhost:9091/gaming-profile?components=5700X3D,RX7800XT&resolution=1440p"
```

Dostaje kompletny profil wydajności we wszystkich kategoriach gier.

---

## 🔮 Przyszłe rozszerzenia

- [ ] **Budżetowy rekomendator** - "Najlepszy build za 4000 PLN"
- [ ] **Analiza RAM/Storage** - wpływ na performance
- [ ] **Power consumption** - szacowanie poboru mocy (TDP)
- [ ] **Cooling requirements** - wymagania chłodzenia
- [ ] **Price/Performance ratio** - best value rekomendacje
- [ ] **Upgrade path calculator** - "Co wymienić najpierw?"
- [ ] **VR readiness** - analiza pod VR gaming

---

## 🎓 Kluczowe wnioski z analizy

### 1. Wagi nie są wystarczające

**Problem:** Wagi 90% CPU / 10% GPU mogą sugerować że GPU nie ma znaczenia.  
**Rozwiązanie:** System trójstopniowy:
- ✅ Minimum requirements (próg wejścia)
- ✅ Tier matching (max 1-2 "oczka" różnicy)
- ✅ Score difference (max 30-60 punktów różnicy)

### 2. Podciąganie słabszego komponentu

**Zasada:** Jeśli różnica jest za duża → rekomenduj upgrade słabszego.

**Przykład:**
```
CPU: Ultra tier (score 100)
GPU: Low tier (score 8)
Game: Simulation (90% CPU)

❌ Nie: "GPU wystarczy, to CPU-heavy game"
✅ Tak: "Upgrade GPU to minimum Mid tier (score 25+)"
```

### 3. Slight bottleneck może być OK!

**GPU bottleneck (5-15%)** = GPU w pełni wykorzystane = **DOBRZE**  
**CPU bottleneck (5-15%)** = CPU w pełni wykorzystane = **DOBRZE**

Dopiero przy >20% bottleneck = problem.

---

## 📝 Notatki implementacyjne

### Dane dostępne w bazie:

✅ **CPU:**
- `passmark_score` - ogólna wydajność
- `single_thread_rating` - ważne dla e-sport/simulation
- `cores` / `threads` - multi-threading
- `base_clock` / `boost_clock`
- `cache` / `l3_cache` - ważne dla gaming

✅ **GPU:**
- `g3d_mark` - główny score
- `memory_size` - VRAM
- `cuda_cores` - NVIDIA
- `memory_bandwidth`

✅ **Normalizacja:**
- `normalized_score` (0-100) - już zaimplementowane
- `tier` (low/mid/high/ultra) - już zaimplementowane

### Co trzeba dodać:

- Logika balansowania według wag kategorii
- Algorytm detekcji bottlenecków
- Estymacje FPS (z disclaimerem)
- System rekomendacji z filtrowaniem
- Scoring pairingu

---

## ⚖️ Disclaimer

> **Uwaga:** Wszystkie estymacje FPS są przybliżone i bazują na korelacji z syntetycznymi benchmarkami PassMark. Rzeczywista wydajność zależy od wielu czynników:
> - Optymalizacji sterowników
> - Konkretnej gry i jej wersji
> - Ustawień graficznych
> - Pozostałych komponentów (RAM, storage)
> - Temperatury i throttlingu
> 
> System służy jako **narzędzie pomocnicze** do planowania buildów, nie jako źródło dokładnych pomiarów.

---

**Wersja:** 1.0  
**Data:** 2025-10-20  
**Status:** Projekt konceptualny - gotowy do implementacji

