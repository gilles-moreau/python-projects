import argparse
import subprocess
import sys
from typing import List

from config import Config, ConfigEntryError

# import existing config to put them in registry
import osu, pcvs_config, pcvs_test_config

class Runner:
    def __init__(self, config: Config):
        self.config = config

    def run(self, show: bool = False):
        cmd = str(self.config.root)
        print(f"Running command: {cmd}")
        if show:
            return
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print("Output:\n", result.stdout)
            if result.stderr:
                print("Errors:\n", result.stderr, file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with code {e.returncode}")
            print("Output:\n", e.stdout)
            print("Errors:\n", e.stderr, file=sys.stderr)
            sys.exit(e.returncode)


def main():
    parser = argparse.ArgumentParser(description="Run command from configuration")
    parser.add_argument(
        "-c", "--config",
        help="Path to JSON configuration file",
        default=None,
    )
    parser.add_argument(
        "-n", "--name",
        help="Name of default configuration",
        default=None,
    )
    parser.add_argument(
        "-s", "--show",
        help="Show command that will be run",
        action='store_true',
        default=False,
    )
    args = parser.parse_args()

    try:
        if args.name:
            cfg = Config(name=args.name)
        elif args.config:
            cfg = Config(json_path=args.config)
        else:
            print(f"Runner error: provide either name or config file")
            sys.exit(1)
    except ConfigEntryError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    runner = Runner(cfg)
    runner.run(args.show)


if __name__ == "__main__":
    main()

