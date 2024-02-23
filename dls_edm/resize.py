"""This script resizes an edm screen <input_screen> to size (<width>,<height>).

It also resizes fonts, then prints the resulting screen to <output_screen>
"""

import argparse
from optparse import OptionParser
from pathlib import Path
from typing import List

from edmObject import EdmObject

author = "Tom Cobb"
usage = """%prog [options] <input_screen> <output_screen> <width> <height>"""


def new_font_size(factor: float, font: str) -> str:
    """Find the closest size for a font.

    Args:
        factor (float): Factor to multiply size by
        font (str): Current font name string including size

    Returns:
        str: New font name string with adjusted size
    """
    sizes: List[int] = [
        80,
        100,
        120,
        140,
        160,
        180,
        200,
        240,
        280,
        320,
        360,
        420,
        480,
        600,
        720,
        960,
        1200,
        1680,
        2160,
        3120,
        4080,
        5040,
    ]
    size = int(font.split("-")[-1].replace('.0"', ""))
    # work out the difference between the desired size and available sizes
    new_size = min(sizes, key=lambda x: abs(x - int(size * factor * 10)))
    new_font = font.replace("-" + str(size), "-" + str(int(new_size / 10.0)))
    return new_font


def Resize(screen: EdmObject, width: int, height: int) -> EdmObject:
    """Resize screen dimensions to be (width,height).

    Resize fonts proportionally.
    Modify the original object, and return it with changes applied.

    Args:
        screen (EdmObject): EdmObject class of the screen
        width (int): New width of the screen
        height (int): New height of the screen

    Returns:
        EdmObject: New screen EdmObject woth adjusted dimensions
    """
    old_width, old_height = screen.getDimensions()
    factor = float(width) / float(old_width)
    screen.setDimensions(width, height, resize_objects=True)
    for ob in screen.flatten():
        if "font" in ob.Properties:
            font = ob.Properties["font"]
            assert isinstance(font, str)
            ob.Properties["font"] = new_font_size(factor, font)
    return screen


def cl_resize():
    """Command line helper function to rezise a screen."""
    parser = argparse.ArgumentParser(prog="resize")
    parser.add_argument("screen", nargs=1, type=Path)
    parser.add_argument("resized_screen", nargs=1, type=Path)
    parser.add_argument("width", nargs=1, type=int)
    parser.add_argument("height", nargs=1, type=int)
    args = parser.parse_args()

    screen = EdmObject("Screen")
    with open(args.screen[0], "r") as f:
        screen.write(f.read())

    Resize(screen, int(args.width[0]), int(args.height[0]))
    with open(args.resized_screen[0], "w") as f:
        f.write(screen.read())
    print(
        f"{args.screen[0]} has been resized. Output written to: {args.resized_screen[0]}"
    )


if __name__ == "__main__":
    cl_resize()
