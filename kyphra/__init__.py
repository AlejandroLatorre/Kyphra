"""Kyphra — privacy and confidentiality classifier for developer AI prompts."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("kyphra")
except PackageNotFoundError:
    __version__ = "0.0.0+local"
