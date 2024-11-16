"""Application to help track prodcution information at Wetering Potlilium"""

try:
    from importlib.metadata import version
    __version__ = version("production_control")
except Exception:
    __version__ = "unknown"
