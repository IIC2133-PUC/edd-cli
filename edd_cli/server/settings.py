from logging import getLogger
from pathlib import Path
from tempfile import gettempdir

from pydantic import Field
from pydantic_settings import BaseSettings

logger = getLogger(__name__)

temp_dir = Path(gettempdir())


def create_secret():
    import secrets

    secret = secrets.token_hex(32)
    logger.warning(f"SECRET not set. Generated {secret}. Set a secret in production.")

    return secret


class ServerSettings(BaseSettings):
    github_org: str = "IIC2133-PUC"
    repository_download_dir: Path = Path(temp_dir, ".edd-repos")
    output_temp_dir: Path = Path(temp_dir, ".edd-cache")
    tests_directory: Path = Path("tests")
    secret: str = Field(default_factory=create_secret)


settings = ServerSettings()
