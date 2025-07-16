import json

from GcodeTools.inkscape import inkscape_compiler


def export_document(input_doc: list[dict]) :
    return '\n'.join((json.dumps(line) for line in input_doc))


