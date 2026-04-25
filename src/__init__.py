"""MMORPG - A 2D MMORPG game engine in Python."""

__version__ = "1.0.0"
__author__ = "MMORPG Engine Team"

from . import protocol
from . import world
from . import server
from . import client
from . import utils

__all__ = [
    "protocol",
    "world",
    "server",
    "client",
    "utils",
]
