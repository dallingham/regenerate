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
Instance List and Model
"""

from typing import Callable, Optional, Tuple
import re
from gi.repository import Gtk, GObject
from regenerate.db import LOGGER, BlockInst, RegProject

from .columns import EditableColumn, ReadOnlyColumn
from .enums import InstCol


class InstMdl(Gtk.TreeStore):
    """
    Provides the list of instances for the module. Instances consist of the
    symbolic ID name and the base address.
    """

    def __init__(self, project: RegProject):

        super().__init__(str, str, str, GObject.TYPE_UINT64, str, str, object)

        self.callback = self.__null_callback
        self.project = project

    def __null_callback(self) -> None:
        """Does nothing, should be overridden"""
        return

    def change_hdl(self, path: str, text: str) -> None:
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        node = self.get_iter(path)
        self.set_value(node, InstCol.HDL, text)
        self.callback()
        obj = self.get_value(node, InstCol.OBJ)
        if obj:
            obj.hdl_path = text

    def change_base(self, path: str, text: str) -> None:
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """

        node = self.get_iter(path)
        try:
            self.set_value(node, InstCol.SORT, int(text, 0))
            self.set_value(node, InstCol.BASE, f"0x{int(text, 0):08x}")
            self.callback()
        except ValueError:
            LOGGER.warning('Illegal base address: "%s"', text)

        obj = self.get_value(node, InstCol.OBJ)
        if obj:
            obj.address_base = int(text, 16)
        self.callback()

    def change_repeat(self, path: str, text: str) -> None:
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """
        node = self.get_iter(path)
        try:
            value = int(text)
            self.set_value(node, InstCol.RPT, text)
            self.callback()
        except ValueError:
            LOGGER.warning(
                '"%s" is not a valid repeat count. '
                "The repeat count must be an integer equal or greater than 1.",
                text,
            )
            return

        if value < 1:
            LOGGER.warning(
                '"%s" is not a valid repeat count. '
                "The repeat count must be an integer equal or greater than 1.",
                text,
            )
            return

        obj = self.get_value(node, InstCol.OBJ)
        if obj:
            obj.repeat = int(text)

    def add_instance(self, block_name: str, new_inst: BlockInst) -> None:
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        row = build_row_data(
            block_name,
            new_inst.name,
            new_inst.address_base,
            new_inst.repeat,
            new_inst.hdl_path,
            new_inst,
        )

        self.append(None, row=row)
        self.callback()


class InstanceList:
    """Instance list"""

    def __init__(self, obj: Gtk.TreeView, callback: Callable):
        self.__obj = obj
        self.__project: Optional[RegProject] = None
        self.__model: Optional[InstMdl] = None
        self.__build_instance_table()
        self.__obj.set_sensitive(False)
        self.modified_callback = callback
        self.need_subsystem = True
        self.need_regset = True

    def set_project(self, project: RegProject) -> None:
        """Set the project object for the instance list"""

        self.__project = project
        self.__obj.set_sensitive(True)
        self.populate()

    def set_model(self, model: InstMdl) -> None:
        """Set the model object for the instance list"""

        self.__obj.set_model(model)
        self.__model = model
        self.__model.callback = self.modified_callback

    def update(self) -> None:
        "updates the rows of the model from the items associated them"

        if self.__project and self.__model:
            for row in self.__model:
                item = row[InstCol.OBJ]
                row[InstCol.ID] = self.__project.blocks[item.blkid].name
                row[InstCol.INST] = item.name
                row[InstCol.BASE] = f"0x{item.address_base:x}"
                row[InstCol.SORT] = item.address_base
                row[InstCol.RPT] = f"{item.repeat}"
                row[InstCol.HDL] = item.hdl_path

    def get_selected_instance(self) -> Tuple[InstMdl, Gtk.TreeIter]:
        """Get the selected instance"""

        return self.__obj.get_selection().get_selected()

    def populate(self) -> None:
        """Fill the list from the project"""

        if self.__project is None or self.__model is None:
            return

        block_insts = sorted(
            self.__project.block_insts, key=lambda x: x.address_base
        )

        self.__model.clear()
        for blk_inst in block_insts:
            block = self.__project.blocks[blk_inst.blkid]
            self.need_subsystem = False
            self.__model.append(
                None,
                row=build_row_data(
                    blk_inst.name,
                    block.name,
                    blk_inst.address_base,
                    blk_inst.repeat,
                    blk_inst.hdl_path,
                    blk_inst,
                ),
            )

    def __build_instance_table(self) -> None:
        """Build the table, adding the columns"""

        column = EditableColumn(
            "Block Instance", self.instance_inst_changed, InstCol.INST
        )
        column.set_sort_column_id(InstCol.INST)
        column.set_min_width(200)
        column.set_resizable(True)
        self.__obj.append_column(column)

        column = ReadOnlyColumn(
            "Block Name",
            InstCol.ID,
        )
        column.set_sort_column_id(InstCol.ID)
        column.set_min_width(150)
        column.set_resizable(True)
        self.__obj.append_column(column)

        column = EditableColumn(
            "Address base", self.instance_base_changed, InstCol.BASE, True
        )
        column.set_sort_column_id(InstCol.SORT)
        column.set_min_width(150)
        column.set_resizable(True)
        self.__obj.append_column(column)

        column = EditableColumn(
            "Repeat", self.instance_repeat_changed, InstCol.RPT, True
        )
        column.set_min_width(125)
        column.set_resizable(True)
        self.__obj.append_column(column)

        column = EditableColumn(
            "HDL Path", self.instance_hdl_changed, InstCol.HDL
        )
        column.set_min_width(250)
        column.set_sort_column_id(InstCol.HDL)
        column.set_resizable(True)
        self.__obj.append_column(column)

    def inst_changed(self, attr: str, path: str, text: str) -> None:
        """Called with the instance name changed"""

        getattr(self.__model, attr)(path, text)

    def instance_inst_changed(
        self, _cell: Gtk.CellRendererText, path: str, text: str, _col: InstCol
    ) -> None:
        """
        Updates the data model when the text value is changed in the model.
        """

        if self.__model is None:
            return

        node = self.__model.get_iter(path)
        if text == self.__model.get_value(node, InstCol.INST):
            return

        items = {row[InstCol.INST] for row in self.__model}

        if text in items:
            LOGGER.warning(
                '"%s" has already been used as a block instance name', text
            )
            return

        if re.match(r"^[A-Za-z_][A-Za-z0-9_]\[.*\]+$", text):
            LOGGER.warning(
                "Array notation not valid. "
                "Use the repeat/repeat count to create arrays"
            )
            return

        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]+$", text):
            LOGGER.warning("'%s' is not a valid block instance name", text)
            return

        self.__model.set_value(node, InstCol.INST, text)

        obj = self.__model.get_value(node, InstCol.OBJ)
        obj.name = text

        self.modified_callback()

    def instance_base_changed(
        self, _cell: Gtk.CellRendererText, path: str, text: str, _col: InstCol
    ) -> None:
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_base", path, text)
        self.modified_callback()

    def instance_format_changed(
        self, _cell: Gtk.CellRendererText, path: str, text: str, _col: InstCol
    ) -> None:
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_format", path, text)
        self.modified_callback()

    def instance_hdl_changed(
        self, _cell: Gtk.CellRendererText, path: str, text: str, _col: InstCol
    ) -> None:
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_hdl", path, text.strip())
        self.modified_callback()

    def instance_repeat_changed(
        self, _cell: Gtk.CellRendererText, path: str, text: str, _col: InstCol
    ) -> None:
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_repeat", path, text)
        self.modified_callback()


def build_row_data(
    inst_name: str,
    blk_name: str,
    offset: int,
    rpt: int,
    hdl: str,
    obj: BlockInst,
) -> Tuple[str, str, str, int, str, str, BlockInst]:
    """Build row data from the data"""

    return (
        blk_name,
        inst_name,
        f"0x{offset:08x}",
        offset,
        f"{rpt:d}",
        hdl,
        obj,
    )
