__author__ = 'Chris'

import enum



_fullFunctionIndexes = {'m_opticalLabel': 0,
                         'm_frequency': 1,
                         'm_etherType': 2,
                         'm_lambda': 4,
                         'm_centralFrequency': 5,
                         'm_bandwidth': 6,
                         'm_vlanId': 7,
                         'm_sourceMac': 8,
                         'm_destinationMac': 9,
                         'm_port': 11,
                         'a_opticalLabel': 12,
                         'a_frequency': 13,
                         'a_etherType': 14,
                         'a_amplify': 15,
                         'a_lambda': 16,
                         'a_centralFrequency': 17,
                         'a_bandwidth': 18,
                         'a_vlanId': 19,
                         'a_sourceMac': 20,
                         'a_destinationMac': 21,
                         'a_port': 23
                        }

class FlowFunction():
    def __init__(self, name, functionType, transport):
        self.name = name
        self.functionType = functionType
        self.transport = transport


def MakeWord(attributes):
    attWord = 0
    for k in attributes:
        attWord |= (1 << _fullFunctionIndexes[k])

    return attWord

# We must account for different mediums and the need to use devices that interface between them
class Transport_Format(enum.Enum):
    Electronic = 0
    Optical = 1
    Wireless = 2
    All = 3     # THIS MUST BE THE LAST ELEMENT OF THE ENUM (sorry)

# instantiate all available flow table functions
m_opticalLabel = FlowFunction('m_opticalLabel','m', Transport_Format.Optical)
m_frequency = FlowFunction('m_frequency','m',Transport_Format.Optical)
m_etherType= FlowFunction('m_etherType','m', Transport_Format.Electronic)
m_lambda = FlowFunction('m_lambda','m',Transport_Format.Optical)
m_centralFrequency = FlowFunction('m_centralFrequency','m',Transport_Format.Optical)
m_bandwidth = FlowFunction('m_bandwidth','m',Transport_Format.Optical)
m_vlanId = FlowFunction('m_vlanId','m',Transport_Format.Electronic)
m_sourceMac = FlowFunction('m_sourceMac','m',Transport_Format.Electronic)
m_destinationMac = FlowFunction('m_destinationMac','m',Transport_Format.Electronic)
m_port = FlowFunction('m_port','m',Transport_Format.Electronic)
a_opticalLabel = FlowFunction('a_opticalLabel','a',Transport_Format.Optical)
a_frequency = FlowFunction('a_frequency','a',Transport_Format.Optical)
a_etherType = FlowFunction('a_etherType','a',Transport_Format.Electronic)
a_amplify = FlowFunction('a_amplify','a',Transport_Format.Optical)
a_lambda = FlowFunction('a_lambda','a',Transport_Format.Optical)
a_centralFrequency = FlowFunction('a_centralFrequency','a',Transport_Format.Optical)
a_bandwidth = FlowFunction('a_bandwidth','a',Transport_Format.Optical)
a_vlanId = FlowFunction('a_vlanId','a',Transport_Format.Electronic)
a_sourceMac= FlowFunction('a_sourceMac','a',Transport_Format.Electronic)
a_destinationMac = FlowFunction('a_destinationMac','a',Transport_Format.Electronic)
a_port = FlowFunction('a_port','a',Transport_Format.All)


FlowFunctionDict = {'m_opticalLabel': m_opticalLabel,
                 'm_frequency': m_frequency,
                 'm_etherType': m_etherType,
                 'm_lambda': m_lambda,
                 'm_centralFrequency': m_centralFrequency,
                 'm_bandwidth': m_bandwidth,
                 'm_vlanId': m_vlanId,
                 'm_sourceMac': m_sourceMac,
                 'm_destinationMac': m_destinationMac,
                 'm_port': m_port,
                 'a_opticalLabel': a_opticalLabel,
                 'a_frequency': a_frequency,
                 'a_etherType': a_etherType,
                 'a_amplify': a_amplify,
                 'a_lambda': a_lambda,
                 'a_centralFrequency': a_centralFrequency,
                 'a_bandwidth': a_bandwidth,
                 'a_vlanId': a_vlanId,
                 'a_sourceMac': a_sourceMac,
                 'a_destinationMac': a_destinationMac,
                 'a_port': a_port
                 }

ReqGenFunctionDict = {'m_opticalLabel': m_opticalLabel,
                 'm_etherType': m_etherType,
                 'm_lambda': m_lambda,
                 'm_centralFrequency': m_centralFrequency,
                 'm_bandwidth': m_bandwidth,
                 'm_vlanId': m_vlanId,
                 'm_sourceMac': m_sourceMac,
                 'm_destinationMac': m_destinationMac,
                 'a_opticalLabel': a_opticalLabel,
                 'a_etherType': a_etherType,
                 'a_amplify': a_amplify,
                 'a_lambda': a_lambda,
                 'a_centralFrequency': a_centralFrequency,
                 'a_bandwidth': a_bandwidth,
                 'a_vlanId': a_vlanId,
                 'a_sourceMac': a_sourceMac,
                 'a_destinationMac': a_destinationMac,
                 }
