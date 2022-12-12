import argparse
import numpy as np
from multiprocessing import shared_memory
import socket
import time

class Parameters:
    def __init__(self, id, cluster, type):
        self.host = '127.0.0.1'
        
        self.id = int(id)
        self.type = int(type)
        self.port = int(id + type)

        self.cluster = [int(member) for member in cluster]
        self.cluster.sort(reverse=True)
        print(self.cluster)

        self.proposal = 42

        self.memoryKey = 'memory' + id

        print(f"Parameters:\nid = {self.id} port = {self.port} cluster = {self.cluster} memoryKey = {self.memoryKey}")

class Process():
    def __init__(self) -> None:
        # Reading input flags
        argParser = argparse.ArgumentParser()
        argParser.add_argument("--id", help="Process identifier", required=True)
        argParser.add_argument("--type", help="Process role (1 for server, 2 for client)", required=True)
        argParser.add_argument("--cluster", help="Numbers of all processes", required=True, nargs='+')
        args = argParser.parse_args()

        self.parameters = Parameters(id=args.id, cluster=[member for member in args.cluster], type=args.type)

        if self.parameters.type == 1:
            l = [(member, -1) for member in self.parameters.cluster]
            #l[self.cluster.index(self.id)] = (self.id, self.proposal)
            a = np.array(l, dtype="i,i")

            self.memory = shared_memory.SharedMemory(create=True, name=self.parameters.memoryKey, size=a.nbytes)

            self.data = np.ndarray(a.shape, dtype=a.dtype, buffer=self.memory.buf)
            self.data[:] = a[:]

            self.actClient()
        elif self.parameters.type == 2:
            self.memory = shared_memory.SharedMemory(name=self.parameters.memoryKey)
            self.data = np.ndarray((len(self.parameters.cluster),), dtype="i,i", buffer=self.memory.buf)

            print(self.data)

            self.actServer()

        return

    def actServer(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.parameters.host, self.parameters.port))

        data = str(self.parameters.proposal)
        port = int(str(self.parameters.id) + '1')

        print(f"Sending {data} to {port}...")
        self.socket.connect((self.parameters.host, port))
        self.socket.send(data.encode())
        data = self.socket.recv(1024)
        print(f"Response received: {data.decode()}")

        self.socket.close()

        print(f"Waiting...")
        time.sleep(5)
        print(f"self.data = {self.data}")
        return
    
    def actClient(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.parameters.host, self.parameters.port))
        print(f"Listening on port {self.parameters.port}...")
        self.socket.listen()

        while True:
            conn, addr = self.socket.accept()
            with conn:
                data = conn.recv(1024)
                print(f"Received {data.decode()} from {addr[1]}")
                conn.send("Received".encode())
                conn.close()

                i = self.parameters.cluster.index(int(addr[1]/10))
                self.data[i] = (int(addr[1]/10), int(data.decode()))
                print(f"self.data = {self.data}")
        return

p = Process()