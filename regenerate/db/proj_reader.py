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
from regenerate.db.group_data import GroupData
from regenerate.db.group_inst_data import GroupInstData


class ProjectReader(object):
    """
    RegProject is the container object for a regenerate project. The project
    consists of several different types. General project information (name,
    company_name, etc.), the list of register sets, groupings of instances,
    and exports (register set and entire project exports), and address maps.
    """

    def __init__(self, project):
        self._prj = project
        self._current_group = None

    def open(self, name):
        """Opens and reads an XML file"""
        self.path = name

        with open(name, "rb") as ofile:
            parser = xml.parsers.expat.ParserCreate()
            parser.StartElementHandler = self.startElement
            parser.EndElementHandler = self.endElement
            parser.CharacterDataHandler = self.characters
            parser.ParseFile(ofile)
        self._prj.modified = False

    def startElement(self, tag, attrs):  # pylint: disable=invalid-name
        """
        Called every time an XML element begins
        """
        self.__token_list = []
        mname = 'start_' + tag
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(attrs)

    def endElement(self, tag):  # pylint: disable=invalid-name
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

    def start_project(self, attrs):
        """Called when a project tag is found"""
        self._prj.name = attrs['name']
        self._prj.short_name = attrs.get('short_name', '')
        self._prj.company_name = attrs.get('company_name', '')

    def start_registerset(self, attrs):
        """Called when a registerset tag is found"""
        self._current = attrs['name']
        self._prj.append_register_set_to_list(self._current)

    def start_export(self, attrs):
        """Called when an export tag is found"""
        path = attrs['path']
        option = attrs['option']
        self._prj.append_to_export_list(path, option, self._current)

    def start_group_export(self, attrs):
        """Called when an group_export tag is found"""
        dest = attrs['dest']
        option = attrs['option']
        self._prj.append_to_group_export_list(self._current_group.name,
                                              dest, option)

    def start_project_export(self, attrs):
        """Called when a project_export tag is found"""
        self._prj.append_to_project_export_list(attrs['option'], attrs['path'])

    def start_grouping(self, attrs):
        """Called when a grouping tag is found"""
        repeat_offset = int(attrs.get('repeat_offset', 0x10000))
        self._current_group = GroupData(
            attrs['name'],
            int(attrs['start'], 16),
            attrs.get('hdl', ""),
            int(attrs.get('repeat', 1)),
            repeat_offset,
            attrs.get('title', "")
        )
        self._prj.add_to_grouping_list(self._current_group)

    def start_map(self, attrs):
        """Called when a map tag is found"""
        sname = attrs['set']

        data = GroupInstData(
            sname,
            attrs.get('inst', sname),
            int(attrs['offset'], 16),
            int(attrs['repeat']),
            int(attrs['repeat_offset']),
            attrs.get("hdl", ""),
            int(attrs.get("no_uvm", "0")),
            int(attrs.get("no_decode", "0")),
            int(attrs.get("array", "0")),
            int(attrs.get("single_decode", "0"))
        )
        self._current_group.register_sets.append(data)

    def start_address_map(self, attrs):
        """Called when an address tag is found"""
        name = attrs['name']
        base = int(attrs.get('base', 0), 16)
        width = int(attrs.get('width', 4))
        fixed = int(attrs.get('fixed', 1))
        uvm = int(attrs.get('no_uvm', 0))
        self._prj.set_address_map(name, base, width, fixed, uvm)
        self._current_map = attrs['name']
        self.current_map_group = None

    def end_documentation(self, text):
        """
        Called when the documentation XML tag is encountered. Assigns the
        current text string to the documentation variable
        """
        self._prj.documentation = text

    def end_overview(self, text):
        """
        Called when the overview XML tag is encountered. Assigns the
        current text string to the current group's docs variable
        """
        if self._current_group:
            self._current_group.docs = text

    def start_map_group(self, attrs):
        self.current_map_group = attrs.get('name')
        self._prj.add_address_map_group(self._current_map,
                                        self.current_map_group)

    def end_map_group(self, text):
        """
        Called when the map_group XML tag is encountered. Assigns the
        current text string to the current group's docs variable
        """
        if self.current_map_group is None:
            self._prj.add_address_map_group(self._current_map, text)

    def start_access(self, attrs):
        self.current_access = int(attrs.get('type', "0"))

    def end_access(self, text):
        self._prj.set_access(
            self._current_map, self.current_map_group,
            text, self.current_access
        )
