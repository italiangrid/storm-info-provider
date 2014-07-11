import os
import re
import pwd
import grp
import time
import tempfile
from ldif import LDIFWriter

import logging

class GlueConstants:

    INFO_SERVICE_CONFIG = "/etc/glite/info/service"
    INFO_SERVICE_SCRIPT = "/usr/bin"
    INFO_PROVIDER_PATH = "/var/lib/bdii/gip/provider"
    INFO_LDIF_PATH = "/var/lib/bdii/gip/ldif"
    INFO_PLUGIN_PATH = "/var/lib/bdii/gip/plugin"

class Glue(object):

    def create_service_file(self, dest_file, info_service, config_file_path, params):
        f = open(dest_file, "w")
        f.write("#!/bin/sh\n. /etc/profile.d/grid-env.sh\n")
        f.write("%s %s" % (info_service, config_file_path))
        for param in params:
            f.write(" %s" % param)
        f.close()
        # Set execute permissions: chmod +x
        os.chmod(dest_file, 0755)
        return dest_file

    def create_service_config_file(self, dest_file, content):
        f = open(dest_file, "w")
        for key, val in content.items():
            f.write("%s=%s\n" % (key, val))
        f.close()
        # set owner
        uid = pwd.getpwnam("ldap").pw_uid
        gid = grp.getgrnam("ldap").gr_gid
        os.chown(dest_file, uid, gid)
        return dest_file

    def create_static_ldif_file(self, dest_file, node_list, info_overwrite_flag):
        # init LDIF exporter obj
        exporter = GlueLDIFExporter()
        # add nodes
        for node in node_list:
            exporter.add_node(node["dn"], node["entries"])
        # save to file
        if not "true" in info_overwrite_flag:
            if os.path.isfile(dest_file):
                os.rename(dest_file, dest_file + ".bkp_" + time.strftime('%Y%m%d_%H%M%S'))
            else:
                dest_file = dest_file + ".yaimnew_" + time.strftime('%Y%m%d_%H%M%S')
        # export ldif
        exporter.save_to_file(dest_file)
        # set owner
        uid = pwd.getpwnam("ldap").pw_uid
        gid = grp.getgrnam("ldap").gr_gid
        os.chown(dest_file, uid, gid)
        os.chmod(dest_file, 0644)
        return dest_file

    def create_plugin_file(self, dest_file, info_service, params):
        f = open(dest_file, "w")
        f.write("#!/bin/sh\n")
        f.write("%s" % info_service)
        for param in params:
            f.write(" %s" % param)
        f.close()
        # set owner
        uid = pwd.getpwnam("ldap").pw_uid
        gid = grp.getgrnam("ldap").gr_gid
        os.chown(dest_file, uid, gid)
        os.chmod(dest_file, 0755)
        return

    def print_update_ldif(self, node_list):
        # Create temp file
        ftmp = tempfile.mkstemp()
        # init LDIF exporter obj
        exporter = GlueLDIFExporter()
        # add nodes
        for node in node_list:
            exporter.add_node(node["dn"], node["entries"])
        # save to file
        exporter.save_to_file(ftmp[1])
        # return its content
        fin = open(ftmp[1], 'r')
        print fin.read()
        fin.close()
        # delete temp file
        os.remove(ftmp[1])
        return

class GlueLDIFExporter:

    def __init__(self):
        self.content = []
        return

    def add_node(self, dn, entries):
        self.content.append({
            "dn": dn,
            "entries": entries
        })
        return self

    def save_to_file(self, fname):
        f = open(fname, "w")
        ldif_writer = LDIFWriter(f, cols=512)
        for node in self.content:
            ldif_writer.unparse(node["dn"], node["entries"])
        f.close()
        return self

    def print_to_stdout(self):
        target = tempfile.mkstemp()
        self.save_to_file(target[1])
        fin = open(target[1], 'r')
        print fin.read()
        fin.close()
        return