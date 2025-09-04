from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Final, List, Literal, Tuple, Type, cast

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

# --- Constants ---
CHANNEL_ID_RE: Final[re.Pattern[str]] = re.compile(r"^(@[A-Za-z0-9_]+|\d+)$")


# --- Models for YAML ---
class AppConfig(BaseModel):
    wait_time_seconds: int = Field(default=600, ge=1)
    state_file: Path = Field(default=Path("state.yaml"))
    session_name: str = Field(default="user_session")


class VKConfig(BaseModel):
    domain: str = Field(..., min_length=1)
    post_count: int = Field(..., ge=1)
    post_source: Literal["wall", "donut"]


class TelegramConfig(BaseModel):
    channel_ids: List[str]

    @field_validator("channel_ids")
    @classmethod
    def validate_channel_ids(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Список channel_ids не может быть пустым")
        for ch in v:
            if not CHANNEL_ID_RE.match(ch):
                raise ValueError(f"Некорректный формат channel_id: {ch}. Используйте @username или числовой ID.")
        return v


class BindingConfig(BaseModel):
    vk: VKConfig
    telegram: TelegramConfig


class RetryConfig(BaseModel):
    count: int = Field(default=3, ge=0)
    delay_seconds: int = Field(default=10, ge=0)


class DownloaderConfig(BaseModel):
    browser: Literal["chrome", "firefox", "edge"]
    output_path: Path
    yt_dlp_opts: Dict[str, Any]
    retries: RetryConfig = Field(default_factory=RetryConfig)
    browser_restart_wait_seconds: int = Field(default=30, ge=0)

    @field_validator("output_path")
    @classmethod
    def ensure_output_path_exists(cls, v: Path) -> Path:
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v


# --- The main model of settings ---
class Settings(BaseSettings):
    # From .env
    vk_service_token: str = Field(..., alias="VK_SERVICE_TOKEN")
    telegram_api_id: int = Field(..., alias="TELEGRAM_API_ID")
    telegram_api_hash: str = Field(..., alias="TELEGRAM_API_HASH")

    # From YAML
    app: AppConfig
    bindings: List[BindingConfig]
    downloader: DownloaderConfig

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Custom source for YAML ---
    class YamlConfigSource(PydanticBaseSettingsSource):
        yaml_path: Path
        _data: Dict[str, Any]

        def __init__(self, settings_cls: Type[BaseSettings], yaml_path: Path) -> None:
            super().__init__(settings_cls)
            self.yaml_path = yaml_path
            self._data = {}

        def _read_yaml(self) -> Dict[str, Any]:
            if not self._data:
                if self.yaml_path.exists():
                    with open(self.yaml_path, "r", encoding="utf-8") as f:
                        loaded = yaml.safe_load(f)
                        self._data = loaded if isinstance(loaded, dict) else {}
            return self._data

        def get_field_value(self, field: Any, field_name: str) -> Tuple[Any, str, bool]:
            data = self._read_yaml()
            if field_name in data:
                return data[field_name], field_name, True
            return None, field_name, False

        def prepare_field_value(self, field_name: str, field: Any, value: Any, value_is_complex: bool) -> Any:
            return value

        def __call__(self) -> Dict[str, Any]:
            """Returns the entire configuration dictionary from YAML."""
            return self._read_yaml()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            cls.YamlConfigSource(settings_cls, Path("config.yaml")),
            file_secret_settings,
        )

    @model_validator(mode="after")
    def check_bindings_not_empty(self) -> Settings:
        if not self.bindings:
            raise ValueError("Список bindings не может быть пустым")
        return self

    @classmethod
    def load(cls) -> Settings:
        """The factory method for the correct call without arguments."""
        factory: Type[Any] = cast(Type[Any], cls)
        instance = factory()
        return cast(Settings, instance)


if __name__ == "__main__":
    settings = Settings.load()
    print(settings.model_dump())

settings = Settings.load()
