import pickle
from pathlib import Path
from typing import Dict, List


def get_properties_dict() -> Dict[str, str | bool | int | List[str] | Dict]:
    PROPERTIES: Dict[str, str | bool | int | List[str] | Dict] = {}
    # code to load the stored dictionaries
    try:
        file_path = Path.absolute(Path(__file__).parent)  # + "/helper.pkl")
        file_path = file_path.joinpath("properties_helper.pkl")
        with open(file_path, "rb") as file:
            pkl = pickle.load(file)
        PROPERTIES = pkl
    except IOError as e:
        print(f"IOError: \n{e}")
        PROPERTIES = {}

    return PROPERTIES


def get_colour_dict() -> Dict[str, str]:
    COLOUR: Dict[str, str] = {}
    # code to load the stored dictionaries
    try:
        file_path = Path.absolute(Path(__file__).parent)  # + "/helper.pkl")
        file_path = file_path.joinpath("colour_helper.pkl")
        if file_path.is_file():
            with open(file_path, "rb") as file:
                pkl = pickle.load(file)
            COLOUR = pkl
        else:
            COLOUR = write_colour_helper()
    except IOError as e:
        print(f"IOError: \n{e}")
        COLOUR = {}

    return COLOUR


def write_colour_helper() -> Dict[str, str]:
    # load the environment so we can find the epics location
    edm_path = Path("/dls_sw/prod/tools/RHEL7-x86_64/defaults/bin/edm")
    while edm_path.is_symlink():
        edm_path = edm_path.readlink()
    edm_dir = Path.joinpath(edm_path.parent, "..", "..", "src", "edm")

    # create the COLOUR dictionary
    COLOUR = {"White": "index 0"}

    with open(Path.joinpath(edm_dir, "setup", "colors.list"), "r") as file:
        lines = file.readlines()

    for line in lines:
        # read each line in colors.list into the dict
        if line.startswith("static"):
            index = line.split()[1]
            name = line[
                line.find('"') : line.find('"', line.find('"') + 1) + 1
            ].replace('"', "")
            COLOUR[name] = f"index {index}"
        elif line.startswith("rule"):
            index = line.split()[1]
            name = line.split()[2]
            COLOUR[name] = f"index {index}"

    try:
        file_path = Path.absolute(Path(__file__).parent)

        colour_pkl_file = file_path.joinpath(Path("colour_helper.pkl"))
        colour_pkl_file.touch()
        with colour_pkl_file.open("wb") as f:
            pickle.dump(COLOUR, f, 0)
    except IOError as e:
        print(f"IOError: \n{e}")
        COLOUR = {}

    return COLOUR
