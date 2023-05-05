from absl import flags
import benchmarks
import tests
import sys
import numpy as np
import matplotlib.pyplot as plt
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

FLAGS = flags.FLAGS

flags.DEFINE_string('pcvsdir', None, 'Path to PCVS build directory')
flags.DEFINE_string('iterator', None, 'PCVS iterator defined in profile') 
flags.DEFINE_string('mpcdir', None, 'Path to mpc results build directory')
flags.DEFINE_string('select', None, 'Name of the benchmark to select')
flags.DEFINE_list('pcvslist', None, 'Path to multiple PCVS build directories')
flags.DEFINE_boolean('output', False, 'Output the results in csv files')

colors = ['b', 'r', 'c', 'm', 'y', 'k', 'w'] 
markers = ['o', 'x', 'd', '*', '<', '>', '.']

def plot_list():

    # read all test suites
    ts_list = []
    for d in FLAGS.pcvslist:
        ts = tests.PCVSTestSuite(d)
        ts.build(FLAGS.iterator)
        ts_list.append(ts)

    # loop over all benchmarks 
    for key in ts_list[0].testsuite:

        b = benchmarks.GetBenchmarkClass(benchmarks.Benchmark, BENCHMARK_NAME=key)

        # loop over all metrics of the benchmark
        for ordinate in b.BENCHMARK_Y:
            logging.info("Plotting " + b.__name__ + " with " + ordinate)

            # Init plot
            fig, ax = plt.subplots(1,1)
            ax.grid()

            nplot = 0
            # loop over all test suites
            for ts in ts_list:

                # loop over all tests in the test suite
                labels = ["lcp multi", "ompi btl bxi", "old"]
                for t in ts.testsuite[key]:
                    d = b.parse(t.output)
                    #d = d.loc[d["bytes"] <= 64*1024]
                    if FLAGS.output:
                        d.to_csv("csv_" + t.uname + ".csv")
                    b.plot(ax, d, b.BENCHMARK_X[0], ordinate, 'dashed', markers[nplot], colors[nplot], labels[nplot])
                    nplot = nplot + 1 

            ax.set_title(b.BENCHMARK_NAME + "")
            fig_name = t.name + "_" + ordinate + "_multi_siam_cse" + ".jpeg"
            plt.savefig(fig_name)
            fig_name = t.name + "_" + ordinate + "_multi_siam_cse" + ".pdf"
            plt.savefig(fig_name)
            plt.close('all')

def plot_speedup():
    # read all test suites
    ts_list = []
    i = 0
    for d in FLAGS.pcvslist:
        ts = tests.PCVSTestSuite(d)
        ts.build(FLAGS.iterator)
        ts_list.append(ts)

    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    ts_list_speedup = list(chunks(ts_list, 2))
    # loop over all benchmarks 
    for key in ts_list[0].testsuite:

        b = benchmarks.GetBenchmarkClass(benchmarks.Benchmark, BENCHMARK_NAME=key)

        # loop over all metrics of the benchmark
        for ordinate in b.BENCHMARK_Y:
            logging.info("Plotting " + b.__name__ + " with " + ordinate)

            # Init plot
            fig, ax = plt.subplots(1,1)
            ax.grid()

            nplot = 0
            # loop over all test suites
            for ts_speedup in ts_list_speedup:
                ts_4nic = ts_speedup[0]
                ts_1nic = ts_speedup[1]
                # loop over all tests in the test suite
                labels = ["lcp offload rput ", "lcp offload rget", "lcp am rput", "lcp am rget", "ompi btl ptl4", "ompi btl bxi"]
                for t4nic, t1nic in zip(ts_4nic.testsuite[key], ts_1nic.testsuite[key]):
                    d4nic = b.parse(t4nic.output)
                    d1nic = b.parse(t1nic.output)
                    d = d4nic
                    d[ordinate] = d4nic[ordinate]/d1nic[ordinate]
                    if FLAGS.output:
                        d.to_csv("csv_" + t4nic.uname + ".csv")
                    b.plot(ax, d, b.BENCHMARK_X[0], ordinate, 'dashed', markers[nplot], colors[nplot], labels[nplot])
                    nplot = nplot + 1 

            ax.set_title(b.BENCHMARK_NAME + " speedup")
            fig_name = t4nic.name + "_" + ordinate + "_speedup" + ".jpeg"
            plt.savefig(fig_name)
            fig_name = t4nic.name + "_" + ordinate + "_speedup" + ".pdf"
            plt.savefig(fig_name)
            plt.close('all')

def plot_dev_vs_lcp_all():
    # Init testsuite
    ts_mpc = tests.PCVSTestSuite(FLAGS.mpcdir)
    ts_lcp = tests.PCVSTestSuite(FLAGS.pcvsdir)

    # Build testsuite
    ts_mpc.build(FLAGS.iterator)
    ts_lcp.build(FLAGS.iterator)

    for key in ts_mpc.testsuite:
        # Get benchmark class to apply specific parser
        b = benchmarks.GetBenchmarkClass(benchmarks.Benchmark, BENCHMARK_NAME=key)

        for ordinate in b.BENCHMARK_Y:
            logging.info("Plotting " + b.__name__ + " with " + ordinate)

            # Init plot
            fig, ax = plt.subplots(1,1)
            ax.grid()

            # first parse and plot lcp all
            nplot = 0
            labels = ["rwrma", "rget", "rput"]
            for t in ts_lcp.testsuite[key]:
                d = b.parse(t.output)
                b.plot(ax, d, b.BENCHMARK_X[0], ordinate, 'dashed', markers[nplot], colors[nplot], labels[nplot])
                #b.plot(ax, d, b.BENCHMARK_X[0], ordinate, markers[nplot], colors[nplot], "dev")
                nplot = nplot + 1

            # first parse and plot dev
            for t in ts_mpc.testsuite[key]:
                d = b.parse(t.output)
                b.plot(ax, d, b.BENCHMARK_X[0], ordinate, 'dashed', markers[nplot+1], colors[nplot+1], "ompi")

            ax.set_title(b.BENCHMARK_NAME)
            fig_name = t.name + "_" + ordinate + ".pdf"
            plt.savefig(fig_name)
            plt.close('all')

def plot_dev_vs_lcp():
    # Init testsuite
    ts_mpc = tests.PCVSTestSuite(FLAGS.mpcdir)
    ts_lcp = tests.PCVSTestSuite(FLAGS.pcvsdir)

    # Build testsuite
    ts_mpc.build(FLAGS.iterator)
    ts_lcp.build(FLAGS.iterator)

    i = 0
    for t1, t2 in zip(ts_mpc.testsuite, ts_lcp.testsuite):
        assert t1.name == t2.name

        if (FLAGS.select != "" and FLAGS.select != t1.name):
            continue

        # Get benchmark class to apply specific parser
        benchclass = benchmarks.GetBenchmarkClass(benchmarks.Benchmark, BENCHMARK_NAME=t1.name)

        # Instanciate benchmark
        b1 = benchclass(t1.output)
        b2 = benchclass(t2.output)

        # Parse output and get DataFrame
        data1 = b1.parse()
        data2 = b2.parse()

        for ordinate in b1.BENCHMARK_Y:
            logging.info("Plotting " + t1.name + " with " + ordinate)
            # Init plot
            fig, ax = plt.subplots(1,1)
            ax.grid()

            # Add plot
            b1.plot(ax, data1, b1.BENCHMARK_X[0], ordinate, markers[0], colors[0], "dev")
            b2.plot(ax, data2, b2.BENCHMARK_X[0], ordinate, markers[1], colors[1], "lcp")

            # global settings
            ax.set_xscale('log')
            ax.set_yscale('log')
            xticks = [d for d in data1["bytes"][0::4]] 
            xtick_labels = []
            for d in xticks:
                if d < 1024:
                    tik = str(int(d)) + "B"
                elif d < 1024*1024:
                    tik = str(int(d/1024)) + "kB"
                elif d < 1024*1024*1024:
                    tik = str(int(d/(1024*1024))) + "MB"
                else:
                    tik = str(int(d/(1024*1024*1024))) + "GB"
                xtick_labels.append(tik)

            ax.set_xticks(ticks=xticks, labels=xtick_labels)
            ax.set_xlabel("Message size")
            
            ax.set_title(b1.BENCHMARK_NAME)
            fig_name = t1.name + "_" + ordinate + ".pdf"
            plt.savefig(fig_name)
            plt.close('all')

def plot_n_ptl():
    # Init testsuite
    ts = tests.PCVSTestSuite(FLAGS.pcvsdir)

    # Build testsuite
    ts.build(FLAGS.iterator)
    
    fig, ax = plt.subplots(1,1)
    ax.grid()
    i=0
    for t in ts.testsuite:
        # Get benchmark class to apply specific parser
        benchclass = benchmarks.GetBenchmarkClass(benchmarks.Benchmark, BENCHMARK_NAME=t.name)

        # Instanciate benchmark
        bench = benchclass(t.output)

        # Parse output and get DataFrame
        data = bench.parse()
        #data = data.loc[data["bytes"] >= 64*1024*1024]

        # Plot
        bench.plot(ax, data, bench.BENCHMARK_X[0], "bandwidth", markers[i], colors[i], "n ptl="+str(t.it_value))
        i = i + 1

    ax.set_ylabel('Bandwidth [MB/sec]')
    ax.set_xlabel('Message Size')
    xticks = [d for d in data["bytes"][0::4]]
    xtick_labels = []
    for d in xticks:
        if d < 1024:
            tik = str(int(d)) + "B"
        elif d < 1024*1024:
            tik = str(int(d/1024)) + "kB"
        elif d < 1024*1024*1024:
            tik = str(int(d/(1024*1024))) + "MB"
        else:
            tik = str(int(d/(1024*1024*1024))) + "GB"
        xtick_labels.append(tik)

    ax.set_xticks(ticks=xticks, labels=xtick_labels)

    plt.title("PingPong, Fragment size=64MB")
    fig_name = ts.testsuite[0].name + "_" + str(FLAGS.iterator) + ".pdf"
    plt.savefig(fig_name)
    plt.close('all')

def main():
    #plot_dev_vs_lcp()
    #plot_n_ptl()
    #plot_diff()
    #plot_dev_vs_lcp_all()
    plot_list()
    #plot_speedup()
    
if __name__=="__main__":
    FLAGS(sys.argv)
    main()
