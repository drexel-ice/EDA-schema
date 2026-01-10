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
