import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

env_file_path = os.path.join(os.path.dirname(__file__), ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_file_path, env_file_encoding="utf-8", extra="ignore")

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARN", "ERROR"] = "INFO"
    """
    The level of logging to be provided.
    """

    DUMP_RAW_MESSAGES: bool = False
    """
    If true, creates a file with dumps of all received messages from the socket connection
    """

    DATA_DUMP_FILE_PATH: Path = "data_dump.txt"
    """
    Filepath at which to dump messages
    """

    LOCAL_SOURCE_FILE_PATH: Path = "data_dump.txt"
    """
    Filepath from which to read messages when running from local dump
    """

    OPENAI_API_KEY: str
    """
    OpenAI API key used to get commentary text
    """

    VOICE_MODEL_FILE_LOCATION: Path
    """
    Absolute path to the voice model file location 
    """

    SILENT_MODE: bool = False
    """
    Makes it so no audio is generated. The commentary is logged in the console instead
    """


settings: Settings = Settings()
