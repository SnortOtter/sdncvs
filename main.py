# main.py
# main script for executing a composite switch experiment
# 1. Here we instantiate devices and add them to an inventory
# 2. Create requests
# 3. Solve those requests and output the results


__author__ = 'Chris Jackson - HPN & Ellen'

import sys
import getopt
import random

import CompoundSwitchSolver
import CompoundSwitchOrchestrator
import deviceProgrammer
import NetworkDevices  # abstract device representations
import RequestGenerator
import collections
from collections import defaultdict

def main():
    print('Compound Switch Experiments v0.1')


# get interface name or correct script usage. Help option too
try:
    opts, args = getopt.getopt(sys.argv[1:], 'c:', ["controller="])
except getopt.GetoptError:
    print('nicControl.py -c <controller IP>')
    sys.exit(2)

for opt, arg in opts:  # processes arguments passed when the script is run
    if opt == '-h' or opt == '-help':
        print('python main.py')
        sys.exit()
    elif opt in ("-c", "-controller"):
        controllerAddress = arg
        print('Controller @ IP: "', controllerAddress)
    else:
        print('Unrecognised parameters, usage is: main.py')
        sys.exit()

# init objects to perform the device search, store/retrieve topology data, store/retrieve comp
topologyMap = deviceProgrammer.Topology()  # holds edges and lets us get info on them
simulatedController = deviceProgrammer.SdnControllerModel(0)  # simulate programming of flows to sdnC, set to address 0
cSwitchInventory = CompoundSwitchSolver.CompoundSwitchStore()

# now initialise a cSwitch store and request solver
solutions = CompoundSwitchSolver.CompoundSwitchStore()
solver = CompoundSwitchSolver.CompoundSwitchSolver()

# Create test devices
dev_generator = RequestGenerator.DeviceGenerator(5, 5, 5, 5, 5, 5)
networkDevices = dev_generator.GenerateDevices()
nicDevices = dev_generator.GenerateNics()

# physical / whole device reservation data
physicalDeviceReg = {}

for dev in networkDevices:
    solver.AddDevice(dev)
    physicalDeviceReg[dev] = 0  # mark unused

for nic in nicDevices:
    solver.AddInterfaceDevice(nic)
    physicalDeviceReg[nic]=0

backplane = NetworkDevices.Backplane(192)   # instantiate backplane

# TODO : connect all devices to backplane
# TODO: add backplane to solver


topologyManager = deviceProgrammer.VirtualPortDeviceConnector(topologyMap, simulatedController,solver)  # TODO: we need to refactor the inventory out of solver ASAP

# create  cSwitch request generator
req_generator = RequestGenerator.RequestGenerator(4, 4, 4)
solutionSwitchesConstructed = defaultdict(list)
solutionSwitchesDestructed = defaultdict(list)

# solve cSwitches / run with some requests to remove cSwitches too
createPerTick = 0.02
destroyPerTick = 0.012
switchLifeTime = 300    # maximum lifetime of a cSwitch / physical request
createdAtTick = defaultdict(list)      # record creation time
destroyedAtTick = defaultdict(list)

maxTicks = 500
requestTotal=0
accepts = [0] * maxTicks    # found and routed a solution
rejects = [0] * maxTicks    # found a solution, could not route - insufficent resources
fails = [0] * maxTicks      # no solutions found - shouldn't happen with valid requests


# TODO: if there is insufficient capacity in a given network device instance, search other instances

# TODO: seperate dictionaries for matches and actions, or have a network function class dictionary

# 1. cSwitch run
for tick in range(0, maxTicks):
    requestsThisTick = int(random.uniform(0, 100) * createPerTick)

    # destroy any timed out ports
    # remove from inventory
    # disconnect ports
    # remove backplane cross-connection

    removesThisTick = int(random.uniform(0,100) * destroyPerTick)

    for rem in range(0,removesThisTick-1):
        cSwitch = random.choice(cSwitchInventory.activeSwitches)    # choose a random cSwitch that is currently active
        # TODO: disconnect each component device's ports
        cSwitchInventory.RemoveSwitch(cSwitch, cSwitch.matchWord, cSwitch.actionWord) # remove it from active
        solutionSwitchesDestructed[tick].append(cSwitch)

    # add new ports
    for newR in range(0,int(requestsThisTick)):
        requestTotal += 1
        req = req_generator.GenerateCompositeRequest(requestTotal)   # generate random requests for composite port, use current total as uid
        req.Print()
        cPort = CompoundSwitchOrchestrator.ProcessRequest(cSwitchInventory,solver, req)

        if cPort is not None:   # check we found solution devices
            completeZ = cPort.searchResultZ
            orderedPort = deviceProgrammer.TransportOrder(solver, completeZ, req.InputTransport, req.OutputTransport)  # get reordered solution for minimal NIC usage

            print('Complete transport-interfaced solution:')
            if orderedPort is not None:
                for d in orderedPort:
                    print(d.label)


                canRoute = topologyManager.BuildPort(orderedPort, req) # wire up the ports via backplane
                solutionSwitchesConstructed[tick].append(cPort)  # store time

                if canRoute:
                    accepts[tick] += 1
                    print('Solved and Routed request')
                else:
                    print('Solved request but insufficient capacity')
                    rejects[tick] += 1
            else:
                print('Solved request but insufficient NIC capacity')
                rejects[tick] += 1

        else:   # reject request
            fails[tick] += 1
            print('Error, failed to return cPort solution!: Fail')



# 2. physical reservation run
# p_accepts=[0] * maxTicks
# p_rejects=[0] * maxTicks
#
# for tick in range(0, maxTicks):
#     buildReqs = createdAtTick[tick]
#     removeReqs = destroyedAtTick[tick]
#
#    for rm in removeReqs:
#     # unreserve devices in request
#
#
#     for req in buildReqs:
#     # attempt to reserve devices
#     # if reserve all, success else reject
#


# TODO: draw graphs
#backplane_drawer = deviceProgrammer.BackplaneGraphDrawer()
#backplane_drawer.GenerateGraph(backplane, 'screen')