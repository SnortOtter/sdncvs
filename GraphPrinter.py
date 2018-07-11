__author__ = 'Ellen'

# routines to visualise:
# 1. the network and all flows, backplane invisible
# 2. the internal backplane connections
# 3. the abstract network with cSwitches, hiding any flows used to implement a cSwitch

import deviceProgrammer
from main import topologyMap
from main import solver

drawer = deviceProgrammer.GraphDrawer()
backplane_drawer = deviceProgrammer.BackplaneGraphDrawer()

print ('\n', 'Graph has edges : ')

for k in topologyMap.edges.keys():
    sourceDevice = solver.addressLookup[k]
    for l in topologyMap.edges[k]:
        destDevice = l.destinationDevice
        print ('Device: ', sourceDevice.label, ' output port ', l.outputPortIndex, ' connects to device: ', destDevice.label, ' on input port ', l.inputPortIndex)
        newNodeId = sourceDevice.label
        if sourceDevice.deviceType.inputMedium == sourceDevice.deviceType.outputMedium:
            newNodeType = sourceDevice.deviceType.inputMedium
        elif sourceDevice.deviceType.inputMedium == 0 or sourceDevice.deviceType.inputMedium == 1 \
                and sourceDevice.deviceType.outputMedium == 0 or sourceDevice.deviceType.outputMedium == 1:
            newNodeType = 'Electro-optical'
        newNode = deviceProgrammer.Node(newNodeId, newNodeType)
        drawer.AddNode(newNode)
        newNodeId = destDevice.label
        if destDevice.deviceType.inputMedium == destDevice.deviceType.outputMedium:
            newNodeType = destDevice.deviceType.inputMedium
        elif destDevice.deviceType.inputMedium == 0 or destDevice.deviceType.inputMedium == 1 \
                and destDevice.deviceType.outputMedium == 0 or destDevice.deviceType.outputMedium == 1:
            newNodeType = 'Electro-optical'
        newNode = deviceProgrammer.Node(newNodeId, newNodeType)
        drawer.AddNode(newNode)
        edgeSource = sourceDevice.label
        edgeSink = destDevice.label
        if sourceDevice.deviceType.inputMedium != 4 and sourceDevice.deviceType.outputMedium != 4 \
                and destDevice.deviceType.inputMedium != 4 and destDevice.deviceType.outputMedium != 4:
            edgeType = 'Real'
        else:
            edgeType = 'Virtual'
        newEdge = deviceProgrammer.Edge(edgeSource, edgeSink, edgeType)
        drawer.AddEdge(newEdge)

#drawer.GenerateGraph('screen', 'physical')  # 'virtual' or 'physical'
#backplane_drawer.GenerateGraph(backplane, 'screen')

solutionSetU = []
for device in zComplete:
    solutionSetU.append(device)

input_request = currentRequest.InputTransport
output_request = currentRequest.OutputTransport

