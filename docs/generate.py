import os
from urllib.parse import urljoin, urlencode, quote

import jinja2
import yaml


BASE_PATH = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_PATH, "templates")
TEMPLATE_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR))
GH_PATH = "https://github.com/pkucmus/EVA/tree/master/"

DEFAULT_PRINT_SETTINGS = {
    "layer_height": "0.3",
    "infill": "20%",
    "parimeters": "4x ~0.4mm",
}

M3_SCREWS = [6, 8, 10, 12, 18, 20, 25, 30, 35, 40]
M5_SCREWS = [35]
HARDWARE = ["M3 hex nut", "M5 hex nut"]
HARDWARE.extend([f"M3 x {length}mm" for length in M3_SCREWS])
HARDWARE.extend([f"M5 x {length}mm" for length in M5_SCREWS])
OTHER = ["E3D Hemera", "E3D V6 Hotend", "E3D Titan", "E3D Titan Aero", "BMG Extruder", "PTFE Bowden tube"]
ELECTRONICS = ["4010/4020 Radial Fan", "5015 Blower Fan", "Nema 17 Pancake 23mm"]


def change_stl_filenames(directory):
    for root, subdirs, files in os.walk(directory):
        for file_name in files:
            parts = file_name.split(" - ")
            if len(parts) > 1:
                print(f"{root}{file_name} -> {root}{parts[1]}")
                os.rename(
                    os.path.join(root, file_name),
                    os.path.join(root, parts[1])
                )


def render_template(template_name, output_path, context):
    template = TEMPLATE_ENV.get_template(template_name)
    with open(output_path, "w") as page_file:
        page_file.write(template.render(context))


def print_parts(stl_directory):
    data = {}
    for root, subdirs, files in os.walk(stl_directory):
        for file_name in files:
            path = os.path.join("stl", os.path.split(root)[-1], file_name)
            data[os.path.splitext(file_name)[0]] = {
                "type": "printed",
                "path": path,
                "url": urljoin(GH_PATH, quote(path)),
                "print_settings": DEFAULT_PRINT_SETTINGS,
            }

    for hardware in HARDWARE:
        data[hardware] = {"type": "hardware"}

    for other in OTHER:
        data[other] = {"type": "other"}

    for electronics in ELECTRONICS:
        data[electronics] = {"type": "electronics"}

    print(yaml.safe_dump({"parts": data}))


def render_sub_assembly_page(name, subassembly, data):
    context = {
        "name": name,
        "data": data,
        "usages": [dict(name=assembly_name, **assembly) for assembly_name, assembly in data["assemblies"].items() if name in assembly["sub_assemblies"]]
    }
    context.update(subassembly)
    render_template("sub_assembly.md.template", os.path.join(BASE_PATH, "sub_assemblies", f"{name}.md"), context)


def render_assembly_page(name, assembly, data):
    context = {
        "name": name,
        "data": data
    }
    context.update(assembly)

    parts = {}
    for sub_assembly in assembly["sub_assemblies"]:
        for part in data["sub_assemblies"][sub_assembly]["parts"]:
            if part["part"] in parts:
                parts[part["part"]]["qty"] += part["qty"]
            else:
                parts[part["part"]] = part
                
    context["parts"] = list(parts.values())
    context["parts"].sort(key=lambda data: data["part"])

    render_template("assembly.md.template", os.path.join(BASE_PATH, "assemblies", f"{name}.md"), context)


if __name__ == "__main__":
    # change_stl_filenames(os.path.join(BASE_PATH, "..", "stl")
    # render_templates()
    # print_parts(os.path.join(BASE_PATH, "..", "stl"))
    with open(os.path.join(BASE_PATH, "data.yml"), "r") as data_file:
        data = yaml.safe_load(data_file)

    context = {"data": data}
    render_template("getting_started.md.template", os.path.join(BASE_PATH, "getting_started.md"), context)

    for name, subassembly in data["sub_assemblies"].items():
        render_sub_assembly_page(name, subassembly, data)

    for name, assembly in data["assemblies"].items():
        render_assembly_page(name, assembly, data)