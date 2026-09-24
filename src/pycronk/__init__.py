try:
    from pycronk._version import __version__
except ImportError:  # ejecutando desde el árbol de fuentes sin instalar
    __version__ = "0.0.0"

__all__ = ["__version__"]
