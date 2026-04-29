.. EDA-Schema documentation master file, created by
   sphinx-quickstart on Thu Jun  6 17:35:34 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to EDA-Schema's documentation!
======================================

EDA-Schema is a **multimodal datamodel schema** developed to represent digital circuit designs and their associated structural, spatial, electrical, and performance attributes throughout the RTL to GDSII physical design flow. The schema provides a unified representation of circuits using heterogeneous graphs, spatial image representations, scalar heatmaps, and structured metric entities, enabling standardized analysis and machine learning applications in digital physical design.

The contributions of this work include:

#. A **standardized multimodal schema** for representing digital circuits, including netlist, clock network, timing path, power delivery network, and quality-of-results entities
#. A **large scale open dataset** of physical designs generated from the IWLS'05 benchmark suite across multiple open source PDKs, including stage resolved multimodal representations spanning synthesis through final routing
#. **Open tooling and workflows** to query, analyze, visualize, and benchmark graph, image, heatmap, and metric based design representations
#. A **benchmarking framework for machine learning in EDA**, including standardized prediction tasks across timing, power, area, parasitics, routing, and physical design quality metrics

NOTE: This GitHub repository is still in the development phase. We are actively working on adding new features, fixing bugs, and enhancing the overall functionality. We appreciate your patience and understanding as we work to finalize the project.

.. mdinclude:: datamodel.md

.. mdinclude:: open_dataset.md

.. mdinclude:: getting_started.md

.. mdinclude:: cite.md


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   eda_schema

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
