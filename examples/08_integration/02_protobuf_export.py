#!/usr/bin/env python3
"""
Example: Protobuf Export

Description: Demonstrates exporting entities to Protobuf format.

Prerequisites:
- EDA-schema installed
- Protobuf support

Key Concepts:
- Protobuf serialization
- Entity conversion
- Export workflow
- Round-trip conversion

Usage:
    python examples/08_integration/02_protobuf_export.py [dataset_path] [output_path]
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB
from eda_schema.serialization.protobuf_io import save_entity_to_protobuf


def export_entities_to_protobuf(dataset: Dataset, flow_id: str, stage: str, 
                                output_path: str):
    """Export entities to Protobuf format."""
    print("=" * 60)
    print(f"Exporting to Protobuf: {flow_id}/{stage}")
    print("=" * 60)

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Export netlist
        netlist = dataset.load_netlist(flow_id, stage)
        netlist_path = output_dir / f"netlist_{flow_id}_{stage}.pb"
        save_entity_to_protobuf(netlist, str(netlist_path))
        print(f"Exported netlist: {netlist_path}")

        # Export metrics
        try:
            power = dataset.db.get_entity('power_metrics', flow_id=flow_id, stage=stage)
            power_path = output_dir / f"power_{flow_id}_{stage}.pb"
            save_entity_to_protobuf(power, str(power_path))
            print(f"Exported power metrics: {power_path}")
        except:
            print("Power metrics not available")

        try:
            area = dataset.db.get_entity('area_metrics', flow_id=flow_id, stage=stage)
            area_path = output_dir / f"area_{flow_id}_{stage}.pb"
            save_entity_to_protobuf(area, str(area_path))
            print(f"Exported area metrics: {area_path}")
        except:
            print("Area metrics not available")

        print()

    except Exception as e:
        print(f"Error exporting: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 02_protobuf_export.py <dataset_path> [output_path]")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    output_path = sys.argv[2] if len(sys.argv) > 2 else "protobuf_output"

    print("\n" + "=" * 60)
    print("EDA-Schema: Protobuf Export")
    print("=" * 60 + "\n")

    # Load dataset
    db = ParquetDB(str(dataset_path))
    dataset = Dataset(db)
    dataset.load_standard_cells()

    try:
        flows_df = dataset.db.get_table_data('design_flows')
        if flows_df.empty:
            print("No flows available")
            return

        flow_id = flows_df.iloc[0]['flow_id']
        stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
 
        if stages_df.empty:
            print("No stages available")
            return

        stage = stages_df.iloc[0]['stage']

        export_entities_to_protobuf(dataset, flow_id, stage, output_path)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print(f"\nProtobuf files saved to: {output_path}")
    print()


if __name__ == "__main__":
    main()

