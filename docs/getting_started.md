

## Getting Started

### Installation

Install the Python dependencies with a modern interpreter (Python 3.11 or newer is recommended) and pip.

- python3.11+
- pip3

```bash
# Clone the repository and install in editable mode
git clone https://github.com/drexel-ice/eda-schema.git
cd eda-schema
# (optional) create and activate a venv
python3 -m venv .venv
source .venv/bin/activate

# Install the package in editable mode
pip install -e .
```

### Download the Open Dataset

Download the latest EDA-Schema dataset release from the Google Drive link in the main README. You can continue using the legacy SQLite/Pickle snapshot, or point to the newer Parquet-based V2 dataset that powers the `research/eda-schema-v2/` workflows.

```bash
export EDA_SCHEMA_V2_DATASET="/path/to/eda-schema-v2"
```

```python
import os
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB

dataset_root = Path(os.environ["EDA_SCHEMA_V2_DATASET"]) / "nangate45"
dataset = Dataset(ParquetDB(dataset_root))
```
