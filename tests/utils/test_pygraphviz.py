# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/utils/test_pygraphviz.py
# Authors :
#     Pratik Shrestha       <ps937@drexel.edu>
#     Amit Varde            <avv39@drexel.edu>
#
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike
# 4.0 International License (CC BY-NC-SA 4.0). You may obtain a copy of the
# license at: https://creativecommons.org/licenses/by-nc-sa/4.0/
#
# This software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. Commercial use is
# expressly prohibited; derivative works must be shared under the same
# license terms (ShareAlike).

"""Test pygraphviz installation and version."""
try:
    import pygraphviz as pgv
except ImportError:
    pgv = None


def test_pygraphviz_installation():
    """
    Test that pygraphviz is installed correctly and its version can be accessed.
    """
    if pgv is None:
        raise AssertionError("pygraphviz is not installed or not properly configured.")
    assert hasattr(pgv, '__version__'), "pygraphviz is installed but version attribute is missing."
    print(f"pygraphviz version: {pgv.__version__}")
