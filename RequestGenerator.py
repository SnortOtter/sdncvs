__author__ = 'Chris'
import NetworkDevices
import CompoundSwitchSolver
import random  # for unique device addresses
import FlowFunctions
from collections import defaultdict
# routines to generate random cSwitch requests


# TODO: change accessibility and type of attribute indexes
class RequestGenerator:
    def __init__(self, maxRequests, maxMatches, maxActions):
        self.maxRequests = maxRequests
        self.maxMatches = maxMatches    # limit total matches requested
        self.maxActions = maxActions    # limit total actions requested
        self.request_list = []

    def GenerateCompositeRequest(self, requestUid):
        maxAttributesAvailable = len(FlowFunctions.FlowFunctionDict)

        matchFunctions = [value for key, value in FlowFunctions.ReqGenFunctionDict.items() if value.functionType == 'm']
        maxMatchIndex = len(matchFunctions) - 1

        actionFunctions = [value for key, value in FlowFunctions.ReqGenFunctionDict.items() if value.functionType == 'a']
        actionFunctions = [value for key, value in FlowFunctions.ReqGenFunctionDict.items() if value.functionType == 'a']
        maxActionIndex = len(actionFunctions) - 1

        name = "Request_" + str(requestUid)
        print(name)
        match_list = []
        action_list = []

        matchIndexes = random.sample(range(0, maxMatchIndex), random.randint(1, self.maxMatches)) # Assign random number of matches

        for i in matchIndexes:
            match_list.append([matchFunctions[i], random.randint(0, 4)])  # For now, assigns attribute a random number. TODO: why?

        actionIndexes = random.sample(range(0, maxActionIndex), random.randint(1, self.maxMatches))

        for i in actionIndexes: # Same for actions
            action_list.append([actionFunctions[i], random.randint(0, 4)])

        input_format = NetworkDevices.Transport_Format(random.randint(0, len(FlowFunctions.Transport_Format) - 2)) # random transport formats , TODO: parameterise e.g. all-optical networks
        output_format = NetworkDevices.Transport_Format(random.randint(0, len(FlowFunctions.Transport_Format) - 2))
        request = CompoundSwitchSolver.VirtualPortRequest(name, match_list, action_list, input_format, output_format)
        print("Test input: " + str(input_format) + ",", "Test output: " + str(output_format))
        return request

    def GeneratePhysicalRequests(self, cSwitchSolutions):
        print('Not implemented')
       # TODO: iterate solutions and get solutions sets to implement


# Instantiate lots of devices
class DeviceGenerator:  # Add other types of devices
    def __init__(self, maxADVA, maxAmplifier, maxEthSwitch, maxOCS, maxOPS, maxWSS):
        self.maxADVA = maxADVA
        self.advas = []
        self.maxAmplifier = maxAmplifier
        self.amplifiers = []
        self.maxEthSwitch = maxEthSwitch
        self.ethSwitches = []
        self.maxOCS = maxOCS
        self.ocss = []
        self.maxOPS = maxOPS
        self.opss = []
        self.maxWSS = maxWSS
        self.wsss = []
        self.newDevices = []
        # TODO: ensure that addresses aren't repeated using a hashtable
        # Let's initialise some devices. Use rand library to ensure unique addresses we don't need to worry about
        self.addressList = random.sample(range(100, 1000000), 500)    # reserve 0-99 for manual instantiations
        

    def GenerateDevices(self):
        for i in range(self.maxADVA):
            name = "ADVA_" + str(i)
            newDeviceInstance = NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceADVA, name, self.addressList.pop())
            self.advas.append(newDeviceInstance)

        for i in range(self.maxAmplifier):
            name = "amp_" + str(i)
            newDeviceInstance = NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceAmplifier, name, self.addressList.pop())
            self.amplifiers.append(newDeviceInstance)

        for i in range(self.maxEthSwitch):
            name = "ethSwitch_" + str(i)
            newDeviceInstance = NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceEth8, name, self.addressList.pop())
            self.ethSwitches.append(newDeviceInstance)

        for i in range(self.maxOCS):
            name = "OCS_" + str(i)
            newDeviceInstance = NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceOCS, name, self.addressList.pop())
            self.ocss.append(newDeviceInstance)

        for i in range(self.maxOPS):
            name = "OPS_" + str(i)
            newDeviceInstance = NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceOPS, name, self.addressList.pop())
            self.opss.append(newDeviceInstance)

        for i in range(self.maxWSS):
            name = "WSS_" + str(i)
            newDeviceInstance = NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceWSS, name, self.addressList.pop())
            self.wsss.append(newDeviceInstance)

        newDevices = self.advas + self.amplifiers + self.ethSwitches + self.ocss + self.opss + self.wsss
        return newDevices
    
    
    def GenerateNics(self):  # Inventory of NICs
        # TODO: reimplemnt as auto-generating
        nicList=[]
        nicList.append(NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceNIC_eo, "eo_nic_0", self.addressList.pop()))
        nicList.append(NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceNIC_ew, "ew_nic_0", self.addressList.pop()))
        nicList.append(NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceNIC_oe, "oe_nic_0", self.addressList.pop()))
        nicList.append(NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceNIC_ow, "ow_nic_0", self.addressList.pop()))
        nicList.append(NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceNIC_we, "we_nic_0", self.addressList.pop()))
        nicList.append(NetworkDevices.NetworkDeviceInstance(NetworkDevices.deviceNIC_wo, "wo_nic_0", self.addressList.pop()))
        return nicList




