# Natural Disaster Distance Monitor - Rust Implementation

🚧 **Status: Planned** - This implementation is not yet started.

## Overview

High-performance Rust implementation of the Natural Disaster Distance Monitor CLI tool.

## Planned Features

- Async HTTP requests with `reqwest` and `tokio`
- Zero-copy JSON parsing with `serde`
- CLI parsing with `clap`
- Identical output format to Python implementation

## Project Structure (Planned)

```
rust/
├── README.md              # This file
├── Cargo.toml             # Rust dependencies
└── src/
    ├── main.rs            # CLI entry point
    ├── lib.rs             # Library exports
    ├── models.rs          # Data structures
    ├── utils.rs           # Haversine, polygon checks
    ├── hurricanes.rs      # Hurricane API client
    ├── tornadoes.rs       # Tornado API client
    └── wildfires.rs       # Wildfire API client
```

## Planned Dependencies

```toml
[dependencies]
reqwest = { version = "0.11", features = ["json"] }
tokio = { version = "1", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
clap = { version = "4.0", features = ["derive"] }
csv = "1.3"
chrono = { version = "0.4", features = ["serde"] }
```

## Getting Started (After Implementation)

```bash
cd rust
cargo build --release

# Single location query
./target/release/disaster-monitor --lat 29.7604 --lon -95.3698

# Batch query from CSV
./target/release/disaster-monitor --csv ../shared/data/test_locations.csv

# JSON output
./target/release/disaster-monitor --lat 29.7604 --lon -95.3698 --json
```

## Implementation Notes

The Rust implementation should:

1. Match the Python CLI interface exactly
2. Produce identical JSON output
3. Use async/await for concurrent API requests
4. Handle errors gracefully with `Result<T, E>`

## Contributing

If you'd like to implement the Rust version:

1. Follow the specs in `../shared/specs/`
2. Use the test data in `../shared/data/test_locations.csv`
3. Ensure output matches Python implementation
4. Add tests for all core functions

