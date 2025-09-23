from config import *

class OSUConfigEntry(RootConfigEntry):
    CFG_KEY = "osu"

    DEFAULT = {
        "runtime": {
            "program": "srun",
            "nodes": 2,
            "ntasks-per-node": 1,
            "account": "inti0037@cpu",
            "partition": "rome-bxi",
            "x11": "batch"
        },
        "mpi": {
            "install": "/ccc/work/cont002/forth/moreaugs/install/install-ompi5-bxi-rel/",
            "environment": [
                {"OMPI_MPA_btl": "^vader,openib"},
                {"OMPI_MPA_coll": "ucc,tuned,libnbc,basic"},
                {"OMPI_MPA_pml": "ucx"},
                {"OMPI_MPA_coll_ucc_triggered": "1"},
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
        },
        "executable": {
            "path": "/ccc/work/cont002/forth/moreaugs/install/install-osu-micro-benchmark-ompi5-rel/libexec/osu-micro-benchmarks/mpi/pt2pt/osu_bw",
            "args": "-b single",
            "wrapper": "std"
        }
    }

if __name__ == "__main__": # Create a composite config with nested entries

    c = Config()

    print("List configs:", c.list())

    c.load("osu")

    print(c.root._ucx)

