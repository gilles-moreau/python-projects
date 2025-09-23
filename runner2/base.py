import abc
import logging
import shutil
import os
from pathlib import Path
from typing import Any, Dict, Optional, List

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

# Global registry
_CFG_REGISTRY: Dict[str, "ConfigEntry"] = {}

def GetConfigEntryClass(base_class, **kwargs):
    key = kwargs["CFG_KEY"]
    if key not in _CFG_REGISTRY:
        logging.fatal("Command arg not defined: " + str(key))
        exit(1)
    return _CFG_REGISTRY.get(key)

# ---- Metaclasses ----

class AutoRegisterConfigEntryMeta(abc.ABCMeta):
    """Metaclass that auto-registers subclasses by CFG_KEY."""

    def __init__(cls, name, bases, dct):
        if getattr(cls, "CFG_KEY", None):
            _CFG_REGISTRY[cls.CFG_KEY] = cls
        super().__init__(name, bases, dct)


class CompositeConfigMeta(AutoRegisterConfigEntryMeta):
    """Metaclass that merges SCHEMA definitions across inheritance."""

    def __init__(cls, name, bases, dct):
        # Merge SCHEMA from bases
        merged: Dict[str, type] = {}
        for base in bases:
            if hasattr(base, "SCHEMA"):
                merged.update(getattr(base, "SCHEMA"))

        # Apply subclass SCHEMA (with overwrite)
        if "SCHEMA" in dct:
            for k, v in dct["SCHEMA"].items():
                if k in merged:
                    # Optional safety: enforce subtype compatibility
                    if not issubclass(v, merged[k]):
                        logging.warning(
                            f"Overwriting schema key '{k}' in {cls.__name__}: "
                            f"{merged[k].__name__} -> {v.__name__}"
                        )
                merged[k] = v

        cls.SCHEMA = merged
        super().__init__(name, bases, dct)


# ---- Errors ----

class ConfigEntryError(Exception):
    def __init__(self, message="Invalid parameter"):
        super().__init__(message)


# ---- Base Entries ----

class ConfigEntry(metaclass=AutoRegisterConfigEntryMeta):
    CFG_KEY: Optional[str] = None

    def __init__(self, value: Any = None):
        if value is not None:
            self.set(value)

    @abc.abstractmethod
    def set(self, value: Any):
        pass

    @abc.abstractmethod
    def get(self) -> Any:
        pass

class IntConfigEntry(ConfigEntry):
    CFG_KEY = None

    def set(self, value: Any):
        if not isinstance(value, int):
            raise ConfigEntryError(f"Expected int, got {type(value)}")
        self.value = value

    def get(self) -> int:
        return self.value


class StrConfigEntry(ConfigEntry):
    CFG_KEY = None

    def set(self, value: Any):
        if not isinstance(value, str):
            raise ConfigEntryError(f"Expected str, got {type(value)}")
        self.value = value

    def get(self) -> str:
        return self.value

class EnumConfigEntry(StrConfigEntry):
    """
    A string ConfigEntry restricted to a set of allowed values.
    """

    ALLOWED_VALUES: List[str] = []

    def __init__(self, value: Any = None):
        if not self.ALLOWED_VALUES:
            raise ConfigEntryError(
                f"{self.__class__.__name__} must define ALLOWED_VALUES"
            )
        super().__init__(value)

    def set(self, value: Any):
        super().set(value)  # ensures it is a string
        if self.value not in self.ALLOWED_VALUES:
            raise ConfigEntryError(
                f"Invalid value '{self.value}' for {self.__class__.__name__}. "
                f"Allowed: {self.ALLOWED_VALUES}"
            )

    def get(self) -> str:
        return self.value

class PathConfigEntry(StrConfigEntry):
    """
    A string entry that must be a valid filesystem path.
    """

    def set(self, value: Any = None):
        super().set(value)  # still a string
        path = Path(self.value)

        if not path.is_absolute():
            # Resolve relative path relative to current working directory
            path = path.resolve()

        if not path.exists():
            raise ConfigEntryError(f"Path does not exist: {self.value}")

        self.path = path  # store Path object for convenience

    def get(self) -> str:
        return str(self.path)

class ProgramConfigEntry(StrConfigEntry):
    """
    A config entry representing a program.
    Validation: checks that the program exists in the system PATH.
    """

    def set(self, value: str):
        super().set(value)  # ensure it's a string

        # Check if the program exists in PATH
        prog_path = shutil.which(self.value)
        if prog_path is None:
            raise ConfigEntryError(f"Program '{self.value}' not found in system PATH")
        
        self.path = prog_path  # store full path for convenience

    def get(self) -> str:
        return self.path

class ExecutableConfigEntry(PathConfigEntry):
    """
    A PathConfigEntry that ensures the path points to an executable file.
    """

    def set(self, value: str):
        super().set(value)  # ensures path exists
        if not self.path.is_file():
            raise ConfigEntryError(f"Path is not a file: {self.path}")
        if not os.access(self.path, os.X_OK):
            raise ConfigEntryError(f"File is not executable: {self.path}")

    def get(self) -> str:
        return str(self.path)

# ---- Composite Entries ----

class TableConfigEntry(ConfigEntry):
    """
    A ConfigEntry that holds a JSON table:
    - value must be a list of dicts
    - no predefined schema, arbitrary columns allowed
    """

    def __init__(self, value: Optional[list] = None):
        self.rows: list[dict] = []
        super().__init__(value)

    def set(self, value: list):
        if not isinstance(value, list):
            raise ConfigEntryError("TableConfigEntry expects a list of dicts")

        for i, row in enumerate(value):
            if not isinstance(row, dict):
                raise ConfigEntryError(f"Row {i} must be a dict")

        self.rows = value

    def get(self) -> list:
        return self.rows

class CompositeConfigEntry(ConfigEntry, metaclass=CompositeConfigMeta):
    SCHEMA: Dict[str, type] = {}

    def __init__(self, value: Optional[Dict[str, Any]] = None):
        super().__init__(value)

    def set(self, value: Dict[str, Any]):
        if not isinstance(value, dict):
            raise ConfigEntryError("Composite entry must be a dict")

        for k, entry_cls in self.SCHEMA.items():
            if k not in value:
                raise ConfigEntryError(
                    f"Missing required key '{k}' in {type(self).__name__}"
                )
            setattr(self, "_" + k, entry_cls(value[k]))

    def get(self) -> Dict[str, Any]:
        return {k: v.get() for k, v in self.__dict__.items() if k.startswith("_")}
