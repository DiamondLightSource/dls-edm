"""Substitutes all embedded windows for their contents in a screen.

Saves as <output_screen_filename>
"""
import os
import re
from optparse import OptionParser
from typing import Dict, List, Tuple, Union

from .edmObject import EdmObject, quoteString

author = "Tom Cobb"
usage = """%prog [options] <input_screen_filename> <output_screen_filename>"""


class Substitute_embed:
    """Substitutes embedded windows in a screen for groups containing their contents.

    Screen is the source EdmObject. paths is a list of paths where the filenames of the
    embedded windows being substituted may be found. dict is an optional dict giving
    the maximum number of temperature, waterflow, and current embedded screens to
    substitute. additional_macros are then substituted in this screen.
    """

    in_screens: Dict = {}

    def __init__(
        self,
        screen: EdmObject,
        paths: List[str],
        dict_: Dict[str, int] = {"NTEMP": 99, "NFLOW": 99, "NCURR": 99},
        ungroup: bool = False,
    ) -> None:
        """Sustitute_embed constructor.

        Args:
            screen (EdmObject): The source EdmObject
            paths (List[str]): List of paths to embedded screen files
            dict_ (Dict[str, int], optional): Optional dict giving the maximum number
                of temperature, waterflow, and current embedded screens to substitute.
                Defaults to {"NTEMP": 99, "NFLOW": 99, "NCURR": 99}.
            ungroup (bool, optional): Flag to determine if embedded screens should be
                ungrouped. Defaults to False.
        """
        self.ungroup = ungroup
        self.screen = screen
        self.paths = paths
        self.dict = dict_
        self.additional_macros: Dict = {}
        self.counter = 0
        outsiders = self.__substitute_recurse(self.screen)
        # combine off screen menu muxes and menu mux pvs
        menu_muxes = []
        menu_mux_pvs = []
        screen_w, screen_h = self.screen.getDimensions()
        for ob in outsiders:
            assert isinstance(ob["numItems"], str)
            if ob.Type in ["Menu Mux", "Menu Mux PV"] and not (
                "numItems" in ob and ob["numItems"] and int(ob["numItems"]) > 1
            ):
                # combine menu muxes and menu mux pvs if they have only 1 state
                x, y = ob.getPosition()
                if x > screen_w or y > screen_h:
                    if ob.Type == "Menu Mux":
                        menu_muxes.append(ob)
                    else:
                        menu_mux_pvs.append(ob)
                else:
                    self.screen.addObject(ob)
            else:
                self.screen.addObject(ob)
        for t, l in [("Menu Mux", menu_muxes), ("Menu Mux PV", menu_mux_pvs)]:
            mux = EdmObject(t)
            for ob in l:
                symbols = [
                    o
                    for o in list(ob.keys())
                    if o.startswith("symbol") and len(o) == len("symbol") + 1
                ]
                symbol_max_num = int(max(symbols)[-1])
                if symbol_max_num > 3 or f"symbol{3 - symbol_max_num}" in mux:
                    screen.addObject(mux)
                    mux = EdmObject(t)
                mux["numItems"] = 1
                mux["symbolTag"] = {0: quoteString(".")}
                x, y = ob.getPosition()
                mux.setPosition(x, y)
                w, h = ob.getDimensions()
                mux.setDimensions(w, h)
                for i in range(3):
                    key = f"symbol{i}"
                    if key in ob:
                        while True:
                            if key not in mux:
                                macro = getattr(ob["symbol" + str(i)], "0")
                                mux[key] = {0: macro}
                                for z in [f"PV{i}", f"value{i}"]:
                                    if z in ob:
                                        mux[z[:-1] + key[-1]] = {0: getattr(ob[z], "0")}
                                break
                            else:
                                key = key[:-1] + str(int(key[-1]) + 1)
            if "symbol0" in mux:
                screen.addObject(mux)

    def __substitute_recurse(self, root: EdmObject) -> List[EdmObject]:
        """Recursive substitute call."""
        outsiders = []
        for ob in root.flatten():
            if ob.Type == "Embedded Window":
                check = self.__check_embed(ob)
                if check == "replace":
                    assert isinstance(ob["displayFileName"], Dict)
                    i = max(ob["displayFileName"].keys())
                    macros = {}
                    assert isinstance(ob["symbols"], List)
                    for sub in ob["symbols"][i].split(","):
                        macro = [x.strip() for x in sub.strip('"').split("=")]
                        if len(macro) == 2:
                            macros[macro[0]] = macro[1]
                    group, new_outsiders = self.__group_from_screen(
                        ob["displayFileName"][i], macros
                    )
                    if group:
                        assert isinstance(group, EdmObject)
                        assert isinstance(new_outsiders, List)
                        for new_ob in [group] + new_outsiders:
                            assert isinstance(new_ob, EdmObject)
                            x, y = ob.getPosition()
                            new_ob.setPosition(x, y, relative=True)
                        try:
                            assert ob.Parent is not None
                            ob.Parent.replaceObject(ob, group)
                        except AssertionError as e:
                            print(f"Object {ob} has no parent object.\n{e}")
                        if self.ungroup:
                            group.ungroup()
                        outsiders += new_outsiders
                elif check == "remove":
                    try:
                        assert ob.Parent is not None
                        ob.Parent.removeObject(ob)
                    except AssertionError as e:
                        print(f"Object {ob} has no parent object.\n{e}")
        return outsiders

    def __group_from_screen(
        self, filename: str, macros: Dict[str, str]
    ) -> Union[Tuple[EdmObject, List[EdmObject]], Tuple[None, None]]:
        """Create a group from a screen given by the filename.

        Args:
            filename (str): Filename of screen
            macros (Dict[str, str]): Macros for screen

        Returns:
            Union[Tuple[EdmObject, List[EdmObject]], Tuple[None, None]:
            Group of EdmObject and a list of the outsider EdmObjects.
        """
        #
        filename = filename.strip('"').replace(".edl", "") + ".edl"
        if filename in self.in_screens:
            screen = self.in_screens[filename].copy()
        else:
            paths = [
                os.path.join(p, filename)
                for p in self.paths
                if os.path.isfile(os.path.join(p, filename))
            ]
            if paths:
                screen = EdmObject("Screen")
                screen.write(open(paths[0], "r").read())
                self.in_screens[filename] = screen.copy()
            else:
                return (None, None)
        outsiders = []
        screen_w, screen_h = screen.getDimensions()
        group = EdmObject("Group")
        group.setDimensions(screen_w, screen_h)
        self.counter += 1
        for ob in screen.Objects:
            ob.substitute("auto-label", "label%d" % self.counter)
            ob_x, ob_y = ob.getPosition()
            if ob_x < screen_w and ob_y < screen_h:
                group.addObject(ob)
            else:
                outsiders.append(ob)
        new_macros = self.additional_macros.copy()
        new_macros.update(macros)
        for key in list(new_macros.keys()):
            for ob in [group] + outsiders:
                ob.substitute("$(" + key + ")", new_macros[key])
        return (group, outsiders)

    def __check_embed(self, ob: EdmObject) -> str:
        """Check embedded screem file PV.

        Check for dummy in filePv, or if it is a temp, flow or curr box controlled
        by $(P):INFO:N<VAR> return replace if it needs to be replaced, remove to remove
        and nothing to do nothing
        """
        filePv = ob["filePv"]
        assert isinstance(filePv, str)
        if "dummy" in filePv:
            return "replace"
        else:
            for string in ["ntemp", "nflow", "ncurr"]:
                # see if the screen is one that we can substitute
                if string.upper() in filePv and "CALC" in filePv:
                    match = re.compile(r"A>=(\d+)\?1:0").search(filePv)
                    if (
                        match
                        and match.groups()
                        and int(match.groups()[0]) <= int(self.dict[string.upper()])
                    ):
                        return "replace"
                    else:
                        return "remove"
            return "nothing"


def cl_substitute_embed():
    """Command line helper function for substitute embed."""
    parser = OptionParser(usage)
    paths = "."
    parser.add_option(
        "-p",
        "--paths",
        dest="paths",
        metavar="COLON_SEPARATED_LIST",
        help="Set the list of paths to look for the embedded "
        + "screens. Default is "
        + paths,
    )
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error("Incorrect number of arguments")
    if options.paths:
        paths = options.paths
    paths = paths.split(":")
    screen = EdmObject("Screen")
    screen.write(open(args[0], "r").read())
    Substitute_embed(screen, paths)
    open(args[1], "w").write(screen.read())
    print(
        "Embedded windows substituted in " + args[0] + ", output written to " + args[1]
    )


if __name__ == "__main__":
    cl_substitute_embed()
