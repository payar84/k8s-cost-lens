"""CLI package for k8s-cost-lens."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("k8s-cost-lens")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["__version__"]
