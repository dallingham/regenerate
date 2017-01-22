
def clean_format_if_needed(obj):
    buf = obj.get_buffer()
    bounds = buf.get_selection_bounds()
    if bounds:
        old_text = buf.get_text(bounds[0], bounds[1])
        new_text = " ".join(old_text.replace("\n", " ").split())
        if old_text != new_text:
            buf.delete(bounds[0], bounds[1])
            buf.insert(bounds[0], new_text)
            return True
    return False
