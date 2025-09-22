import abc
import logging
from typing import Any, Dict, List, Optional

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

    def __init__(self, value: Any = None, required: Any = None):
        self.value = None
        if value is not None:
            self.set(value, required)

    @abc.abstractmethod
    def set(self, value: Any, required: Any):
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

    def set(self, value: Any, required: Any):
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
    SCHEMA: Optional[Dict[str, ConfigEntry]] = None

    def __init__(self, value: Optional[Dict[str, Any]] = None, 
                 required: Optional[Dict[str, ConfigEntry]] = None):
        super().__init__(value, required)

    def set(self, value: Dict[str, Any], required: Dict[str, ConfigEntry]):
        if not isinstance(value, dict):
            raise ConfigEntryError("Composite entry must be a dict")
  
        for key, cls in required.items():
            if key not in value:
                raise ConfigEntryError(f"Missing required key '{key}'")
            if not hasattr(self, key):
                setattr(self, key, cls(value[key]))
            else:
                getattr(self, key)(value[key])

    def get(self) -> Dict[str, Any]:
        return {k: o.get() for k, o in self.__dict__.items() }
    
    def is_valid(self) -> bool:
        return all(key in self.__dict__.items() for key in self.SCHEMA.keys())

class RuntimeConfigEntry(CompositeConfigEntry):
    CFG_KEY = None 

    SCHEMA = {
        'program': StrConfigEntry,
        'args': StrConfigEntry 
    }

    def __init__(self, value: Dict[str, Any]):
        super().__init__(value, RuntimeConfigEntry.SCHEMA)

class EnvironmentConfigEntry(CompositeConfigEntry):
    CFG_KEY = None 

    SCHEMA: Optional[Dict[str, ConfigEntry]] = None

    def set(self, value: Dict[str, Any], required: Dict[str, Any]):
        for key in value.keys():
            setattr(self, key, StrConfigEntry(str(value[key])))

class RootConfigEntry(CompositeConfigEntry):
    CFG_KEY = None 

    SCHEMA = {
        'runtime': RuntimeConfigEntry,
        'environment': EnvironmentConfigEntry
    }

    def __init__(self, value: Dict[str, Any]):
        super().__init__(value, RootConfigEntry.SCHEMA)

    def is_valid(self) -> bool:
        return True 

class Config():

    def __init__(self, value: Dict[str, Any]):
        if len(value.keys()) > 1:
            raise ConfigEntryError(f"Root config must have only one key.")

        # take root key and then class
        rkey = next(iter(value))
        root = GetConfigEntryClass(RootConfigEntry, CFG_KEY=rkey)

        if (not issubclass(root, RootConfigEntry)):
            raise ConfigEntryError(f"Provided config is not a root config.")

        self.root = root(value[rkey])
        
