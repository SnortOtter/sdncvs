__author__ = 'cscrj'

# This script contains a class that accepts the solutions set and the virtual port request and provide
# an abstract representation of the flows that must be programmed.
import copy
from collections import defaultdict
import collections
import NetworkDevices  # contains device representations
from NetworkDevices import Transport_Format
import CompoundSwitchSolver  # contains request representation
import networkx as nx # to draw graphs
from networkx.algorithms import bipartite
import matplotlib.pyplot as plt
from collections import namedtuple
from collections import deque


# connects the devices selected to build a virtual port
# if device doesn't have capacity attempts to find an identically typed device before rejecting due to lack of capacity
class VirtualPortDeviceConnector():
    def __init__(self, topology, sdnProgrammer, solver):
        self.topologyMap = topology
        self.controller = sdnProgrammer
        self.directory = solver

    # connects devices by obtaining unused ports and connecting these to the backplane
    # if there isn't an available port return -1
    def BuildPort(self, solutionSetZ, portRequest):
        solutionSet = copy.deepcopy(solutionSetZ)
        devicePortCapacity = True

        # before we loop, we need to reserve an input on the first device that isn't connected to anything
        s_entry = solutionSet.pop()  # deque the first switch in the solution set

        if s_entry.NextFreeInput is None:
            devicePortCapacity = False
            otherDevices = self.directory.deviceDirectoryByType[s_entry.deviceType] # get other instances of device types
            alt_device = next((x for x in otherDevices if x.NextFreeInput), None) # get one with free capacity if possible
            if alt_device is not None:
                s_entry = alt_device
                devicePortCapacity = True

        inPortNext = s_entry.NextFreeInput
        s_entry.ReserveInputPort(portRequest.name)
        solutionSet.append(s_entry)     # goes back on the device stack to be connected to rest of devices below

        programFlowList = []

        # check all devices have capacity
        # if we loop successfully then form connections
        while len(solutionSet) > 0 and devicePortCapacity is True:  # must have capacity for each device

            s_0 = solutionSet.pop()
            inPort = inPortNext

            if len(solutionSet) == 0:
                outPort = s_0.ReserveOutputPort(portRequest.name)
            else:
                s_1 = solutionSet.pop()
                solutionSet.append(s_1) # want to refer to s_1 in place

                if s_0.NextFreeOutput is None:
                    devicePortCapacity = False
                    otherDevices = self.directory.deviceDirectoryByType[s_0.deviceType] # get other instances of device types
                    alt_device = next((x for x in otherDevices if x.NextFreeOutput), None) # get one with free capacity if possible

                    if alt_device is not None:              # set alternative device
                        for index, item in solutionSetZ:    # modify solution
                            if item == s_0:
                                solutionSetZ[index] = alt_device
                        s_0 = alt_device
                        devicePortCapacity = True

                outPort = s_0.NextFreeOutput

                if s_1.NextFreeInput is None:
                    devicePortCapacity = False
                    otherDevices = self.directory.deviceDirectoryByType[s_1.deviceType] # get other instances of device types
                    alt_device = next((x for x in otherDevices if x.NextFreeInput), None) # get one with free capacity if possible

                    if alt_device is not None:
                        for index, item in solutionSetZ:    # modify solution
                            if item == s_1:
                                solutionSetZ[index] = alt_device
                        s_1 = alt_device
                        devicePortCapacity = True

                inPortNext = s_1.NextFreeInput

                # create channel and add to topology map
                if devicePortCapacity:
                    chan = Channel(s_0.Duplex and s_1.Duplex, s_0, s_1, outPort, inPortNext)
                    #chanList.append(chan)   # store channel to add later
                    #self.topologyMap.AddEdge(chan)
                    #self.controller.ProgramDevice(s_0, inPort, outPort, portRequest)
                    FlowData = namedtuple('FlowData', 's_0 s_1 inPort outPort inPortNext req channel')
                    programFlowList.append(FlowData(s_0, s_1, inPort, outPort, inPortNext, portRequest, chan)) # store tuple for program device call later

                # we may have changed the device

        if devicePortCapacity:  # true on exit while if all devices had capacity
            for x in programFlowList:
                x.s_0.ReserveOutputPort(x.req.name)
                x.s_1.ReserveInputPort(x.req.name)
                self.topologyMap.AddEdge(x.channel)  # record the edge
                self.controller.ProgramDevice(x.s_0, x.inPort, x.outPort, x.req) # program the flow
            return True
        else:
            return False


    def DeletePort(self,cPort):
        # TODO : mark ports as unused
        print('Not implemented!')


# simple topology map for storing/checking edge connections via backplane
class Channel():
    def __init__(self, isDuplex, sourceDevice, destinationDevice, outputPortIndex, inputPortIndex):
        self.sourceDevice = sourceDevice
        self.destinationDevice = destinationDevice
        self.outputPortIndex = outputPortIndex
        self.inputPortIndex = inputPortIndex
        self.isDuplex = isDuplex  # both devices must have a duplex port

    def Reverse(self):
        temp = self.destinationDevice
        self.destinationDevice = self.sourceDevice
        self.sourceDevice = temp


class Topology():
    def __init__(self):
        self.edges = defaultdict(list)  # key is source, list has destinations

    def AddEdge(self, channel):
        self.edges[channel.sourceDevice.address].append(channel)

        if channel.sourceDevice.Duplex is True and channel.destinationDevice.Duplex is True:  # duplex mirror edge
            revChannel = channel
            revChannel.Reverse()
            self.edges[channel.destinationDevice].append(revChannel)

    def RemoveEdge(self, sourceDevice, destinationDevice):
        self.edges[sourceDevice.address].remove(destinationDevice.address)

        if sourceDevice.isDuplex is True and destinationDevice.isDuplex is True:  # duplex mirror edge
            self.edges[destinationDevice.address].remove(sourceDevice.address)

    def IsConnected(self, sourceDevice, destinationDevice):  # ascertains if two devices are connected
        connectedChannels = self.edges[sourceDevice.address]
        connectedDevices = [channel.destinationDeviceAddress for channel in connectedChannels]
        return destinationDevice.address in connectedDevices

    def GetChannelIndexes(self, sourceDevice, destinationDevice):  # get port indexes for the devices either end of channel
        sourceChannels = self.edges[sourceDevice.address]
        requestedChannel = next(k for k in sourceChannels if k.destinationDevice.address == destinationDevice.address)
        return requestedChannel.inputPortIndex, requestedChannel.outputPortIndex


# Will eventually CURL to the REST FlowProgrammer Interface or equivalent,
class SdnControllerModel():
    def __init__(self, address):
        self.address = address

    def ProgramDevice(self, device, inputPort, outputPort, portRequest):
        print ('\n', 'Programming device: ', device.label, ' of type ', device.deviceTypeName, ' @ address: ', device.address)

        # device to be programmed with solutionAttributes
        deviceMatches = device.solverMatchAttributes
        deviceActions = device.solverActionAttributes

        matches = [k for k in portRequest.Matches.keys()]
        matches = list(set(matches).intersection(deviceMatches))
        actions = [k for k in portRequest.Actions.keys()]
        actions = list(set(actions).intersection(deviceActions))

        print ("Input port: ", inputPort)
        for m in matches:
            print ('match attribute:', m, 'value: ', portRequest.Matches[m])
        for a in actions:
            print ('action attribute:', a, ' value: ', portRequest.Actions[a])
        print ("Output port: ", outputPort)


class Node:
    def __init__(self, nodeId, nodeType):
        self.id = nodeId
        self.type = nodeType


class Edge:
    def __init__(self, startNode, endNode, edgeType):
        self.source = startNode
        self.sink = endNode
        self.type = edgeType


class GraphDrawer():
    def __init__(self):
        self.typeColour = {0: 'blue',  # Electronic
                           1: 'green',  # Optical
                           'Electro-optical': 'yellow',
                           #2: '',
                           #3: '',
                           4: 'red'  # Composite
                           }
        self.realNodes = {i: self.typeColour[i] for i in self.typeColour if i != 4}
        self.edgeColours = {'Real': 'black',
                            'Virtual': 'red'
                            }
        self.realEdges = {'Real': 'black'
                          }
        self.graph = nx.Graph()
        self.nodeDict = {}
        self.edgeDict = {}

    def AddNode(self, node):
        self.nodeDict[node.id] = node
        self.graph.add_node(node.id)

    def AddEdge(self, edge):
        self.edgeDict[edge.source, edge.sink] = edge
        self.graph.add_edge(edge.source, edge.sink)

    def GenerateGraph(self, mode, show_or_save):
        pos = nx.spring_layout(self.graph)
        if mode == 'virtual': # includes composite switch & edges
            for dev_type, colour in self.typeColour.iteritems():
                typeNodes = [x.id for x in self.nodeDict.values() if x.type == dev_type]
                nx.draw_networkx_nodes(self.graph, pos, nodelist=typeNodes, node_color=colour)
            for edg_type, colour in self.edgeColours.iteritems():
                typeEdges = [(x.source, x.sink) for x in self.edgeDict.values() if x.type == edg_type]
                nx.draw_networkx_edges(self.graph, pos, edgelist=typeEdges, edge_color=colour)
            nx.draw_networkx_labels(self.graph, pos)
        elif mode == 'physical':
            for dev_type, colour in self.realNodes.iteritems():
                typeNodes = [x.id for x in self.nodeDict.values() if x.type == dev_type]
                nx.draw_networkx_nodes(self.graph, pos, nodelist=typeNodes, node_color=colour)
            label = [(x.id, x.id) for x in self.nodeDict.values() if x.type != 4]
            labels = dict(label)
            nx.draw_networkx_labels(self.graph, pos, labels)
            for edg_type, colour in self.realEdges.iteritems():
                typeEdges = [(x.source, x.sink) for x in self.edgeDict.values() if x.type == edg_type]
                nx.draw_networkx_edges(self.graph, pos, edgelist=typeEdges, edge_color=colour)
        plt.axis('off')
        if show_or_save == 'show':
            plt.show(self.graph)
        else:
            file_name = raw_input("Enter file name: ") + ".png"
            plt.savefig(file_name)
        plt.clf()


class BackplaneGraphDrawer():
    def __init__(self):
        self.b = nx.Graph()

    def GenerateGraph(self, backplane, display_or_save):
        backplane.backplaneAPortNode = [x for x in backplane.backplaneAPortNode if x != None]
        backplane.backplaneBPortNode = [x for x in backplane.backplaneBPortNode if x != None]
        backplane.crossBar = [x for x in backplane.crossBar if x != None]
        self.b.add_nodes_from(backplane.backplaneAPortNode, bipartite=0)
        self.b.add_nodes_from(backplane.backplaneBPortNode, bipartite=1)
        self.b.add_edges_from(backplane.crossBarNodes)
        X = set(n for n, d in self.b.nodes(data=True) if d['bipartite']==0)
        Y = set(n for n, d in self.b.nodes(data=True) if d['bipartite']==1)
        nx.is_connected(self.b)
        pos = dict()
        for x in X:
            pos[x] = (1, x[0])
        for y in Y:
            pos[y] = (2, y[0])
        nx.draw(self.b, pos=pos)
        if display_or_save == 'display':
            plt.show(self.b)
        else:
            file_name_2 = raw_input("Enter file name: ") + ".png"
            plt.savefig(file_name_2)


transport_formats_solver = {'Electronic': 0,
                            'Optical': 1,
                            'Wireless': 2
                            }


# TODO: reimplement to reorder middle devices if insufficient NIC availability

def TransportOrder(solver, solutionSetZ, t_i, t_o):
    transportGroups = defaultdict(list)
    outputDevices = []   # we will add devices to both ends
    haveInputDevice = False
    haveOutputDevice = False

    # group by transport (input = output, interface devices are added after ordering
    for device in solutionSetZ:
        transportGroups[device.deviceType.inputMedium].append(device)   # store devices by transport format

    # check if a group matches the input format
    if t_i in transportGroups:
        haveInputDevice = True
        for d in transportGroups[t_i]:
            outputDevices.append(d)

    # Add the groups between the entry and egress groups
    # but do not add a group with egress format yet
    for key, val in transportGroups.items():
        if key != t_o and key != t_i:
            for d in val:   # list of devices
                outputDevices.append(d)

    # add the group matching the output format last
    if t_o in transportGroups and t_o != t_i: # last clause prevents partition being used twice
        haveOutputDevice = True
        for d in transportGroups[t_o]:
            outputDevices.append(d)

    # now add all groups to outputDevices, adding their transport formats to an dequeue in the same order
    if not haveInputDevice:
        nics = solver.GetTransportInterfaceDeviceList(t_i, outputDevices[0].deviceType.inputMedium) # get nics for t_i->z[0]
        if nics is not None:
            nic = solver.GetFreeNic(nics)

            if nic is not None:
                outputDevices.insert(0,nic)
            else:
                print("Insufficient NICs to complete port solution")
                return None
        else:
            print("No suitable  NICs present to complete port solution")
            return None

    # interface all the devices
    for i in range(0, len(outputDevices)-1):    # perform check on all elements except the last
        nic = None
        if outputDevices[i].deviceType.outputMedium != outputDevices[i+1].deviceType.inputMedium:
            nics = solver.GetTransportInterfaceDeviceList(outputDevices[i].deviceType.outputMedium, outputDevices[i + 1].deviceType.inputMedium)
            if nics is not None:
                nic = solver.GetFreeNic(nics)

            if nic is not None:
                outputDevices.insert(i+1, nic)
            else:
                print("Insufficient NICs to complete port solution")
                return None

    # lastly, let's ensure the egress device outputs to transport format t_o
    if not haveOutputDevice:
        nics = solver.GetTransportInterfaceDeviceList(outputDevices[len(outputDevices) - 1].deviceType.outputMedium, t_o) # get nics for z[last]->t_o
        if nics is not None:
            nic = solver.GetFreeNic(nics)

        if nic is not None:
            outputDevices.append(nic)
            return outputDevices
        else:
            print("Insufficient NICs to complete port solution")
            return None;

    return outputDevices


