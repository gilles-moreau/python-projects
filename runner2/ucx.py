import config
from typing import Any, Dict, List, Optional

class UCXEnvironmentConfigEntry(config.EnvironmentConfigEntry):
    verbose: config.IntConfigEntry 

class UCXConfigEntry(config.RootConfigEntry):
    CFG_KEY = "ucx"

    def __init__(self, value: Dict[str, Any]):
        self.environment = UCXEnvironmentConfigEntry

        super().__init__(value)

if __name__ == "__main__":
    # Create a composite config with nested entries
    config_data = {
        "ucx": {
            "runtime": {
                "program": "exe",
                "args": "",
            },
            "environment": {
                "verbose": 3
            }
        }
    }

    ucx = config.Config(config_data)

    print("Root config:", ucx.root.runtime.program)

