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


class GroupData(object):
    """Basic group information"""
    def __init__(self, name="", base=0, hdl="", repeat=1,
                 repeat_offset=0x10000):
        self.name = name
        self.base = base
        self.hdl = hdl
        self.repeat = repeat
        self.repeat_offset = repeat_offset
        self.register_sets = []
        self.docs = ""


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
        """
        Saves the data to an XML file.
        """
        ofile = open(self.path, "w")
        ofile.write('<?xml version="1.0"?>\n')
        ofile.write('<project name="%s" short_name="%s" company_name="%s">\n' %
                    (self.name, self.short_name, self.company_name))

        if self.documentation:
            ofile.write('  <documentation>%s</documentation>\n' %
                        escape(self.documentation))

        if self.__addr_map_list:
            self._print_address_maps(ofile)

        if self.__groupings:
            self._print_groupings(ofile)

        for fname in self.__filelist:
            if self.__exports[fname]:
                ofile.write('  <registerset name="%s">\n' % fname)
                for pair in self.__exports[fname]:
                    ofile.write('    <export option="%s" path="%s"/>\n' % pair)
                ofile.write('  </registerset>\n')
            else:
                ofile.write('  <registerset name="%s"/>\n' % fname)

        for pair in self.__project_exports:
            ofile.write('  <project_export option="%s" path="%s"/>\n' % pair)

        ofile.write('</project>\n')
        self.__modified = False

    def _print_address_maps(self, ofile):
        """
        Prints the address map list to the XML file
        """
        ofile.write('  <address_maps>\n')
        for data in self.__addr_map_list:
            groups = self.__addr_map_grps.get(data.name, [])
            ofile.write('    <address_map name="%s" base="%x" ' %
                        (data.name, data.base))
            ofile.write('fixed="%d" width="%d"' %
                        (data.fixed, data.width))
            if groups:
                ofile.write('>\n')
                for group in groups:
                    ofile.write('      <map_group>%s</map_group>\n' % group)
                ofile.write('    </address_map>\n')
            else:
                ofile.write('/>\n')
        ofile.write('  </address_maps>\n')

    def _print_groupings(self, ofile):
        """
        Prints the grouping list
        """
        ofile.write('  <groupings>\n')
        for group in self.__groupings:
            ofile.write('    <grouping name="%s" start="%x" hdl="%s"' %
                        (group.name, group.base, group.hdl))
            ofile.write(' repeat="%d" repeat_offset="%d">\n' %
                        (group.repeat, group.repeat_offset))
            if group.docs:
                ofile.write("<overview>%s</overview>" %
                            cleanup(group.docs))
            for item in group.register_sets:
                ofile.write('      <map set="%s" inst="%s" offset="%x" ' %
                            (item.set, item.inst, item.offset))
                ofile.write('repeat="%s" repeat_offset="%s"' %
                            (item.repeat, item.repeat_offset))
                if item.hdl:
                    ofile.write(' hdl="%s"' % item.hdl)
                if item.no_uvm:
                    ofile.write(' no_uvm="%s"' % int(item.no_uvm))
                if item.format:
                    ofile.write(' format="%s"' % item.format)
                ofile.write("/>\n")
            ofile.write('    </grouping>\n')
        ofile.write('  </groupings>\n')

    def open(self, name):
        """
        Opens and reads an XML file
        """
        self.__modified = False
        self.path = name
        ofile = open(self.path)
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.startElement
        parser.EndElementHandler = self.endElement
        parser.CharacterDataHandler = self.characters
        parser.ParseFile(ofile)
        ofile.close()

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
        self.__current = os.path.relpath(path, os.path.dirname(self.path))
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

    def get_export_list(self, path):
        """
        Converts the export list to be relative to the passed path.
        """
        path = os.path.relpath(path, os.path.dirname(self.path))
        return self.__exports.get(path, [])

    def get_project_export_list(self):
        return self.__project_exports

    def add_to_export_list(self, path, option, dest):
        self.__modified = True
        path = os.path.relpath(path, os.path.dirname(self.path))
        dest = os.path.relpath(dest, os.path.dirname(self.path))
        self.__exports[path].append((option, dest))

    def add_to_project_export_list(self, option, dest):
        self.__modified = True
        dest = os.path.relpath(dest, os.path.dirname(self.path))
        self.__project_exports.append((option, dest))

    def remove_from_export_list(self, path, option, dest):
        self.__modified = True
        path = os.path.relpath(path, os.path.dirname(self.path))
        self.__exports[path].remove((option, dest))

    def remove_from_project_export_list(self, option, dest):
        self.__modified = True
        self.__project_exports.remove((option, dest))

    def get_register_set(self):
        base = os.path.dirname(self.path)
        return [os.path.normpath(os.path.join(base, i))
                for i in self.__filelist]

    def get_register_paths(self):
        return self.__filelist

    def get_grouping_list(self):
        """
        Returns a list of named tuples (GroupData) that defines the groups.
        The group contents are found by indexing using the Group name
        (GroupData.name) into the group map.
        """
        return self.__groupings

    def set_grouping_list(self, glist):
        self.__groupings = glist

    def set_grouping(self, index, name, start, hdl, repeat, repeat_offset):
        self.__modified = True
        self.__groupings[index] = GroupData(name, start, hdl,
                                            repeat, repeat_offset)

    def add_to_grouping_list(self, name, start, hdl, repeat, repeat_offset):
        self.__modified = True
        self.__groupings.append(GroupData(name, start, hdl,
                                          repeat, repeat_offset))

    def remove_from_grouping_list(self, name, start, hdl, repeat,
                                  repeat_offset):
        self.__modified = True
        self.__groupings.remove(GroupData(name, start, hdl,
                                          repeat, repeat_offset))

    def remove_group_from_grouping_list(self, grp):
        self.__modified = True
        self.__groupings.remove(grp)

    def get_address_maps(self):
        return self.__addr_map_list

    def get_address_map_groups(self, name):
        return self.__addr_map_grps.get(name, [])

    def change_address_map_name(self, old_name, new_name):
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
        if group_name not in self.__addr_map_grps[name]:
            self.__addr_map_grps[name].append(group_name)
            return True
        else:
            return False

    def remove_address_map_group(self, name, group_name):
        for (i, group_name) in self.__addr_map_grps[name]:
            if group_name == name:
                del self.__addr_map_grps[name][i]
                return

    def get_address_base(self, name):
        for data in self.__addr_map_list:
            if name == data.name:
                return data.base
        return None

    def get_address_fixed(self, name):
        for data in self.__addr_map_list:
            if name == data.name:
                return data.fixed
        return None

    def get_address_width(self, name):
        for data in self.__addr_map_list:
            if name == data.name:
                return data.width
        return None

    def set_address_map(self, name, base, width, fixed):
        self.__modified = True
        new_data = AddrMapData(name, base, width, fixed)
        for (i, data) in enumerate(self.__addr_map_list):
            if (data.name == name):
                self.__addr_map_list[i] = new_data
                return
        self.__addr_map_list.append(new_data)
        self.__addr_map_grps[name] = []

    def remove_address_map(self, name):
        self.__modified = True
        for (i, data) in enumerate(self.__addr_map_list):
            if (data.name == name):
                del self.__addr_map_list[i]
                if data.name in self.__addr_map_grps:
                    del self.__addr_map_grps[data.name]

    def startElement(self, tag, attrs):
        """
        Called every time an XML element begins
        """
        self.__token_list = []
        mname = 'start_' + tag
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(attrs)

    def endElement(self, tag):
        """
        Called every time an XML element end
        """
        text = ''.join(self.__token_list)
        mname = 'end_' + tag
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(text)

    def characters(self, data):
        """
        Called with segments of the character data. This is not predictable
        in how it is called, so we must collect the information for assembly
        later.
        """
        self.__token_list.append(data)

    def end_documentation(self, text):
        self.documentation = text

    def start_project(self, attrs):
        self.name = attrs['name']
        self.short_name = attrs.get('short_name', '')
        self.company_name = attrs.get('company_name', '')

    def start_registerset(self, attrs):
        self.__filelist.append(attrs['name'])
        self.__current = attrs['name']
        self.__exports[self.__current] = []

    def start_export(self, attrs):
        value = (attrs['option'], attrs['path'])
        self.__exports[self.__current].append(value)

    def start_project_export(self, attrs):
        value = (attrs['option'], attrs['path'])
        self.__project_exports.append(value)

    def start_grouping(self, attrs):
        self._current_group = GroupData(attrs['name'],
                                        int(attrs['start'], 16),
                                        attrs.get('hdl', ""),
                                        int(attrs.get('repeat', 1)),
                                        int(attrs.get('repeat_offset',
                                                      0x10000)))
        self.__groupings.append(self._current_group)

    def start_map(self, attrs):
        sname = attrs['set']
        data = GroupMapData(sname,
                            attrs.get('inst', sname),
                            int(attrs['offset'], 16),
                            int(attrs['repeat']),
                            int(attrs['repeat_offset']),
                            attrs.get("format", ""),
                            attrs.get("hdl", ""),
                            int(attrs.get("no_uvm", "0")))
        self._current_group.register_sets.append(data)

    def start_address_map(self, attrs):
        data = AddrMapData(attrs['name'],
                           int(attrs.get('base', 0), 16),
                           int(attrs.get('width', 4)),
                           int(attrs.get('fixed', 1)))
        self.__addr_map_list.append(data)
        self.__addr_map_grps[data.name] = []
        self.__current_map = data.name

    def end_overview(self, text):
        self._current_group.docs = text

    def end_map_group(self, text):
        self.__addr_map_grps[self.__current_map].append(text)

    def set_modified(self):
        self.__modified = True

    def clear_modified(self):
        self.__modified = False

    def get_modified(self):
        return self.__modified

    def is_not_saved(self):
        if self.__modified:
            return True
