# Feature Tracking

> Quick reference for all planned, in-progress, and completed features.  
> See `.cursor/rules/feature-tracking.mdc` for workflow details.

---

## 🚧 In Progress

| Feature | Scope | Branch | Notes |
|---------|-------|--------|-------|
| Interactive CLI | python/cli | feature/interactive-cli | Arrow-key menus, colored output, ASCII art |

---

## 📋 Backlog

### Interactive CLI (Phase D)

- [ ] **[python/cli]** P1: Create interactive mode (no args required)
- [ ] **[python/cli]** P1: Add ASCII art banner on startup
- [ ] **[python/cli]** P1: Add colored terminal output (rich/colorama)
- [ ] **[python/cli]** P1: Add arrow-key menu navigation (questionary)
- [ ] **[python/cli]** P1: Add coordinate input with format validation
- [ ] **[python/cli]** P2: Add disaster type multi-select menu
- [ ] **[python/cli]** P2: Add radius selection menu
- [ ] **[python/cli]** P2: Add "query again" loop option
- [ ] **[python/cli]** P3: Add loading spinners during API calls

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
- [ ] **[docs]** P3: Create API documentation
- [ ] **[test]** P2: Add unit tests for distance calculations
- [ ] **[test]** P2: Add integration tests with mocked APIs

---

## ✅ Completed

### Phase B - Python Implementation (Jan 2026)

- [x] **[python/utils]** Extract haversine_vectorized from existing code ✓
- [x] **[python/utils]** Extract is_point_in_polygon_vectorized ✓
- [x] **[python/utils]** Extract HTTP retry session logic ✓
- [x] **[python/utils]** Add coordinate validation helpers ✓
- [x] **[python/utils]** Add CSV loading utility ✓
- [x] **[python/models]** Create DisasterType enum ✓
- [x] **[python/models]** Create Location dataclass ✓
- [x] **[python/models]** Create DisasterResult base class ✓
- [x] **[python/models]** Create HurricaneResult class ✓
- [x] **[python/models]** Create TornadoResult class ✓
- [x] **[python/models]** Create WildfireResult class ✓
- [x] **[python/models]** Create severity enums ✓
- [x] **[python/hurricanes]** Create fetch_active_hurricanes() ✓
- [x] **[python/hurricanes]** Create get_hurricanes_near_location() ✓
- [x] **[python/hurricanes]** Add cone distance calculation ✓
- [x] **[python/tornadoes]** Create fetch_recent_tornadoes() ✓
- [x] **[python/tornadoes]** Create get_tornadoes_near_location() ✓
- [x] **[python/wildfires]** Create fetch_active_wildfires() ✓
- [x] **[python/wildfires]** Create get_wildfires_near_location() ✓
- [x] **[python/wildfires]** Add perimeter distance calculation ✓
- [x] **[python/cli]** Create main.py CLI entry point ✓
- [x] **[python/cli]** Support --lat/--lon arguments ✓
- [x] **[python/cli]** Support --csv argument ✓
- [x] **[python/cli]** Support --json output ✓
- [x] **[python/cli]** Support --type filtering ✓
- [x] **[python]** Create unified get_nearby_disasters() interface ✓

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

