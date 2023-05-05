import argparse
import json
import os
import sys
import logging
import config as cfg
import subprocess

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

sh_out="""#!/bin/sh

OUT="$(hostname).$$.out"
"$@" 2>&1 | tee ${OUT}
"""

#TODO: add program args automatically
gdbscript="""set breakpoint pending on
set pagination off

run
"""

class Runner():

    def __init__(self):
        self.cmd = ""

    def build_cmd(self, config):
        def add_cmd_prefix(cmd, cfgarg):
            if cfgarg.to_string() != "":
                return cmd + cfgarg.to_string() + "\n"
            else:
                return cmd
        def add_cmd_arg(cmd, cfgarg):
            if cfgarg.to_string() != "":
                return cmd + " " + cfgarg.to_string()
            else:
                return cmd
        def add_cmd_exe(cmd, cfgarg, with_args):
            return cmd + " " + cfgarg.to_string(with_args)

        # add source mpc
        self.cmd = add_cmd_prefix(self.cmd, config.install)

        # add environment variables
        self.cmd = add_cmd_prefix(self.cmd, config.n_ptl)
        self.cmd = add_cmd_prefix(self.cmd, config.n_tcp)
        self.cmd = add_cmd_prefix(self.cmd, config.ptl_max_mr)
        self.cmd = add_cmd_prefix(self.cmd, config.rndv_mode)
        self.cmd = add_cmd_prefix(self.cmd, config.offload)
        self.cmd = add_cmd_prefix(self.cmd, config.t_name)

        # launcher
        self.cmd += "mpcrun"

        # verbose
        self.cmd = add_cmd_arg(self.cmd, config.verbose)

        # add MPI config
        self.cmd = add_cmd_arg(self.cmd, config.c)
        self.cmd = add_cmd_arg(self.cmd, config.n)
        self.cmd = add_cmd_arg(self.cmd, config.N)
        self.cmd = add_cmd_arg(self.cmd, config.p)
        self.cmd = add_cmd_arg(self.cmd, config.net)

        # add opt mpcrun
        self.cmd = add_cmd_arg(self.cmd, config.opt)

        # add wrapper config
        self.cmd = add_cmd_arg(self.cmd, config.type)

        # add exec
        if config.type.value == "gdb":
            self.cmd = add_cmd_exe(self.cmd, config.fq_name, False)
        else:
            if config.program_args.value == "":
                self.cmd = add_cmd_exe(self.cmd, config.fq_name, True)
            else:
                self.cmd = add_cmd_exe(self.cmd, config.fq_name, False)
                self.cmd = add_cmd_arg(self.cmd, config.program_args)

    def run(self, show=False):
        if show == True:
            logging.info("Printing command:\n{}".format(self.cmd))
        else:
            subprocess.run(['/bin/bash', '-c', self.cmd])

def init(args):
    """Init runner by creating a local configuration file.
    Use --cfg-file to specify custom configutation file name"""
    if args.cfg_file:
        if os.path.exists(args.cfg_file) and not args.force:
            logging.warning("{} already exists. Overwrite with --force"
                    .format(args.cfg_file))
        else:
            cfg.Config().config_dump(args.cfg_file)
            logging.info("Create configuration file '{}'"
                    .format(args.cfg_file))
    else:
        if os.path.exists("./config.json") and not args.force:
            logging.warning("{} already exists. Overwrite with --force"
                    .format("./config.json"))
        else:
            cfg.Config().config_dump("./config.json")
            logging.info("Create configuration file '{}'"
                    .format("./config.json"))

    with open("./out.sh", 'w') as f:
        f.write(sh_out)
        os.chmod("./out.sh", 0o755)

    with open("gdbscript.gdb", 'w') as f:
        f.write(gdbscript)

def printenv(args):
    """Print current configuration."""
    if args.cfg_file:
        logging.info("Using configuration file '{}'"
                .format(os.path.basename(args.cfg_file)))
        config = cfg.Config.config_load(args.cfg_file)
    else:
        logging.info("Using default configuration file '{}'"
                .format("./config.json"))
        config = cfg.Config.config_load("./config.json")

    config.config_print()

def setenv(args):
    """Modify current configuration."""
    if args.cfg_file:
        logging.info("Using configuration file '{}'"
                .format(os.path.basename(args.cfg_file)))
        config = cfg.Config.config_load(args.cfg_file)
    else:
        logging.info("Using default configuration file '{}'"
                .format("./config.json"))
        config = cfg.Config.config_load("./config.json")

    if args.build:
        config.set("build", args.build)
        logging.info("Set PCVS build directory") 

    if args.install:
        config.set("install", args.install)
        logging.info("Set MPC install directory") 

    if args.key_value:
        try:
            keyval = json.loads(args.key_value)
            for key, value in keyval.items():
                if config.has_key(key):
                    config.set(key, value) 
                else:
                    raise KeyError("Key {} not found".format(key))
        except json.decoder.JSONDecodeError as e:
            print(e)
            raise json.decoder.JSONDecodeError

    if args.fq_name:
        config.set("fq_name", args.fq_name)
        logging.info("Set PCVS test fq name") 

    if args.cfg_file:
        config.config_dump(args.cfg_file)
    else:
        config.config_dump("./config.json")

    config.config_print()

def run(args):
    """Run (or show)."""
    runner = Runner()

    if args:
        setenv(args)

    # load configuration from file
    config = cfg.Config.config_load("./config.json")

    # build command
    runner.build_cmd(config)
    if args.show:
        runner.run(show=True)
    else:
        runner.run(show=False)

parser = argparse.ArgumentParser(description='Test runner tool')
subparsers = parser.add_subparsers(dest="cmd")
subparsers.required = True

init_p = subparsers.add_parser('init')
init_p.add_argument("--force", action='store_true', help="Force overwrite configuration file")
init_p.add_argument("--cfg-file", type=str, help="Path to custom configuration file")
init_p.set_defaults(func=init)

printenv_p = subparsers.add_parser('printenv')
printenv_p.add_argument("--cfg-file", type=str, help="Path to custom configuration file")
printenv_p.set_defaults(func=printenv)

setenv_p = subparsers.add_parser('setenv')
setenv_p.add_argument("--key-value", type=str,
        help="JSON list of key values (example: {\"type\": \"log\", \"c\": 2})")
setenv_p.add_argument("--build", type=str, help="Path to directory of PCVS generated binaries")
setenv_p.add_argument("--cfg-file", type=str, help="Path to custom configuration file")
setenv_p.add_argument("--install", type=str, help="Path to MPC installation directory")
setenv_p.add_argument("--fq-name", type=str, help="FQ name of PCVS test")
setenv_p.set_defaults(func=setenv)

run_p = subparsers.add_parser('run')
run_p.add_argument("--build", type=str, help="Path to directory of PCVS generated binaries")
run_p.add_argument("--install", type=str, help="Path to MPC installation directory")
run_p.add_argument("--cfg-file", type=str, help="Path to custom configuration file")
run_p.add_argument("--key-value", type=str,
        help="JSON list of key values (example: {\"type\": \"log\", \"c\": 2})")
run_p.add_argument("--show", action='store_true', help="Print command that will be executed")
run_p.add_argument("--fq-name", type=str, help="FQ name of PCVS test")
run_p.set_defaults(func=run)

def main():
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
