import os
import re
import pwd
import grp
import time
import tempfile
import logging
from ldif import LDIFWriter

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

    def create_static_ldif_file(self, dest_file, nodes, info_overwrite_flag):
        # init LDIF exporter obj
        exporter = GlueLDIFExporter()
        # add nodes
        for node in nodes:
            exporter.add_node(node)
        # save to file
        if info_overwrite_flag:
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

    def print_update_ldif(self, nodes):
        # Create temp file
        ftmp = tempfile.mkstemp()
        # init LDIF exporter obj
        exporter = GlueLDIFExporter()
        # add nodes
        for node in nodes:
            exporter.add_node(node)
        # save to file
        exporter.save_to_file(ftmp[1])
        # return its content
        fin = open(ftmp[1], 'r')
        print fin.read()
        fin.close()
        # delete temp file
        os.remove(ftmp[1])
        return

class GlueLDIFNode:

    def __init__(self, baseDN, default_entries):
        self.default_entries = default_entries
        self.baseDN = baseDN
        self.dn = baseDN
        return

    def clear_all(self):
        self.entries = {}
        return self

    def add(self, entries):
        # add/update entries
        for entry_name in entries:
            self.entries[entry_name] = entries[entry_name]
        return self

    def init_as_default(self):
        self.clear_all()
        self.add(self.default_entries)
        return self

    def get_info(self):
        return {"dn": self.dn, "entries": self.entries}

    def __str__(self):
        out = "dn = '" + self.dn + "'\n"
        for entry_name, entry_values in self.entries.items():
            for value in entry_values:
                out += "# " + entry_name + " = '" + value + "'\n"
        return out 

class GlueLDIFExporter:

    def __init__(self):
        self.nodes = []
        return

    def add_node(self, node):
        if not isinstance(node, GlueLDIFNode):
            raise Exception("GlueLDIFExporter.add_node error: Invalid node type")
        self.nodes.append(node.get_info())
        logging.debug("Added %s node:\n%s", node.__class__.__name__, node)
        return self

    def save_to_file(self, fname):
        f = open(fname, "w")
        ldif_writer = LDIFWriter(f, cols=512)
        for node in self.nodes:
            ldif_writer.unparse(node["dn"], node["entries"])
        f.close()
        return self

    def print_to_stdout(self):
        target = tempfile.mkstemp()
        self.save_to_file(target[1])
        fin = open(target[1], 'r')
        print fin.read()
        fin.close()
        os.remove(target[1])
        return