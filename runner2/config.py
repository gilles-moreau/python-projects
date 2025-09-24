import subprocess
import re
import json
import abc
from typing import Any, Optional

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
        return f"{str(self._program)} {str(self._args)}--"

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

class AppConfigEntry(CompositeConfigEntry):
    SCHEMA = {
        "path": ExecutableConfigEntry,
        "args": ArgListConfigEntry,
        "wrapper": WrapperEnumConfigEntry
    }

    def __str__(self):
        return f"{self._wrapper.prefix()} {str(self._path)} {self._wrapper.suffix()}".strip()

# ---- Root Entry ----

class RootConfigEntry(CompositeConfigEntry):
    SCHEMA = {
        "runtime": RuntimeConfigEntry,
        "mpi": MPILibraryEntry,
        "ucx": UCXLibraryEntry,
        "ucc": UCCLibraryEntry,
        "app": AppConfigEntry
    }

    def __str__(self):
        return f"{str(self._runtime)} {str(self._app)}"

class Config():
    
    def __init__(self, key: Optional[str] = None):
        if key:
            # take root key and then class
            root = GetConfigEntryClass(RootConfigEntry, CFG_KEY=key)

            if (not issubclass(root, RootConfigEntry)):
                raise ConfigEntryError(f"Provided config is not a root config.")

            self.root = root(value[rkey])

    def is_loaded(self):
        return hasattr(self, 'root')
        
    def list(self):
        """
        List all available configs.
        """
        return [key for key in _CFG_REGISTRY.keys()]

    def load(self, key: str):
        """
        Load a config from its root key. For example, "osu".
        """
        if key not in _CFG_REGISTRY:
            raise ConfigEntryError(f"Provided config is not available. key={key}")
        
        root = GetConfigEntryClass(RootConfigEntry, CFG_KEY=key)

        if (not issubclass(root, RootConfigEntry)):
            raise ConfigEntryError(f"Provided config is not a root config.")

        self.root = root(root.DEFAULT, check=False)

    def show(self):
        if not self.is_loaded():
            raise ConfigEntryError(f"No config was loaded.")

        print(self.root.get())

