import argparse
import numpy as np
from multiprocessing import shared_memory
import socket
import time
import sys

class Parameters:
    def __init__(self, id, cluster, type, failures):
        self.host = '127.0.0.1'
        
        self.id = int(id)
        self.type = int(type)
        self.port = int(id + type)

        self.cluster = [int(member) for member in cluster]
        self.cluster.sort(reverse=True)
        print(self.cluster)

        self.proposal = 42

        self.memoryKey = 'memory' + id
        self.flagsKey = 'flag' + id

        self.failures = int(failures)
        self.rounds = self.failures + 1
        self.currentRound = 0
        
        self.timeout = 3 # seconds

        print(f"Parameters: id = {self.id} port = {self.port} cluster = {self.cluster} memoryKey = {self.memoryKey}")

class Process():
    def __init__(self) -> None:
        # Reading input flags
        argParser = argparse.ArgumentParser()
        argParser.add_argument("--id", help="Process identifier", required=True)
        argParser.add_argument("--type", help="Process role (1 for server, 2 for client)", required=True)
        argParser.add_argument("--cluster", help="Numbers of all processes", required=True, nargs='+')
        argParser.add_argument("--failures", help="Amount of failures to tolerate", required=True)
        args = argParser.parse_args()

        self.parameters = Parameters(id=args.id, cluster=[member for member in args.cluster], type=args.type, failures=args.failures)

        if self.parameters.type == 1:
            l = [(member, -1) for member in self.parameters.cluster]
            l[self.parameters.cluster.index(self.parameters.id)] = (self.parameters.id, self.parameters.proposal)
            a = np.array(l, dtype="i,i")
            self.dataMemory = shared_memory.SharedMemory(create=True, name=self.parameters.memoryKey, size=a.nbytes)
            self.data = np.ndarray(a.shape, dtype=a.dtype, buffer=self.dataMemory.buf)
            self.data[:] = a[:]

            l = []
            if max(self.parameters.cluster) == self.parameters.id: # Flag to the sender sibling process if it's its turn to send
                l.append(int(True))
            else:
                l.append(int(False))
            l.append(self.parameters.currentRound) # Tells the sender sibling process the current round so it can print the number
            b = np.array(l)
            self.flagsMemory = shared_memory.SharedMemory(create=True, name=self.parameters.flagsKey, size=b.nbytes)
            self.flags = np.ndarray(b.shape, dtype=b.dtype, buffer=self.flagsMemory.buf)
            self.flags[:] = b[:]

            self.makeServer()
            self.actServer()

        elif self.parameters.type == 2:
            self.dataMemory = shared_memory.SharedMemory(name=self.parameters.memoryKey)
            self.data = np.ndarray((len(self.parameters.cluster),), dtype="i,i", buffer=self.dataMemory.buf)

            self.flagsMemory = shared_memory.SharedMemory(name=self.parameters.flagsKey)
            self.flags = np.ndarray((2,), dtype=np.int32, buffer=self.flagsMemory.buf)

            print(f"self.data = {self.data} self.flags = {self.flags}")

            self.makeClient()
            self.actClient()

        return

    def makeServer(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.socket.settimeout(2)
        self.socket.bind((self.parameters.host, self.parameters.port))
        print(f"Listening on port {self.parameters.port}...")
        self.socket.listen()
    
    def actServer(self):
        #lastConnection = time.time()
        #print(lastConnection)
        while True:
            conn, addr = self.socket.accept()
            print(f"testing something")
            with conn:
                data = conn.recv(1024)
                if int(addr[1]/10) == self.parameters.id:
                    print(f"{data.decode()}")
                    quit()

                print(f"(Round {self.flags[1]}) Received {data.decode()} from {addr[1]}")
                conn.send("Received".encode())
                conn.close()

                i = self.parameters.cluster.index(int(addr[1]/10))
                self.data[i] = (int(addr[1]/10), int(data.decode()))
                print(f"self.data = {self.data}")

                #lastConnection = time.time()
                iRecv = self.parameters.cluster.index(int(addr[1]/10))
                iSelf = self.parameters.cluster.index(self.parameters.id)
                print(f"iRecv = {iRecv} iSelf = {iSelf}")
                if iRecv + 1 == iSelf or (iSelf == 0 and iRecv + 1 == len(self.parameters.cluster)):
                    self.flags[0] = int(True)

    def makeClient(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.parameters.host, self.parameters.port))
        print(f"Port {self.parameters.port} waiting for its turn...")       

    def actClient(self):
        while True:
            status = bool(self.flags[0])
            if status:
                self.flags[1] += 1
                if self.flags[1] <= self.parameters.rounds:
                    print(f">>>>> Starting round {self.flags[1]}")
                    data = str(self.parameters.proposal)

                    for member in self.parameters.cluster:
                        if member != self.parameters.id:
                            port = int(str(member) + '1')
                            #port = 10021
                            print(f"Sending {data} to {port}...")
                            self.socket.connect((self.parameters.host, port))
                            self.socket.send(data.encode())
                            rec = self.socket.recv(1024)
                            print(f"Response received: {rec.decode()}")

                    self.flags[0] = int(False)
                    #print(f"Waiting...")
                    #time.sleep(1)
                    #print(f"self.data = {self.data} self.flags = {self.flags}")
                else:
                    k = sorted(self.data, key=lambda tup: tup[1])
                    for i in k:
                        if i[1] == -1:
                            continue
                        else:
                            consensus = i

                    port = int(str(self.parameters.id) + '1') # Telling the receiver sibling process to shut down
                    data = f"Consensus reached: {consensus[1]}"
                    print(data)
                    self.socket.connect((self.parameters.host, port))
                    self.socket.send(data.encode())
                    quit()

p = Process()