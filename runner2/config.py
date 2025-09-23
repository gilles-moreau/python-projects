import subprocess
import re
import json
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
        if not bin_dir.exists():
            raise ConfigEntryError(f"No mpirun binary found in {self.path}/bin")

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
        if not bin_dir.exists():
            raise ConfigEntryError(f"No ucx_info binary found in {self.path}/bin")

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
        if not bin_dir.exists():
            raise ConfigEntryError(f"No ucc_info binary found in {self.path}/bin")

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
    }

class X11EnumConfigEntry(EnumConfigEntry):
    ALLOWED_VALUES = ["batch", "first", "last", "all"]

class SlurmRuntimeConfigEntry(RuntimeConfigEntry):

    SCHEMA = {
        "nodes": IntConfigEntry,
        "ntasks-per-node": IntConfigEntry,
        "partition": StrConfigEntry,
        "account": StrConfigEntry,
        "x11": X11EnumConfigEntry,
    }

# ---- Executable Entry ----

class WrapperEnumConfigEntry(EnumConfigEntry):
    ALLOWED_VALUES = ["std", "gdb", "perf", "valgrind", "log"]

class ExecutableConfigEntry(CompositeConfigEntry):
    SCHEMA = {
        "path": ExecutableConfigEntry,
        "args": StrConfigEntry,
        "wrapper": WrapperEnumConfigEntry
    }

# ---- Root Entry ----

class RootConfigEntry(CompositeConfigEntry):
    SCHEMA = {
        "runtime": SlurmRuntimeConfigEntry,
        "mpi": MPILibraryEntry,
        "ucx": UCXLibraryEntry,
        "ucc": UCCLibraryEntry,
        "executable": ExecutableConfigEntry
    }

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
        Load a specific config.
        """
        if key not in _CFG_REGISTRY:
            raise ConfigEntryError(f"Provided config is not available. key={key}")
        
        root = GetConfigEntryClass(RootConfigEntry, CFG_KEY=key)

        if (not issubclass(root, RootConfigEntry)):
            raise ConfigEntryError(f"Provided config is not a root config.")

        self.root = root(root.DEFAULT)

    def show(self):
        if not self.is_loaded():
            raise ConfigEntryError(f"No config was loaded.")

        print(self.root.get())

class CommandBuilder():
    def __init__(self, c: Config):
        self.c = c
            

