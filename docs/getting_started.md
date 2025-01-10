

## Getting Started

### Installation

The key dependencies that are required by EDA-schema are the following

- python3.6 or beyond
- pip3
- mongoDB

Clone the [repository](https://github.com/drexel-ice/eda-schema) and use [pip](https://pip.pypa.io/en/stable/) for installation.

```bash
$ git clone git@github.com:drexel-ice/eda-schema.git
$ cd eda-schema
$ pip install -e .
```

### Get Open Dataset

To use the dataset, first download the zip file of mongoDB data dump, unzip it, and execute the follwing command.
```bash
$ sudo systemctl stop mongod
$ mongod --dbpath <path_to_the_data_dump>
```
