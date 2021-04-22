import logging

from ldif import LDIFWriter


class LDIFNode:

    def __init__(self, dn, default_entries):
        self.default_entries = default_entries
        self.dn = dn
        self.entries = {}
        return

    def add(self, entries):
        # add/update entries
        for entry_name in entries:
            if isinstance(entries[entry_name], list):
                self.entries[entry_name] = []
                for item in entries[entry_name]:
                    self.entries[entry_name].append(str(item))
            elif isinstance(entries[entry_name], str):
                self.entries[entry_name] = [entries[entry_name]]
            else:
                self.entries[entry_name] = [str(entries[entry_name])]
        return self

    def init(self):
        self.entries = {}
        self.add(self.default_entries)
        return self

    def get_info(self):
        return {"dn": self.dn, "entries": self.entries}

    def __str__(self):
        out = "dn = '" + self.dn + "'\n"
        for entry_name, entry_values in list(self.entries.items()):
            for value in entry_values:
                out += "# " + entry_name + " = '" + str(value) + "'\n"
        return out 


class LDIFExporter:

    def __init__(self):
        self.nodes = []
        return

    def add_node(self, node):
        if not isinstance(node, LDIFNode):
            raise Exception("LDIFExporter.add_node error: Invalid node type")
        self.nodes.append(node.get_info())
        logging.debug("LDIFExporter - Added %s node:\n%s",
            node.__class__.__name__, node)
        return self

    def add_nodes(self, nodes):
        for node in nodes:
            self.add_node(node)
        return self

    def print_nodes(self, stream):
        ldif_writer = LDIFWriter(stream, cols=512)
        for node in self.nodes:
            ldif_writer.unparse(node["dn"], node["entries"])
        return self

    def save_to_file(self, fname):
        logging.debug("Saving nodes to file %s", fname)
        f = open(fname, 'w')
        self.print_nodes(f)
        f.close()
        return
