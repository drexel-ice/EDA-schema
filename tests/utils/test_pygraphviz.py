import pytest

def test_pygraphviz_installation():
    """
    Test that pygraphviz is installed correctly and its version can be accessed.
    """
    try:
        import pygraphviz as pgv
        assert hasattr(pgv, '__version__'), "pygraphviz is installed but version attribute is missing."
        print(f"pygraphviz version: {pgv.__version__}")
    except ImportError:
        raise AssertionError("pygraphviz is not installed or not properly configured.")
