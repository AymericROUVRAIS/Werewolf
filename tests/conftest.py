"""Test setup.

``werewolf_bot.session`` only needs a few exception classes and
``PermissionOverwrite`` from discord.py. When discord.py isn't installed
(e.g. a minimal CI image) a tiny stand-in is registered so the game logic
can still be tested. With discord.py installed, the real module is used.
"""

import importlib.util
import sys
import types

if importlib.util.find_spec("discord") is None:
    stub = types.ModuleType("discord")

    class HTTPException(Exception):
        pass

    class Forbidden(HTTPException):
        pass

    class PermissionOverwrite:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    stub.HTTPException = HTTPException
    stub.Forbidden = Forbidden
    stub.PermissionOverwrite = PermissionOverwrite
    sys.modules["discord"] = stub
