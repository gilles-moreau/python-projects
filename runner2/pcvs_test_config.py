import subprocess
import os
from pathlib import Path

from config import *

from pcvs.orchestration.publishers import BuildDirectoryManager 

class PCVSTestRuntimeArgConfigEntry(CompositeConfigEntry):
    SCHEMA = {
        "nodes": IntConfigEntry,
        "ntasks-per-node": IntConfigEntry,
        "account": StrConfigEntry,
        "partition": StrConfigEntry,
    }

    def __str__(self):
        s = ""
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                s += f"--{k[1:]} {v.get()} " 
        return s

class PCVSTestRuntimeConfigEntry(RuntimeConfigEntry):
    SCHEMA = {
        "args": PCVSTestRuntimeArgConfigEntry
    }

class PCVSTestAppConfigEntry(CompositeConfigEntry):

    SCHEMA = {
        "test": StrConfigEntry,
        "builddir": PathConfigEntry,
    }

    @staticmethod
    def parse_exec_line(cmd):
        cmd_split = cmd.split(" ")

        path = ""
        args = ""
        for arg in reversed(cmd_split):
            if os.path.isfile(arg) and os.access(arg, os.X_OK):
                path = arg + " " + path
                return (path, args)
            else:
                args = arg + " " + args
        raise ConfigEntryError("Executable from command {} not " \
                "found.".format(cmd))


    def set(self, value:Any):
        super().set(value)

        bdm = BuildDirectoryManager(self._builddir.get())
        bdm.init_results()

        tests = bdm.results.retrieve_tests_by_name(self._test.get())
        if not tests:
            raise ConfigEntryError(f"PCVS test {self._test.get()} not found!")

        for t in tests:
            # Set executable path and its arguments
            (self.path, self.args) = self.parse_exec_line(t.command)

    def __str__(self):
        return f"{self.path} {self.args}"

class PCVSTestConfigEntry(RootConfigEntry):
    CFG_KEY = "pcvs_test"

    SCHEMA = {
        "runtime": PCVSTestRuntimeConfigEntry,
        "app": PCVSTestAppConfigEntry
    }

    DEFAULT = {
        "runtime": {
            "program": "srun",
            "args": {
                "nodes": 2,
                "ntasks-per-node": 1,
                "account": "inti0037@cpu",
                "partition": "rome-bxi",
            }
        },
        "app": {
            "test": "OSU/pt2pt_osu_mbw_mr_n2",
            "builddir": "/ccc/work/cont002/forth/moreaugs/runs/osu",
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
                    {"UCX_LOG_LEVEL": "error"},
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
