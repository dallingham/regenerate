import gtk

DEF_DIALOG_FLAGS = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
DEF_DIALOG_BUTTONS = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)


class GroupOptions (gtk.Dialog):

    def __init__(self, instance, parent, modified, width=600, height=260):

        gtk.Dialog.__init__(
            self,
            title="Instance Options (%s)" % instance.inst,
            parent=parent,
            flags=DEF_DIALOG_FLAGS,
            buttons=DEF_DIALOG_BUTTONS
        )
        self.instance = instance
        self.set_size_request(width, height)
        self.build_window(instance.inst)
        self.set_transient_for(parent)

        changed = False
        response = self.run()
        if response == gtk. RESPONSE_ACCEPT:
            if self.val_array != self.instance.array:
                self.instance.array = self.val_array
                changed = True
            if self.val_no_decode != self.instance.no_decode:
                self.instance.no_decode = self.val_no_decode
                changed = True
            if self.val_no_uvm != self.instance.no_uvm:
                self.instance.no_uvm = self.val_no_uvm
                changed = True
            if self.val_single_decode != self.instance.single_decode:
                self.instance.single_decode = self.val_single_decode
                changed = True
        if changed:
            modified()
        self.hide()
        self.destroy()

    def build_window(self, title):

        area = self.get_content_area()
        title_label = gtk.Label()
        title_label.set_xalign(0.5)
        title_label.set_markup("<b>%s</b>" % title)

        table = gtk.Table(4, 5)
        table.set_row_spacings(6)
        table.set_col_spacings(6)

        uvm_exclude = gtk.CheckButton(
            "Exclude the instance from the UVM register package")
        uvm_exclude.set_active(self.instance.no_uvm)
        self.val_no_uvm = self.instance.no_uvm

        table.attach(
            uvm_exclude,
            1,
            3,
            1,
            2,
            xoptions=gtk.FILL,
            yoptions=gtk.FILL
        )

        decode_exclude = gtk.CheckButton(
            "Exclude from register decode"
        )
        decode_exclude.set_active(self.instance.no_decode)
        self.val_no_decode = self.instance.no_decode

        table.attach(
            decode_exclude,
            1,
            3,
            2,
            3,
            xoptions=gtk.FILL,
            yoptions=gtk.FILL
        )

        force_arrays = gtk.CheckButton(
            "Force array notation even for scalar instances"
        )
        force_arrays.set_active(self.instance.array)
        self.val_array = self.instance.array

        table.attach(
            force_arrays,
            1,
            3,
            3,
            4,
            xoptions=gtk.FILL,
            yoptions=gtk.FILL
        )

        single_decode = gtk.CheckButton(
            "Use a single decode for arrays"
        )
        single_decode.set_active(self.instance.single_decode)
        self.val_single_decode = self.instance.single_decode

        table.attach(
            single_decode,
            1,
            3,
            4,
            5,
            xoptions=gtk.FILL,
            yoptions=gtk.FILL
        )

        box = gtk.VBox(spacing=6)
        box.pack_start(title_label, fill=True, expand=True, padding=12)
        box.pack_start(table, fill=True, expand=True, padding=12)
        area.add(box)

        self.show_all()

    def uvm_toggle(self, obj):
        self.val_no_uvm = obj.get_active()

    def decode_toggle(self, obj):
        self.val_no_decode = obj.get_active()

    def single_toggle(self, obj):
        self.val_single_decode = obj.get_active()

    def arrays_toggle(self, obj):
        self.val_array = obj.get_active()
