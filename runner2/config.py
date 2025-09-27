import subprocess
import re
import json
import abc
from typing import Any, Optional, Dict

from base import \
    GetConfigEntryClass, \
    ConfigEntryError, \
    CompositeConfigEntry, \
    StrConfigEntry, \
    IntConfigEntry, \
    EnumConfigEntry, \
    PathConfigEntry, \
    TableConfigEntry, \
    ProgramConfigEntry, \
    ExecutableConfigEntry, \
    _CFG_REGISTRY

# ---- Args list ----

class ArgListConfigEntry(TableConfigEntry):

    def __str__(self):
        s = ""
        for row in self.rows:
            for k, v in row.items():
                s += f"--{k} {v} " 
        return s


# ---- Parallel Library Entries ----

class LibraryEntry(CompositeConfigEntry):
    SCHEMA = {
        "install": PathConfigEntry,
        "environment": TableConfigEntry
    }

    def __str__(self):
        s = ""
        for row in self._environment.get():
            for k, v in row.items():
                s += f"export {k}={v}\n"
        return s

# ---- MPI Library ----

class MPIInstallEntry(PathConfigEntry):
    """
    A PathConfigEntry that must point to an MPI installation.
    Validation: runs `<path>/bin/mpirun --version`.
    """

    def set(self, value: Any):
        super().set(value)  # validates path exists
        bin_dir = self.path / "bin" / "ompi_info"
        if self.check and not bin_dir.exists():
            raise ConfigEntryError(f"No mpirun binary found in {self.path}/bin")

        if not self.check:
            return

        try:
            result = subprocess.run(
                [str(bin_dir), "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            match = re.search(r"Open MPI v([0-9]+\.[0-9]+\.[0-9]+)", result.stdout)
            if not match:
                raise ConfigEntryError(
                    f"Could not get version from ucx_info: {result.stdout}"
                )
            self.version = match.group(1)
        except subprocess.CalledProcessError as e:
            raise ConfigEntryError(
                f"mpirun failed in {self.path}: {e.stderr.strip()}"
            )

    def get(self) -> dict:
        return {"path": str(self.path), "version": self.version}

class MPILibraryEntry(LibraryEntry):
    SCHEMA = {
        "install": MPIInstallEntry
    }

# ---- UCX Library ----

class UCXInstallEntry(PathConfigEntry):
    """
    A PathConfigEntry that must point to a UCX installation.
    Validation: runs `<path>/bin/ucx_info --version`.
    """

    def set(self, value: Any):
        super().set(value)  # validates path exists
        bin_dir = self.path / "bin" / "ucx_info"
        if self.check and not bin_dir.exists():
            raise ConfigEntryError(f"No ucx_info binary found in {self.path}/bin")

        if not self.check:
            return

        try:
            result = subprocess.run(
                [str(bin_dir), "-v"],
                capture_output=True,
                text=True,
                check=True,
            )
            match = re.search(r"# Library version: ([0-9]+\.[0-9]+\.[0-9]+)", result.stdout)
            if not match:
                raise ConfigEntryError(
                    f"Could not get version from ucx_info: {result.stdout}"
                )
            self.version = match.group(1)
        except subprocess.CalledProcessError as e:
            raise ConfigEntryError(
                f"ucx_info failed in {self.path}: {e.stderr.strip()}"
            )

    def get(self) -> dict:
        return {"path": str(self.path), "version": self.version}

class UCXLibraryEntry(LibraryEntry):
    SCHEMA = {
        "install": UCXInstallEntry
    }

# ---- UCC Library ----

class UCCInstallEntry(PathConfigEntry):
    """
    A PathConfigEntry that must point to a UCC installation.
    Validation: runs `<path>/bin/ucc_info -v`.
    """

    def set(self, value: Any):
        super().set(value)  # validates path exists
        bin_dir = self.path / "bin" / "ucc_info"
        if self.check and not bin_dir.exists():
            raise ConfigEntryError(f"No ucc_info binary found in {self.path}/bin")

        if not self.check:
            return

        try:
            result = subprocess.run(
                [str(bin_dir), "-v"],
                capture_output=True,
                text=True,
                check=True,
            )
            match = re.search(r"# UCC version=([0-9]+\.[0-9]+\.[0-9]+)", result.stdout)
            if not match:
                raise ConfigEntryError(
                    f"Could not get version from ucc_info: {result.stdout}"
                )
            self.version = match.group(1)
        except subprocess.CalledProcessError as e:
            raise ConfigEntryError(
                f"ucc_info failed in {self.path}: {e.stderr.strip()}"
            )

    def get(self) -> dict:
        return {"path": str(self.path), "version": self.version}

class UCCLibraryEntry(LibraryEntry):
    SCHEMA = {
        "install": UCCInstallEntry
    }

# ---- Runtime Entries ----

class RuntimeConfigEntry(CompositeConfigEntry):
    SCHEMA = {
        "program": ProgramConfigEntry,
        "args": ArgListConfigEntry,
    }

    def __str__(self):
        return f"{str(self._program)} {str(self._args)}-- "

# ---- Executable Entry ----

class WrapperEnumConfigEntry(EnumConfigEntry):
    ALLOWED_VALUES = ["std", "gdb", "perf", "valgrind", "log"]

    class Wrapper(abc.ABCMeta):

        @abc.abstractmethod
        def prefix(self) -> str:
            pass

        @abc.abstractmethod
        def suffix(self) -> str:
            pass

    class GdbWrapper(metaclass=Wrapper):
        def prefix(self) -> str:
            return "xterm -e gdb --command=./gdbscript.gdb"

        def suffix(self) -> str:
            return ""

    class PerfWrapper(metaclass=Wrapper):
        def prefix(self) -> str:
            return "perf record"

        def suffix(self) -> str:
            return ""

    class LogWrapper(metaclass=Wrapper):
        def prefix(self) -> str:
            return ""

        def suffix(self) -> str:
            return ""

    class StdWrapper(metaclass=Wrapper):
        def prefix(self) -> str:
            return ""

        def suffix(self) -> str:
            return ""

    class ValgrindWrapper(metaclass=Wrapper):
        def prefix(self) -> str:
            return ""

        def suffix(self) -> str:
            return ""

    class LogWrapper(metaclass=Wrapper):
        def prefix(self) -> str:
            return ""

        def suffix(self) -> str:
            return ""

    WRAPPERS = {
        "std": StdWrapper,
        "gdb": GdbWrapper,
        "perf": PerfWrapper,
        "valgrind": ValgrindWrapper,
        "log": LogWrapper
    }

    def __init__(self, value: Any = None, check: bool = True):
        super().__init__(value, check)

        self.wrapper = WrapperEnumConfigEntry.WRAPPERS[self.value]()

    def prefix(self) -> str:
        return self.wrapper.prefix()

    def suffix(self) -> str:
        return self.wrapper.suffix()

class EnvConfigEntry(CompositeConfigEntry):
    SCHEMA = {
        "mpi": MPILibraryEntry,
        "ucx": UCXLibraryEntry,
        "ucc": UCCLibraryEntry,
    }

    def __str__(self):
        return f"{self._mpi}\n{str(self._ucx)}\n{self._ucc}\n"

class AppConfigEntry(CompositeConfigEntry):
    SCHEMA = {
        "bin": ExecutableConfigEntry,
        "args": ArgListConfigEntry,
        "wrapper": WrapperEnumConfigEntry
    }

    def __str__(self):
        return f"{self._wrapper.prefix()} {str(self._path)} {self._wrapper.suffix()}".strip()

# ---- Root Entry ----

class RootConfigEntry(CompositeConfigEntry, metaclass=abc.ABCMeta):
    DEFAULT: dict = None
    SCHEMA = {
        "runtime": RuntimeConfigEntry,
        "app": AppConfigEntry,
        "env": EnvConfigEntry
    }

    # Enforce subclass to have a DEFAULT configuration
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "DEFAULT") or cls.DEFAULT is None:
            raise TypeError(f"{cls.__name__} must define a DEFAULT configuration")

    def __init__(self, value: Optional[Dict[str, Any]] = None, 
                 check: bool = True):
        if value is None:
            value = type(self).DEFAULT
        super().__init__(value, check)

    def __str__(self):
        s =  f"{str(self._env)}"
        s += f"{str(self._runtime)}"
        s += f"{str(self._app)}"

        return s.strip()

class Config():
    """
    Configuration object that can read from JSON file. It respects the 
    specification defined by the ConfigEntry implementation.
    """
    
    def __init__(self, name: Optional[str] = None, json_path: Optional[str] = None):
        if name:
            value = None
        elif path:
            value = self.read(json_path)
            name = None

        self.load(name=name, value=value)

    def isloaded(self):
        return hasattr(self, 'root')
        
    def list(self):
        """
        List all available configs.
        """
        return [key for key in _CFG_REGISTRY.keys()]

    def load(self, name: str = None, value: Dict[str, Any] = None):
        """
        Load a config from its root key and thus default configuration 
        or a json config.
        """
        if name is not None:
            value = None
        elif value is not None:
            name = next(iter(value))
            value = value[name]
        else:
            raise ConfigEntryError(f"Must at least provide a key or a json config")

        if name not in _CFG_REGISTRY:
            raise ConfigEntryError(f"Provided config is not available. name={name}")
        self.root = GetConfigEntryClass(RootConfigEntry, CFG_KEY=name)(value)

    def read(self, json_path: str):
        with open(json_path) as f:
           value = json.load(f)

    def show(self):
        if not self.isloaded():
            raise ConfigEntryError(f"No config was loaded.")

        print(self.root.get())

