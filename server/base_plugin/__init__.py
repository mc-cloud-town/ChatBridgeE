from .. import BaseServer
from .commands import setup as commands_setup
from .events import setup as events_setup


def setup(server: "BaseServer"):
    commands_setup(server)
    events_setup(server)
