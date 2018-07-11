__author__ = 'cscrj'

from FlowFunctions import * # get our flow functions

# Here we will enumerate the types of devices
# represents a single physical instance of a device type
class NetworkDeviceInstance():
    def __init__(self, deviceType, label, address):
        self.deviceTypeName = deviceType.type
        self.deviceType = deviceType
        self.label = label
        self.address = address
        self.flowTable = []    # Not sure how to init. this currently
        self.solverMatchAttributes = self.deviceType.matchFunctions    # These are MUTABLE! use the underlying devicetype to get an immutable list
        self.solverActionAttributes = self.deviceType.actionFunctions
        self.solverFlowFunctions = self.solverMatchAttributes + self.solverMatchAttributes

        #  Some devices do not have duplex ports
        #  These will behave differently when we attempt port allocation
        if self.deviceType.duplexPorts is True:
            self.Duplex = True
            self.availableDuplexPorts = self.deviceType.countDuplexPort
            self.duplexPortConnections = [None] * self.deviceType.countDuplexPort
        else:
            self.Duplex = False
            self.availableInputs = self.deviceType.countInputPort         # count of input ports
            self.availableOutputs = self.deviceType.countOutputPort       # count of output ports
            self.inputPortConnections = [None] * self.availableInputs     # create connection records - will have address of backplane connected device
            self.outputPortConnections = [None] * self.availableOutputs

    def InputTransport(self):
        return self.deviceType.inputMedium

    def OutputTransport(self):
        return self.deviceType.outputMedium

    def solverAttributes(self, attType):
        if attType is 'match':
            return self.solverMatchAttributes
        elif attType is 'action':
            return self.solverActionAttributes

    def RemoveAttribute(self, attribute):
        self.solverFlowFunctions = [f for f in self.solverFlowFunctions if f is not attribute]

    # These port methods vary depending on whether the devices ports are duplex

    # methods to store pointer to connected devices
    def ConnectInput(self, index, connectedDevice):
        if self.Duplex is True:
            self.duplexPortConnections[index] = connectedDevice.address
            self.availableDuplexPorts -= self.availableDuplexPorts
        else:
            self.inputPortConnections[index]=connectedDevice.address
            self.availableInputs -= self.availableInputs

    def ConnectOutput(self, index, connectedDevice):
        if self.Duplex is True:
            self.duplexPortConnections[index] = connectedDevice.address
            self.availableDuplexPorts -= self.availableDuplexPorts
        else:
            self.outputPortConnections[index] = connectedDevice.address
            self.availableOutputs -= self.availableOutputs

    @property
    def NextFreeInput(self):
        if self.Duplex is True:
            i = self.duplexPortConnections.index(None) if None in self.duplexPortConnections else None
        else:
            i = self.inputPortConnections.index(None) if None in self.inputPortConnections else None
        return i

    @property
    def NextFreeOutput(self):
        if self.Duplex is True:
            i = self.duplexPortConnections.index(None) if None in self.duplexPortConnections else None
        else:
            i = self.outputPortConnections.index(None) if None in self.outputPortConnections else None
        return i



    #  port is marked differently depending on how and when it is reserved
    #  return -1 if no available port
    def ReserveInputPort(self, reserveMark):
        if self.Duplex is True:
            index = self.duplexPortConnections.index(None) if None in self.duplexPortConnections else -1
            self.duplexPortConnections[index] = reserveMark if index is not -1 else self.duplexPortConnections[index]
        else:
            index = self.inputPortConnections.index(None) if None in self.inputPortConnections else -1
            self.inputPortConnections[index] = reserveMark if index is not -1 else self.inputPortConnections[index]
        return index  # return first free input port index

    def ReserveOutputPort(self, reserveMark):
        if self.Duplex is True:
            index = self.duplexPortConnections.index(None) if None in self.duplexPortConnections else -1
            self.duplexPortConnections[index] = reserveMark if index is not -1 else self.duplexPortConnections[index]
        else:
            index = self.outputPortConnections.index(None) if None in self.outputPortConnections else -1
            self.outputPortConnections[index] = reserveMark if index is not -1 else self.outputPortConnections[index]
        return index  # return first outnput port index

    # Add a programmed flow to this device
    def NewFlow(self, matchPairs, actionPairs):
        self.flowTable[matchPairs] = actionPairs


class Backplane():
    def __init__(self, radix):
        self.radix = radix
        self.backplaneAPorts = [None] * radix
        self.backplaneAPortNode = [None] * radix
        self.backplaneBPorts = [None] * radix
        self.backplaneBPortNode = [None] * radix
        self.crossBar = [None] * radix
        self.crossBarNodes = []

    def GetFreeBackplaneA(self, device):
        if device.deviceType.duplexPorts is True:
            index = self.backplaneAPorts.index(None) if None in device.duplexPortConnections else -1
        else:
            index = self.backplaneAPorts.index(None) if None in device.outputPortConnections else -1
        return index

    def GetFreeBackplaneB(self, device):
        if device.deviceType.duplexPorts is True:
            index = self.backplaneBPorts.index(None) if None in device.duplexPortConnections else -1
        else:
            index = self.backplaneBPorts.index(None) if None in device.inputPortConnections else -1
        return index

    def ConnectBackplaneA(self, device):
        if device.deviceType.duplexPorts is True:
            halfIndex = device.deviceType.countDuplexPort // 2 + (device.deviceType.countDuplexPort % 2 > 0) # // is integer division
            for x in range(0, halfIndex):
                index = self.GetFreeBackplaneA(device)
                self.backplaneAPorts[index] = [device.label, index]
                self.backplaneAPortNode[index] = (index, device.label, 'A')
        else:
            for x in range(device.deviceType.countOutputPort):
                index = self.GetFreeBackplaneA(device)
                self.backplaneAPorts[index] = [device.label, index]
                self.backplaneAPortNode[index] = (index, device.label, 'A')

    def DisconnectBackplaneA(self, device):
        for x in self.backplaneAPorts:
            count = 0
            while count != self.radix - 1:
                if self.backplaneAPorts[count] == None:
                    return
                if x == device.label:
                    self.backplaneAPorts[count] = None
                count += 1
                self.crossBar = [None] * self.radix

    def ConnectBackplaneB(self, device):
        if device.deviceType.duplexPorts is True:
            halfIndex = device.deviceType.countDuplexPort // 2 + (device.deviceType.countDuplexPort % 2 > 0)
            for x in range(halfIndex + 1, device.deviceType.countDuplexPort + 1):
                index = self.GetFreeBackplaneB(device)
                self.backplaneBPorts[index] = [device.label, index]
                self.backplaneBPortNode[index] = (index, device.label, 'B')
        else:
            for x in range(device.deviceType.countInputPort):
                index = self.GetFreeBackplaneB(device)
                self.backplaneBPorts[index] = [device.label, index]
                self.backplaneBPortNode[index] = (index, device.label, 'B')

    def DisconnectBackplaneB(self, device):
        for x in self.backplaneBPorts:
            count = 0
            while count != self.radix - 1:
                if self.backplaneBPorts[count] is None:
                    return
                if x == device.label:
                    self.backplaneBPorts[count] = None
                count += 1
                self.crossBar = [None] * self.radix

    def AddCrossbarConnection(self, inputIndex, outputIndex):
        self.crossBar[inputIndex] = outputIndex

    def CreateCrossbarConnection(self, ADevice, BDevice): # Finds first available connection between two devices
        connectionsAvailableA = []
        for x in self.backplaneAPorts:
            if x is not None:
                if x[0] == ADevice.label and self.crossBar[x[1]] == None:
                    connectionsAvailableA.append(x[1])
        connectionsAvailableB = []
        for x in self.backplaneBPorts:
            if x is not None:
                if x[0] == BDevice.label and x[1] not in self.crossBar:
                    connectionsAvailableB.append(x[1])
        if connectionsAvailableA == [] or connectionsAvailableB == []:
            print ("Unable to connect " + ADevice.label + " to " + BDevice.label + " - insufficent ports.")
        else:
            self.AddCrossbarConnection(connectionsAvailableA[0],connectionsAvailableB[0])
            self.crossBarNodes.append([(connectionsAvailableA[0], ADevice.label, 'A'),(connectionsAvailableB[0], BDevice.label, 'B')])

    def RemoveCrossbarConnection(self, inputIndex):
        self.crossBar[inputIndex] = None


#  all network devices use this class
class NetworkDeviceType():
    def __init__(self, deviceType, isProgrammable, matchAttributes, actionAttributes, countDuplex, countInput
                 , countOutput, inputMedium, outputMedium):
        self.type = deviceType
        self.matchFunctions = matchAttributes      # map of possible match attributes
        self.actionFunctions = actionAttributes    # map of action attributes
        self.isProgrammable = isProgrammable
        self.inputMedium = inputMedium
        self.outputMedium = outputMedium
        self.FlowFunctions = self.matchFunctions + self.actionFunctions

        if countDuplex == 0:   # devices that have fixed ports
            self.countInputPort = countInput
            self.countOutputPort = countOutput
            self.duplexPorts = False
        else:
            self.countDuplexPort = countDuplex
            self.duplexPorts = True

    def Attributes(self, attType):
        if attType == 'match':
            return self.matchFunctions
        elif attType == 'action':
            return self.actionFunctions

    def RemoveAttribute(self, attType, attrib):
        if attType == 'match':
            self.matchFunctions = [x for x in self.matchFunctions if x != attrib]
        elif attType == 'action':
            self.actionFunctions = [x for x in self.actionFunctions if x != attrib]

#  Traditional ethernet switches

deviceEth8 = NetworkDeviceType('Eth8', True, [m_vlanId, m_sourceMac, m_destinationMac, m_etherType, m_port, m_destinationMac]
                               , [a_port, a_etherType,a_sourceMac, a_vlanId, a_destinationMac], 8, 0, 0, Transport_Format.Electronic, Transport_Format.Electronic)

# Optical / Passive / special devices
deviceOPS = NetworkDeviceType('OPS', True, [m_vlanId, m_sourceMac, m_destinationMac, m_port, m_opticalLabel]
                              , [a_opticalLabel, a_lambda, a_port], 0, 1, 2, Transport_Format.Optical, Transport_Format.Optical)

deviceOCS = NetworkDeviceType('OCS', True, [m_vlanId, m_sourceMac, m_destinationMac,m_port]
                              , [a_lambda], 2, 0, 0, Transport_Format.Optical, Transport_Format.Optical)

deviceADVA = NetworkDeviceType('ADVA', True, [m_lambda, m_port], [a_lambda, a_port], 2, 0, 0, Transport_Format.Optical
                               , Transport_Format.Optical)

deviceWSS = NetworkDeviceType('WSS', True, [m_centralFrequency, m_bandwidth, m_port]
                              , [a_port,a_centralFrequency, a_bandwidth], 0, 1, 1, Transport_Format.Optical, Transport_Format.Optical)

deviceAmplifier = NetworkDeviceType('Amplifier', False, [m_port]
                                    , [a_amplify,a_port], 0, 2, 2, Transport_Format.Optical, Transport_Format.Optical)

devicePolatis = NetworkDeviceType('Polatis', True, [m_port], [a_port], 0, 192, 192, Transport_Format.Optical, Transport_Format.Optical)

deviceTypes = [deviceADVA, deviceAmplifier, deviceEth8, deviceOCS, deviceOPS, deviceWSS]


# Mixed medium / interface devices
deviceNIC_eo = NetworkDeviceType('NIC', True, [m_port, m_vlanId], [a_port, a_opticalLabel]
                                 , 0, 10, 10, Transport_Format.Electronic, Transport_Format.Optical)

deviceNIC_ew = NetworkDeviceType('NIC', True, [m_port, m_vlanId], [a_port]
                                 , 0, 10, 10, Transport_Format.Electronic, Transport_Format.Wireless)

deviceNIC_oe = NetworkDeviceType('NIC', True, [m_port, m_vlanId], [a_port]
                                 , 0, 10, 10, Transport_Format.Optical, Transport_Format.Electronic)

deviceNIC_ow = NetworkDeviceType('NIC', True, [m_port, m_vlanId], [a_port]
                                 , 0, 10, 10, Transport_Format.Optical, Transport_Format.Wireless)

deviceNIC_we = NetworkDeviceType('NIC', True, [m_port, m_vlanId], [a_port]
                                 , 0, 10, 10, Transport_Format.Wireless, Transport_Format.Electronic)

deviceNIC_wo = NetworkDeviceType('NIC', True, [m_port, m_vlanId], [a_port, a_opticalLabel]
                                 , 0, 10, 10, Transport_Format.Wireless, Transport_Format.Optical)





