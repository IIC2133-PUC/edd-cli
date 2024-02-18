import logging

from rich.logging import RichHandler
from typer import Option


def set_logging_level(
    verbose: bool = Option(False, "-v", "--verbose"),
    debug: bool = Option(False, "-d", "--debug"),
    quiet: bool = Option(False, "-q", "--quiet"),
    disable_rich: bool = Option(False, "--disable-rich"),
):
    import os

    if debug:
        logging_level = logging.DEBUG
    elif verbose:
        logging_level = logging.INFO
    elif quiet:
        logging_level = logging.WARNING
    else:
        logging_level = logging.INFO

    if disable_rich:
        os.environ["NO_COLOR"] = "1"
        os.environ["TERM"] = "dumb"
        logging.basicConfig(level=logging_level)
    else:
        logging.basicConfig(
            level=logging_level, handlers=[RichHandler(rich_tracebacks=True)]
        )
