import abc
import logging
from typing import Any, Dict, List, Optional, TypedDict

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

_CFG_REGISTRY: Dict[str, "ConfigEntry"] = {}


def GetConfigEntryClass(base_class, **kwargs):
    key = kwargs["CFG_KEY"]
    if key not in _CFG_REGISTRY:
        logging.fatal("Command arg not defined: " + str(key))
        exit(1)

    return _CFG_REGISTRY.get(key)


class AutoRegisterConfigEntryMeta(abc.ABCMeta):
    """Metaclass that auto-registers subclasses by CFG_KEY."""

    def __init__(cls, name, bases, dct):
        if getattr(cls, "CFG_KEY", None):
            _CFG_REGISTRY[cls.CFG_KEY] = cls
        super().__init__(name, bases, dct)


class ConfigEntryError(Exception):
    def __init__(self, message="Invalid parameter"):
        super().__init__(message)


class ConfigEntry(metaclass=AutoRegisterConfigEntryMeta):
    CFG_KEY: Optional[str] = None
    CFG_STR: Optional[str] = None

    def __init__(self, value: Any = None):
        self.value = None
        if value is not None:
            self.set(value)

    @abc.abstractmethod
    def set(self, value: Any):
        pass

    @abc.abstractmethod
    def get(self) -> Any:
        pass

    @abc.abstractmethod
    def is_valid(self) -> bool:
        pass

# ---- Example concrete entries ----

class IntConfigEntry(ConfigEntry):
    CFG_KEY = None
    CFG_STR = None

    def set(self, value: Any):
        if not isinstance(value, int):
            raise ConfigEntryError(f"Expected int, got {type(value)}")
        self.value = value

    def get(self) -> int:
        return self.value

    def is_valid(self) -> bool:
        return isinstance(self.value, int)

class StrConfigEntry(ConfigEntry):
    CFG_KEY = None 
    CFG_STR = None 

    def set(self, value: Any):
        if not isinstance(value, str):
            raise ConfigEntryError(f"Expected str, got {type(value)}")
        self.value = value

    def get(self) -> str:
        return self.value

    def is_valid(self) -> bool:
        return isinstance(self.value, str)

class CompositeConfigEntry(ConfigEntry):
    """
    Composite entry that contains multiple ConfigEntry children.
    This allows recursive nesting.
    """

    CFG_KEY = None 
    CFG_STR = None 

    SCHEMA: Dict[str, type[ConfigEntry]] = {}

    def __init__(self, value: Optional[Dict[str, Any]] = None):
        self.children: Dict[str, ConfigEntry] = {}
        super().__init__(value)

    def set(self, value: Dict[str, Any]):
        if not isinstance(value, dict):
            raise ConfigEntryError("Composite entry must be a dict")

        for key, cls in self.SCHEMA.items():
            if key not in value:
                raise ConfigEntryError(f"Missing required key '{key}' in {self.CFG_KEY}")
            self.children[key] = cls(value[key])

    def get(self) -> Dict[str, Any]:
        return {k: child.get() for k, child in self.children.items()}

    def is_valid(self) -> bool:
        return all(child.is_valid() for child in self.children.values())

class RuntimeConfigEntry(CompositeConfigEntry):
    CFG_KEY = "runtime"

    SCHEMA = {
        "program": StrConfigEntry,
        "args": StrConfigEntry,
    }

class EnvironmentConfigEntry(CompositeConfigEntry):
    CFG_KEY = "environment"

    SCHEMA = Dict[str, ConfigEntry]

class RootConfigEntry(CompositeConfigEntry):
    CFG_KEY = None 

    SCHEMA = { 
        "runtime": RuntimeConfigEntry, 
        "environment": EnvironmentConfigEntry,
    }

    def __init__(self, value: Dict[str, Any]):
        self.children: Dict[str, ConfigEntry] = {}
        super().__init__(list(value.values())[0])

    def is_valid(self) -> bool:
        return all(child.is_valid() for child in self.children.values())

