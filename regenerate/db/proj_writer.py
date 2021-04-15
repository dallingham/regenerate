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

from xml.sax.saxutils import escape
from .textutils import clean_text


class ProjectWriter:
    """
    ProjectWriter writes the data in the project to the XML file.
    """

    def __init__(self, project):
        self._prj = project

    def save(self, path):
        """Saves the data to an XML file."""

        with open(path, "w") as ofile:
            ofile.write('<?xml version="1.0"?>\n')
            ofile.write(
                '<project name="%s" short_name="%s" company_name="%s">\n'
                % (
                    self._prj.name,
                    self._prj.short_name,
                    self._prj.company_name,
                )
            )

            if self._prj.documentation:
                ofile.write(
                    "  <documentation>%s</documentation>\n"
                    % escape(self._prj.documentation)
                )

            if self._prj.get_address_maps:
                self._print_address_maps(ofile)

            if self._prj.get_grouping_list:
                self._print_groupings(ofile)

            if self._prj.parameters.get():
                self._print_parameter_list(ofile)

            for fname in self._prj.files:
                if self._prj.get_exports(fname):
                    ofile.write('  <registerset name="%s">\n' % fname)
                    for pair in self._prj.get_exports(fname):
                        ofile.write(
                            '    <export option="%s" path="%s"/>\n' % pair
                        )
                    ofile.write("  </registerset>\n")
                else:
                    ofile.write('  <registerset name="%s"/>\n' % fname)

            for pair in self._prj.get_project_exports():
                ofile.write(
                    '  <project_export option="%s" path="%s"/>\n' % pair
                )

            ofile.write("</project>\n")
            self._prj.modified = True

    def _print_parameter_list(self, ofile):
        plist = self._prj.parameters.get()
        if plist:
            ofile.write("  <parameters>\n")
            for (name, value) in plist:
                ofile.write(
                    '    <parameter name="{}" value="{}"/>\n'.format(
                        name, value
                    )
                )
            ofile.write("  </parameters>\n")

    def _print_address_maps(self, ofile):
        """
        Prints the address map list to the XML file
        """
        ofile.write("  <address_maps>\n")
        for data in self._prj.get_address_maps():
            groups = self._prj.get_address_map_groups(data.name)
            ofile.write(
                '    <address_map name="%s" base="%x" '
                % (data.name, data.base)
            )
            ofile.write(
                'fixed="%d" width="%d" no_uvm="%d"'
                % (data.fixed, data.width, data.uvm)
            )
            if groups:
                ofile.write(">\n")

                for group in groups:
                    access_list = self._prj.get_access_items(data.name, group)
                    access_list = [val for val in access_list if val[1]]
                    if access_list:
                        ofile.write('      <map_group name="%s">\n' % group)
                        for inst, val in access_list:
                            ofile.write(
                                '        <access type="%d">%s</access>\n'
                                % (val, inst)
                            )
                        ofile.write("      </map_group>\n")
                    else:
                        ofile.write('      <map_group name="%s"/>\n' % group)
                ofile.write("    </address_map>\n")
            else:
                ofile.write("/>\n")
        ofile.write("  </address_maps>\n")

    def _print_groupings(self, ofile):
        """
        Prints the grouping list
        """
        ofile.write("  <groupings>\n")
        for group in self._prj.get_grouping_list():
            ofile.write(
                '    <grouping name="%s" start="%x" hdl="%s"'
                % (group.name, group.base, group.hdl)
            )
            ofile.write(' title="%s"' % escape(clean_text(group.title)))
            ofile.write(
                ' repeat="%d" repeat_offset="%d">\n'
                % (group.repeat, group.repeat_offset)
            )
            if group.docs:
                doc = escape(clean_text(group.docs))
                ofile.write("<overview>%s</overview>\n" % doc)
            for item in group.register_sets:
                ofile.write(
                    '      <map set="%s" inst="%s" offset="%x" '
                    % (item.set, item.inst, item.offset)
                )
                ofile.write(
                    'repeat="%s" repeat_offset="%s"'
                    % (item.repeat, item.repeat_offset)
                )
                if item.hdl:
                    ofile.write(' hdl="%s"' % item.hdl)
                if item.no_uvm:
                    ofile.write(' no_uvm="%s"' % int(item.no_uvm))
                if item.no_decode:
                    ofile.write(' no_decode="%s"' % int(item.no_decode))
                if item.single_decode:
                    ofile.write(
                        ' single_decode="%s"' % int(item.single_decode)
                    )
                if item.array:
                    ofile.write(' array="%s"' % int(item.array))
                ofile.write("/>\n")
            for item in self._prj.get_group_exports(group.name):
                ofile.write(
                    '      <group_export dest="%s" option="%s"/>' % item
                )
            ofile.write("\n    </grouping>\n")
        ofile.write("  </groupings>\n")
