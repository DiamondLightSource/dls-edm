"""
This script takes an edm screen and flips it horizontally, keeping groups intact.

It also replaces symbols and images with their flipped counterparts if they exist.
"""
import os
from optparse import OptionParser
from typing import Dict, List

from .common import flip_axis
from .edmObject import EdmObject, quoteString

author = "Tom Cobb"
usage = """%prog [options] <input_screen> <output_screen>"""


def Flip_horizontal(
    screen: EdmObject, paths: List[str], flip_group_contents: bool = False
) -> EdmObject:
    """Flip the screen object, and return it with changes applied.

    Paths gives the list of paths to look for flipped symbols or pngs.
    If flip_group_contents: flip the contents of groups, otherwise keep
    them intact when flipping.

    Args:
        screen (EdmObject): The screen object
        paths (List[str]): The list of paths to look for flipped symbols or pngs
        flip_group_contents (bool, optional): Flag to determine whether to flip
        the contents of groups. Defaults to False.

    Returns:
        EdmObject: The updated screen object
    """
    screenw, screenh = screen.getDimensions()
    files = []
    for p in paths:
        files.extend([f for f in os.listdir(p) if f.endswith(".png") or "symbol" in f])
    for ob in screen.Objects:
        # check groups' dimensions exactly enclose their contents
        ob.autofitDimensions()
        if "visPv" in ob:
            assert isinstance(ob["visPv"], str)
            visPv = ob["visPv"].strip('"')
        else:
            visPv = ""
        x, y = ob.getPosition()
        w, h = ob.getDimensions()
        if ob.Type == "Group":
            symbols = [o for o in ob.Objects if o.Type == "Symbol"]
            if visPv.startswith("#<AXIS_"):
                # replace AXIS with the reverse object
                if visPv.startswith("#<AXIS_RIGHT"):
                    new_ob = flip_axis("left")
                else:
                    new_ob = flip_axis("right")
                new_ob.setPosition(screenw - x - w, y)
                screen.replaceObject(ob, new_ob)
            elif visPv.startswith("#<"):
                for ob2 in [o for o in ob.flatten() if o.Type == "Symbol"]:
                    assert isinstance(ob2["file"], str)
                    # replace symbols with their flipped version if applicable
                    filename = (
                        ob2["file"].strip('"').replace("-symbol", "-flipped-symbol")
                    )
                    if filename[-4:] != ".edl":
                        filename += ".edl"
                    if filename in files:
                        ob2["file"] = quoteString(filename.replace(".edl", ""))
            if (
                flip_group_contents
                or not symbols
                or (symbols and "filter" in symbols[0]["file"])
            ):
                # if it is the beam object then reverse the order and positions
                # of the components
                for ob2 in ob.Objects:
                    ob2x, ob2y = ob2.getPosition()
                    ob2w, ob2h = ob2.getDimensions()
                    ob2.setPosition(x + w - (ob2x - x + ob2w), ob2y)
                    if (not symbols or flip_group_contents) and ob2.Type == "Lines":
                        flip_lines(ob2)
        elif ob.Type == "Lines" and ob["lineColor"] == ob.Colour["Controller"]:
            # flip lines in symbols
            flip_lines(ob)
        elif ob.Type == "PNG Image" or ob.Type == "Image":
            # replace images with their flipped version if applicable
            assert isinstance(ob["file"], str)
            filename = ob["file"].strip('"').replace(".png", "") + "-flipped.png"
            if filename in files:
                ob["file"] = quoteString(filename.replace(".png", ""))
        # mirror the group on the other side of the screen
        ob.setPosition(screenw - (x + w), y)
    return screen


def flip_lines(ob: EdmObject) -> None:
    """Flip lines of EdmObject.

    Args:
        ob (EdmObject): The EdmObject to update
    """
    if "xPoints" in ob and ob["xPoints"]:
        ob2x, ob2y = ob.getPosition()
        ob2w, ob2h = ob.getDimensions()
        assert isinstance(ob["xPoints"], Dict)
        for key in list(ob["xPoints"].keys()):
            px = int(ob["xPoints"][key])
            ob["xPoints"][key] = str(ob2x + ob2w - (px - ob2x))


def cl_flip_horizontal() -> None:
    """Command line helper function to flip screen horizontally."""
    parser = OptionParser(usage)
    paths = "."
    parser.add_option(
        "-p",
        "--paths",
        dest="paths",
        metavar="COLON_SEPARATED_LIST",
        help="Set the list of paths to look for the symbols "
        + "and images to flip. Default is "
        + paths,
    )
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error("Incorrect number of arguments")
    if options.paths:
        paths = options.paths.split(":")
    screen = EdmObject("Screen")
    screen.write(open(args[0], "r").read())
    assert isinstance(paths, List)
    Flip_horizontal(screen, paths)
    open(args[1], "w").write(screen.read())
    print(args[0] + " has been flipped. Output written to: " + args[1])


if __name__ == "__main__":
    cl_flip_horizontal()
