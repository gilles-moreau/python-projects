import abc
import logging
import pandas as pd
import io
import matplotlib
import matplotlib.pyplot as plt
from typing import List

_BENCHMARK_REGISTRY = {}

def GetBenchmarkClass(base_class, **kwargs):
    key = [kwargs["BENCHMARK_NAME"]]
    if tuple(key) not in _BENCHMARK_REGISTRY:
        logging.fatal("Benchmark not defined: " + str(key))
        exit(1)

    return _BENCHMARK_REGISTRY.get(tuple(key))

class AutoRegisterBenchmarkMeta(abc.ABCMeta):

    BENCHMARK_NAME: str
    BENCHMARK_X: List[str] # Abscisse 
    BENCHMARK_Y: List[str] # Ordonnees

    def __init__(cls, name, bases, dct):
        if cls.BENCHMARK_NAME:
            key = [cls.BENCHMARK_NAME]
            _BENCHMARK_REGISTRY[tuple(key)] = cls
        super(AutoRegisterBenchmarkMeta, cls).__init__(name, bases, dct)

class Benchmark(metaclass=AutoRegisterBenchmarkMeta):

    BENCHMARK_NAME = None

    @classmethod
    @abc.abstractmethod
    def parse(cls, output):
        return io.StringIO(output)

    @classmethod
    @abc.abstractmethod
    def plot(cls, ax, df, x, y, linestyle, color, label):
        pass

class OSU(Benchmark):

    @staticmethod
    def my_readline(f):
        byte_str = f.readline()
        if len( byte_str ) == 0:
            return None
        try:
            if byte_str[0] in 'abc':
                ch_str = byte_str   # python2
            else:
                ch_str = byte_str
        except:                     # python3
            ch_str = byte_str.decode()
    
        if len( ch_str ) > 0:
            ch_str = ch_str[0:-1]   # remove newline
        tokens = ch_str.split()
        return tokens

    @staticmethod
    def get_benchmark(f):
        while( True ):
            tokens = OSU.my_readline(f)
            if tokens is None:
                return (None, None)
            nc = len( tokens )
            if nc < 2:
                continue;
            if tokens[1] == "OSU":
                bench = tokens[3]
                #if not GetBenchmarkClass(Benchmark, BENCHMARK_NAME=bench):
                #    print( 'Unsupported benchmark: ', bench )
                #    continue
                break
        # skip one line
        OSU.my_readline(f)    

        return (bench, 2)

    @classmethod
    def plot(cls, ax, df, x, y, linestyle, marker, color, label):
        ax.plot(df[x], df[y], linestyle=linestyle, marker=marker, label=label, color=color)

        # set labels
        ax.set_xlabel(cls.x_plt_label[x])
        ax.set_ylabel(cls.y_plt_label[y])

        # set legend
        ( h0, l0 ) = ax.get_legend_handles_labels()
        ax.legend( h0, l0, loc='upper left' )

        # set scales 
        ax.set_xscale('log')
        ax.set_yscale('log')

        # set ticks
        xticks = [d for d in df[x][0::4]] 
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

class OSULatency(OSU):
    BENCHMARK_NAME = "pt2pt_osu_latency" 
    BENCHMARK_X = ['bytes']
    BENCHMARK_Y = ['latency']

    x_plt_label = {
            "bytes": "Message Size"
            }
    y_plt_label = {
            "latency": "Latency [usec]"
            }

    @classmethod
    def parse(cls, output):
        f = super().parse(output)
        (bench, proc) = OSU.get_benchmark(f)

        dct = {
                "bytes": [],
                "latency": []
                }
        while True:
            tokens = OSU.my_readline(f)
            if tokens == [] or tokens is None:
                break;
            try:
                if int(tokens[0]) == 0:
                    continue
                dct["bytes"].append(int(tokens[0]))
                dct["latency"].append(float(tokens[1]))
            except:
                break

        pp_data = pd.DataFrame(dct)

        return pp_data

class OSUBandwidth(OSU):
    BENCHMARK_NAME = "pt2pt_osu_bw" 
    BENCHMARK_X = ['bytes']
    BENCHMARK_Y = ['bandwidth']

    x_plt_label = {
            "bytes": "Message Size"
            }
    y_plt_label = {
            "bandwidth": "Bandwidth [MB/sec]"
            }

    @classmethod
    def parse(cls, output):
        f = super().parse(output)
        (bench, proc) = OSU.get_benchmark(f)

        dct = {
                "bytes": [],
                "bandwidth": []
                }
        while True:
            tokens = OSU.my_readline(f)
            if tokens == [] or tokens is None:
                break;
            try:
                if int(tokens[0]) == 0:
                    continue
                dct["bytes"].append(int(tokens[0]))
                dct["bandwidth"].append(float(tokens[1]))
            except:
                break

        pp_data = pd.DataFrame(dct)

        return pp_data


class IMB(Benchmark):

    @staticmethod
    def my_readline(f):
        byte_str = f.readline()
        if len( byte_str ) == 0:
            return None
        try:
            if byte_str[0] in 'abc':
                ch_str = byte_str   # python2
            else:
                ch_str = byte_str
        except:                     # python3
            ch_str = byte_str.decode()
    
        if len( ch_str ) > 0:
            ch_str = ch_str[0:-1]   # remove newline
        tokens = ch_str.split()
        return tokens

    @staticmethod
    def get_benchmark(f):
        while( True ):
            tokens = IMB.my_readline(f)
            if tokens is None:
                return (None, None)
            nc = len( tokens )
            if nc > 3:
                if tokens[1] == 'BAD' and tokens[2] == 'TERMINATION':
                    #print( 'BAD TERMINATION' )
                    return (None, None)
                continue
            if nc != 3:
                continue
            if tokens[1] == 'Benchmarking':
                bench = tokens[2]
                if not GetBenchmarkClass(Benchmark, BENCHMARK_NAME=bench):
                    print( 'Unsupported benchmark: ', bench )
                    continue
                break
    
        tokens = IMB.my_readline( f )
        if tokens is None:
            return (None, None)
        nprocs = int( tokens[3] )
        # skip '#-----'
        while( True ):
            tokens = IMB.my_readline( f )
            if tokens is None:
                return (None, None)
            if len( tokens ) == 1 and tokens[0][0] == '#' and tokens[0][1] == '-':
                while( True ) :
                    tokens = IMB.my_readline( f )
                    if tokens[0] == '#bytes' or tokens[0] == '#repetitions':
                        break;
                break
        return ( bench, nprocs )

    @classmethod
    def plot(cls, ax, df, x, y, linestyle, marker, color, label):
        ax.plot(df[x], df[y], linestyle=linestyle, marker=marker, label=label, color=color)

        # set labels
        ax.set_xlabel(cls.x_plt_label[x])
        ax.set_ylabel(cls.y_plt_label[y])

        # set legend
        ( h0, l0 ) = ax.get_legend_handles_labels()
        ax.legend( h0, l0, loc='upper left' )

        # set scales 
        ax.set_xscale('log')
        ax.set_yscale('log')

        # set ticks
        xticks = [d for d in df[x][0::4]] 
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

class IMBPing(IMB):
    BENCHMARK_NAME = None
    BENCHMARK_X = ['bytes']
    BENCHMARK_Y = ['latency', 'bandwidth']

    x_plt_label = {
            "bytes": "Message Size"
            }
    y_plt_label = {
            "latency": "Latency [usec]",
            "bandwidth": "Bandwidth [MB/sec]"
            }

    @classmethod
    def parse(cls, output):
        f = super().parse(output)
        (bench, proc) = IMB.get_benchmark(f)
        dct = {
                "bytes": [],
                "latency": [],
                "bandwidth": []
                }
        if (bench, proc) == (None, None):
            logging.error("Wrong output for benchmark " + str(cls))
            return pd.DataFrame(dct)

        while True:
            while True:
                tokens = IMB.my_readline(f)
                
                if tokens == [] or tokens is None:
                    break
                try:
                    if int(tokens[0]) == 0:
                        continue
                    dct["bytes"].append(int(tokens[0]))
                    dct["latency"].append(float(tokens[2]))
                    dct["bandwidth"].append(float(tokens[3]))
                except:
                    break

            pp_data = pd.DataFrame(dct)

            rv = IMB.get_benchmark(f)
            if rv is None:
                break
            ( b, p ) = rv
            if b != bench or p != np:
                break
    
        return pp_data 


class IMBCollective(IMB):
    BENCHMARK_NAME = None
    BENCHMARK_X = ['bytes']
    BENCHMARK_Y = ['avgtime']

    x_plt_label = {
            "bytes": "Message Size"
            }
    y_plt_label = {
            "avgtime": "Latency [usec]"
            }
    
    @classmethod
    def parse(cls, f):
        f = cls.super().parse(output)
        (bench, proc) = IMB.get_benchmark(f)

        while True:
            dct = {
                    "bytes": [],
                    "avgtime": []
                    }
            while True:
                tokens = IMB.my_readline(f)
                if tokens == [] or tokens is None:
                    break;
                dct["bytes"].append(int(tokens[0]))
                dct["avgtime"].append(float(tokens[4]))

            pp_data = pd.DataFrame(dct)

            rv = IMB.get_benchmark(f)
            if rv is None:
                break
            ( b, p ) = rv
            if b != bench or p != np:
                break

        return pp_data

class IMBExchange(IMB):
    BENCHMARK_NAME = None
    BENCHMARK_X = ['bytes']
    BENCHMARK_Y = ['latency', 'bandwidth']

    x_plt_label = {
            "bytes": "Length"
            }
    y_plt_label = {
            "latency": "Latency [usec]",
            "bandwidth": "Bandwidth [MB/sec]"
            }

    @classmethod
    def parse(cls, f):
        f = super().parse(output)
        (bench, proc) = IMB.get_benchmark(f)
        dct = {
                "bytes": [],
                "latency": [],
                "bandwidth": []
                }
        if (bench, proc) == (None, None):
            logging.error("Wrong output for benchmark " + str(cls))
            return pd.DataFrame(dct)

        while True:
            while True:
                tokens = IMB.my_readline(f)
                if tokens == [] or tokens is None:
                    break;
                dct["bytes"].append(int(tokens[0]))
                dct["latency"].append(float(tokens[4]))
                dct["bandwidth"].append(float(tokens[5]))

            pp_data = pd.DataFrame(dct)

            rv = IMB.get_benchmark(f)
            if rv is None:
                break
            ( b, p ) = rv
            if b != bench or p != np:
                break

        return pp_data

#TODO: Barrier must be parsed differently

class IMBNBC(IMB):
    BENCHMARK_X = ['bytes']
    BENCHMARK_Y = ['overlap', 'cpu', 'overlappercent']

    x_plt_label = {
            "bytes": "Length"
            }
    y_plt_label = {
            "overlap": "Overlap [usec]",
            "cpu": "CPU [usec]",
            "overlappercent": "Overlap [%]"
            }

    @classmethod
    def parse(cls, f):
        f = super().parse(output)
        (bench, proc) = IMB.get_benchmark(f)
        dct = {
                "bytes": [],
                "overlap": [],
                "cpu": [],
                "overlappercent": []
                }
        if (bench, proc) == (None, None):
            logging.error("Wrong output for benchmark " + str(cls))
            return pd.DataFrame(dct)

        while True:
            while True:
                tokens = IMB.my_readline(f)
                if tokens == [] or tokens is None:
                    break;
                dct["bytes"].append(int(tokens[0]))
                dct["overlap"].append(float(tokens[2]))
                dct["cpu"].append(float(tokens[4]))
                dct["overlappercent"].append(float(tokens[5]))

            pp_data = pd.DataFrame(dct)

            rv = IMB.get_benchmark(f)
            if rv is None:
                break
            ( b, p ) = rv
            if b != bench or p != np:
                break

        return pp_data

class IMBPingPong(IMBPing):
    BENCHMARK_NAME = 'PingPong'

class IMBPingPongSpecificSource(IMBPing):
    BENCHMARK_NAME = 'PingPongSpecificSource'

class IMBPingPing(IMBPing):
    BENCHMARK_NAME = 'PingPing'

class IMBPingPingSpecificSource(IMBPing):
    BENCHMARK_NAME = 'PingPingSpecificSource'

class IMBSendRecv(IMBExchange):
    BENCHMARK_NAME = 'Sendrecv'

class IMBExchange(IMBExchange):
    BENCHMARK_NAME = 'Exchange'

class IMBIbarrier(IMBNBC):
    BENCHMARK_NAME = 'Ibarrier'

class IMBIallreduce(IMBNBC):
    BENCHMARK_NAME = 'Iallreduce'

class IMBIreduce_scatter(IMBNBC):
    BENCHMARK_NAME = 'Ireduce_scatter'

class IMBIreduce(IMBNBC):
    BENCHMARK_NAME = 'Ireduce'

class IMBIalltoall(IMBNBC):
    BENCHMARK_NAME = 'Ialltoall'

class IMBIalltoallv(IMBNBC):
    BENCHMARK_NAME = 'Ialltoallv'

class IMBIscatter(IMBNBC):
    BENCHMARK_NAME = 'Iscatter'

class IMBIscatterv(IMBNBC):
    BENCHMARK_NAME = 'Iscatterv'

class IMBIgather(IMBNBC):
    BENCHMARK_NAME = 'Igather'

class IMBIgatherv(IMBNBC):
    BENCHMARK_NAME = 'Igatherv'

class IMBIallgather(IMBNBC):
    BENCHMARK_NAME = 'Iallgather'

class IMBIallgatherv(IMBNBC):
    BENCHMARK_NAME = 'Iallgatherv'

class IMBIbcast(IMBNBC):
    BENCHMARK_NAME = 'Ibcast'

class IMBBcast(IMBCollective):
    BENCHMARK_NAME = 'Bcast'

class IMBAlltoall(IMBCollective):
    BENCHMARK_NAME = 'Alltoall'

class IMBAlltoallv(IMBCollective):
    BENCHMARK_NAME = 'Alltoallv'

class IMBScatter(IMBCollective):
    BENCHMARK_NAME = 'Scatter'

class IMBScatterv(IMBCollective):
    BENCHMARK_NAME = 'Scatterv'

class IMBGather(IMBCollective):
    BENCHMARK_NAME = 'Gather'

class IMBGatherv(IMBCollective):
    BENCHMARK_NAME = 'Gatherv'

class IMBAllgather(IMBCollective):
    BENCHMARK_NAME = 'Allgather'

class IMBAllgatherv(IMBCollective):
    BENCHMARK_NAME = 'Allgatherv'

class IMBReduce(IMBCollective):
    BENCHMARK_NAME = 'Reduce'

class IMBAllreduce(IMBCollective):
    BENCHMARK_NAME = 'Allreduce'

class IMBReduce(IMBCollective):
    BENCHMARK_NAME = 'Reduce'

class IMBReduce_scatter(IMBCollective):
    BENCHMARK_NAME = 'Reduce_scatter'
