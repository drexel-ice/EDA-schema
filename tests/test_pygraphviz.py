import pygraphviz as pgv
def test_pygraphviz_installation():
    """
    test_pygraphviz_installation

    This function tests the installation of the pygraphviz library. It attempts to print the version of pygraphviz if it is installed. If pygraphviz is not installed, it catches the ImportError and prints a message indicating that pygraphviz is not installed.

    Raises:
        ImportError: If pygraphviz is not installed.
    """
    try:
        print("pygraphviz is installed correctly.")
        print(f"pygraphviz version: {pgv.__version__}")
    except ImportError:
        print("pygraphviz is not installed.")

test_pygraphviz_installation()