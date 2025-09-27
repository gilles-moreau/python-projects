import subprocess
from pathlib import Path

from config import *

from pcvs import io
import pcvs.backend.profile as profile

class ProfileConfigEntry(CompositeConfigEntry):

    SCHEMA = {
        "name": StrConfigEntry,
        "compilers": PathConfigEntry,
        "partition": StrConfigEntry,
    }

    def set(self, value: Any):
        super().set(value)

        # Because of global variable initialization, this needs to be called
        io.init()
        profile.init() 

        p = profile.Profile(self._name.get())
        if p.is_found():
            p.load_from_disk()
        else:
            raise ConfigEntryError(f"PCVS profile {str(self._name)} not found. " \
                                   f"Make sure to run where .pcvs dir is located")

        # Modify the profile entries
        p._details.compiler.cc.program = self._compilers.get() + "/bin/mpicc"
        p._details.compiler.cxx.program = self._compilers.get() + "/bin/mpicxx"
        p._details.compiler.f08.program = self._compilers.get() + "/bin/mpifort"
        p._details.compiler.f77.program = self._compilers.get() + "/bin/mpif77"
        p._details.compiler.f90.program = self._compilers.get() + "/bin/mpif90"
        p._details.compiler.fc.program = self._compilers.get() + "/bin/mpifort"

        p.flush_to_disk()


class PCVSRuntimeArgConfigEntry(CompositeConfigEntry):

    SCHEMA = {
        "output": PathConfigEntry,
        "input": PathConfigEntry,
        "profile": ProfileConfigEntry,
    }

class PCVSRuntimeConfigEntry(RuntimeConfigEntry):
    SCHEMA = {
        "args": PCVSRuntimeArgConfigEntry
    }

    def __str__(self):
        return f"{str(self._program)} run -P all -f -p {str(self._args._profile._name)} " \
               f"-o {str(self._args._output)} {str(self._args._input)}"

class PCVSAppConfigEntry(AppConfigEntry):

    def set(self, value:Any):
        pass

    def __str__(self):
        return ""

class PCVSConfigEntry(RootConfigEntry):
    CFG_KEY = "pcvs"

    SCHEMA = {
        "runtime": PCVSRuntimeConfigEntry,
        "app": PCVSAppConfigEntry
    }

    DEFAULT = {
        "runtime": {
            "program": "pcvs",
            "args": {
                "output": "/ccc/work/cont002/forth/moreaugs/runs/osu",
                "input": "/ccc/work/cont002/forth/moreaugs/src/pcvs-benchmarks/performance/OSU/",
                "profile": {
                    "name": "ucx",
                    "compilers": "/ccc/work/cont002/forth/moreaugs/install/install-ompi5-bxi-rel/",
                    "partition": "rome-bxi"
                }
            }
        },
        "app": {
            "bin": "/ccc/work/cont002/forth/moreaugs/src/pcvs-benchmarks/performance/OSU/",
            "args": [],
            "wrapper": "std"
        },
        "env": {
            "mpi": {
                "install": "/ccc/work/cont002/forth/moreaugs/install/install-ompi5-bxi-rel/",
                "environment": [
                    {"OMPI_MCA_btl": "^vader,openib"},
                    {"OMPI_MCA_coll": "ucc,tuned,libnbc,basic"},
                    {"OMPI_MCA_pml": "ucx"},
                    {"OMPI_MCA_coll_ucc_triggered": "1"},
                ]
            },
            "ucx": {
                "install": "/ccc/work/cont002/forth/moreaugs/install/install-ucx-bxi-rel",
                "environment": [
                    {"UCX_BXI_TM_ENABLE": "y"},
                    {"UCX_LOG_LEVEL": "debug"},
                    {"UCX_TLS": "bxi"},
                    {"UCX_TM_THRESH": "1024"},
                    {"UCX_STATS_DEST": "file:ucx-%e-t@t-m@m-%h.stats"},
                    {"UCX_PROFILE_MODE": "accum"},
                    {"UCX_PROFILE_FILE": "ucx-%e-t@t-m@m-%h.prof"},
                    {"UCX_TM_THRESH": "1024"},
                ]
            },
            "ucc": {
                "install": "/ccc/work/cont002/forth/moreaugs/install/install-ucc-bxi-rel",
                "environment": [
                    {"UCC_TL_UCP_BCAST_KN_RADIX": "2"},
                    {"UCC_TL_UCP_SCATTER_KN_RADIX": "2"},
                    {"UCC_TL_UCP_GATHER_KN_RADIX": "2"},
                ]
            }
        }
    }
