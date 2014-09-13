#
# Manage registers in a hardware design
#
# Copyright (C) 2008  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
RegProject is the container object for a regenerate project
"""

import xml.parsers.expat
from xml.sax.saxutils import escape
import os.path
from regenerate.db import LOGGER
from regenerate.db.proj_writer import ProjectWriter
from regenerate.db.proj_reader import ProjectReader
from regenerate.db.group_data import GroupData
from collections import namedtuple

AddrMapData = namedtuple("AddrMapData", "name base width fixed")
GroupMapData = namedtuple("GroupMapData",
                          "set inst offset repeat repeat_offset format hdl no_uvm")


def cleanup(data):
    "Convert some unicode characters to standard ASCII"
    data = data.replace(u"\u2013", "-")
    data = data.replace(u"\u201c", "\"")
    data = data.replace(u"\ue280a2", "*")
    return escape(data.replace(u"\u201d", "\""))


class RegProject(object):
    """
    RegProject is the container object for a regenerate project. The project
    consists of several different types. General project information (name,
    company_name, etc.), the list of register sets, groupings of instances,
    and exports (register set and entire project exports), and address maps.
    """

    def __init__(self, path=None):
        self.name = "unnamed"
        self.short_name = "unnamed"
        self.company_name = ""
        self.documentation = ""
        self.__filelist = []
        self.__groupings = []
        self.__addr_map_list = []
        self.__addr_map_grps = {}
        self.__exports = {}
        self.__project_exports = []
        self.__token_list = []
        self.__modified = False
        self.__current = ""
        self.path = path
        if path:
            self.open(path)

    def save(self):
        writer = ProjectWriter(self)
        writer.save(self.path)

    def open(self, name):
        """
        Opens and reads an XML file
        """

        reader = ProjectReader(self)
        self.path = name
        reader.open(name)
        return
        self.__modified = False

        with open(self.path) as ofile:

            parser = xml.parsers.expat.ParserCreate()
            parser.StartElementHandler = self.startElement
            parser.EndElementHandler = self.endElement
            parser.CharacterDataHandler = self.characters
            parser.ParseFile(ofile)

    def set_new_order(self, new_order):
        """
        Alters the order of the items in the files in the list.
        """
        self.__modified = True
        htbl = {}
        for i in self.__filelist:
            htbl[os.path.splitext(os.path.basename(i))[0]] = i
        self.__filelist = [htbl[i] for i in new_order]

    def add_register_set(self, path):
        """
        Adds a new register set to the project. Note that this only records
        the filename, and does not actually keep a reference to the RegisterDb.
        """
        self.__modified = True
        self.__current = os.path.join(os.path.dirname(self.path), path)
        self.__current = os.path.relpath(self.__current,
                                         os.path.dirname(self.path))
        self.__filelist.append(self.__current)
        self.__exports[self.__current] = []

    def remove_register_set(self, path):
        """
        Removes the specified register set from the project.
        """
        self.__modified = True
        try:
            path2remove = os.path.relpath(path, os.path.dirname(self.path))
            self.__filelist.remove(path2remove)
        except ValueError, msg:
            LOGGER.error(str(msg))

    def get_exports(self, path):
        """
        Converts the exports to be relative to the passed path. Returns a
        read-only tuple
        """
        path = os.path.relpath(path, os.path.dirname(self.path))
        return tuple(self.__exports.get(path, []))

    def get_project_exports(self):
        """
        Returns the export project list, returns a read-only tuple
        """
        return tuple(self.__project_exports)

    def add_to_export_list(self, path, option, dest):
        """
        Adds an export to the export list. The exporter will only operation
        on the specified register database (XML file).

        path - path to the the register XML file. Converted to a relative path
        option - the chosen export option (exporter)
        dest - destination output name
        """
        self.__modified = True
        path = os.path.relpath(path, os.path.dirname(self.path))
        dest = os.path.relpath(dest, os.path.dirname(self.path))
        self.__exports[path].append((option, dest))

    def add_to_project_export_list(self, option, dest):
        """
        Adds a export to the project export list. Project exporters operation
        on the entire project, not just a specific register database (XML file)

        path - path to the the register XML file. Converted to a relative path
        option - the chosen export option (exporter)
        dest - destination output name
        """
        self.__modified = True
        dest = os.path.relpath(dest, os.path.dirname(self.path))
        self.__project_exports.append((option, dest))

    def remove_from_export_list(self, path, option, dest):
        """
        Removes the export from the export list
        """
        self.__modified = True
        path = os.path.relpath(path, os.path.dirname(self.path))
        self.__exports[path].remove((option, dest))

    def remove_from_project_export_list(self, option, dest):
        """
        Removes the export from the project export list
        """
        self.__modified = True
        self.__project_exports.remove((option, dest))

    def get_register_set(self):
        """
        Returns the register databases (XML files) referenced by the project
        file.
        """
        base = os.path.dirname(self.path)
        return [os.path.normpath(os.path.join(base, i))
                for i in self.__filelist]

    def get_grouping_list(self):
        """
        Returns a list of named tuples (GroupData) that defines the groups.
        The group contents are found by indexing using the Group name
        (GroupData.name) into the group map.
        """
        return self.__groupings

    def set_grouping_list(self, glist):
        """
        Sets the grouping list
        """
        self.__groupings = glist

    def set_grouping(self, index, name, start, hdl, repeat, repeat_offset):
        """
        Modifies an existing grouping.
        """
        self.__modified = True
        self.__groupings[index] = GroupData(name, start, hdl,
                                            repeat, repeat_offset)

    def add_to_grouping_list(self, group_data):
        """
        Adds a new grouping to the grouping list
        """
        self.__modified = True
        self.__groupings.append(group_data)

    def _add_to_grouping_list(self, name, start, hdl, repeat, repeat_offset):
        """
        Adds a new grouping to the grouping list
        """
        self.__modified = True
        self.__groupings.append(GroupData(name, start, hdl,
                                          repeat, repeat_offset))

    def remove_group_from_grouping_list(self, grp):
        """
        Removes a grouping from the grouping list
        """
        self.__modified = True
        self.__groupings.remove(grp)

    def get_address_maps(self):
        """
        Returns a tuple of the existing address maps
        """
        return tuple(self.__addr_map_list)

    def get_address_map_groups(self, name):
        """
        Returns the address maps associated with the specified group.
        """
        return tuple(self.__addr_map_grps.get(name, []))

    def change_address_map_name(self, old_name, new_name):
        """
        Changes the name of an address map
        """
        for (i, addrmap) in enumerate(self.__addr_map_list):
            if addrmap.name != old_name:
                continue
            old_data = self.__addr_map_list[i]
            self.__addr_map_list[i] = AddrMapData(new_name,
                                                  old_data.base,
                                                  old_data.width,
                                                  old_data.fixed)
            self.__addr_map_grps[new_name] = self.__addr_map_grps[old_name]
            del self.__addr_map_grps[old_name]
            self.__modified = True
            return

    def add_address_map_group(self, name, group_name):
        """
        Adds an address map to a group if it does not already exist
        """
        if group_name not in self.__addr_map_grps[name]:
            self.__addr_map_grps[name].append(group_name)
            return True
        else:
            return False

    def remove_address_map_group(self, name, group_name):
        """
        Removes an address map from a group
        """
        for (i, group_name) in self.__addr_map_grps[name]:
            if group_name == name:
                del self.__addr_map_grps[name][i]
                return

    def get_address_base(self, name):
        """
        Returns the base address  of the address map
        """
        for data in self.__addr_map_list:
            if name == data.name:
                return data.base
        return None

    def get_address_fixed(self, name):
        """
        Indicates if the specified address map is at a fixed location
        """
        for data in self.__addr_map_list:
            if name == data.name:
                return data.fixed
        return None

    def get_address_width(self, name):
        """
        Returns the width of the address group
        """
        for data in self.__addr_map_list:
            if name == data.name:
                return data.width
        return None

    def set_address_map(self, name, base, width, fixed):
        """
        Sets the specififed address map
        """
        self.__modified = True
        new_data = AddrMapData(name, base, width, fixed)
        for i, data in enumerate(self.__addr_map_list):
            if data.name == name:
                self.__addr_map_list[i] = new_data
                return
        self.__addr_map_list.append(new_data)
        self.__addr_map_grps[name] = []

    def remove_address_map(self, name):
        """
        Removes the address map
        """
        self.__modified = True
        for i, data in enumerate(self.__addr_map_list):
            if data.name == name:
                del self.__addr_map_list[i]
                if data.name in self.__addr_map_grps:
                    del self.__addr_map_grps[data.name]

    @property
    def files(self):
        return tuple(self.__filelist)

    @property
    def modified(self):
        """
        Sets the modified flag
        """
        return self.__modified

    @modified.setter
    def modified(self, value):
        """
        Clears the modified flag
        """
        self.__modified = bool(value)
