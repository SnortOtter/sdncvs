__author__ = 'cscrj'

import copy
from collections import defaultdict
import collections
import FlowFunctions


# Port request class
# matchPairs and actionPairs are dictionaries of form {[attribute type],[attribute value]}
# TODO: add input and output transport format for port
class VirtualPortRequest:
    def __init__(self, nameString, matchPairs, actionPairs, inputFormat, outputFormat):
        self.name = nameString
        self.Matches = {}
        self.Actions = {}
        self.flowFunctions={}
        self.InputTransport = inputFormat
        self.OutputTransport = outputFormat

        for pair in matchPairs:  # build dictionary of attribute types and attribute values
            self.Matches[pair[0]] = pair[1]
            self.flowFunctions[pair[0]]= pair[1]

        for pair in actionPairs:
            self.Actions[pair[0]] = pair[1]
            self.flowFunctions[pair[0]] = pair[1]

        self.matchWord = FlowFunctions.MakeWord([func.name for func in self.Matches.keys()])  # Obtain word representing the match attributes
        self.actionWord = FlowFunctions.MakeWord([func.name for func in self.Actions.keys()])
        self.matchActionWord = hex(self.matchWord) + hex(self.actionWord)[2:]


    # Check if a supplied solution set of switches covers our complete request. Check either match or action
    # return empty list if all is well!
    def MissingAttributes(self, Z):
        reqAttributes = list(self.Matches.keys()) + list(self.Actions.keys())
        reqAttributes = [func.name for func in reqAttributes]
        zAttributesAll = [device.deviceType.FlowFunctions for device in Z]  # get the flow function type and not the value for each device

        zAttributes = [item.name for subList in zAttributesAll for item in subList]  # decompose list of lists into one list
        return set(reqAttributes).difference(zAttributes)  # return difference i.e. the functions not solved for by Z

    def Print(self):
        print("Port Request\n")
        print("Match functions: ")
        for k, v in self.Matches.items():
            print(k.name, " ")
        print("\n")
        print("Action functions: ")
        for k, v in self.Actions.items():
            print(k.name, " ")
        print("\n")

# compound switch record
class CompoundSwitch():
    def __init__(self, matches, actions, Z,  matchWord, actionWord):
        self.matchDict = matches
        self.actionDict = actions
        self.searchResultZ = Z
        self.matchWord = matchWord
        self.actionWord = actionWord


# Hold data on established compound switches
class CompoundSwitchStore():
    def __init__(self):
        self.matchMap = defaultdict(list)  # match attribute list -> compound switch
        self.actionMap = defaultdict(list)  # action attribute list -> compound switch
        self.matchActionMap = defaultdict(list)  # match attribute list + action attribute list -> compound switch
        self.activeSwitches = []

    def CheckActionWord(self, checkWord):
        return self.actionMap[checkWord]

    def CheckMatchWord(self, checkWord):
        return self.matchMap[checkWord]

    def CheckCombinedWord(self, checkWord):
        return self.matchActionMap[checkWord]

    # Add a new compound switch to the relative hashmaps
    def AddSwitch(self, cSwitch, actionWord, matchWord):

        # calculate match-action key, add device to list of devices at that key
        matchActionKey = hex(matchWord) + hex(actionWord)[2:]
        self.matchActionMap[matchActionKey].append(cSwitch)

        # add to match map
        self.matchMap[matchWord].append(cSwitch)

        # add to action map
        self.actionMap[actionWord].append(cSwitch)

        # add to temporary store of active switches
        self.activeSwitches.append(cSwitch)

    # Remove an existing compound switch from the maps
    def RemoveSwitch(self, device, actionWord, matchWord):
        # remove from action map
        switches = self.actionMap[actionWord]
        switches = [x for x in switches if x != device]
        self.actionMap[actionWord] = switches

        # remove from match map
        switches = self.matchMap[matchWord]
        switches = [x for x in switches if x != device]
        self.matchMap[matchWord] = switches

        # remove from match-action map
        matchActionKey = hex(matchWord) + hex(actionWord)[2:]
        switches = self.matchActionMap[matchActionKey]
        switches = [x for x in switches if x != device]
        self.matchActionMap[matchActionKey] = switches

        # remove from active directory
        switches = [x for x in self.activeSwitches if x != device]
        self.activeSwitches = switches

    # Check a request against compound switch inventory using attribute types to see if we can avoid executing a search
    # Return a tuple: {hit type, set of devices fulfilling hit}
    def ServeRequest(self, portRequest):

        # First check to see if we can retrieve a solution set from the existing composite switch store
        # We only really need to do these one at a time, but the look-up should be quick
        tryAM = self.CheckCombinedWord(portRequest.matchActionWord)

        if len(tryAM) is not 0:
            z = tryAM[0].searchResultZ  # currently we're returning the first element only, but multiple cswitches may be able to solve the request
            zType = 'am'

        else:  # No hits, we'll have to
            z = None
            zType = ''

        return zType, z


def FormatInterfaceKey(input, output):  # For adding NICS
    return str(input) + " -> " + str(output)


# TODO : refactor so that device directories are not embedded in the solver

# Use this as a directory of network devices, also implements our compound switch solution algorithm
class CompoundSwitchSolver():
    def __init__(self):
        self.deviceDirectory = []
        self.deviceDirectoryByType = defaultdict(list)
        self.maxFunctionCardinality = 0  # store the maximum cardinality so we can iterate down from it in main search loop
        self.mapByFlowFunction = defaultdict(list)
        self.mapByFunctionCardinality = defaultdict(list)
        self.z = collections.deque()
        self.addressLookup = {}
        self.interfaceDirectory = defaultdict(list)  # keyed by interface type e.g. "eo"

    def AddInterfaceDevice(self, device):
        key = FormatInterfaceKey(device.deviceType.inputMedium, device.deviceType.outputMedium)
        self.interfaceDirectory[key].append(device)

    # return list of suitable nics
    def GetTransportInterfaceDeviceList(self, inputFormat, outputFormat):
        interfaceNeeded = FormatInterfaceKey(inputFormat, outputFormat)
        return self.interfaceDirectory.get(interfaceNeeded, None)

    def GetFreeNic(self, nicList):
        for nic in nicList:
            if nic.availableInputs > 0 and nic.availableOutputs > 0:
                return nic
            else:
                return None

    # TODO : RemoveDevice() ?

    # device is of class NetworkDevice, defined above
    # N.B. : Devices are mutable!!
    def AddDevice(self, device):
        self.deviceDirectory.append(device) # record device in list
        self.deviceDirectoryByType[device.deviceType].append(device)    # record in type-keyed dictionary
        self.addressLookup[device.address] = device

    # return a set of devices that can fulfil a request, portRequest is type VirtualPortRequest
    # Copy the device before adding to maps, as we will strip attributes during the search
    def BuildSolutionMaps(self, portRequest):
        self.z = collections.deque()
        self.maxFunctionCardinality = 0  # RESET
        self.mapByFlowFunction = defaultdict(list)  # reset
        self.mapByFunctionCardinality=defaultdict(list)

        # Lets create copies of our match and action hashmaps and remove irrelevant attributes for this request
        reqMatches = [f.name for f in list(portRequest.flowFunctions.keys())]   # convert to name string for search

        # Lets build the cardinality hashmap and make a copy of the attribute map
        # The map now contains only the attributes requested and therefore only point to useful devices
        # We need to construct the cardinality map now
        for device in self.deviceDirectory:
            # count intersection & add to cardinality maps
            # if added to cardinality[0] the device goes unused
            deviceCopy = copy.deepcopy(device)
            commonFlowFunctions = set(reqMatches).intersection([f.name for f in device.deviceType.FlowFunctions])

            deviceCopy.solverFlowFunctions = commonFlowFunctions  # discard unnecessary attributes for search
            self.mapByFunctionCardinality[len(commonFlowFunctions)].append(deviceCopy)

            if len(commonFlowFunctions) > self.maxFunctionCardinality:
                self.maxFunctionCardinality = len(commonFlowFunctions)  # we need the max to iterate down from later

            for f in commonFlowFunctions:  # build map by (common) attribute
                self.mapByFlowFunction[f].append(deviceCopy)

    # utilises maps constructed by BuildSolutionMaps
    def GetSolutionSet(self, portRequest):

        mapCardinality = self.mapByFunctionCardinality
        mapAttributes = self.mapByFlowFunction
        maxCardinality = self.maxFunctionCardinality

        mapAttributes = copy.deepcopy(
            self.mapByFlowFunction)  # create full copy as we will manipulate the underlying device objects during the search

        for l in range(maxCardinality, 0, -1):  # loop from max useful attributes to 1 useful attribute (0 useless...)
            if l in list(mapCardinality.keys()) and len(mapCardinality[l]) > 0:  # test key

                while len(mapCardinality[l]) > 0:
                    selectedDevice = mapCardinality[l].pop()
                    self.z.appendleft(selectedDevice)

                    for attrib in selectedDevice.solverFlowFunctions:  # for all attributes of s_0
                        for otherDevice in mapAttributes[attrib]:  # for all other devices
                            if otherDevice is not selectedDevice:
                                m = len(otherDevice.solverFlowFunctions)  # get cardinality of device atts
                                mapCardinality[m] = [x for x in mapCardinality[m] if x.label != otherDevice.label]  # remove from cardinality map
                                mapAttributes[attrib] = [x for x in mapAttributes[attrib] if x.label != otherDevice.label]  # remove device from that attribute element in the map
                                otherDevice.RemoveAttribute(attrib)  # remove attribute from device
                                m = m - 1
                                mapCardinality[m].append(otherDevice)  # add device to new location in cardinality map

        return self.z
