# Feature Tracking

> Quick reference for all planned, in-progress, and completed features.  
> See `.cursor/rules/feature-tracking.mdc` for workflow details.

---

## 🚧 In Progress

| Feature | Scope | Branch | Notes |
|---------|-------|--------|-------|
| Project restructuring for multi-language | setup | - | Phase A complete |

---

## 📋 Backlog

### Python Implementation (Phase B)

- [ ] **[python/utils]** P1: Extract haversine_vectorized from existing code
- [ ] **[python/utils]** P1: Extract is_point_in_polygon_vectorized
- [ ] **[python/utils]** P1: Extract HTTP retry session logic
- [ ] **[python/utils]** P2: Add coordinate validation helpers
- [ ] **[python/utils]** P2: Add CSV loading utility
- [ ] **[python/models]** P1: Create DisasterType enum
- [ ] **[python/models]** P1: Create Location dataclass
- [ ] **[python/models]** P1: Create DisasterResult base class
- [ ] **[python/models]** P1: Create HurricaneResult class
- [ ] **[python/models]** P1: Create TornadoResult class
- [ ] **[python/models]** P1: Create WildfireResult class
- [ ] **[python/models]** P2: Create severity enums
- [ ] **[python/hurricanes]** P1: Create fetch_active_hurricanes()
- [ ] **[python/hurricanes]** P1: Create get_hurricanes_near_location()
- [ ] **[python/hurricanes]** P2: Add cone distance calculation
- [ ] **[python/tornadoes]** P1: Create fetch_recent_tornadoes()
- [ ] **[python/tornadoes]** P1: Create get_tornadoes_near_location()
- [ ] **[python/wildfires]** P1: Create fetch_active_wildfires()
- [ ] **[python/wildfires]** P1: Create get_wildfires_near_location()
- [ ] **[python/wildfires]** P2: Add perimeter distance calculation
- [ ] **[python/cli]** P1: Create main.py CLI entry point
- [ ] **[python/cli]** P1: Support --lat/--lon arguments
- [ ] **[python/cli]** P1: Support --csv argument
- [ ] **[python/cli]** P2: Support --json output
- [ ] **[python/cli]** P2: Support --type filtering
- [ ] **[python/cli]** P3: Add progress indicators
- [ ] **[python]** P1: Create unified get_nearby_disasters() interface

### Rust Implementation (Phase C - Future)

- [ ] **[rust]** P3: Set up Cargo project structure
- [ ] **[rust]** P3: Port data models from Python
- [ ] **[rust]** P3: Port utility functions
- [ ] **[rust]** P3: Port hurricane module
- [ ] **[rust]** P3: Port tornado module
- [ ] **[rust]** P3: Port wildfire module
- [ ] **[rust]** P3: Create CLI with clap

### Enhancements (Future)

- [ ] **[all]** P3: Add caching for API responses
- [ ] **[all]** P3: Add rate limiting protection
- [ ] **[python/cli]** P3: Add rich console output
- [ ] **[docs]** P3: Create API documentation
- [ ] **[test]** P2: Add unit tests for distance calculations
- [ ] **[test]** P2: Add integration tests with mocked APIs

---

## ✅ Completed

### Phase A - Project Setup (Jan 2026)

- [x] **[setup]** Create multi-language project structure ✓
- [x] **[setup]** Create shared/data/test_locations.csv ✓
- [x] **[setup]** Create shared/specs/api-endpoints.md ✓
- [x] **[setup]** Create shared/specs/data-models.md ✓
- [x] **[setup]** Create python/ directory structure ✓
- [x] **[setup]** Create rust/ directory placeholder ✓
- [x] **[setup]** Create .cursor/rules for project standards ✓
- [x] **[setup]** Create IMPLEMENTATION_PLAN.md ✓
- [x] **[docs]** Create root README.md ✓
- [x] **[docs]** Create python/README.md ✓
- [x] **[docs]** Create rust/README.md ✓

---

## ❌ Cancelled

_None_

---

## Legend

| Symbol | Meaning |
|--------|---------|
| `P0` | Critical - Must have |
| `P1` | High - Core functionality |
| `P2` | Medium - Important |
| `P3` | Low - Nice to have |
| `🚧` | In Progress |
| `⏸️` | On Hold |
| `✓` | Completed |

