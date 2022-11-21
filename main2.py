import multiprocessing
from multiprocessing import Process
import time
import argparse

class Parameters():
    def __init__(self):
        argParser = argparse.ArgumentParser()
        argParser.add_argument("--port", help="Port for first process to listen to, also process identifier", required=True)
        argParser.add_argument("--amount", help="Number of processes", required=True)
        argParser.add_argument("--rounds", help="Number of rounds", required=True)
        #argParser.add_argument("--cluster", help="List of ports for all running processes in the cluster", required=True, nargs = '+')
        #argParser.add_argument("--fail", help="Whether process should crash (Y/N), default N")
        #argParser.add_argument("--proposal", help="Set value for process to try to propose", required=True)
        args = argParser.parse_args()

        self.port = int(args.port)
        self.amount = int(args.amount)
        self.rounds = int(args.rounds)

def round(arg, proposal, rounds):
    print(f"{arg} {time.time() - start}")

    #Initialization
    values = []
    values.append(set())
    values.append(set())
    values[1].add(proposal)
    
    for r in range(rounds + 1):
        print(r)

    while True:
        print(f"{arg}")
        time.sleep(1)

start = time.time()

if __name__ == '__main__':
    parameters = Parameters()
    processes = [Process(target=round, args=(f"p{port}", 42, parameters.rounds)) for port in range(parameters.port, parameters.port + parameters.amount + 1)]
    
    start = time.time()
    for p in processes:
        p.start()
        p.join()