from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, get_type_hints

from astrbot.api import logger
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.utils.astrbot_path import (
    get_astrbot_plugin_data_path,
    get_astrbot_plugin_path,
)

from .model import SupervisorModel


class ConfigNode:
    """Expose mapping fields as typed attributes with lazy nested nodes."""

    _SCHEMA_CACHE: dict[type, dict[str, type]] = {}
    _FIELDS_CACHE: dict[type, set[str]] = {}

    @classmethod
    def _schema(cls) -> dict[str, type]:
        return cls._SCHEMA_CACHE.setdefault(cls, get_type_hints(cls))

    @classmethod
    def _fields(cls) -> set[str]:
        return cls._FIELDS_CACHE.setdefault(
            cls,
            {key for key in cls._schema() if not key.startswith("_")},
        )

    def __init__(self, data: MutableMapping[str, Any]):
        object.__setattr__(self, "_data", data)
        object.__setattr__(self, "_children", {})
        for key in self._fields():
            if key not in data:
                logger.warning(f"{self.__class__.__name__} missing key: {key}")

    def __getattr__(self, key: str) -> Any:
        if key not in self._fields():
            raise AttributeError(key)

        value = self._data.get(key)
        field_type = self._schema()[key]
        if isinstance(field_type, type) and issubclass(field_type, ConfigNode):
            children: dict[str, ConfigNode] = self.__dict__["_children"]
            if key not in children:
                if not isinstance(value, MutableMapping):
                    raise TypeError(
                        f"{self.__class__.__name__} "
                        f"key {key} requires a mapping, got {type(value).__name__}"
                    )
                children[key] = field_type(value)
            return children[key]
        return value

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self._fields():
            self._data[key] = value
            return
        object.__setattr__(self, key, value)

    def raw_data(self) -> Mapping[str, Any]:
        return MappingProxyType(self._data)

    def save_config(self) -> None:
        if not isinstance(self._data, AstrBotConfig):
            raise RuntimeError(
                f"{self.__class__.__name__}.save_config() requires AstrBotConfig"
            )
        self._data.save_config()


class ImageConfig(ConfigNode):
    weight: int
    files: list[str]


class LLMConfig(ConfigNode):
    weight: int
    prompt: str


class PokeConfig(ConfigNode):
    weight: int
    times: int


class PluginConfig(ConfigNode):
    """Expose typed plugin configuration and derived runtime values."""

    user_ids: list[str]
    default_minute: int
    max_minute: int
    image: ImageConfig
    llm: LLMConfig
    poke: PokeConfig

    _plugin_name = "astrbot_plugin_supervisor"

    def __init__(self, config: AstrBotConfig):
        super().__init__(config)
        self.data_dir = Path(get_astrbot_plugin_data_path()) / self._plugin_name
        self.plugin_dir = Path(get_astrbot_plugin_path()) / self._plugin_name
        self._ensure_default_images()

    def _ensure_default_images(self) -> None:
        """Copy bundled images into file storage when no images are configured."""
        if self.image.files:
            return

        default_files = []
        source_dir = self.plugin_dir / "image"
        target_dir = self.data_dir / "files" / "image" / "files"
        for source_path in sorted(source_dir.glob("*")):
            if not source_path.is_file():
                continue
            relative_path = Path("files") / "image" / "files" / source_path.name
            target_path = self.data_dir / relative_path
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                if not target_path.exists():
                    target_path.write_bytes(source_path.read_bytes())
            except OSError as exc:
                logger.error(f"Failed to copy default supervisor image: {exc}")
                continue
            default_files.append(relative_path.as_posix())

        if default_files:
            self.image.files = default_files
            self.save_config()
            logger.info(f"Loaded {len(default_files)} default supervisor images")

    @property
    def default_second(self) -> int:
        return self.default_minute * 60

    @property
    def max_second(self) -> int:
        return self.max_minute * 60

    @property
    def image_files(self) -> list[Path]:
        return [self.data_dir / Path(file_path) for file_path in self.image.files]

    def weight_of(self, model: SupervisorModel) -> int:
        """Return the configured weight for a response model"""
        return {
            SupervisorModel.IMAGE: self.image.weight,
            SupervisorModel.LLM: self.llm.weight,
            SupervisorModel.POKE: self.poke.weight,
        }[model]
