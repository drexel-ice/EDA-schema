

## Getting Started

### Installation

The key dependencies that are required by EDA-schema are the following

- python3.6 or beyond
- pip3

Clone the [repository](https://github.com/drexel-ice/eda-schema) and use [pip](https://pip.pypa.io/en/stable/) for installation.

```bash
$ git clone git@github.com:drexel-ice/eda-schema.git
$ cd eda-schema
$ pip install -e .
```

### Get Open Dataset

To use the dataset, download the data dump and use the following commands.
```python
from eda_schema.dataset import Dataset
from eda_schema.db import SQLitePickleDB

DATASET_DIR = "../dataset/dataset_openroad_sky130hd_iwls05_v1.1_final"
dataset = Dataset(SQLitePickleDB(DATASET_DIR<path_to_the_data_dump>
```
