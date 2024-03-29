from typer import Typer

from . import commands, config_logging

app = Typer()
app.command()(commands.run)
app.command()(commands.server)
app.command(name="list")(commands.list_test_groups)
app.callback()(config_logging.set_logging_level)

__all__ = ["app"]
