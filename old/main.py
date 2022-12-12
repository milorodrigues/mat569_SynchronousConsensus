import argparse
import socket
import time

class Parameters:
    def __init__(self, port, cluster, failures):
        self.host = '127.0.0.1'
        self.port = port

        cluster.sort(reverse=True)
        self.cluster = cluster

        self.failures = failures
        self.rounds = self.failures + 1
        self.proposal = 42

class Process:
    def __init__(self):
        # Reading input flags
        argParser = argparse.ArgumentParser()
        argParser.add_argument("--port", help="Port for first process to listen to, also process identifier", required=True)
        argParser.add_argument("--cluster", help="Numbers of all processes", required=True, nargs='+')
        argParser.add_argument("--failures", help="Amount of failures to tolerate", required=True)
        args = argParser.parse_args()

        self.parameters = Parameters(port=int(args.port), cluster=[int(member) for member in args.cluster], failures=int(args.failures))

        self.values = []
        self.values.append(set())
        self.values.append(set())
        self.values[1].add(self.parameters.proposal)

        for r in range(1,self.parameters.rounds):
            self.round(r)

        consensus = min(self.values[-1])
        print(f">>>> Consensus reached: {consensus}")

    def round(self, r):
        print(f"##### Round {r} #####")

        newSet = set()
        newSet.update(self.values[r])
        self.values.append(newSet)

        for turn in self.parameters.cluster:
            print(f"## {turn}'s turn ##")
            if turn == self.parameters.port:
                self.actSender(r)
            else:
                self.actReceiver(r)
    
    def actSender(self, r):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.parameters.host, self.parameters.port))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(5)

        setToSend = self.values[r].difference(self.values[r-1])

        for member in self.parameters.cluster:
            if member != self.parameters.port:
                data = f"{self.parameters.port},{self.setToString(setToSend)}"
                print(f"Sending {data} to {member}...", end='')
                for attempt in range(1,4):
                    try:
                        self.socket.connect((self.parameters.host, member))
                        self.socket.send(data.encode())
                        data = self.socket.recv(1024)
                        if data:
                            print(f"sent")
                            break
                    except socket.timeout as e:
                        print("\nTimed out, trying again...")

        self.socket.close()
    
    def actReceiver(self, r):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.parameters.host, self.parameters.port))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if r > 1:
            self.socket.settimeout(5)

        print(f"Listening on port {self.parameters.port}...")
        self.socket.listen()

        try:
            while True:
                conn, addr = self.socket.accept()
                with conn:
                    data = conn.recv(1024)
                    values = data.decode().split(',')[1:]
                    self.values[r+1].update(set(map(int, values)))
                    print(f"Received {values} from {addr[1]}")
                    conn.send("Received".encode())
                    conn.close()
                    print("Stopping listening...")
                    break
        except socket.timeout as e:
            print("\nTimed out, stopping listening")
        
        self.socket.close()

    def setToString(self, input):
        return ','.join(set(map(str, input)))

p = Process()