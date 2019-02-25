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

from collections import namedtuple, defaultdict
import os.path
import xml.sax.saxutils
import regenerate.db

(MAP_FULL, MAP_RO, MAP_WO) = range(3)

AddrMapData = namedtuple(
    "AddrMapData",
    ["name", "base", "width", "fixed", "uvm"]
)


def nested_dict(depth, dict_type):
    if depth == 1:
        return defaultdict(dict_type)
    return defaultdict(lambda: nested_dict(depth-1, dict_type))


def cleanup(data):
    "Convert some unicode characters to standard ASCII"
    return xml.sax.saxutils.escape(regenerate.db.textutils.clean_text(data))


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
        self._filelist = []
        self._groupings = []
        self._addr_map_list = []
        self._addr_map_grps = {}
        self._exports = {}
        self._project_exports = []
        self._group_exports = {}
        self._token_list = []
        self._modified = False
        self.path = path
        self.access_map = nested_dict(3, int)
        if path:
            self.open(path)

    def save(self):
        writer = regenerate.db.ProjectWriter(self)
        writer.save(self.path)

    def open(self, name):
        """Opens and reads an XML file"""

        reader = regenerate.db.ProjectReader(self)
        self.path = name
        reader.open(name)

    def set_new_order(self, new_order):
        """Alters the order of the items in the files in the list."""
        self._modified = True
        htbl = {}
        for i in self._filelist:
            htbl[os.path.splitext(os.path.basename(i))[0]] = i
        self._filelist = [htbl[i] for i in new_order]

    def append_register_set_to_list(self, name):
        self._modified = True
        self._filelist.append(name)
        self._exports[name] = []

    def add_register_set(self, path, alter_path=True):
        """
        Adds a new register set to the project. Note that this only records
        the filename, and does not actually keep a reference to the RegisterDb.
        """
        self._modified = True
        path = os.path.relpath(path, os.path.dirname(self.path))
        self.append_register_set_to_list(path)

    def remove_register_set(self, path):
        """Removes the specified register set from the project."""
        self._modified = True
        try:
            path2remove = os.path.relpath(path, os.path.dirname(self.path))
            self._filelist.remove(path2remove)
        except ValueError as msg:
            regenerate.db.LOGGER.error(str(msg))

    def get_exports(self, path):
        """
        Converts the exports to be relative to the passed path. Returns a
        read-only tuple
        """
        return tuple(self._exports.get(path, []))

    def get_project_exports(self):
        """Returns the export project list, returns a read-only tuple"""
        return tuple(self._project_exports)

    def get_group_exports(self, name):
        """Returns the export group list, returns a read-only tuple"""
        return tuple(self._group_exports.get(name, []))

    def append_to_export_list(self, path, option, dest):
        """
        For internal use only.

        Adds an export to the export list. The exporter will only operation
        on the specified register database (XML file).

        path - path to the the register XML file. Converted to a relative path
        option - the chosen export option (exporter)
        dest - destination output name
        """
        self._modified = True
        self._exports[dest].append((option, path))

    def add_to_export_list(self, path, option, dest):
        """
        Adds an export to the export list. The exporter will only operation
        on the specified register database (XML file).

        path - path to the the register XML file. Converted to a relative path
        option - the chosen export option (exporter)
        dest - destination output name
        """
        self._modified = True
        path = os.path.relpath(path, os.path.dirname(self.path))
        dest = os.path.relpath(dest, os.path.dirname(self.path))
        self._exports[path].append((option, dest))

    def append_to_project_export_list(self, option, dest):
        """
        Adds a export to the project export list. Project exporters operation
        on the entire project, not just a specific register database (XML file)

        path - path to the the register XML file. Converted to a relative path
        option - the chosen export option (exporter)
        dest - destination output name
        """
        self._modified = True
        self._project_exports.append((option, dest))

    def append_to_group_export_list(self, group, option, dest):
        """
        Adds a export to the group export list. Group exporters operation
        on the entire group, not just a specific register database (XML file)

        path - path to the the register XML file. Converted to a relative path
        option - the chosen export option (exporter)
        dest - destination output name
        """
        self._modified = True
        self._group_exports[group].append((option, dest))

    def add_to_project_export_list(self, option, dest):
        """
        Adds a export to the project export list. Project exporters operation
        on the entire project, not just a specific register database (XML file)

        path - path to the the register XML file. Converted to a relative path
        option - the chosen export option (exporter)
        dest - destination output name
        """
        self._modified = True
        dest = os.path.relpath(dest, os.path.dirname(self.path))
        self._project_exports.append((option, dest))

    def add_to_group_export_list(self, group, option, dest):
        """
        Adds a export to the group export list. Group exporters operation
        on the entire group, not just a specific register database (XML file)

        path - path to the the register XML file. Converted to a relative path
        option - the chosen export option (exporter)
        dest - destination output name
        """
        self._modified = True
        dest = os.path.relpath(dest, os.path.dirname(self.path))
        self._group_exports[group].append((option, dest))

    def remove_from_export_list(self, path, option, dest):
        """Removes the export from the export list"""
        self._modified = True
        path = os.path.relpath(path, os.path.dirname(self.path))
        self._exports[path].remove((option, dest))

    def remove_from_project_export_list(self, option, dest):
        """Removes the export from the project export list"""
        self._modified = True
        self._project_exports.remove((option, dest))

    def remove_from_group_export_list(self, group, option, dest):
        """Removes the export from the group export list"""
        self._modified = True
        self._group_exports[group].remove((option, dest))

    def get_register_set(self):
        """
        Returns the register databases (XML files) referenced by the project
        file.
        """
        base = os.path.dirname(self.path)
        return [os.path.normpath(os.path.join(base, i))
                for i in self._filelist]

    def get_grouping_list(self):
        """
        Returns a list of named tuples (GroupData) that defines the groups.
        The group contents are found by indexing using the Group name
        (GroupData.name) into the group map.
        """
        return self._groupings

    def set_grouping_list(self, glist):
        """Sets the grouping list"""
        self._groupings = glist

    def set_grouping(self, index, name, start, hdl, repeat, repeat_offset):
        """Modifies an existing grouping."""
        self._modified = True
        self._groupings[index] = regenerate.db.GroupData(
            name, start, hdl, repeat, repeat_offset
        )

    def add_to_grouping_list(self, group_data):
        """Adds a new grouping to the grouping list"""
        self._modified = True
        self._group_exports[group_data.name] = []
        self._groupings.append(group_data)

    def _add_to_grouping_list(self, name, start, hdl, repeat, repeat_offset):
        """Adds a new grouping to the grouping list"""
        self._modified = True
        self._groupings.append(
            regenerate.db.GroupData(
                name, start, hdl, repeat, repeat_offset
            )
        )

    def remove_group_from_grouping_list(self, grp):
        """Removes a grouping from the grouping list"""
        self._modified = True
        self._groupings.remove(grp)

    def get_address_maps(self):
        """Returns a tuple of the existing address maps"""
        return tuple(self._addr_map_list)

    def get_address_map_groups(self, name):
        """Returns the address maps associated with the specified group."""
        return tuple(self._addr_map_grps.get(name, []))

    def get_address_maps_used_by_group(self, name):
        """Returns the address maps associated with the specified group."""
        used_in_uvm = set([m.name for m in self._addr_map_list if m.uvm == 0])

        return [key for key in self._addr_map_grps
                if key in used_in_uvm and name in self._addr_map_grps[key]]

    def change_address_map_name(self, old_name, new_name):
        """Changes the name of an address map"""
        for (i, addrmap) in enumerate(self._addr_map_list):
            if addrmap.name != old_name:
                continue
            old_data = self._addr_map_list[i]
            self._addr_map_list[i] = AddrMapData(
                new_name,
                old_data.base,
                old_data.width,
                old_data.fixed,
                old_data.uvm
            )
            self._addr_map_grps[new_name] = self._addr_map_grps[old_name]
            del self._addr_map_grps[old_name]
            self._modified = True
            return

    def add_address_map_group(self, name, group_name):
        """Adds an address map to a group if it does not already exist"""
        if group_name not in self._addr_map_grps[name]:
            self._addr_map_grps[name].append(group_name)
            return True
        return False

    def set_address_map_group_list(self, name, group_list):
        """Adds an address map to a group if it does not already exist"""
        self._addr_map_grps[name] = group_list

    def remove_address_map_group(self, name, group_name):
        """Removes an address map from a group"""
        for (i, group_name) in self._addr_map_grps[name]:
            if group_name == name:
                del self._addr_map_grps[name][i]
                return

    def get_address_base(self, name):
        """Returns the base address  of the address map"""
        return next((d.base for d in self._addr_map_list
                     if name == d.name), None)

    def get_address_fixed(self, name):
        """Indicates if the specified address map is at a fixed location"""
        return next((d.fixed for d in self._addr_map_list
                     if name == d.name), None)

    def get_address_uvm(self, name):
        """Indicates if the specified address map is at a fixed location"""
        return next((d.uvm for d in self._addr_map_list
                     if name == d.name), None)

    def get_address_width(self, name):
        """Returns the width of the address group"""
        for data in self._addr_map_list:
            if name == data.name:
                return data.width
        regenerate.db.LOGGER.error("Address map not found (%s)" % name)
        return None

    def set_access(self, map_name, group_name, block_name, access):
        self.access_map[map_name][group_name][block_name] = access

    def get_access_items(self, map_name, group_name):
        items = []
        for key in self.access_map[map_name][group_name]:
            items.append((key, self.access_map[map_name][group_name][key]))
        return items

    def get_access(self, map_name, group_name, block_name):
        try:
            return self.access_map[map_name][group_name][block_name]
        except:
            return 0

    def set_address_map(self, name, base, width, fixed, uvm):
        """Sets the specififed address map"""
        self._modified = True
        new_data = AddrMapData(name, base, width, fixed, uvm)
        for i, data in enumerate(self._addr_map_list):
            if data.name == name:
                self._addr_map_list[i] = new_data
                return
        self._addr_map_list.append(new_data)
        self._addr_map_grps[name] = []

    def remove_address_map(self, name):
        """Removes the address map"""
        self._modified = True
        for i, data in enumerate(self._addr_map_list):
            if data.name == name:
                del self._addr_map_list[i]
                if data.name in self._addr_map_grps:
                    del self._addr_map_grps[data.name]

    @property
    def files(self):
        return tuple(self._filelist)

    @property
    def modified(self):
        """Sets the modified flag"""
        return self._modified

    @modified.setter
    def modified(self, value):
        """Clears the modified flag"""
        self._modified = bool(value)

    def change_subsystem_name(self, old, cur):
        """
        Changes the name of a subsystem from 'old' to 'cur'.
        Searches through the access maps the group definitions
        to find the old reference, and replaces it with the new
        reference
        """

        # Search access map to find items to replace. We must
        # delete the old entry, and create a new entry. Since
        # we cannot delete in the middle of a search, we must save
        # the matches we found. After we identify them, we can
        # delete the items we found.

        to_delete = []
        for m in self.access_map:
            for subsys in self.access_map[m]:
                if subsys == old:
                    to_delete.append((m, old, cur))

        for (m, old, cur) in to_delete:
            self.access_map[m][cur] = self.access_map[m][old]
            del self.access_map[m][old]

        # Search groups for items to rename. Just change the name
        for g_data in self._groupings:
            if g_data.name == old:
                g_data.name = cur
        self._modified = True

    def change_instance_name(self, subsystem, old, cur):
        """
        Changes the register set instance name for a particular
        instance in the identified subsystem. Updates the access
        map and the groupings.
        """

        # Search access maps for items to rename. Search each
        # map, for instances of the specified subsystem, then
        # search for the instance name to be replaced in the
        # subsystem. Since the object is a tuple, and has to be
        # replaced instead of altered, we must store the items
        # to be changed, since we cannot alter the dictionary
        # as we search it.

        to_delete = []
        for m in self.access_map:
            for b in self.access_map[m][subsystem]:
                if b == old:
                    to_delete.append((m, subsystem, cur, old))

        for (m, s, cur, old) in to_delete:
            self.access_map[m][s][cur] = self.access_map[m][s][old]
            del self.access_map[m][s][old]

        # Search groups for items to rename
        for g_data in self._groupings:
            if g_data.name == subsystem:
                for gd in g_data.register_sets:
                    if gd.inst == old:
                        gd.inst = cur
        self._modified = True
