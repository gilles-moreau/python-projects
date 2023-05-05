import json
import base64
import os
import io
import pathlib
import logging

class PCVSTest():

    def __init__(self, t_js, testdir, it):
        self.data  = t_js 
        self.name  = self.data["id"]["te_name"]
        self.uname = str(testdir) + "_" + self.data["id"]["fq_name"]
        self.uname = self.uname.replace("/","_")

        try:
            self.it_value = self.data["id"]["comb"][it]
        except KeyError as err:
            logging.warning("test name= " + self.name +": it= " + str(it))

        try:
            self.benchname = self.data["data"]["tags"]
        except KeyError as err:
            logging.error(err)
            logging.error("Tests were not tagged.")
            sys.exit(1)

        #TODO: add some semantic to improve tag parsing
        self.output = base64.b64decode(self.data["result"]["output"]).decode()
        logging.info("Initialized PCVSTest: name=" + self.name)

class PCVSTestSuite():

    def __init__(self, test_dir):
        self.testdir   = pathlib.Path(test_dir + "rawdata/")
        self.files     = self.testdir.iterdir()
        self.testsuite = {}
        self.ntests    = 0
        logging.info("Initialized PCVSSuite: directory=" + self.testdir.name)

    def build(self, it):
        for f in self.files:
            with f.open('r') as f_h:
                data = json.load(f_h)
                for t_js in data["tests"]:
                    if t_js["id"]["te_name"] == "Barrier" or \
                            t_js["id"]["te_name"] == "Ibarrier":
                        continue
                    t = PCVSTest(t_js, self.testdir, it)
                    if "compilation" not in t.benchname:
                        if not t.name in self.testsuite:
                            self.testsuite[t.name] = [t]
                        else:
                            self.testsuite[t.name].append(t)
                        self.ntests = self.ntests + 1

        # sort list of test by name
        for t_name in self.testsuite:
            self.testsuite[t_name].sort(key=lambda x: x.uname, reverse=True);

        logging.info("Built PCVSSuite: ntests=" + str(self.ntests))
