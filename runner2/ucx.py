import config

class UCXVerbose(config.IntConfigEntry):
    CFG_KEY = "verbose"

class UCXEnvironmentConfigEntry(config.EnvironmentConfigEntry):
    SCHEMA = {
        "verbose": config.IntConfigEntry
    }

class UCXConfigEntry(config.RootConfigEntry):
    CFG_KEY = "ucx"

    SCHEMA = config.RootConfigEntry.SCHEMA | {
        "environment": UCXEnvironmentConfigEntry
    }

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

    root = UCXConfigEntry(config_data)

    print("Root config:", root.get())
    print("Is valid:", root.is_valid())

