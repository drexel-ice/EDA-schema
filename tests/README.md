# EDA Schema Test Suite

Comprehensive pytest test suite for the `eda_schema` library.

## Structure

The test suite is organized into 4 simple categories:

```
tests/
├── conftest.py              # Shared fixtures and test utilities
├── README.md               # This file
├── unit/                   # Core functionality unit tests
│   ├── test_base.py        # BaseEntity and GraphEntity tests
│   ├── test_entities.py    # All entity classes tests
│   ├── test_errors.py      # Custom exceptions tests
│   ├── test_dataset.py     # Dataset class tests
│   ├── test_db.py          # Database backend tests
│   ├── test_json_utils.py  # JSON utilities tests
│   ├── test_protobuf_io.py # Protobuf serialization tests
│   ├── test_grpc_server.py # gRPC server tests
│   ├── test_schema_metadata.py # SchemaMetadata registry tests
│   └── test_edge_cases.py  # Edge case tests
├── integration/            # Integration tests
│   ├── test_integration.py # Complete workflows and multi-component tests
│   └── test_edaschema_to_protobuf.py # EDA schema ↔ Protobuf conversion tests
├── data/                   # Dataset and database tests with real data
│   └── test_sample_dataset.py # Tests using real dataset samples
└── utils/                  # Utility function tests
    ├── test_netlist_diff.py # Netlist comparison utilities tests
    └── test_pygraphviz.py   # PyGraphviz integration tests
```

## Running Tests

### Fast Development Workflow

**Run only fast tests (recommended for development):**
```bash
pytest tests/ -m "not slow"
```
This runs unit tests only (~0.8 seconds) and skips slow integration/data tests.

**Run all tests (including slow ones):**
```bash
pytest tests/
```

### Running Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit/

# Integration tests only (slow - uses real datasets)
pytest tests/integration/

# Data/database tests with real data (slow)
pytest tests/data/

# Utility tests (slow - uses real datasets)
pytest tests/utils/
```

### Other Options

Run specific test file:
```bash
pytest tests/unit/test_base.py
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run with coverage (slower):
```bash
pytest tests/ --cov=eda_schema --cov-report=html
```

Run tests in parallel (requires pytest-xdist):
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

## Test Categories

### Unit Tests (`tests/unit/`)

Core functionality unit tests covering all major components:

- **test_base.py** - Tests for BaseEntity and GraphEntity base classes
  - BaseEntity creation and validation
  - Tabular and image data extraction
  - Type validation
  - GraphEntity graph operations
  - Node and edge management
  - Graph traversal methods

- **test_entities.py** - Tests for all entity classes
  - All entity types (NetlistEntity, GateEntity, PortEntity, etc.)
  - Entity creation with required and optional fields
  - Entity validation
  - DesignStages enum

- **test_errors.py** - Tests for custom exceptions
  - EDASchemaError
  - ValidationError
  - DataNotFoundError

- **test_dataset.py** - Tests for Dataset class
  - Dataset creation and initialization
  - StandardCellData management
  - Standard cell loading and dumping

- **test_db.py** - Tests for database backends
  - ParquetDB operations
  - Entity storage and retrieval
  - Error handling for missing data

- **test_json_utils.py** - Tests for JSON utilities
  - JSON serialization/deserialization
  - File operations

- **test_protobuf_io.py** - Tests for Protobuf serialization/deserialization
  - Protobuf I/O operations
  - Entity conversion to/from Protobuf
  - File save/load operations

- **test_grpc_server.py** - Tests for gRPC server implementation
  - gRPC server functionality
  - Import/export operations
  - Request/response handling

- **test_schema_metadata.py** - Tests for SchemaMetadata registry
  - Entity metadata registration
  - Primary key extraction
  - Graph entity detection

- **test_edge_cases.py** - Edge case tests
  - Boundary conditions
  - Invalid input handling
  - Error scenarios

### Integration Tests (`tests/integration/`)

- **test_integration.py** - Complete workflows and multi-component tests
  - Multi-entity interactions
  - Graph operations
  - Image handling
  - Error scenarios
  - Multi-stage workflows

- **test_edaschema_to_protobuf.py** - EDA schema to/from Protobuf conversion tests
  - End-to-end conversion workflows
  - Round-trip conversion (EDA → Protobuf → EDA)
  - Data preservation validation
  - Metrics equality checks (cell, area, power, timing)
  - Uses real dataset (`dataset/test`)

### Data Tests (`tests/data/`)

- **test_sample_dataset.py** - Tests using real dataset samples
  - Real dataset loading and operations
  - Production data validation
  - Netlist sanity checks across design stages
  - Clock tree structure validation

### Utils Tests (`tests/utils/`)

- **test_netlist_diff.py** - Tests for netlist comparison utilities
  - Netlist comparison and diffing
  - Cell and net mapping
  - Comparison across design stages

- **test_pygraphviz.py** - Tests for PyGraphviz integration (if available)
  - Graph visualization
  - Export to Graphviz format

## Fixtures

The test suite includes reusable fixtures in `conftest.py` (at the root of `tests/`):
- `temp_dir` - Temporary directory for test data
- `sample_netlist_data` - Sample NetlistEntity data
- `sample_gate_data` - Sample GateEntity data
- `sample_port_data` - Sample PortEntity data
- `sample_pin_data` - Sample PinEntity data
- `sample_net_data` - Sample NetEntity data
- `sample_power_metrics_data` - Sample PowerMetricsEntity data
- `sample_area_metrics_data` - Sample AreaMetricsEntity data
- `sample_cell_metrics_data` - Sample CellMetricsEntity data
- `sample_timing_metrics_data` - Sample TimingMetricsEntity data
- `sample_routability_metrics_data` - Sample RoutabilityMetricsEntity data
- `sample_standard_cell_data` - Sample StandardCellEntity data
- `sample_net_arc_data` - Sample NetArcEntity data
- `sample_cell_arc_data` - Sample CellArcEntity data
- `sample_pdn_data` - Sample PDNEntity data
- `sample_clock_tree_data` - Sample ClockTreeEntity data
- `sample_dataset` - Sample Dataset instance
- `sample_file_db` - Sample FileDB instance

## Requirements

- pytest
- eda_schema library
- All eda_schema dependencies

## Notes

- Tests use temporary directories that are automatically cleaned up
- Some tests may be skipped if certain features aren't available (e.g., PyGraphviz)
- Integration tests require more setup and may take longer to run
- Tests in `data/test_sample_dataset.py` and `utils/test_netlist_diff.py` require the `dataset/test` directory to exist
- The `conftest.py` file at the root of `tests/` is automatically discovered by pytest and provides fixtures to all test files
- Total: **120 tests** covering all major functionality
