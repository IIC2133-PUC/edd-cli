from typer import Typer

from . import commands, config_logging

app = Typer(name="edd")
app.command()(commands.run)
app.command()(commands.server)
app.command(name="run-cloned")(commands.run_cloned_folders)
app.command(name="list")(commands.list_test_groups)
app.callback()(config_logging.set_logging_level)

__all__ = ["app"]
