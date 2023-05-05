import abc
import shutil
import os
import pathlib
import logging
import json
from typing import List

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

_CFG_REGISTRY = {}

def GetCfgArgClass(base_class, **kwargs):
    key = [kwargs["CFG_KEY"]]
    if tuple(key) not in _CFG_REGISTRY:
        logging.fatal("Command arg not defined: " + str(key))
        exit(1)

    return _CFG_REGISTRY.get(tuple(key))

class AutoRegisterCfgArgMeta(abc.ABCMeta):

    CFG_KEY: str
    CFG_STR: str
    ALLOWED_VALUES: List[str]

    def __init__(cls, name, bases, dct):
        if cls.CFG_KEY:
            key = [cls.CFG_KEY]
            _CFG_REGISTRY[tuple(key)] = cls
        super(AutoRegisterCfgArgMeta, cls).__init__(name, bases, dct)

class CfgArgError(Exception):
    def __init__(self, message="Invalid parameter"):
        self.message = message
        super().__init__(self.message)


class CfgArg(metaclass=AutoRegisterCfgArgMeta):

    CFG_KEY = None
    CFG_STR = None

    @abc.abstractmethod
    def __init__(self, value):
        pass

    @abc.abstractmethod
    def set(self, value):
        pass

    @abc.abstractmethod
    def get(self):
        pass
    
    @abc.abstractmethod
    def is_valid(self):
        pass

    @abc.abstractmethod
    def check_arg(self, value):
        pass

class CfgArgDir(CfgArg):

    CFG_KEY = None
    CFG_STR = None

    def __init__(self, value="."):
        self.is_valid = self.check_arg(value)
        self.value    = os.path.abspath(value)

    def check_arg(self, value):
        return os.path.isdir(os.path.abspath(value))

    def set(self, value):
        self.is_valid = self.check_arg(value)
        if self.is_valid == True:
            self.value = os.path.abspath(value)
        else:
            raise CfgArgError("Invalid parameter '{}': {} not a directory"
                    .format(self.CFG_KEY, os.path.abspath(value))) 

    def get(self):
        return self.value

    def is_valid(self):
        return self.is_valid

class CfgArgBuild(CfgArgDir):

    CFG_KEY = "build"

    def check_arg(self, value):
        is_valid = super().check_arg(value) 
        if is_valid == True:
            is_valid = os.path.isfile(os.path.abspath(value) \
                + "/conf.yml")
        return is_valid

    def set(self, value):
        self.is_valid = self.check_arg(value)
        if self.is_valid == True:
            self.value = os.path.abspath(value)
        else:
            raise CfgArgError("Invalid parameter '{}': {} not a PCVS build directory"
                    .format(self.CFG_KEY, os.path.abspath(value))) 

class CfgArgInstall(CfgArgDir):

    CFG_KEY = "install"

    def check_arg(self, value):
        is_valid = super().check_arg(value) 
        if is_valid == True:
            is_valid = os.path.isfile(os.path.abspath(value) \
                + "/mpcvars.sh")
        return is_valid

    def set(self, value):
        self.is_valid = self.check_arg(value)
        if self.is_valid == True:
            self.value = os.path.abspath(value)
        else:
            raise CfgArgError("Invalid parameter '{}': {} not an MPC directory"
                    .format(self.CFG_KEY, os.path.abspath(value))) 

    def to_string(self):
        return "source {}/mpcvars.sh".format(self.value)

class CfgArgKeyValue(CfgArg):

    CFG_KEY = None
    CFG_STR = None
    
    def __init__(self, value):
        self.is_valid = self.check_arg(value)
        if self.is_valid == True:
            self.value = value
        else:
            raise CfgArgError("Invalid parameter: {}".format(self.CFG_KEY))

    def set(self, value):
        self.is_valid = self.check_arg(value)
        if self.is_valid == True:
            self.value = value
        else:
            raise CfgArgError("Invalid parameter: {}".format(self.CFG_KEY))

    def get(self):
        return self.value

    def is_valid(self):
        return self.is_valid

    def to_string(self):
        return self.CFG_STR + str(self.value)

class CfgArgCore(CfgArgKeyValue):

    CFG_KEY = "c"
    CFG_STR = "-c="

    def __init__(self, value=2):
        super().__init__(value)

    def check_arg(self, value):
        return isinstance(value, int) and value >= 1 

class CfgArgProc(CfgArgKeyValue):

    CFG_KEY = "p"
    CFG_STR = "-p="

    def __init__(self, value=2):
        super().__init__(value)

    def check_arg(self, value):
        return isinstance(value, int) and value >= 1 

class CfgArgNode(CfgArgKeyValue):

    CFG_KEY = "N"
    CFG_STR = "-N="

    def __init__(self, value=2):
        super().__init__(value)

    def check_arg(self, value):
        return isinstance(value, int) and value >= 1 

class CfgArgMPIProc(CfgArgKeyValue):

    CFG_KEY = "n"
    CFG_STR = "-n="

    def __init__(self, value=2):
        super().__init__(value)

    def check_arg(self, value):
        return isinstance(value, int) and value >= 1 

class CfgArgNet(CfgArgKeyValue):

    CFG_KEY = "net"
    CFG_STR = "--net="
    ALLOWED_VALUES = ["portals4", "tcp", "ib"]

    def __init__(self, value="tcp"):
        self.is_valid = self.check_arg(value)
        if self.is_valid == True:
            self.value = value
        else:
            raise CfgArgError("Invalid parameter: '{}' not in '{}'"
                    .format(value, *self.ALLOWED_VALUES))

    def set(self, value):
        self.is_valid = self.check_arg(value)
        if self.is_valid == True:
            self.value = value
        else:
            raise CfgArgError("Invalid parameter: '{}' not in '{}'"
                    .format(value, *self.ALLOWED_VALUES))

    def check_arg(self, value):
        return value in self.ALLOWED_VALUES 

class CfgArgOpt(CfgArgKeyValue):

    CFG_KEY = "opt"
    CFG_STR = "--opt='{}'"

    def __init__(self, value=""):
        super().__init__(value)

    def check_arg(self, value):
        #TODO: no arg check for opt
        return True 

    def to_string(self):
        return self.CFG_STR.format(self.value)

class CfgArgNPtl(CfgArgKeyValue):

    CFG_KEY = "n_ptl"
    CFG_STR = "export MPCFRAMEWORK_LOWCOMM_NETWORKING_RAILS_" \
            "PORTALSMPI_MAXIFACES="

    def __init__(self, value=0):
        super().__init__(value)

    def check_arg(self, value):
        return isinstance(value, int) and value >= 0

class CfgArgNPtl(CfgArgKeyValue):

    CFG_KEY = 'n_tcp'
    CFG_STR = ""

    def __init__(self, value=0):
        super().__init__(value)

    def check_arg(self, value):
        return isinstance(value, int) and value >= 0

    def to_string(self):
        return ""

class CfgArgPtlMaxMr(CfgArgKeyValue):

    CFG_KEY = 'ptl_max_mr'
    CFG_STR = "export MPCFRAMEWORK_LOWCOMM_NETWORKING_CONFIGS_" \
            "PORTALSCONFIGMPI_PORTALS_MAXMSGSIZE="

    def __init__(self, value=67108864):
        super().__init__(value)

    def check_arg(self, value):
        return isinstance(value, int) and value >= 0

class CfgArgOffload(CfgArgKeyValue):

    CFG_KEY = 'offload'
    CFG_STR = "export MPCFRAMEWORK_LOWCOMM_PROTOCOL_OFFLOAD="
    ALLOWED_VALUES = [0,1]

    def __init__(self, value=0):
        super().__init__(value)

    def check_arg(self, value):
        return value in self.ALLOWED_VALUES 

class CfgArgRndvMode(CfgArgKeyValue):

    CFG_KEY = 'rndv_mode'
    CFG_STR = "export MPCFRAMEWORK_LOWCOMM_PROTOCOL_RNDV_MODE="
    ALLOWED_VALUES = [0,1,2]

    def __init__(self, value=1):
        super().__init__(value)

    def check_arg(self, value):
        return value in self.ALLOWED_VALUES 

class CfgArgTransport(CfgArgKeyValue):

    CFG_KEY = 't_name'
    CFG_STR = "export MPCFRAMEWORK_LOWCOMM_PROTOCOL_TRANSPORTS="
    ALLOWED_VALUES = ["tbsm", "ptl", "tcp"]

    def __init__(self, value="tcp"):
        super().__init__(value)

    def check_arg(self, value):
        t_names = value.split(",")    
        for t_name in t_names:
            if t_name not in self.ALLOWED_VALUES:
                return False
        return True

class CfgArgVerbose(CfgArgKeyValue):

    CFG_KEY = 'verbose'
    CFG_STR = "export MPCFRAMEWORK_LOWCOMM_PROTOCOL_VERBOSITY="
    ALLOWED_VALUES = [0,1,2,3]

    def __init__(self, value=3):
        super().__init__(value)

    def check_arg(self, value):
        return value in self.ALLOWED_VALUES 

    def to_string(self):
        if self.value == 0:
            return ""
        elif self.value == 1:
            return "-v"
        elif self.value == 2:
            return "-vv"
        else:
            return "-vvv"

class CfgArgExeWrapper(CfgArg):

    CFG_KEY = "type" 
    CFG_STR = None
    ALLOWED_VALUES = ["std", "gdb", "log", "valgrind"]

    def __init__(self, value="std"):
        self.is_valid = self.check_arg(value)
        if self.is_valid == True:
            self.value = value
        else:
            raise CfgArgError("Invalid parameter: '{}' not in '{}'"
                    .format(value, *self.ALLOWED_VALUES))

    def check_arg(self, value):
        return value in self.ALLOWED_VALUES 

    def set(self, value):
        self.is_valid = self.check_arg(value)
        if self.is_valid == True:
            self.value = value
        else:
            raise CfgArgError("Invalid parameter: '{}' not in '{}'"
                    .format(value, str(self.ALLOWED_VALUES)))

    def get(self):
        return self.value

    def is_valid(self):
        return self.is_valid

    def to_string(self):
        if self.value == "gdb":
            return "xterm -e gdb --command=./gdbscript.gdb"
        elif self.value == "std":
            return ""
        elif self.value == "log":
            return "./out.sh"
        elif self.value == "valgrind":
            return "valgrind --log-file='vg-%p.out' --leak-check=full " \
                    "--show-leak-kinds=all --tool=memcheck --leak-check=yes"

class CfgArgExe(CfgArg):

    CFG_KEY = "fq_name"
    CFG_STR = None

    class Found(Exception):
        pass

    def __init__(self, value="exe"):
        self.value  = value
        self.is_valid = False

    def check_arg(self, value):
        return True

    def set(self, value):
        self.value = value

    def get(self):
        return self.value

    def is_valid(self):
        return self.is_valid

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

    def search(self, build):
        testdir = pathlib.Path(build + "/rawdata/")

        try:
            for f in testdir.iterdir():
                with f.open('r') as f_h:
                    data = json.load(f_h)
                    for t_js in data["tests"]:
                        if t_js["id"]["fq_name"] == self.value:
                            (path, args) = self.parse_exec_line(t_js["exec"])
                            raise self.Found
            self.is_valid = False
            raise CfgArgError("Could not find test with fq_name={}".
                    format(self.value))
        except self.Found:
            self.path = path
            self.args = args
            logging.debug("Found test: {}".format(self.value))
            logging.debug("Test path: {}. Tests args: {}".format(self.path, self.args))
            self.is_valid = True

    def to_string(self, with_arg):
        if self.is_valid == False:
            logging.warning("Test '{}' not set".format(self.value))
            return ""
        else:
            if with_arg == True:
                return self.path + " " + self.args
            else:
                return self.path

class CfgArgExeArgs(CfgArg):

    CFG_KEY = "program_args"

    def __init__(self, value=""):
        self.value  = value
        self.is_valid = True

    def check_arg(self, value):
        return True

    def set(self, value):
        self.value = value

    def get(self):
        return self.value

    def is_valid(self):
        return self.is_valid

    def to_string(self):
        return self.value

class Config():

    class ConfigEncoder(json.JSONEncoder):
        def __init__(self, *args, **kwargs):
            json.JSONEncoder.__init__(self, default=self.default, \
                    indent=4, *args, **kwargs)

        def default(self, o):
            if isinstance(o, CfgArg):
                return o.get()

    class ConfigDecoder(json.JSONDecoder):
        def __init__(self, *args, **kwargs):
            json.JSONDecoder.__init__(self, object_hook=self.object_hook, \
                    *args, **kwargs)

        def object_hook(self, o):
            config = Config()
            for key in o.keys():
                try:
                    config.set(key, o[key])
                except CfgArgError as e:
                    logging.warning(e) 

            return config

    def __init__(self):
        for key, cfgarg in _CFG_REGISTRY.items():
            self.__dict__[key[0]] = cfgarg()

    def set(self, key, value):
        self.__dict__[key].set(value)
        if key == "fq_name" and self.build.is_valid:
            self.fq_name.search(self.build.value)

    def get(self, key):
        return self.__dict__[key].get()

    def has_key(self, key):
        if key in self.__dict__:
            return True
        else:
            return False

    def __str__(self):
        config_dict = {}
        for key, cfgarg in self.__dict__.items():
            config_dict[key] = cfgarg.get()
        return str(config_dict)

    @classmethod
    def config_load(cls, json_filepath):
        with open(json_filepath, 'r') as f:
            return cls.ConfigDecoder().decode(f.read())

    def config_dump(self, json_filepath):
        with open(json_filepath, 'w') as f:
            json_str = self.ConfigEncoder().encode(self.__dict__)
            f.write(json_str)

    def config_print(self):
        logging.info("Printing configuration:\n{}"
                .format(self.ConfigEncoder().encode(self.__dict__)))

