import time
import os

from info_provider.ldap_utils import LDIFNode
from info_provider.glue.constants import *

class GLUE2StorageService(LDIFNode):

    def __init__(self, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2ServiceID=" + GLUE2ServiceID + "," + GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'objectClass': ['GLUE2Service', 'GLUE2StorageService'],
                'GLUE2ServiceType': 'storm',
                'GLUE2ServiceCapability': 'data.management.storage',
                'GLUE2EntityOtherInfo': ['ProfileName=EGI', 
                    'ProfileVersion=1.0']
            })
        return

class GLUE2StorageServiceCapacity(LDIFNode):

    def __init__(self, GLUE2StorageServiceCapacityID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2StorageServiceCapacityID=" + GLUE2StorageServiceCapacityID + 
                ",GLUE2ServiceID=" + GLUE2ServiceID + "," + GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'GLUE2StorageServiceCapacityID': GLUE2StorageServiceCapacityID,
                'objectClass': ['GLUE2StorageServiceCapacity'],
                'GLUE2StorageServiceCapacityStorageServiceForeignKey': 
                    GLUE2ServiceID
            })
        return

class GLUE2StorageAccessProtocol(LDIFNode):

    def __init__(self, GLUE2StorageAccessProtocolID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2StorageAccessProtocolID=" + GLUE2StorageAccessProtocolID + 
                ",GLUE2ServiceID=" + GLUE2ServiceID + "," + GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'GLUE2StorageAccessProtocolID': GLUE2StorageAccessProtocolID,
                'objectClass': ['GLUE2StorageAccessProtocol'],
                'GLUE2StorageAccessProtocolStorageServiceForeignKey': 
                    GLUE2ServiceID
            })
        return

class GLUE2StorageManager(LDIFNode):

    def __init__(self, GLUE2ManagerID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2ManagerID=" + GLUE2ManagerID + ",GLUE2ServiceID=" + 
                GLUE2ServiceID + "," + GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'GLUE2ManagerID': GLUE2ManagerID,
                'objectClass': ['GLUE2Manager', 'GLUE2StorageManager'],
                'GLUE2ManagerProductName': 'StoRM',
                'GLUE2StorageManagerStorageServiceForeignKey': GLUE2ServiceID,
                'GLUE2ManagerServiceForeignKey': GLUE2ServiceID
            })
        return

class GLUE2DataStore(LDIFNode):

    def __init__(self, GLUE2ResourceID, GLUE2ManagerID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2ResourceID=" + GLUE2ResourceID + ",GLUE2ManagerID=" + 
                GLUE2ManagerID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + 
                GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'GLUE2ResourceID': GLUE2ResourceID,
                'objectClass': ['GLUE2DataStore', 'GLUE2Resource'],
                'GLUE2ResourceManagerForeignKey': GLUE2ManagerID,
                # it seems necessary:
                'GLUE2DataStoreStorageManagerForeignKey': GLUE2ManagerID
            })
        return

class GLUE2StorageShare(LDIFNode):

    def __init__(self, GLUE2ShareID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2ShareID=" + GLUE2ShareID + ",GLUE2ServiceID=" + 
                GLUE2ServiceID + "," + GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'GLUE2ShareID': GLUE2ShareID,
                'objectClass': ['GLUE2Share', 'GLUE2StorageShare'],
                'GLUE2StorageShareExpirationMode': 'neverexpire',
                'GLUE2StorageShareStorageServiceForeignKey': GLUE2ServiceID,
                # it seems necessary:
                'GLUE2ShareServiceForeignKey': GLUE2ServiceID
            })
        return

class GLUE2MappingPolicy(LDIFNode):

    def __init__(self, GLUE2PolicyID, GLUE2ShareID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2PolicyID=" + GLUE2PolicyID + ",GLUE2ShareID=" + 
                GLUE2ShareID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + 
                GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'GLUE2PolicyID': GLUE2PolicyID,
                'objectClass': ['GLUE2Policy', 'GLUE2MappingPolicy'],
                'GLUE2PolicyScheme': 'basic',
                'GLUE2MappingPolicyShareForeignKey': GLUE2ShareID
            })
        return

class GLUE2StorageShareCapacity(LDIFNode):

    def __init__(self, GLUE2StorageShareCapacityID, GLUE2ShareID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2StorageShareCapacityID=" + GLUE2StorageShareCapacityID + 
                ",GLUE2ShareID=" + GLUE2ShareID + ",GLUE2ServiceID=" + 
                GLUE2ServiceID + "," + GLUE2_BASEDN,
            {
                'GLUE2StorageShareCapacityID': GLUE2StorageShareCapacityID,
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'objectClass': ['GLUE2StorageShareCapacity'],
                'GLUE2StorageShareCapacityStorageShareForeignKey': GLUE2ShareID
            })
        return

class GLUE2StorageEndpoint(LDIFNode):

    def __init__(self, GLUE2EndpointID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2EndpointID=" + GLUE2EndpointID + ",GLUE2ServiceID=" + 
                GLUE2ServiceID + "," + GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'objectClass': ['GLUE2Endpoint', 'GLUE2StorageEndpoint'],
                'GLUE2EndpointImplementationName': 'StoRM',
                'GLUE2EndpointHealthState': 'ok',
            })
        return

class GLUE2HttpStorageEndpoint(LDIFNode):

    def __init__(self, GLUE2EndpointID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2EndpointID=" + GLUE2EndpointID + ",GLUE2ServiceID=" + 
                GLUE2ServiceID + "," + GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'objectClass': ['GLUE2Endpoint', 'GLUE2StorageEndpoint'],
                'GLUE2EndpointID': GLUE2EndpointID,
                'GLUE2EndpointImplementationName': 'StoRM',
                'GLUE2EndpointHealthState': 'ok',
                'GLUE2EndpointInterfaceName': 'http',
                'GLUE2EndpointInterfaceVersion': '1.1.0',
                'GLUE2EndpointSemantics': 'http://tools.ietf.org/html/rfc4918',
                'GLUE2EndpointTechnology': 'webservice',
                'GLUE2EndpointCapability': 'data.management.storage',
                'GLUE2EndpointServiceForeignKey': GLUE2ServiceID,
                'GLUE2StorageEndpointStorageServiceForeignKey': GLUE2ServiceID
            })
        return

class GLUE2HttpsStorageEndpoint(LDIFNode):

    def __init__(self, GLUE2EndpointID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2EndpointID=" + GLUE2EndpointID + ",GLUE2ServiceID=" + 
                GLUE2ServiceID + "," + GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'objectClass': ['GLUE2Endpoint', 'GLUE2StorageEndpoint'],
                'GLUE2EndpointID': GLUE2EndpointID,
                'GLUE2EndpointImplementationName': 'StoRM',
                'GLUE2EndpointHealthState': 'ok',
                'GLUE2EndpointInterfaceName': 'https',
                'GLUE2EndpointInterfaceVersion': '1.1.0',
                'GLUE2EndpointSemantics': 'http://tools.ietf.org/html/rfc4918',
                'GLUE2EndpointTechnology': 'webservice',
                'GLUE2EndpointCapability': 'data.management.storage',
                'GLUE2EndpointServiceForeignKey': GLUE2ServiceID,
                'GLUE2StorageEndpointStorageServiceForeignKey': GLUE2ServiceID
            })
        return

class GLUE2WebDAVStorageEndpoint(LDIFNode):

    def __init__(self, GLUE2EndpointID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2EndpointID=" + GLUE2EndpointID + ",GLUE2ServiceID=" + 
                GLUE2ServiceID + "," + GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'objectClass': ['GLUE2Endpoint', 'GLUE2StorageEndpoint'],
                'GLUE2EndpointID': GLUE2EndpointID,
                'GLUE2EndpointImplementationName': 'StoRM',
                'GLUE2EndpointHealthState': 'ok',
                'GLUE2EndpointInterfaceName': 'webdav',
                'GLUE2EndpointInterfaceVersion': '1.1',
                'GLUE2EndpointSemantics': 'http://www.ietf.org/rfc/rfc4918.txt',
                'GLUE2EndpointTechnology': 'webservice',
                'GLUE2EndpointCapability': [
                    'data.management.storage',
                    'data.management.transfer'
                    ],
                'GLUE2EndpointServiceForeignKey': GLUE2ServiceID,
                'GLUE2StorageEndpointStorageServiceForeignKey': GLUE2ServiceID
            })
        return

class GLUE2AccessPolicy(LDIFNode):

    def __init__(self, GLUE2PolicyID, GLUE2EndpointID, GLUE2ServiceID):
        LDIFNode.__init__(self, 
            "GLUE2PolicyID=" + GLUE2PolicyID + ",GLUE2EndpointID=" + 
                GLUE2EndpointID + ",GLUE2ServiceID=" + GLUE2ServiceID + "," + 
                GLUE2_BASEDN,
            {
                'GLUE2EntityCreationTime': time.strftime('%Y-%m-%dT%T'),
                'GLUE2PolicyID': GLUE2PolicyID,
                'objectClass': ['GLUE2Policy', 'GLUE2AccessPolicy'],
                'GLUE2PolicyScheme': 'org.glite.standard',
                'GLUE2AccessPolicyEndpointForeignKey': GLUE2EndpointID
            })
        return