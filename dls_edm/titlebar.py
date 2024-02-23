"""Adds a titlebar and exit button to the screen."""
import argparse
from pathlib import Path

from common import (
    exit_button,
    raised_PV_button_circle,
    raised_PV_circle,
    raised_PV_shell_circle,
    raised_text_circle,
)
from edmObject import EdmObject, quoteListString, quoteString

author = "Oliver Copping"


def titlebar_group(width: int, tooltip_str: str) -> EdmObject:
    """Create a grouptitlebar group.

    Placed at 0,0 with width width and height 30, with a tooltip and shadow.

    Args:
        width (int): Width of titlebar
        tooltip_str (str):  Tooltip string

    Returns:
        EdmObject: Titlebar group object
    """
    group = EdmObject("Group")
    top_shadow = EdmObject("Rectangle")
    top_shadow.setPosition(0, 2)
    top_shadow.setDimensions(width - 2, 25)
    top_shadow.Properties["lineColor"] = top_shadow.Properties.Colour["Top Shadow"]
    group.addObject(top_shadow)
    bottom_shadow = EdmObject("Rectangle")
    bottom_shadow.setPosition(1, 3)
    bottom_shadow.setDimensions(width - 2, 25)
    bottom_shadow.Properties["lineColor"] = bottom_shadow.Properties.Colour[
        "Bottom Shadow"
    ]
    group.addObject(bottom_shadow)
    tooltip = EdmObject("Related Display")
    tooltip.setPosition(1, 3)
    tooltip.setDimensions(width - 2, 24)
    tooltip.Properties["xPosOffset"] = 5
    tooltip.Properties["yPosOffset"] = 5
    tooltip.Properties["button3Popup"] = True
    tooltip.Properties["invisible"] = True
    tooltip.Properties["buttonLabel"] = quoteString("tooltip")
    tooltip.Properties["displayFileName"] = {0: quoteString(tooltip_str)}
    tooltip.Properties["setPosition"] = {0: quoteString("button")}
    tooltip.Properties["font"] = quoteString("arial-bold-r-14.0")
    tooltip.Properties["numDsps"] = 1
    group.addObject(tooltip)
    group.setPosition(0, 0, move_objects=False)
    group.setDimensions(width, 30, resize_objects=False)
    return group


def PV_titlebar(width: int, pv_string: str, tooltip: str, ta: str = "CO") -> EdmObject:
    """Create a titlebar group with a PV name as a label.

    Args:
        width (int): Width of titlebar
        pv_string (str): PV name for label text
        tooltip (str): Tooltip string
        ta (str, optional): Technical area code. Defaults to "CO".

    Returns:
        EdmObject: PV Titlebar EdmObject class
    """
    group = titlebar_group(width, tooltip)
    PV = EdmObject("Textupdate")
    PV.setPosition(1, 3)
    PV.setDimensions(width + 40, 25)
    PV.Properties["font"] = quoteString("arial-bold-r-16.0")
    PV.Properties["fontAlign"] = quoteString("center")
    PV.Properties["fgColor"] = PV.Properties.Colour["Black"]
    PV.Properties["bgColor"] = PV.Properties.Colour[ta + " title"]
    PV.Properties["fill"] = True
    PV.Properties["controlPv"] = quoteString(pv_string)
    group.addObject(PV)
    return group


def text_titlebar(
    width: int, string_name: str, tooltip: str, ta: str = "CO"
) -> EdmObject:
    """Create a titlebar group with the stringname as a label.

    Args:
        width (int): Width of titlebar
        stringname (str): String name for label text
        tooltip (str): Tooltip string
        ta (str, optional): Technical area code. Defaults to "CO".

    Returns:
        EdmObject: Text Titlebar EdmObject class
    """
    group = titlebar_group(width, tooltip)
    text = EdmObject("Static Text")
    text.setPosition(1, 3)
    text.setDimensions(width + 40, 25)
    text.Properties["font"] = quoteString("arial-bold-r-16.0")
    text.Properties["fontAlign"] = quoteString("center")
    text.Properties["bgColor"] = text.Properties.Colour[ta + " title"]
    text.Properties["fgColor"] = text.Properties.Colour["Black"]
    text.Properties["value"] = quoteListString(string_name)
    group.addObject(text)
    return group


def Titlebar(
    screen: EdmObject,
    ta: str = "CO",
    button: str = "text",
    button_text: str = "$(dom)",
    header: str = "text",
    header_text: str = "Temperature Summary",
    tooltip: str = "generic-tooltip",
    title: str = "Temperatures - $(dom)",
) -> EdmObject:
    """Add a titlebar and exit button to screen.

    ta gives the colour of the buttons and titlebar, it can be any technical area,
    like CO, MO, VA, DI, etc. button can be "text","PV",or "button". If it is "text":
    button_text is displayed in a circle at the top left, if it is "PV": the value
    of the pv button_text is displayed, and if it is "button": as "PV", but with a
    button to bring up the help screen. header can be "text" or "PV" with header_text
    operating in the same way as button_text. tooltip is the tooltip filename brought
    up by the tooltip under the titlebar. title is the screen title.

    Args:
        screen (EdmObject): EdmObject class of screen
        ta (str, optional): Technical area code. Defaults to "CO".
        button (str, optional): Button type. Defaults to "text".
        button_text (str, optional): Button text. Defaults to "$(dom)".
        header (str, optional): Header type. Defaults to "text".
        header_text (str, optional): Header text. Defaults to "Temperature Summary".
        tooltip (str, optional): Tooltip text. Defaults to "generic-tooltip".
        title (str, optional): Title text. Defaults to "Temperatures - $(dom)".

    Returns:
        EdmObject: Titlebar EdmObject class
    """
    ####################
    # hardcoded fields #
    ####################
    incryheader = 30
    incryspacer = 10
    incrxspacer = 10
    exitw = 90
    exith = 20
    min_title_width = 210

    ##############
    # initialise #
    ##############
    maxy = 0
    maxx = 0
    points = []

    assert (
        screen.Properties.Type == "Screen"
    ), f"Can't add a titlebar to an object of type: {screen.Properties.Type}"

    # 1st iteration to find max x and y
    screen.autofitDimensions(xborder=incrxspacer, yborder=incryspacer)
    for ob in screen.Objects:
        if ob.Properties.Type not in ["Screen", "Menu Mux PV"]:
            x, y = ob.getPosition()
            w, h = ob.getDimensions()
            maxx = max(maxx, x + w)
            maxy = max(maxy, y + h + incryheader)
            points.append((x + w, y + h + incryheader))

    # 2nd interation to find width and height,
    # then modify each y value to make room for header
    exit_button_x = max(maxx + incrxspacer, min_title_width) - exitw - 10
    exit_button_y = maxy + incryspacer - exith - 10
    for x, y in points:
        if x > exit_button_x - incrxspacer and y > exit_button_y - incryspacer:
            exit_button_y = y + incryspacer
    w = exit_button_x + exitw + 10
    h = exit_button_y + exith + 10
    screen.setDimensions(w, h, resize_objects=False)

    # move all the objects down to put the titlebar in
    for ob in screen.Objects:
        if ob.Properties.Type not in ["Screen", "Menu Mux PV"]:
            ob.setPosition(0, incryheader, relative=True)

    # add the circular button on the left
    if button == "text":
        left = raised_text_circle(0, 0, 50, 30, button_text, ta=ta)
    elif button == "PV":
        left = raised_PV_circle(0, 0, 50, 30, button_text, ta=ta)
    elif button == "button":
        left = raised_PV_button_circle(0, 0, 50, 30, button_text, ta=ta)
    elif button == "shell":
        left = raised_PV_shell_circle(0, 0, 50, 30, button_text, ta=ta)
    screen.addObject(left)

    # add the titlebar
    if header == "text":
        middle = text_titlebar(w, header_text, tooltip, ta)
    elif header == "PV":
        middle = PV_titlebar(w, header_text, tooltip, ta)
    screen.addObject(middle)
    middle.lowerObject()

    # add the exit button
    exit = exit_button(exit_button_x, exit_button_y, exitw, exith)
    screen.addObject(exit)

    # set title
    screen.Properties["title"] = quoteString(title)

    return screen


def cl_titlebar():
    """Command line helper function for titlebar."""
    parser = argparse.ArgumentParser(prog="Titlebar")

    parser.add_argument("input_filename", nargs=1, type=Path)
    parser.add_argument("output_filename", nargs=1, type=Path)

    ta = "CO"
    left = "text"
    left_text = "$(dom)"
    header = "text"
    header_text = "Temperature Summary"
    tooltip = "generic-tooltip"
    title = "Temperatures - $(dom)"
    parser.add_argument(
        "-a",
        "--area",
        metavar="TECHNICAL_AREA",
        default=ta,
        help=f"Technical area (MO,VA,DI,etc.) for colour of titlebar. Default: {ta}",
    )
    parser.add_argument(
        "-l",
        "--left",
        metavar="TYPE",
        default=left,
        help=f"Left Button type: text, PV or button. Default: {left}",
    )
    parser.add_argument(
        "-L",
        "--left_text",
        metavar="TEXT",
        default=left_text,
        help=f"Left Button text: text or PV. Default: {left_text}",
    )
    parser.add_argument(
        "-r",
        "--header",
        metavar="TYPE",
        default=header,
        help=f"Header type: text or PV. Default: {header}",
    )
    parser.add_argument(
        "-R",
        "--header_text",
        metavar="TEXT",
        default=header_text,
        help=f"Header text: text or PV. Default: {header_text}",
    )
    parser.add_argument(
        "-t",
        "--tooltip",
        metavar="FILE",
        default=tooltip,
        help=f"Tooltip filename. Default: {tooltip}",
    )
    parser.add_argument(
        "-i",
        "--title",
        metavar="TEXT",
        default=title,
        help=f"Screen title text. Default: {title}",
    )

    args = parser.parse_args()

    screen = EdmObject("Screen")
    with open(args.input_filename, "r") as f:
        screen.write(f.read())

    new_screen = Titlebar(
        screen,
        args.area,
        args.left,
        args.left_text,
        args.header,
        args.header_text,
        args.tooltip,
        args.title,
    )
    with open(args.output_filename, "w") as f:
        f.write(new_screen.read())
    print(
        "Titlebar added to:", args.filename, "screen written to:", args.output_filename
    )


if __name__ == "__main__":
    cl_titlebar()
