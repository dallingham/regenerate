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
import os.path


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
        self.__filelist = []
        self.__groupings = []
        self.__grouping_excludes = {}
        self.__exports = {}
        self.__project_exports = []
        self.__token_list = []
        self.__modified = False
        self.__current = ""
        self.__address_maps = {}
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

        if self.__address_maps:
            ofile.write('  <address_maps>\n')
            for key in self.__address_maps:
                ofile.write('    <address_map name="%s" base="%x"/>\n' %
                            (key, self.__address_maps[key]))
            ofile.write('  </address_maps>\n')

        if self.__groupings:
            ofile.write('  <groupings>\n')
            for grouping in self.__groupings:
                if self.__grouping_excludes[grouping[0]]:
                    ofile.write('    <grouping name="%s" start="%x" end="%x">\n' %
                                grouping)
                    for item in self.__grouping_excludes[grouping[0]]:
                        ofile.write('      <group_exclude name="%s"/>\n' % item)
                    ofile.write('    </grouping>\n')
                else:
                    ofile.write('    <grouping name="%s" start="%x" end="%x"/>\n' %
                                grouping)
            ofile.write('  </groupings>\n')

        for fname in self.__filelist:
            if self.__exports[fname]:
                ofile.write('  <registerset name="%s">\n' % fname)
                for pair in self.__exports[fname]:
                    ofile.write('    <export option="%s" path="%s"/>\n' % pair)
                ofile.write('  </registerset>\n')
            else:
                ofile.write('  <registerset name="%s"/>\n' % fname)

        if self.__project_exports:
            for pair in self.__project_exports:
                ofile.write('  <project_export option="%s" path="%s"/>\n' % pair)

        ofile.write('</project>\n')
        self.__modified = False

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
            print str(msg)
            print path2remove
            print self.__filelist

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
        return self.__groupings

    def get_excludes(self, name):
        return self.__grouping_excludes.get(name, [])

    def set_grouping(self, index, name, start, end):
        self.__modified = True
        self.__groupings[index] = (name, start, end)

    def add_to_grouping_list(self, name, start, end):
        self.__modified = True
        self.__groupings.append((name, start, end))

    def remove_from_grouping_list(self, name, start, end):
        self.__modified = True
        self.__groupings.remove((name, start, end))

    def get_address_maps(self):
        return self.__address_maps

    def get_address_base(self, name):
        return self.__address_maps[name]

    def set_address_map(self, name, base):
        self.__modified = True
        self.__address_maps[name] = base

    def remove_address_map(self, name):
        self.__modified = True
        del self.__address_maps[name]

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
        self.__groupings.append((attrs['name'], int(attrs['start'],16),
                                 int(attrs['end'],16)))
        self.__grouping_excludes[attrs['name']] = []

    def start_group_exclude(self, attrs):
        self.__grouping_excludes[self.__groupings[-1][0]].append(attrs['name'])

    def start_address_map(self, attrs):
        self.__address_maps[attrs['name']] = int(attrs['base'],16)

    def is_not_saved(self):
        if self.__modified:
            return True
