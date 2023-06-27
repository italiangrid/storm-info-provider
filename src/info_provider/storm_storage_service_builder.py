import logging

from urlparse import urlparse

from info_provider.model.storage import StorageShare, StorageEndpoint, \
    StorageService


class StorageServiceBuilder:

    def __init__(self, configuration, space_info):
        self._configuration = configuration
        self._spaceinfo = space_info

    def build(self):
        sitename = self._configuration.get_sitename()
        version = self._configuration.get_implementation_version()
        quality_level = self._configuration.get_quality_level()

        service = StorageService(name=sitename, version=version, quality_level=quality_level)

        for name, vfs in self._spaceinfo.get_vfs().items():
            access_latency = vfs.get_accesslatency().lower()
            retention_policy = vfs.get_retentionpolicy().lower()
            total_size = vfs.get_space().get_total()
            used_size = vfs.get_space().get_used()
            paths = vfs.get_stfnroot()
            vos = vfs.get_vos()
            token = vfs.get_token()
            sa = StorageShare(name=token, access_latency=access_latency, retention_policy=retention_policy, total_size=total_size, used_size=used_size, path=paths, vo_list=vos)
            service.add_share(sa)

        srm_endpoint_url = self._configuration.get_public_srm_endpoint()
        srm_endpoint = StorageEndpoint(name="SRM_0", url=srm_endpoint_url, type="srm", version="2.2", capabilities=['data.management.transfer', 'data.management.storage'], quality_level=quality_level)
        service.add_endpoint(srm_endpoint)

        #gsiftp_endpoint = StorageEndpoint(name=name + "_gridftp", url="", type="gsiftp", version="1.0.0", capabilities=['data.management.transfer'], quality_level=quality_level)
        #service.add_endpoint(gsiftp_endpoint)

        if self._configuration.has_webdav():
            counter = {}
            counter["HTTP"] = 0
            counter["HTTPS"] = 0
            for dav_endpoint_url in self._configuration.get_webdav_endpoints():
                protocol = urlparse(dav_endpoint_url).scheme.upper()
                name = protocol + "_" + str(counter[protocol])
                se = StorageEndpoint(name=name, url=dav_endpoint_url, type="DAV", version="1.1", capabilities=['data.management.transfer', 'data.management.storage'], quality_level=quality_level)
                service.add_endpoint(se)
                counter[protocol] += 1
        elif self._configuration.has_gridhttps():
            dav_http_endpoint = StorageEndpoint(name="HTTP_0", url=self._configuration.get_public_http_endpoint(), type="DAV", version="1.1", capabilities=['data.management.transfer', 'data.management.storage'], quality_level=quality_level)
            service.add_endpoint(dav_http_endpoint)
            dav_https_endpoint = StorageEndpoint(name="HTTPS_0", url=self._configuration.get_public_https_endpoint(), type="DAV", version="1.1", capabilities=['data.management.transfer', 'data.management.storage'], quality_level=quality_level)
            service.add_endpoint(dav_https_endpoint)

        return service
