from tests.utils import get_default_test_configuration,\
    get_default_storm_gateway
from info_provider.storm_space_info_builder import SpaceInfoBuilder
from info_provider.glue.glue2_constants import GLUE2_BASEDN
from info_provider.glue.glue2 import Glue2
from info_provider.glue.utils import as_gigabytes


try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestGlue2(unittest.TestCase):

    def _check_generated_storage_service(self, node, configuration):
        expected_id = configuration.get_backend_hostname() + "/storage"
        expected_dn = "GLUE2ServiceID=" + expected_id + "," + GLUE2_BASEDN
        self.assertEqual(node["dn"], expected_dn)
        self.assertIsNotNone(node["entries"]["GLUE2EntityCreationTime"])
        self.assertEqual(node["entries"]["GLUE2ServiceQualityLevel"], [configuration.get_quality_level()])
        self.assertEqual(node["entries"]["GLUE2ServiceAdminDomainForeignKey"], [configuration.get_sitename()])
        self.assertEqual(node["entries"]["objectClass"], ['GLUE2Service', 'GLUE2StorageService'])
        self.assertEqual(node["entries"]["GLUE2ServiceType"], ["storm"])
        self.assertEqual(node["entries"]["GLUE2ServiceCapability"], ["data.management.storage"])
        self.assertEqual(node["entries"]["GLUE2EntityOtherInfo"], ["ProfileName=EGI", "ProfileVersion=1.0"])

    def _check_generated_storage_service_capacity(self, node, configuration, spaceinfo):
        service_id = configuration.get_backend_hostname() + "/storage"
        expected_id = service_id +"/capacity/online"
        expected_dn = "GLUE2StorageServiceCapacityID=" + expected_id + ",GLUE2ServiceID=" + service_id + "," + GLUE2_BASEDN
        self.assertEqual(node["dn"], expected_dn)
        self.assertIsNotNone(node["entries"]["GLUE2EntityCreationTime"])
        self.assertEqual(node["entries"]["GLUE2StorageServiceCapacityID"], [expected_id])
        self.assertEqual(node["entries"]["objectClass"], ['GLUE2StorageServiceCapacity'])
        self.assertEqual(node["entries"]["GLUE2StorageServiceCapacityStorageServiceForeignKey"], [service_id])
        self.assertEqual(node["entries"]["GLUE2StorageServiceCapacityType"], ["online"])
        self.assertEqual(node["entries"]["GLUE2StorageServiceCapacityTotalSize"], [str(as_gigabytes(spaceinfo.get_summary().get_total()))])
        self.assertEqual(node["entries"]["GLUE2StorageServiceCapacityFreeSize"], [str(as_gigabytes(spaceinfo.get_summary().get_free()))])
        self.assertEqual(node["entries"]["GLUE2StorageServiceCapacityUsedSize"], [str(as_gigabytes(spaceinfo.get_summary().get_used()))])
        self.assertEqual(node["entries"]["GLUE2StorageServiceCapacityReservedSize"], [str(as_gigabytes(spaceinfo.get_summary().get_reserved()))])

    def test_static_ldif(self):
        configuration = get_default_test_configuration()
        gateway = get_default_storm_gateway()
        spaceinfo = SpaceInfoBuilder(configuration, gateway).build()
        glue2 = Glue2(configuration)
        nodes = glue2.get_static_ldif_nodes(spaceinfo)
        self._check_generated_storage_service(nodes[0].get_info(), configuration)
        self._check_generated_storage_service_capacity(nodes[1].get_info(), configuration, spaceinfo)

if __name__ == "__main__":
    unittest.main()