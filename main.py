import argparse
import numpy as np
from multiprocessing import shared_memory

class Parameters:
    def __init__(self, id, cluster, type):
        self.host = '127.0.0.1'
        
        self.id = int(id)
        self.type = int(type)
        self.port = int(id + type)

        self.cluster = [int(member + '2') for member in cluster]
        self.cluster.sort(reverse=True)

        self.proposal = 42

        self.memoryKey = 'memory' + id

        print(f"{self.port} {self.cluster} {self.memoryKey}")

        if self.type == 1: # Client process
            print(f"Entering if")
            a = np.array([(1, 2), (3, 4)], dtype="i,i")
            print(a.dtype)

            self.memory = shared_memory.SharedMemory(create=True, name=self.memoryKey, size=a.nbytes)

            b = np.ndarray(a.shape, dtype=a.dtype, buffer=self.memory.buf)
            b[:] = a[:]

            while True:
                x = 1+1
                continue
        
        elif self.type == 2: # Server process
            self.memory = shared_memory.SharedMemory(name=self.memoryKey)
            c = np.ndarray((2,), dtype="i,i", buffer=self.memory.buf)
            print(c)

class Process():
    def __init__(self) -> None:
        # Reading input flags
        argParser = argparse.ArgumentParser()
        argParser.add_argument("--id", help="Process identifier", required=True)
        argParser.add_argument("--type", help="Process role (1 for server, 2 for client)", required=True)
        argParser.add_argument("--cluster", help="Numbers of all processes", required=True, nargs='+')
        args = argParser.parse_args()

        self.parameters = Parameters(id=args.id, cluster=[member for member in args.cluster], type=args.type)

        return

p = Process()