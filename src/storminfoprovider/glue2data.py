from .glue import GlueLDIFNode

class QualityLevel_t:
    quality_levels = ["development", "pre-production", "production", "testing"]
    def __init__(self, int_value):
        self.int_value = int(int_value)
        return
    def __str__(self):
        return self.quality_levels[self.int_value]

class Glue2LDIFNode(GlueLDIFNode):

    def __init__(self, default_entries):
        GlueLDIFNode.__init__(self, "GLUE2GroupID=resource,o=glue", default_entries)
        return

    def __str__(self):
        return GlueLDIFNode.__str__(self)

class GLUE2StorageService(Glue2LDIFNode):

    def __init__(self, GLUE2ServiceID):
        Glue2LDIFNode.__init__(self, {
            'objectClass': ['GLUE2Service', 'GLUE2StorageService'],
            'GLUE2ServiceType': ['storm'],
            'GLUE2ServiceCapability': ['data.management.storage'],
            'GLUE2EntityOtherInfo': ['ProfileName=EGI', 'ProfileVersion=1.0']
        })
        self.dn = "GLUE2ServiceID=" + GLUE2ServiceID + "," + self.baseDN
        return

class GLUE2StorageServiceCapacity(Glue2LDIFNode):

    def __init__(self, GLUE2StorageServiceCapacityID, GLUE2ServiceID):
        Glue2LDIFNode.__init__(self, {
            'objectClass': ['GLUE2StorageServiceCapacity']
        })
        self.dn = "GLUE2StorageServiceCapacityID=" + GLUE2StorageServiceCapacityID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + self.baseDN
        return

class GLUE2StorageAccessProtocol(Glue2LDIFNode):

    def __init__(self, GLUE2StorageAccessProtocolID, GLUE2ServiceID):
        Glue2LDIFNode.__init__(self, {
            'objectClass': ['GLUE2StorageAccessProtocol']
        })
        self.dn = "GLUE2StorageAccessProtocolID=" + GLUE2StorageAccessProtocolID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + self.baseDN
        return

class GLUE2StorageManager(Glue2LDIFNode):

    def __init__(self, GLUE2ManagerID, GLUE2ServiceID):
        Glue2LDIFNode.__init__(self, {
            'objectClass': ['GLUE2Manager', 'GLUE2StorageManager'],
            'GLUE2ManagerProductName': ['StoRM'],
            'GLUE2ManagerProductVersion': ["`rpm -q --queryformat='%{VERSION}' storm-backend-server`"]
        })
        self.dn = "GLUE2ManagerID=" + GLUE2ManagerID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + self.baseDN
        return

class GLUE2DataStore(Glue2LDIFNode):

    def __init__(self, GLUE2ResourceID, GLUE2ManagerID, GLUE2ServiceID):
        Glue2LDIFNode.__init__(self, {
            'objectClass': ['GLUE2DataStore', 'GLUE2Resource']
        })
        self.dn = "GLUE2ResourceID=" + GLUE2ResourceID + ",GLUE2ManagerID=" + GLUE2ManagerID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + self.baseDN
        return

class GLUE2StorageShare(Glue2LDIFNode):

    def __init__(self, GLUE2ShareID, GLUE2ServiceID):
        Glue2LDIFNode.__init__(self, {
            'objectClass': ['GLUE2Share', 'GLUE2StorageShare'],
            'GLUE2StorageShareExpirationMode': ['neverexpire']
        })
        self.dn = "GLUE2ShareID=" + GLUE2ShareID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + self.baseDN
        return

class GLUE2MappingPolicy(Glue2LDIFNode):

    def __init__(self, GLUE2PolicyID, GLUE2ShareID, GLUE2ServiceID):
        Glue2LDIFNode.__init__(self, {
            'objectClass': ['GLUE2Policy', 'GLUE2MappingPolicy'],
            'GLUE2PolicyScheme': ['basic']
        })
        self.dn = "GLUE2PolicyID=" + GLUE2PolicyID + ",GLUE2ShareID=" + GLUE2ShareID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + self.baseDN
        return

class GLUE2StorageShareCapacity(Glue2LDIFNode):

    def __init__(self, GLUE2StorageShareCapacityID, GLUE2ShareID, GLUE2ServiceID):
        Glue2LDIFNode.__init__(self, {
            'objectClass': ['GLUE2StorageShareCapacity']
        })
        self.dn = "GLUE2StorageShareCapacityID=" + GLUE2StorageShareCapacityID + ",GLUE2ShareID=" + GLUE2ShareID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + self.baseDN
        return

class GLUE2StorageEndpoint(Glue2LDIFNode):

    def __init__(self, GLUE2EndpointID, GLUE2ServiceID):
        Glue2LDIFNode.__init__(self, {
            'objectClass': ['GLUE2Endpoint', 'GLUE2StorageEndpoint'],
            'GLUE2EndpointImplementationName': ['StoRM'],
            'GLUE2EndpointImplementationVersion': ["`rpm -q --queryformat='%{VERSION}' storm-backend-server`"],
            'GLUE2EndpointHealthState': ['ok'],
            'GLUE2EndpointIssuerCA': ["`openssl x509 -issuer -noout -in /etc/grid-security/hostcert.pem | sed 's/^[^/]*//'`"]
        })
        self.dn = "GLUE2EndpointID=" + GLUE2EndpointID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + self.baseDN
        return

class GLUE2AccessPolicy(Glue2LDIFNode):

    def __init__(self, GLUE2PolicyID, GLUE2EndpointID, GLUE2ServiceID):
        Glue2LDIFNode.__init__(self, {
            'objectClass': ['GLUE2Policy', 'GLUE2AccessPolicy'],
            'GLUE2PolicyScheme': ['basic']
        })
        self.dn = "GLUE2PolicyID=" + GLUE2PolicyID + ",GLUE2EndpointID=" + GLUE2EndpointID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + self.baseDN
        return
