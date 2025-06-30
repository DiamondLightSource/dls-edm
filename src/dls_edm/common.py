"""
Module containing some useful EdmObjects for building dls screens.

Author: Tom Cobb
Updated to Python3 by: Oliver Copping
"""

from pathlib import Path
from typing import Collection, Optional, Tuple

from .edmObject import EdmObject, quoteListString, quoteString

__all__ = [
    "arrow",
    "dummy",
    "embed",
    "exit_button",
    "label",
    "raised_PV_button_circle",
    "raised_PV_circle",
    "raised_button_circle",
    "raised_circle",
    "raised_text_button_circle",
    "raised_text_circle",
    "rd",
    "rd_visible",
    "rectangle",
    "symbol",
    "text_monitor",
    "tooltip",
    "shell",
    "shell_visible",
    "can_optimise",
]
__all__.sort()


def can_optimise(x: str) -> bool:
    """Check if item can be optimised.

    Return True if the item can be optimised (i.e. if it is an autogen screen
    or one of the selected optimisable screens

    Args:
        x (str): List of objects of item to be optimised

    Returns:
        bool: True if the item can be optimised
    """
    return (
        ("camera" in x and "2cam" not in x and not "camera" == x)
        or "autogen" in x
        or "slit" in x
        or "mirror" in x
    )


def label(
    x: int, y: int, w: int, h: int, text: str, fontAlign: str = "left"
) -> EdmObject:
    """Return a Static Text box with position (x,y) dimensions (w,h).

    Text is the display text and fontAlign is how it is aligned.
    Font is arial medium 10

    Args:
        x (int): X position of Static Text box
        y (int): Y position of Static Text box
        w (int): Width of Static Text box
        h (int): Height of Static Text box
        text (str): Text of Static Text box
        fontAlign (str, optional): Alignment of font in Static Text box.
            Defaults to "left".

    Returns:
        EdmObject: EdmObject class of Static Text box
    """
    ob = EdmObject("Static Text")
    ob.setDimensions(w, h)
    ob.setPosition(x, y)
    ob.Properties["font"] = quoteString("arial-medium-r-10.0")
    ob.Properties["fgColor"] = ob.Properties.Colour["Black"]
    ob.Properties["useDisplayBg"] = True
    ob.Properties["value"] = quoteListString(text)
    ob.Properties["fontAlign"] = quoteString(fontAlign)
    return ob


def text_monitor(
    x: int,
    y: int,
    w: int,
    h: int,
    pv: str,
    showUnits: bool = False,
    fontAlign: str = "left",
) -> EdmObject:
    """Return a Text Monitor with position (x,y) dimensions (w,h).

    pv is the display pv and fontAlign is how it is aligned.
    Font is arial medium 10.
    If showUnits, then units from the Db are shown.

    Args:
        x (int): X position of Text Monitor
        y (int): Y position of Text Monitor
        w (int): Width of Text Monitor
        h (int): Height of Text Monitor
        pv (str): PV to monitor
        showUnits (bool, optional): Flag to show units. Defaults to False.
        fontAlign (str, optional): Alignment of font in Text Monitor.
            Defaults to "left".

    Returns:
        EdmObject: EdmObject class of Text Monitor
    """
    ob = EdmObject("Text Monitor")
    ob.setDimensions(w, h)
    ob.setPosition(x, y)
    ob.Properties["controlPv"] = quoteString(pv)
    ob.Properties["font"] = quoteString("arial-medium-r-10.0")
    ob.Properties["fgColor"] = ob.Properties.Colour["Black"]
    ob.Properties["useDisplayBg"] = True
    ob.Properties["precision"] = 3
    ob.Properties["fontAlign"] = quoteString(fontAlign)
    ob.Properties["smartRefresh"] = True
    ob.Properties["fastUpdate"] = True
    ob.Properties["showUnits"] = showUnits
    ob.Properties["limitsFromDb"] = False
    ob.Properties["newPos"] = True
    return ob


def dummy(x: int, y: int, w: int, h: int) -> EdmObject:
    """Return a dummy invisible rectangle with position (x,y) dimensions (w,h).

    Args:
        x (int): X position of invisible rectangle
        y (int): Y position of invisible rectangle
        w (int): Width of invisible rectangle
        h (int): Height of invisible rectangle

    Returns:
        EdmObject: EdmObject class of invisible rectangle
    """
    ob = EdmObject("Rectangle")
    ob.setDimensions(w, h)
    ob.setPosition(x, y)
    ob.Properties["lineColor"] = ob.Properties.Colour["Canvas"]
    ob.Properties["invisible"] = True
    return ob


def rectangle(
    x: int,
    y: int,
    w: int,
    h: int,
    lineColour: str = "Black",
    fillColour: str = "Controller",
):
    """Return a filled rectangle with position (x,y) dimensions (w,h).

    fillColour and lineColour are looked up in ob.Properties.Colour

    Args:
        x (int): X position of rectangle
        y (int): Y position of rectangle
        w (int): Width of rectangle
        h (int): Height of rectangle

    Returns:
        EdmObject: EdmObject class of rectangle
    """
    ob = EdmObject("Rectangle")
    ob.setDimensions(w, h)
    ob.setPosition(x, y)
    ob.Properties["lineColor"] = ob.Properties.Colour[lineColour]
    ob.Properties["fill"] = True
    ob.Properties["fillColor"] = ob.Properties.Colour[fillColour]
    return ob


def tooltip(x: int, y: int, w: int, h: int, text: str) -> EdmObject:
    """Return an invisible related display with position (x,y) dimensions (w,h).

    When right clicked, it displays a tooltip with the given text.

    Args:
        x (int): X position of tooltip
        y (int): Y position of tooltip
        w (int): Width of tooltip
        h (int): Height of tooltip
        text (str): The tooltip text

    Returns:
        EdmObject: EdmObject class of tooltip
    """
    ob = EdmObject("Related Display")
    ob.setDimensions(w, h)
    ob.setPosition(x, y)
    ob.Properties["yPosOffset"] = max(h, 22) + 8
    ob.Properties["xPosOffset"] = int(w / 2) - 100
    ob.Properties["button3Popup"] = True
    ob.Properties["invisible"] = True
    ob.Properties["buttonLabel"] = quoteString("tooltip")
    ob.Properties["numPvs"] = 4
    ob.Properties["numDsps"] = 1
    ob.Properties["displayFileName"] = {0: quoteString("symbols-tooltip-symbol")}
    ob.Properties["setPosition"] = {0: quoteString("button")}
    ob.Properties["symbols"] = {0: quoteString("text=" + text)}
    return ob


def rd(x: int, y: int, w: int, h: int, filename: Path, symbols: str) -> EdmObject:
    """Return an invisible related display with position (x,y) dimensions (w,h).

    filename and symbols as defined.

    Args:
        x (int): X position of related display
        y (int): Y position of related display
        w (int): Width of related display
        h (int): Height of related display
        filename (str): The related display screen filename
        symbols (str): String of all symbols (macros)

    Returns:
        EdmObject: EdmObject class of related display
    """
    ob = EdmObject("Related Display")
    ob.setDimensions(w, h)
    ob.setPosition(x, y)
    ob.Properties["invisible"] = True
    ob.Properties["buttonLabel"] = quoteString("device screen")
    ob.Properties["numPvs"] = 4
    if filename:
        ob.Properties["displayFileName"] = {0: quoteString(str(filename))}
        ob.Properties["numDsps"] = 1
        if symbols:
            ob.Properties["symbols"] = {0: quoteString(symbols)}
    else:
        ob.Properties["numDsps"] = 0
    return ob


def shell(x: int, y: int, w: int, h: int, command: str) -> EdmObject:
    """Return an invisible shell command button.

    With position (x,y) dimensions (w,h) and command as defined.

    Args:
        x (int): X position of shell command button
        y (int): Y position of shell command button
        w (int): Width of shell command button
        h (int): Height of shell command button
        command (str): The command string

    Returns:
        EdmObject: EdmObject class of shell command button
    """
    ob = EdmObject("Shell Command")
    ob.setDimensions(w, h)
    ob.setPosition(x, y)
    ob.Properties["invisible"] = True
    ob.Properties["buttonLabel"] = quoteString("Shell Command")
    ob.Properties["numCmds"] = 1
    ob.Properties["command"] = {0: quoteString(command)}
    return ob


def shell_visible(x: int, y: int, w: int, h: int, text: str, command: str) -> EdmObject:
    """Return an invisible shell command button.

    With position (x,y) dimensions (w,h) and command as defined.

    Args:
        x (int): X position of shell command button
        y (int): Y position of shell command button
        w (int): Width of shell command button
        h (int): Height of shell command button
        text (str): The shell command button text
        command (str): The command string

    Returns:
        EdmObject: EdmObject class of shell command button
    """
    ob = EdmObject("Shell Command")
    ob.setDimensions(w, h)
    ob.setPosition(x, y)
    ob.Properties["buttonLabel"] = quoteString(text)
    ob.Properties["numCmds"] = 1
    ob.Properties["command"] = {0: quoteString(command)}
    ob.Properties["fgColor"] = ob.Properties.Colour["Related display"]
    ob.Properties["bgColor"] = ob.Properties.Colour["Canvas"]
    ob.Properties["font"] = quoteString("arial-bold-r-14.0")
    ob.setShadows()
    return ob


def rd_visible(
    x: int,
    y: int,
    w: int,
    h: int,
    text: str,
    filename: Path,
    symbols: Optional[str] = None,
):
    """Return an visible related display with position (x,y) dimensions (w,h).

    text is the button label and filename and symbols are as defined.

    Args:
        x (int): X position of related display
        y (int): Y position of related display
        w (int): Width of related display
        h (int): Height of related display
        text (str): Text of related display
        filename (str): The related display screen filename
        symbols (str, optional): String of all symbols (macros), if provided

    Returns:
        EdmObject: EdmObject class of related display
    """
    ob = EdmObject("Related Display")
    ob.setDimensions(w, h)
    ob.setPosition(x, y)
    ob.Properties["buttonLabel"] = quoteString(text)
    ob.Properties["numPvs"] = 4
    ob.Properties["numDsps"] = 1
    ob.Properties["displayFileName"] = {0: quoteString(str(filename))}
    if symbols:
        ob.Properties["symbols"] = {0: quoteString(symbols)}
    ob.Properties["fgColor"] = ob.Properties.Colour["Related display"]
    ob.Properties["bgColor"] = ob.Properties.Colour["Canvas"]
    ob.Properties["font"] = quoteString("arial-bold-r-14.0")
    ob.setShadows()
    return ob


def symbol(
    x: int,
    y: int,
    w: int,
    h: int,
    filename: Path,
    pv: str,
    nstates: int,
    truth: bool = False,
) -> EdmObject:
    """Return a symbol with position (x,y) dimensions (w,h).

    For i in nstates: connect values i-1 to i to symbol state i. If truth,
    treat it as a truth table.

    Args:
        x (int): X position of symbol
        y (int): Y position of symbol
        w (int): Width of symbol
        h (int): Height of symbol
        filename (str): Filename of symbol icon
        pv (str): PV that the symbol refers to for its state
        nstates (int): Number of states of the PV
        truth (bool, optional): Flag to determine whether to treat the states
            as a truth table. Defaults to False.

    Returns:
        EdmObject: EdmObject class of symbol
    """
    ob = EdmObject("Symbol")
    ob.setDimensions(w, h)
    ob.setPosition(x, y)
    ob.Properties["file"] = quoteString(str(filename))
    ob.Properties["truthTable"] = truth
    ob.Properties["numStates"] = nstates
    mindict, maxdict = {}, {}
    for i in range(1, nstates):
        if i > 1:
            mindict[i] = i - 1
        maxdict[i] = i
    ob.Properties["minValues"] = mindict
    ob.Properties["maxValues"] = maxdict
    ob.Properties["controlPvs"] = {0: quoteString(pv)}
    ob.Properties["numPvs"] = 1
    ob.Properties["useOriginalColors"] = True
    return ob


def raised_circle(x: int, y: int, w: int, h: int, ta: str = "CO") -> EdmObject:
    """Return a 3d look circle with position (x,y) dimensions (w,h).

    ta gives the colour, ie CO, MO, DI, VA, etc.

    Args:
        x (int): X position of raised circle
        y (int): Y position of raised circle
        w (int): Width of raised circle
        h (int): Height of raised circle
        ta (str, optional): Colour of the raised circle. Defaults to "CO".

    Returns:
        EdmObject: EdmObject class of raised circle
    """
    group = EdmObject("Group")
    top_shadow = EdmObject("Circle")
    top_shadow.setDimensions(w - 2, h - 1)
    top_shadow.setPosition(x, y)
    top_shadow.Properties["lineColor"] = top_shadow.Properties.Colour["Top Shadow"]
    top_shadow.Properties["lineWidth"] = 2
    group.addObject(top_shadow)
    bottom_shadow = EdmObject("Circle")
    bottom_shadow.setDimensions(w - 2, h - 1)
    bottom_shadow.setPosition(x + 2, y + 2)
    bottom_shadow.Properties["lineColor"] = bottom_shadow.Properties.Colour[
        "Bottom Shadow"
    ]
    bottom_shadow.Properties["lineWidth"] = 2
    group.addObject(bottom_shadow)
    base = EdmObject("Circle")
    base.setDimensions(w - 3, h - 3)
    base.setPosition(x + 2, y + 2)
    base.Properties["lineColor"] = base.Properties.Colour[ta + " help"]
    base.Properties["fillColor"] = base.Properties.Colour[ta + " title"]
    base.Properties["lineWidth"] = 3
    base.Properties["fill"] = True
    group.addObject(base)
    sparkle = EdmObject("Circle")
    sparkle.setDimensions(4, 3)
    sparkle.setPosition(x + 12, y + 6)
    sparkle.Properties["lineColor"] = sparkle.Properties.Colour["Top Shadow"]
    sparkle.Properties["fillColor"] = sparkle.Properties.Colour["White"]
    sparkle.Properties["lineWidth"] = 2
    sparkle.Properties["fill"] = True
    group.addObject(sparkle)
    group.setPosition(x, y, move_objects=False)
    group.setDimensions(w, h, resize_objects=False)
    return group


def raised_text_circle(
    x: int,
    y: int,
    w: int,
    h: int,
    text: str,
    font: str = "arial-bold-r-14.0",
    fontAlign: str = "center",
    ta: str = "CO",
) -> EdmObject:
    """Return a 3d look circle with a text label text.

    Has position (x,y) dimensions (w,h), font and fontAlign.
    ta gives the colour, ie CO, MO, DI, VA, etc.

    Args:
        x (int): X position of raised text circle
        y (int): Y position of raised text circle
        w (int): Width of raised text circle
        h (int): Height of raised text circle
        text (str): Text of raised text circle
        font (str, optional): Font name and size. Defaults to "arial-bold-r-14.0".
        fontAlign (str, optional): Aligned of font in raised text circle.
            Defaults to "center".
        ta (str, optional): Colour of the raised text circle. Defaults to "CO".

    Returns:
        EdmObject: EdmObject class of raised text circle
    """
    group = raised_circle(x, y, w, h, ta)
    text_label = label(x, y, w, h, text)
    text_label.Properties["fontAlign"] = quoteString(fontAlign)
    text_label.Properties["font"] = quoteString(font)
    group.addObject(text_label)
    return group


def raised_button_circle(
    x: int, y: int, w: int, h: int, filename: Path, symbols: str, ta: str = "CO"
) -> EdmObject:
    """Return a 3d look circular button.

    Has position (x,y) dimensions (w,h), filename and symbols.
    ta gives the colour, ie CO, MO, DI, VA, etc.

    Args:
        x (int): X position of raised button circle
        y (int): Y position of raised button circle
        w (int): Width of raised button circle
        h (int): Height of raised button circle
        text (str): Text of raised button circle
        filename (str): Filename of symbol icon.
        symbols (str): String of all symbols.
        ta (str, optional): Colour of the raised button circle. Defaults to "CO".

    Returns:
        EdmObject: EdmObject class of raised text circle
    """
    group = raised_circle(x, y, w, h, ta)
    RD = rd(4, 4, 42, 24, filename, symbols)
    group.addObject(RD)
    RD.lowerObject()
    return group


def raised_text_button_circle(
    x: int,
    y: int,
    w: int,
    h: int,
    text: str,
    filename: Path,
    symbols: str,
    font: str = "arial-bold-r-14.0",
    fontAlign: str = "center",
    ta: str = "CO",
) -> EdmObject:
    """Return a 3d look circular button with a text label text.

    Has position (x,y) dimensions (w,h), filename, symbols, font and fontAlign.
    ta gives the colour, ie CO, MO, DI, VA, etc.

    Args:
        x (int): X position of raised text button circle
        y (int): Y position of raised text button circle
        w (int): Width of raised text button circle
        h (int): Height of raised text button circle
        text (str): Text of raised text button circle
        filename (str): Filename of symbol icon.
        symbols (str): String of all symbols.
        font (str, optional): Font name and size. Defaults to "arial-bold-r-14.0".
        fontAlign (str, optional): Aligned of font in raised text button circle.
            Defaults to "center".
        ta (str, optional): Colour of the raised text button circle. Defaults to "CO".

    Returns:
        EdmObject: EdmObject class of raised text circle
    """
    group = raised_button_circle(x, y, w, h, filename, symbols, ta)
    text_label = label(x, y, w, h, text)
    text_label.Properties["fontAlign"] = quoteString(fontAlign)
    text_label.Properties["font"] = quoteString(font)
    group.addObject(text_label)
    return group


def raised_PV_circle(
    x: int, y: int, w: int, h: int, pv: str, ta: str = "CO"
) -> EdmObject:
    """Return a 3d look circle with a PV monitor.

    Has position (x,y) dimensions (w,h).
    ta gives the colour, ie CO, MO, DI, VA, etc.

    Args:
        x (int): X position of raised PV circle
        y (int): Y position of raised PV circle
        w (int): Width of raised PV circle
        h (int): Height of raised PV circle
        pv (str): PV monitor pv
        ta (str, optional): Colour of the raised PV circle. Defaults to "CO".

    Returns:
        EdmObject: EdmObject class of raised PV circle
    """
    group = raised_circle(x, y, w, h, ta)
    PV = text_monitor(x, y, w, h, pv)
    PV.Properties["font"] = quoteString("arial-bold-r-14.0")
    PV.Properties["fontAlign"] = quoteString("center")
    group.addObject(PV)
    return group


def raised_PV_button_circle(
    x: int,
    y: int,
    w: int,
    h: int,
    pv: str,
    filename: Path = Path("generic-help"),
    symbols: str = "draw=$(P).png",
    ta: str = "CO",
) -> EdmObject:
    """Return a 3d look circular button with a a PV monitor.

    Has position (x,y) dimensions (w,h) filename and symbols.
    ta gives the colour, ie CO, MO, DI, VA, etc.

    Args:
        x (int): X position of raised PV button circle
        y (int): Y position of raised PV button circle
        w (int): Width of raised PV button circle
        h (int): Height of raised PV button circle
        pv (str): PV monitor pv
        filename (str): Filename of symbol icon
        symbols (str): String of all symbols
        ta (str, optional): Colour of the raised PV button circle. Defaults to "CO".

    Returns:
        EdmObject: EdmObject class of raised PV button circle
    """
    group = raised_PV_circle(x, y, w, h, pv, ta)
    RD = rd(x + 4, y + 4, w - 8, h - 6, filename, symbols)
    group.addObject(RD)
    RD.lowerObject()
    return group


def raised_PV_shell_circle(
    x: int,
    y: int,
    w: int,
    h: int,
    pv: str,
    command: str = "firefox $(autogen)/documentation/$(P)-help.html",
    ta: str = "CO",
) -> EdmObject:
    """Return a 3d look circular button with a PV monitor and shell command.

    Has position (x,y) dimensions (w,h) filename and symbols.
    ta gives the colour, ie CO, MO, DI, VA, etc.

    Args:
        x (int): X position of raised PV shell circle
        y (int): Y position of raised PV shell circle
        w (int): Width of raised PV shell circle
        h (int): Height of raised PV shell circle
        pv (str): PV monitor pv
        command (str, optional): The command string
        ta (str, optional): Colour of the raised PV shell circle. Defaults to "CO"

    Returns:
        EdmObject: EdmObject class of raised PV shell circle
    """
    group = raised_PV_circle(x, y, w, h, pv, ta)
    RD = shell(x + 4, y + 4, w - 8, h - 6, command)
    group.addObject(RD)
    RD.lowerObject()
    return group


def embed(
    x: int, y: int, w: int, h: int, filename: Path, symbols: Optional[str] = None
) -> EdmObject:
    """Return an embedded window.

    Has position (x,y) dimensions (w,h) filename and symbols.

    Args:
        x (int): X position of embedded window
        y (int): Y position of embedded window
        w (int): Width of embedded window
        h (int): Height of embedded window
        filename (str): Filename of embedded window screen
        symbols (str, optional): String of embedded window symbols

    Returns:
        EdmObject: EdmObject class of embedded window
    """
    ob = EdmObject("Embedded Window")
    ob.setPosition(x, y)
    ob.setDimensions(w, h)
    ob.Properties["displaySource"] = quoteString("menu")
    ob.Properties["filePv"] = quoteString(r"LOC\dummy=i:0")
    ob.Properties["numDsps"] = 1
    ob.Properties["displayFileName"] = {0: str(filename)}
    if symbols:
        ob.Properties["symbols"] = {0: quoteString(symbols)}
    ob.Properties["noScroll"] = True
    return ob


def exit_button(x: int, y: int, w: int, h: int) -> EdmObject:
    """Return an exit button with position (x,y) dimensions (w,h).

    Args:
        x (int): X position of exit button
        y (int): Y position of exit button
        w (int): Width of exit button
        h (int): Height of exit button

    Returns:
        EdmObject: EdmObject class of exit button
    """
    button = EdmObject("Exit Button")
    button.setPosition(x, y)
    button.setDimensions(w, h)
    button.Properties["fgColor"] = button.Properties.Colour["Exit/Quit/Kill"]
    button.Properties["bgColor"] = button.Properties.Colour["Canvas"]
    button.setShadows()
    button.Properties["label"] = quoteString("EXIT")
    button.Properties["font"] = quoteString("arial-medium-r-16.0")
    button.Properties["3d"] = True
    return button


def lines(points: Collection[Tuple[int, int]], col: str = "Black") -> EdmObject:
    """Return a line object with coordinates (x1,y1),(x2,y2),... and colour.

    Args:
        points (Collection[Tuple[int, int]]): List of tuples of (x,y) coordinates
        col (str, optional): Colour of the lines. Defaults to "Black".

    Returns:
        EdmObject: EdmObject class of lines object
    """
    ob = EdmObject("Lines")
    ob.Properties["lineColor"] = ob.Properties.Colour[col]
    ob.Properties["numPoints"] = len(points)
    ob.Properties["xPoints"] = dict((i, x) for i, (x, y) in enumerate(points))
    ob.Properties["yPoints"] = dict((i, y) for i, (x, y) in enumerate(points))
    ob.autofitDimensions()
    return ob


def arrow(x0: int, x1: int, y0: int, y1: int, col: str = "Black") -> EdmObject:
    """Return an arrow from (x0,y0) to (x1,y1) with colour col.

    Args:
        x0 (int): Start x position
        x1 (int): End x position
        y0 (int): Start y position
        y1 (int): End y position
        col (str, optional): Colour of arrow. Defaults to "Black".

    Returns:
        EdmObject: EdmObject class of arrow
    """
    ob = lines([(x0, y0), (x1, y1)], col)
    ob.Properties["arrows"] = quoteString("to")
    return ob


def component_symbol(
    x: int, y: int, w: int, h: int, StatusPv: str, SevrPv: str, filename: Path
) -> EdmObject:
    """Return a component symbol with position (x,y) dimensions (w,h).

    Has a Status PV and Severity PV, and filename.

    Args:
        x (int): X position of component symbol
        y (int): Y position of component symbol
        w (int): Width of component symbol
        h (int): Height of component symbol
        StatusPv (str): Status PV
        SevrPv (str): Severity PV
        filename (str): Filename of symbol

    Returns:
        EdmObject: EdmObject class of component symbol
    """
    if not SevrPv.startswith("LOC") and not SevrPv.startswith("CALC"):
        SevrPv = SevrPv.split(".")[0] + ".SEVR"
    ob = EdmObject("Symbol")
    ob.setDimensions(w, h)
    ob.setPosition(x, y)
    ob.Properties["file"] = quoteString(str(filename))
    ob.Properties["numStates"] = 5
    ob.Properties["minValues"] = {0: 6, 1: 0, 2: 2, 3: 4, 4: 1}
    ob.Properties["maxValues"] = {0: 8, 1: 1, 2: 4, 3: 6, 4: 2}
    ob.Properties["controlPvs"] = {0: quoteString(StatusPv), 1: quoteString(SevrPv)}
    ob.Properties["numPvs"] = 2
    ob.Properties["shiftCount"] = {1: 1}
    ob.Properties["useOriginalColors"] = True
    return ob


def colour_changing_rd(
    x: int,
    y: int,
    w: int,
    h: int,
    name: str,
    StatusPv: str,
    SevrPv: str,
    filename: Path,
    symbols: str = "",
    edl: bool = True,
) -> EdmObject:
    """Return a symbol with an invisible rd behind it.

    Has a Status PV and Severity PV, filename and symbols.
    Changes col based on STA and SEVR PVs.


    Args:
        x (int): X position of colour changing related display
        y (int): Y position of colour changing related display
        w (int): Width of colour changing related display
        h (int): Height of colour changing related display
        name (str): Name of colour changing related display label
        StatusPv (str): Status PV
        SevrPv (str): Severity PV
        filename (str): Filename of colour changing related display screen
        symbols (str, optional): Symbols of colour changing rd. Defaults to "".
        edl (bool, optional): Flag to determine if being generated using
            another edl file. Defaults to True.

    Returns:
        EdmObject: _description_
    """
    obgroup = EdmObject("Group")
    if edl:
        obgroup.addObject(rd_visible(x, y, w, h, "", filename, symbols))
    else:
        obgroup.addObject(shell_visible(x, y, w, h, "", str(filename)))
    obtext = label(x + 2, y + 2, w - 4, h - 4, name, fontAlign="center")
    obtext.Properties["font"] = quoteString("arial-bold-r-14.0")
    obtext.Properties["fgColor"] = obtext.Properties.Colour["Related display"]
    obtext.Properties["bgAlarm"] = True
    obtext.Properties["alarmPv"] = quoteString(SevrPv)
    obtext.Properties["visPv"] = quoteString(StatusPv)
    obtext.Properties["visMin"] = quoteString("1")
    obtext.Properties["visMax"] = quoteString("2")
    obtext.Properties["useDisplayBg"] = False
    obtext2 = obtext.copy()
    obtext.Properties["visInvert"] = True
    obtext2.Properties["bgColor"] = obtext.Properties.Colour["Monitor: NORMAL"]
    obgroup.addObject(obtext)
    obgroup.addObject(obtext2)
    obgroup.autofitDimensions()
    return obgroup


def flip_axis(direction: str):
    """Create a set of axis for a beam going left or right.

    Args:
        direction (str): Direction of beam

    Returns:
        EdmObject: EdmObject of beam
    """
    # create a set of axis for a beam going left or right
    group = EdmObject("Group")
    if direction == "left":
        zlab = label(50, 50, 10, 20, "Z", "center")
        zlab.Properties["font"] = quoteString("arial-bold-r-14.0")
        group.addObject(zlab)
        z = arrow(5, 45, 60, 60, "grey-13")
        group.addObject(z)
        y = arrow(5, 5, 60, 20, "grey-13")
        group.addObject(y)
        ylab = label(0, 0, 10, 16, "Y", "center")
        ylab.Properties["font"] = quoteString("arial-bold-r-14.0")
        group.addObject(ylab)
        xlab = label(40, 20, 77, 32, "X (into \n    screen)", "center")
        xlab.Properties["font"] = quoteString("arial-bold-r-14.0")
        group.addObject(xlab)
        x = arrow(5, 35, 60, 45, "Black")
        group.addObject(x)
    else:
        zlab = label(5, 25, 10, 15, "Z", "center")
        zlab.Properties["font"] = quoteString("arial-bold-r-14.0")
        group.addObject(zlab)
        z = arrow(40, 0, 45, 45, "Black")
        group.addObject(z)
        y = arrow(40, 40, 45, 5, "Black")
        group.addObject(y)
        ylab = label(15, 0, 20, 20, "Y", "center")
        ylab.Properties["font"] = quoteString("arial-bold-r-14.0")
        group.addObject(ylab)
        xlab = label(50, 30, 69, 32, "X (out of  \n   screen)", "center")
        xlab.Properties["font"] = quoteString("arial-bold-r-14.0")
        group.addObject(xlab)
        x = arrow(40, 70, 45, 65, "grey-13")
        group.addObject(x)
    group.autofitDimensions()
    return group
