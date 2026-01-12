#!/usr/bin/env python3
"""
Example: Using MongoDB

Description: Demonstrates using MongoDB backend for distributed storage.

Prerequisites:
- EDA-schema installed
- MongoDB running (or connection string)
- pymongo

Key Concepts:
- MongoDB initialization
- Collection storage
- Distributed storage
- MongoDB queries

Usage:
    python examples/07_database_backends/04_mongodb.py [mongodb_uri] [db_name]
"""

import sys

from eda_schema import entity
from eda_schema.dataset import Dataset
from eda_schema.db import MongoDB


def demonstrate_mongodb_basic(mongodb_uri: str, db_name: str):
    """Demonstrate basic MongoDB usage."""
    print("=" * 60)
    print("MongoDB: Basic Usage")
    print("=" * 60)

    try:
        # Initialize MongoDB
        db = MongoDB(mongodb_uri, db_name)
        db.create_dataset_tables()
        print(f"Connected to MongoDB: {db_name}")
 
        # Add data
        flow_id = 'test_flow'
        stage = 'floorplan'
 
        # Add gates
        for i in range(5):
            gate = entity.GateEntity(
                flow_id=flow_id,
                stage=stage,
                name=f'U{i+1}',
                standard_cell='NAND2_X1',
                x_min=10.0 + i * 20.0,
                y_min=10.0,
                x_max=15.0 + i * 20.0,
                y_max=15.0,
                no_of_inputs=2,
                no_of_outputs=1
            )
            db.add_table_row('gates', gate.get_tabular_data())
 
        print("Added 5 gates")
 
        # Read data
        gates_df = db.get_table_data('gates')
        print(f"Retrieved {len(gates_df)} gates")
        print()

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: MongoDB must be running and accessible")
        print("Example: mongodb://localhost:27017")
        print()


def main():
    """Main function."""
    if len(sys.argv) > 2:
        mongodb_uri = sys.argv[1]
        db_name = sys.argv[2]
    else:
        mongodb_uri = "mongodb://localhost:27017"
        db_name = "eda_schema_test"
        print(f"Using default: {mongodb_uri}/{db_name}")
        print("(Provide URI and DB name as arguments if different)\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: MongoDB Backend")
    print("=" * 60 + "\n")

    demonstrate_mongodb_basic(mongodb_uri, db_name)

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nKey Points:")
    print("  - Tables stored in MongoDB collections")
    print("  - Good for distributed systems")
    print("  - Requires MongoDB server running")
    print()


if __name__ == "__main__":
    main()
