from typer import Typer

from . import commands, config_logging

app = Typer()
app.add_typer(config_logging.app)
app.add_typer(commands.app)

__all__ = ["app"]
