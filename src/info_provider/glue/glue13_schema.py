from info_provider.glue.glue13_constants import GLUE13_BASEDN
from info_provider.utils.ldap_utils import LDIFNode


class GlueSE(LDIFNode):
    
    def __init__(self, GlueSEUniqueID):
        LDIFNode.__init__(self,
            "GlueSEUniqueID=" + GlueSEUniqueID + "," + GLUE13_BASEDN,
            {
                'GlueSEUniqueID': GlueSEUniqueID,
                'objectClass': ['GlueSETop', 'GlueSE', 'GlueInformationService',
                    'GlueKey', 'GlueSchemaVersion'],
                'GlueSESizeTotal': 0,
                'GlueSESizeFree': 0,
                'GlueSETotalOnlineSize': 0,
                'GlueSEUsedOnlineSize': 0,
                'GlueSETotalNearlineSize': 0,
                'GlueSEUsedNearlineSize': 0,
                'GlueSEArchitecture': "multidisk",
                'GlueSEStatus': "Production",
                'GlueSEImplementationName': "StoRM",
                'GlueSchemaVersionMajor': 1,
                'GlueSchemaVersionMinor': 3
            })
        return


class GlueSALocal(LDIFNode):

    def __init__(self, GlueSALocalID, GlueSEUniqueID):
        LDIFNode.__init__(self,
            "GlueSALocalID=" + GlueSALocalID + ",GlueSEUniqueID=" + 
                GlueSEUniqueID + "," + GLUE13_BASEDN,
            {
                'GlueSALocalID': GlueSALocalID,
                'objectClass': ['GlueSATop', 'GlueSA', 'GlueSAPolicy',
                    'GlueSAState', 'GlueSAAccessControlBase', 'GlueKey',
                    'GlueSchemaVersion'],
                'GlueSATotalOnlineSize': 0,
                'GlueSAUsedOnlineSize': 0,
                'GlueSAFreeOnlineSize': 0,
                'GlueSAReservedOnlineSize': 0,
                'GlueSATotalNearlineSize': 0,
                'GlueSAUsedNearlineSize': 0,
                'GlueSAFreeNearlineSize': 0,
                'GlueSAReservedNearlineSize': 0,
                'GlueSAAccessLatency': 'online',
                'GlueSAExpirationMode': 'neverExpire',
                'GlueSAPolicyFileLifeTime': 'permanent',
                'GlueSAType': 'permanent',
                'GlueSchemaVersionMajor':  1,
                'GlueSchemaVersionMinor': 3,
                'GlueChunkKey': "GlueSEUniqueID=" + GlueSEUniqueID
            })
        return


class GlueSAVOInfoLocal(LDIFNode):
    
    def __init__(self, GlueVOInfoLocalID, GlueSALocalID, GlueSEUniqueID):
        LDIFNode.__init__(self,
            "GlueVOInfoLocalID=" + GlueVOInfoLocalID + ",GlueSALocalID=" + 
                GlueSALocalID + ",GlueSEUniqueID=" + GlueSEUniqueID + "," + 
                GLUE13_BASEDN,
            {
                'GlueVOInfoLocalID': GlueVOInfoLocalID,
                'objectClass': ['GlueSATop', 'GlueVOInfo', 'GlueKey',
                    'GlueSchemaVersion'],
                'GlueSchemaVersionMajor': 1,
                'GlueSchemaVersionMinor': 3,
                'GlueChunkKey': ["GlueSALocalID=" + GlueSALocalID,
                    "GlueSEUniqueID=" + GlueSEUniqueID]
            })
        return


class GlueSEControlProtocol(LDIFNode):
    
    def __init__(self, GlueSEControlProtocolLocalID, GlueSEUniqueID):
        LDIFNode.__init__(self,
            "GlueSEControlProtocolLocalID=" + GlueSEControlProtocolLocalID + 
                ",GlueSEUniqueID=" + GlueSEUniqueID + "," + GLUE13_BASEDN,
            {
                'GlueSEControlProtocolLocalID': GlueSEControlProtocolLocalID,
                'objectClass': ['GlueSETop', 'GlueSEControlProtocol', 'GlueKey',
                    'GlueSchemaVersion'],
                'GlueSEControlProtocolType': 'SRM',
                'GlueSEControlProtocolVersion': '2.2.0',
                'GlueSchemaVersionMajor': 1,
                'GlueSchemaVersionMinor': 3,
                'GlueChunkKey': "GlueSEUniqueID=" + GlueSEUniqueID
            })
        return


class GlueSEAccessProtocol(LDIFNode):

    def __init__(self, GlueSEAccessProtocolLocalID, GlueSEUniqueID):
        LDIFNode.__init__(self,
            "GlueSEAccessProtocolLocalID=" + GlueSEAccessProtocolLocalID + 
                ",GlueSEUniqueID=" + GlueSEUniqueID + "," + GLUE13_BASEDN,
            {
                'GlueSEAccessProtocolLocalID': GlueSEAccessProtocolLocalID,
                'GlueSEAccessProtocolType': GlueSEAccessProtocolLocalID,
                'objectClass': ['GlueSETop', 'GlueSEAccessProtocol', 'GlueKey',
                    'GlueSchemaVersion'],
                'GlueSEAccessProtocolSupportedSecurity': ['GSI'],
                'GlueSchemaVersionMajor': 1,
                'GlueSchemaVersionMinor': 3,
                'GlueChunkKey': "GlueSEUniqueID=" + GlueSEUniqueID
            })
        return
