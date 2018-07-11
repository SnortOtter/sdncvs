# CompoundSwitchOrchestrator.py
# Functions that marshal the classes in the cswitch libraries to solve requests

__author__ = 'Chris'

import CompoundSwitchSolver
import deviceProgrammer
import NetworkDevices
import collections


# TODO: We need to react to insufficient free ports. Best way is to remove a device from the inventory when full
# Function to take a port request, device inventory and cover solver to return switch
# and add to the inventory
def ProcessRequest(inventory, cSwitchSolver, portRequest):

    # devices from the inventory when they have no more free inputs, outputs or 2 duplex ports
    # Attempt a look-up in the existing composite switch store
    req_0_devices = collections.deque()
    hitType, hitZ = inventory.ServeRequest(portRequest)

    if hitType is 'am':  # this is messy, couldn't easily locate a nicer way
        req_0_devices = hitZ
        print('Located existing MATCH+ACTION solution')

    # Build hash-tables for search & execute, but only if we haven't found an existing solution
    solved = False
    if len(req_0_devices) ==0:
        cSwitchSolver.BuildSolutionMaps(portRequest)
        req_0_devices = cSwitchSolver.GetSolutionSet(portRequest)

    missingAttributes = portRequest.MissingAttributes(req_0_devices)

    if len(missingAttributes) != 0:
        print('Failed to solve match devices for requested cSwitch: ', portRequest.name)

    else:
        print('Found devices to cover all requested functions:')
        print([name.label for name in req_0_devices])
        solved = True

    if solved:
        lReq0 = [k for k in req_0_devices]

        print ('\n', "Solution set Z")
        print ('===========')
        print( [name.label for name in lReq0], '\n')

        # record cSwitch
        matchWord = NetworkDevices.MakeWord([j.name for j in portRequest.Matches.keys()])  # construct match word from list of match attributes
        actionWord = NetworkDevices.MakeWord([j.name for j in portRequest.Actions.keys()])
        cSwitch0 = CompoundSwitchSolver.CompoundSwitch(portRequest.Matches, portRequest.Actions, req_0_devices, matchWord, actionWord)
        inventory.AddSwitch(cSwitch0, cSwitch0.actionWord, cSwitch0.matchWord)   # add to inventory

    else:
        print ('FAILURE : Unable to solve port request', '\n')
        cSwitch0 = None

    return cSwitch0


# TODO: Finish implementation of this function
# Having solved the portRequest and produced the deviceList, program those devices to implement the request


def ProgramDevices(deviceList, portRequest,topologyMap,controller):

    deviceConnector = deviceProgrammer.VirtualPortBuilder(topologyMap, controller)     # builds compound switch
    deviceConnector.BuildPortConnections(deviceList, portRequest)

