.. EDA-Schema documentation master file, created by
   sphinx-quickstart on Thu Jun  6 17:35:34 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to EDA-Schema's documentation!
======================================

EDA-schema is a property graph datamodel schema developed to represent digital circuit designs and the associated attributes.
The contributions of this work include:

#. A standardized set of graph structures and feature sets representing a digital circuit and corresponding subcomponents
#. A dataset of physical designs generated from the IWLS'05 benchmark circuit suite utilizing the open-source 130 nm Process Design Kit (PDK) provided by Skywater and the open-source toolset OpenROAD

NOTE: This GitHub repository is still in the development phase. We are actively working on adding new features, fixing bugs, and enhancing the overall functionality. We appreciate your patience and understanding as we work to finalize the project.

.. mdinclude:: datamodel.md

.. mdinclude:: open_dataset.md

.. mdinclude:: getting_started.md

.. mdinclude:: cite.md


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   eda_schema
   datamodel
   open_dataset
   cite
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
