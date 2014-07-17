from glue import GlueLDIFNode

class Glue13LDIFNode(GlueLDIFNode):

    def __init__(self, default_entries):
        GlueLDIFNode.__init__(self, "mds-vo-name=resource,o=grid", default_entries)
        return

    def __str__(self):
        return GlueLDIFNode.__str__(self)

class GlueSALocal(Glue13LDIFNode):

    def __init__(self, GlueSALocalID, GlueSEUniqueID):
        Glue13LDIFNode.__init__(self, {
            'objectClass': ['GlueSATop', 'GlueSA', 'GlueSAPolicy', 'GlueSAState', 
                'GlueSAAccessControlBase', 'GlueKey', 'GlueSchemaVersion'],
            'GlueSATotalOnlineSize': [str(0)],
            'GlueSAUsedOnlineSize': [str(0)],
            'GlueSAFreeOnlineSize': [str(0)],
            'GlueSAReservedOnlineSize': [str(0)],
            'GlueSATotalNearlineSize': [str(0)],
            'GlueSAUsedNearlineSize': [str(0)],
            'GlueSAFreeNearlineSize': [str(0)],
            'GlueSAReservedNearlineSize': [str(0)],
            'GlueSAAccessLatency': ['online'],
            'GlueSAExpirationMode': ['neverExpire'],
            'GlueSAPolicyFileLifeTime': ['permanent'],
            'GlueSAType': ['permanent'],
            'GlueSchemaVersionMajor': ['1'],
            'GlueSchemaVersionMinor': ['3']
        })
        self.dn = "GlueSALocalID=" + GlueSALocalID + ",GlueSEUniqueID=" + GlueSEUniqueID + "," + self.baseDN
        return

class GlueSAVOInfoLocal(Glue13LDIFNode):
    
    def __init__(self, GlueVOInfoLocalID, GlueSALocalID, GlueSEUniqueID):
        Glue13LDIFNode.__init__(self, {
            'objectClass': ['GlueSATop', 'GlueVOInfo', 'GlueKey', 'GlueSchemaVersion'],
            'GlueSchemaVersionMajor': ['1'],
            'GlueSchemaVersionMinor': ['3']
        })
        self.dn = "GlueVOInfoLocalID=" + GlueVOInfoLocalID + ",GlueSALocalID=" + GlueSALocalID + ",GlueSEUniqueID=" + GlueSEUniqueID + "," + self.baseDN
        return

class GlueSE(Glue13LDIFNode):
    
    def __init__(self, GlueSEUniqueID):
        Glue13LDIFNode.__init__(self, {
            'objectClass': ['GlueSETop', 'GlueSE', 'GlueInformationService', 
                'GlueKey', 'GlueSchemaVersion'],
            'GlueSEArchitecture': ['multidisk'],
            'GlueSEStatus': ['Production'],
            'GlueSEImplementationName': ['StoRM'],
            'GlueSEImplementationVersion': ["`rpm -q --queryformat='%{VERSION}' storm-backend-server`"],
            'GlueSchemaVersionMajor': ['1'],
            'GlueSchemaVersionMinor': ['3']
        })
        self.dn = "GlueSEUniqueID=" + GlueSEUniqueID + "," + self.baseDN
        return


class GlueSEControlProtocol(Glue13LDIFNode):
    
    def __init__(self, GlueSEControlProtocolLocalID, GlueSEUniqueID):
        Glue13LDIFNode.__init__(self, {
            'objectClass': ['GlueSETop', 'GlueSEControlProtocol', 'GlueKey', 'GlueSchemaVersion'],
            'GlueSchemaVersionMajor': ["1"],
            'GlueSchemaVersionMinor': ["3"]
        })
        self.dn = "GlueSEControlProtocolLocalID=" + GlueSEControlProtocolLocalID + ",GlueSEUniqueID=" + GlueSEUniqueID + "," + self.baseDN
        return

class GlueSEAccessProtocol(Glue13LDIFNode):

    def __init__(self, GlueSEAccessProtocolLocalID, GlueSEUniqueID):
        Glue13LDIFNode.__init__(self, {
            'objectClass': ['GlueSETop', 'GlueSEAccessProtocol', 'GlueKey', 'GlueSchemaVersion'],
            'GlueSEAccessProtocolSupportedSecurity': ['GSI'],
            'GlueSchemaVersionMajor': ["1"],
            'GlueSchemaVersionMinor': ["3"]
        })
        self.dn = "GlueSEAccessProtocolLocalID=" + GlueSEAccessProtocolLocalID + ",GlueSEUniqueID=" + GlueSEUniqueID + "," + self.baseDN
        return
