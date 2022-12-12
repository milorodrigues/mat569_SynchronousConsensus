import argparse
import socket
import time

class Parameters:
    def __init__(self, id, cluster, failures):
        self.host = '127.0.0.1'
        
        self.id = int(id)

        self.cluster = [int(member) for member in cluster]
        self.cluster.sort(reverse=True)
        print(self.cluster)

        self.proposal = 42

        self.failures = int(failures)
        self.rounds = self.failures + 1

class Process():
    def __init__(self) -> None:
        # Reading input flags
        argParser = argparse.ArgumentParser()
        argParser.add_argument("--id", help="Process identifier", required=True)
        argParser.add_argument("--cluster", help="Identifiers of all processes", required=True, nargs='+')
        argParser.add_argument("--failures", help="Amount of failures to tolerate", required=True)
        args = argParser.parse_args()

        self.parameters = Parameters(id=args.id, cluster=[member for member in args.cluster], failures=args.failures)

        self.firstInLine = False
        self.currentRound = 0
        if max(self.parameters.cluster) == self.parameters.id:
            self.firstInLine = True
        self.lastConnection = -1

        self.values = {}
        self.values[0] = set()
        self.values[1] = set()
        self.values[1].add(self.parameters.proposal)

        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket.settimeout(2)
        self.socket.bind((self.parameters.host, self.parameters.id))

        if self.firstInLine:
            self.actSender()
        else:
            self.actListener()

    def actListener(self):
        print(f"Listening on port {self.parameters.id}...")

        # Uncomment to simulate crashes
        """if self.parameters.id == 10003:
            print(f"Simulating crash...")
            #self.socket.shutdown(2)
            self.socket.close()
            return
        elif self.parameters.id == 10001 and self.currentRound == 2:
            print(f"Simulating crash...")
            #self.socket.shutdown(2)
            self.socket.close()
            return"""

        while True:
            try:
                pair = self.socket.recvfrom(1024)
                data = list(map(int, pair[0].decode().split(',')))
                self.lastConnection = pair[1][1]

                print(f"Received {data} from {self.lastConnection}")

                if data[0] > self.currentRound:
                    self.currentRound = data[0]
                    self.values.setdefault(self.currentRound, set())
                    self.values.setdefault(self.currentRound + 1, self.values[self.currentRound])
                self.values[self.currentRound + 1].update(set(data[1:]))
                
                iSender = self.parameters.cluster.index(self.lastConnection)
                iSelf = self.parameters.cluster.index(self.parameters.id)

                if iSender + 1 == iSelf or (iSelf == 0 and iSender + 1 == len(self.parameters.cluster)):
                    time.sleep(1)
                    self.actSender()
                
                print(self.values)
            except socket.timeout:
                if self.lastConnection == -1: continue
                else:
                    print(f"Timed out, assuming crash")

                    if (self.lastConnection in self.parameters.cluster):
                        iExpected = (self.parameters.cluster.index(self.lastConnection) + 1) % len(self.parameters.cluster)
                        iSelf = self.parameters.cluster.index(self.parameters.id)

                        if iExpected != iSelf:
                            self.parameters.cluster.remove(self.parameters.cluster[iExpected])
                            
                        if iExpected == iSelf or iExpected + 1 == iSelf or (iSelf == 0 and iExpected + 1 == len(self.parameters.cluster)):
                            self.firstInLine = True
                            self.actSender()
                    
                    elif max(self.parameters.cluster) == self.parameters.id:
                        self.firstInLine = True
                        self.actSender()

                    else:
                        self.parameters.cluster.remove(max(self.parameters.cluster))
            except ConnectionResetError:
                pass
            
    def actSender(self):
        if self.firstInLine:
            self.currentRound += 1

        if self.currentRound <= self.parameters.rounds:
            print(f"### Starting round {self.currentRound}")

            setToSend = self.values[self.currentRound].difference(self.values[self.currentRound-1])
            data = f"{str(self.currentRound)}"
            if len(setToSend) > 0:
                data = data + f",{self.setToString(setToSend)}"

            for member in self.parameters.cluster:
                if member != self.parameters.id:
                    print(f"Sending {data} to {member}...")
                    self.socket.sendto(data.encode(), (self.parameters.host, member))

            self.values.setdefault(self.currentRound, set())
            self.values.setdefault(self.currentRound + 1, self.values[self.currentRound])
            self.actListener()       
        else:
            consensus = max(self.values[max(self.values)])
            print(f"Consensus reached: {consensus}")
            quit()

    def setToString(self, input):
        return ','.join(set(map(str, input)))

p = Process()