"""
This script takes an edm screen and flips it horizontally, keeping groups intact.

It also replaces symbols and images with their flipped counterparts if they exist.
"""
import argparse
import os
from pathlib import Path
from typing import Dict, List

from common import flip_axis
from edmObject import EdmObject, quoteString

author = "Oliver Copping"


def Flip_horizontal(
    screen: EdmObject, paths: List[Path], flip_group_contents: bool = False
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
        if "visPv" in ob.Properties:
            tmp = ob.Properties["visPv"]
            assert isinstance(tmp, str)
            visPv = tmp.strip('"')
        else:
            visPv = ""
        x, y = ob.getPosition()
        w, h = ob.getDimensions()
        if ob.Properties.Type == "Group":
            symbols = [o for o in ob.Objects if o.Properties.Type == "Symbol"]
            if visPv.startswith("#<AXIS_"):
                # replace AXIS with the reverse object
                if visPv.startswith("#<AXIS_RIGHT"):
                    new_ob = flip_axis("left")
                else:
                    new_ob = flip_axis("right")
                new_ob.setPosition(screenw - x - w, y)
                screen.replaceObject(ob, new_ob)
            elif visPv.startswith("#<"):
                for ob2 in [o for o in ob.flatten() if o.Properties.Type == "Symbol"]:
                    tmp = ob2.Properties["file"]
                    assert isinstance(tmp, str)
                    # replace symbols with their flipped version if applicable
                    filename = tmp.strip('"').replace("-symbol", "-flipped-symbol")
                    if filename[-4:] != ".edl":
                        filename += ".edl"
                    if filename in files:
                        ob2.Properties["file"] = quoteString(
                            filename.replace(".edl", "")
                        )
            if (
                flip_group_contents
                or not symbols
                or (symbols and "filter" in symbols[0].Properties["file"])
            ):
                # if it is the beam object then reverse the order and positions
                # of the components
                for ob2 in ob.Objects:
                    ob2x, ob2y = ob2.getPosition()
                    ob2w, ob2h = ob2.getDimensions()
                    ob2.setPosition(x + w - (ob2x - x + ob2w), ob2y)
                    if (
                        not symbols or flip_group_contents
                    ) and ob2.Properties.Type == "Lines":
                        flip_lines(ob2)

        elif ob.Properties.Type == "Lines":
            if ob.Properties["lineColor"] == ob.Properties.Colour["Controller"]:
                # flip lines in symbols
                flip_lines(ob)
        elif ob.Properties.Type == "PNG Image" or ob.Properties.Type == "Image":
            # replace images with their flipped version if applicable
            tmp = ob.Properties["file"]
            assert isinstance(tmp, str)
            filename = tmp.strip('"').replace(".png", "") + "-flipped.png"
            if filename in files:
                ob.Properties["file"] = quoteString(filename.replace(".png", ""))
        # mirror the group on the other side of the screen
        ob.setPosition(screenw - (x + w), y)
    return screen


def flip_lines(ob: EdmObject) -> None:
    """Flip lines of EdmObject.

    Args:
        ob (EdmObject): The EdmObject to update
    """
    if "xPoints" in ob.Properties and ob.Properties["xPoints"]:
        ob2x, ob2y = ob.getPosition()
        ob2w, ob2h = ob.getDimensions()
        tmp = ob.Properties["xPoints"]
        assert isinstance(tmp, Dict)
        for key in list(tmp.keys()):
            px = int(tmp[key])
            ob.Properties["xPoints"][key] = str(ob2x + ob2w - (px - ob2x))


def cl_flip_horizontal() -> None:
    """Command line helper function to flip screen horizontally."""
    parser = argparse.ArgumentParser(prog="flip_horizontal")  # , usage=usage)
    parser.add_argument("screen", nargs=1, type=Path)
    parser.add_argument("flipped_screen", nargs=1, type=Path)
    paths = "."
    parser.add_argument(
        "-p",
        # "--paths",
        dest="paths",
        metavar="COLON_SEPARATED_LIST",
        help=f"Set the list of paths to look for the symbols and images to flip. Default is {paths}",
    )
    args = parser.parse_args()

    if args.paths:
        paths = [Path(p) for p in args.paths.split(":")]

    screen = EdmObject("Screen", defaults=False)
    with open(args.screen[0], "r") as f:
        screen.write(f.read())

    assert isinstance(paths, List)
    new_screen = Flip_horizontal(screen, paths)
    with open(args.flipped_screen[0], "w") as f:
        f.write(new_screen.read())
    print(
        f"{args.screen[0]} has been flipped. Output written to: {args.flipped_screen[0]}"
    )


if __name__ == "__main__":
    cl_flip_horizontal()
