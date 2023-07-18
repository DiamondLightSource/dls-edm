"""Takes a signal list and creates the vacuum synoptic from the _GUI_VA sheet."""

from typing import Dict, List, Optional

from .common import dummy, label, rd, rectangle, symbol, text_monitor, tooltip
from .edmObject import EdmObject, quoteString
from .edmTable import EdmTable
from .flip_horizontal import Flip_horizontal
from .titlebar import Titlebar

author = "Tom Cobb"
usage = """%prog [options] <xls_file>"""


def pressure(
    x: int,
    y: int,
    w: int,
    h: int,
    pv: str,
    showUnits: bool = False,
    fontAlign: str = "left",
) -> EdmObject:
    """Make a pressure object.

    Args:
        x (int): X position of pressure object
        y (int): Y position of pressure object
        w (int): Width of pressure object
        h (int): Height of pressure object
        pv (str): PV of pressure object
        showUnits (bool, optional): Flag to determine if units are shown.
            Defaults to False.
        fontAlign (str, optional): Font alignment setting. Defaults to "left".

    Returns:
        EdmObject: Pressure EdmObject class
    """
    ob = text_monitor(x, y, w, h, pv, showUnits, fontAlign)
    ob["format"] = quoteString("exponential")
    ob["objType"] = quoteString("monitors")
    return ob


def gaugeRd(
    x: int, y: int, w: int, h: int, PREFIX: str, GID: str, GCTLR: str
) -> EdmObject:
    """Make a gauge object.

    Args:
        x (int): _description_
        y (int): _description_
        w (int): _description_
        h (int): _description_
        PREFIX (str): _description_
        GID (str): _description_
        GCTLR (str): _description_

    Returns:
        EdmObject: _description_
    """
    ob = rd(x, y, w, h, "mks937aGauge.edl", f"dom=$(dom), id={GID}")
    assert isinstance(ob["displayFileName"], Dict)
    ob["displayFileName"][1] = quoteString("mks937a.edl")
    assert isinstance(ob["symbols"], Dict)
    ob["symbols"][1] = quoteString(f"device={PREFIX}{GCTLR}")
    ob["numDsps"] = 2
    return ob


def Vacuum(
    row_dicts: List[Dict[str, str]],
    title: str = "BLxxI-VA",
    domain: Optional[str] = None,
    flipped_paths: Optional[List[str]] = None,
) -> EdmObject:
    """Create a vacuum screen from a row_dicts.

    row_dicts should be a list of dicts where each dict can contain the
    following values:
    { 'PREFIX': 'BLxxI-VA-', # Prefix for IONP,RGA,IMG,etc.
      'WALL': 'Left', # Draw a wall, can be Left or Right
      'IONP': 'IONP-01', # Draw IONP symbol: PREFIX+IONP = Ion Pump PV
      'RGA': 'RGA-01', # Draw RGA symbol: PREFIX+RGA = RGA PV
      'SPACE': 'SPACE-01', # Draw Vacuum Space: PREFIX+SPACE = Space PV
      'IMG': 'IMG-01', # Draw IMG symbol: PREFIX+IMG = IMG PV
      'PIRG': 'PIRG-01', # Draw Pirg symbol: PREFIX+PIRG = PIRG PV
      'VALVE': 'FE11I-VA-VALVE-01', # Draw valve symbol, VALVE = Valve PV
      'GID': '01', # Gauge ID: needed for IMG & PIRG
      'GCTLR': 'GCTLR-01' # PREFIX+GCCTLR = Gauge Ctlr PV, needed for IMG & PIRG
    }
    title is the screen title, like BLxxI-VA-OH. domain is BLxxI, or can be
    obtained from the title. If flipped_paths are defined, they should be a list of
    paths where the flipped symbols could be found. If flipped_paths, the screen is
    flipped before being output.

    Args:
        row_dicts (List[Dict[str, str]]): Dictionary representing a line from
            the spreadsheet.
        title (str, optional): Screen title. Defaults to "BLxxI-VA".
        domain (Optional[str], optional): The beamline domain, e.g. BLxxI.
            Defaults to None.
        flipped_paths (Optional[List[str]], optional): List of paths to flipped symbols.
            Defaults to None.

    Returns:
        EdmObject: Vacuum EdmObject class
    """
    screen = EdmObject("Screen")
    table = EdmTable(xborder=0, yborder=16)
    screen.addObject(table)
    if flipped_paths is not None:
        align = "right"
    else:
        align = "left"
    # set the domain or work it out from the title
    if domain:
        domain = domain
    else:
        domain = title.split("-")[0]
    # line_cons[x] = [ob] where obs are symbols to be connected with black line
    line_cons: Dict = {}
    # spaces = [(PREFIX,text,ob)] where obs are valves to be connected with a
    #          space symbol, labelled with text
    spaces = []
    # wall obs = [ob] where ob is an object to fit a wall around
    wall_obs = []
    for dict in row_dicts:
        # set PREFIX
        if "PREFIX" in dict:
            PREFIX = dict["PREFIX"]
        else:
            PREFIX = ""
        # add VALVE
        if "VALVE" in dict or "WALL" in dict or "SPACE" in dict:
            if "VALVE" in dict:
                # add the valve, aperture or window symbol
                VALVE = dict["VALVE"]
                ob = EdmObject("Group")
                if VALVE.upper().find("WIND") > -1:
                    ob.addObject(tooltip(0, 0, 16, 32, VALVE))
                    ob.addObject(rectangle(0, 0, 16, 32))
                elif VALVE.upper().find("APER") > -1:
                    ob.addObject(tooltip(0, 0, 16, 32, VALVE))
                    ob.addObject(
                        symbol(
                            0,
                            0,
                            16,
                            32,
                            "symbols-vacuum-aperture-symbol.edl",
                            r"LOC\\dummy0=i:0",
                            2,
                        )
                    )
                else:
                    ob.addObject(tooltip(0, 0, 16, 32, "Valve: " + VALVE))
                    ob.addObject(rd(0, 0, 16, 32, "vacuumValve.edl", "device=" + VALVE))
                    ob.addObject(
                        symbol(
                            0, 0, 16, 32, "vacuumValve-symbol.edl", VALVE + ":STA", 6
                        )
                    )
                # a space symbol will be added later
                if "SPACE" in dict:
                    spaces.append((PREFIX, dict["SPACE"], ob))
                else:
                    spaces.append(("", "", ob))
            else:
                # if no valve, put in a dummy placeholder
                ob = dummy(0, 0, 16, 32)
                if "SPACE" in dict:
                    spaces.append((PREFIX, dict["SPACE"], ob))
            # add in the left wall
            if "WALL" in dict and dict["WALL"].upper() == "LEFT":
                wall_obs.append(ob)
            table.addObject(ob, y=3)
            table.nextCol()
        x = table["__def_x"]
        line_cons[x] = []
        has_things = False
        # add RGA
        if "RGA" in dict:
            RGA = dict["RGA"]
            ob = EdmObject("Group")
            ob.addObject(tooltip(0, 0, 32, 32, "Residual Gas Analyser: " + RGA))
            ob.addObject(rd(0, 0, 32, 32, "rga.edl", "device=" + PREFIX + RGA))
            ob.addObject(
                symbol(0, 0, 32, 32, "rga-symbol.edl", PREFIX + RGA + ":STA", 11)
            )
            ob.addObject(label(36, 0, 60, 16, RGA, fontAlign=align))
            table.addObject(ob)
            line_cons[x].append(ob)
        table.nextCell()
        # add GCTLR
        if "GID" in dict:
            GID = dict["GID"]
            if len(GID) < 2:
                GID = "0" + GID[0]
            GCTLR = dict["GCTLR"]
        # add PIRGs
        if "PIRG" in dict:
            PIRG = dict["PIRG"]
            ob = EdmObject("Group")
            ob.addObject(tooltip(0, 0, 32, 32, "Pirani Gauge: " + PIRG))
            ob.addObject(gaugeRd(0, 0, 32, 32, PREFIX, GID, GCTLR))
            ob.addObject(
                symbol(
                    0, 0, 32, 32, "mks937aPirg-symbol.edl", PREFIX + PIRG + ":STA", 17
                )
            )
            ob.addObject(label(36, 0, 60, 16, PIRG, fontAlign=align))
            ob.addObject(
                pressure(36, 16, 60, 16, PREFIX + PIRG + ":P", fontAlign=align)
            )
            table.addObject(ob)
            line_cons[x].append(ob)
        table.nextCell()
        # add IMGs
        if "IMG" in dict:
            IMG = dict["IMG"]
            ob = EdmObject("Group")
            ob.addObject(tooltip(0, 0, 32, 32, "Inverted Magnetron Gauge: " + IMG))
            ob.addObject(gaugeRd(0, 0, 32, 32, PREFIX, GID, GCTLR))
            ob.addObject(
                symbol(0, 0, 32, 32, "mks937aImg-symbol.edl", PREFIX + IMG + ":STA", 17)
            )
            ob.addObject(label(36, 0, 60, 16, IMG, fontAlign=align))
            ob.addObject(pressure(36, 16, 60, 16, PREFIX + IMG + ":P", fontAlign=align))
            table.addObject(ob)
            line_cons[x].append(ob)
        table.nextCell()
        if "GID" in dict or "IONP" in dict or "RGA" in dict:
            has_things = True
            ob = dummy(0, 0, 32, 32)
            table.addObject(ob)
            line_cons[x].append(ob)
        table.nextCell()
        # add IONP
        if "IONP" in dict:
            IONP = dict["IONP"]
            ob = EdmObject("Group")
            ob.addObject(tooltip(0, 0, 32, 32, "Ion Pump: " + IONP))
            ob.addObject(
                rd(0, 0, 32, 32, "digitelMpcIonpControl.edl", "device=" + PREFIX + IONP)
            )
            ob.addObject(
                symbol(
                    0,
                    0,
                    32,
                    32,
                    "digitelMpcIonp-symbol.edl",
                    PREFIX + IONP + ":STA",
                    10,
                )
            )
            ob.addObject(label(36, 0, 60, 16, IONP, fontAlign=align))
            ob.addObject(
                pressure(36, 16, 60, 16, PREFIX + IONP + ":P", fontAlign=align)
            )
            table.addObject(ob)
            line_cons[x].append(ob)
        table.nextCell()
        # add WALL
        if "WALL" in dict and dict["WALL"].upper() == "RIGHT":
            ob = dummy(0, 0, 32, 32)
            wall_obs.append(ob)
            table.nextCol()
            table.addObject(ob, y=3)
        table.nextCol()
    if has_things:
        # put in a dummy group to make the last space
        ob = dummy(0, 0, 2, 32)
        spaces.append(("", "", ob))
        table.addObject(ob, y=3)

    # resize the screen so we know where the objects are
    screen.autofitDimensions()
    table.ungroup()

    # create the walls
    for ob in wall_obs:
        x, y = ob.getPosition()
        w, h = ob.getDimensions()
        group = EdmObject("Group")
        top = EdmObject("Rectangle")
        top.setPosition(int(x + w / 2 - 5), y - 143)
        top.setDimensions(10, 138)
        top["fill"] = True
        top["fillColor"] = top.Colour["grey-13"]
        top["lineColor"] = top.Colour["Black"]
        group.addObject(top)
        bottom = EdmObject("Rectangle")
        bottom.setPosition(int(x + w / 2 - 5), y + h + 5)
        bottom.setDimensions(10, 64)
        bottom["fill"] = True
        bottom["fillColor"] = bottom.Colour["grey-13"]
        bottom["lineColor"] = bottom.Colour["Black"]
        group.addObject(bottom)
        group.autofitDimensions()
        screen.addObject(group)

    # create the lines
    for x in list(line_cons.keys()):
        obs = line_cons[x]
        if obs:
            x = obs[0].getPosition()[0] + 17
            ys = [o.getPosition()[1] for o in obs]
            miny, maxy = min(ys) + 16, max(ys) + 16
            line = EdmObject("Lines")
            assert isinstance(x, (int, float))
            line.setPosition(int(x), miny, move_objects=False)
            line.setDimensions(0, maxy - miny, resize_objects=False)
            line["lineColor"] = line.Colour["Black"]
            line["lineWidth"] = 2
            line["xPoints"] = {0: x, 1: x}
            line["yPoints"] = {0: miny, 1: maxy}
            screen.addObject(line)
            line.lowerObject()

    # create the spaces
    pairs = [
        (spaces[i][0], spaces[i][1], spaces[i][2], spaces[i + 1][2])
        for i in range(len(spaces) - 1)
    ]
    for PREFIX, text, ob1, ob2 in pairs:
        (ob1x, ob1y), (ob2x, _) = ob1.getPosition(), ob2.getPosition()
        (ob1w, ob1h), (_, _) = ob1.getDimensions(), ob2.getDimensions()
        ob = EdmObject("Group")
        ob.addObject(
            tooltip(
                ob1x + ob1w + 2,
                ob1y + int(ob1h / 2 - 4),
                ob2x - ob1x - ob1w - 4,
                8,
                "Vacuum Space: " + text,
            )
        )
        ob.addObject(
            rd(
                ob1x + ob1w + 2,
                ob1y + int(ob1h / 2 - 4),
                ob2x - ob1x - ob1w - 4,
                8,
                "space.edl",
                "device=" + PREFIX + text,
            )
        )
        ob.addObject(
            symbol(
                ob1x + ob1w,
                ob1y + int(ob1h / 2 - 4),
                ob2x - ob1x - ob1w,
                8,
                "symbols-vacuum-symbol.edl",
                PREFIX + text + ":STA",
                3,
                True,
            )
        )
        ob.addObject(label(ob1x + ob1w + 28, ob1y - 4, 80, 16, text, fontAlign=align))
        ob.addObject(
            pressure(
                ob1x + ob1w + 20,
                ob1y + ob1h - 12,
                80,
                16,
                PREFIX + text + ":P",
                True,
                fontAlign=align,
            )
        )
        screen.addObject(ob)

    # create screen
    hutchText = title
    if title.find("OH") > -1:
        hutchText = "Optics Hutch " + title[title.find("OH") + 2].replace(".", "-")
    if title.find("EH") > -1:
        hutchText = "Experiment Hutch " + title[title.find("EH") + 2].replace(".", "-")
    if title.find("EE") > -1:
        hutchText = "Experimental Enclosure " + title[title.find("EE") + 2].replace(
            ".", "-"
        )
    if title.find("BE") > -1:
        hutchText = "Branchline Enclosure " + title[title.find("BE") + 2].replace(
            ".", "-"
        )
    screen["title"] = quoteString(title.split(".")[0])
    if flipped_paths is not None:
        screen = Flip_horizontal(screen, flipped_paths, flip_group_contents=True)
    Titlebar(
        screen,
        ta="VA",
        button="text",
        button_text=domain,
        header="text",
        header_text=hutchText + " Vacuum Summary",
        tooltip="generic-vacuum-tooltip",
        title=title.split(".")[0],
    )
    return screen


# testing option commented out as it requires BLGen
# def cl_vacuum():
#    from excel_parser import ExcelHandler
#    from subst_file import gen_subst_files
#    parser = OptionParser(usage)
#    parser.add_option("-f","--flip",action="store",type="string",dest="flip",\
#                      help="Flip the vacuum screen so beam is right -> left")
#    (options, args) = parser.parse_args()
#    assert len(args)==1, "Incorrect number of arguments - "+\
#                         "run the program with -h for help"
#    e = ExcelHandler(args[0])
#    subst_files = []
#    for (name,table) in e.tables:
#        if name in ["!GUI-VA","_GUI_VA"]:
#            subst_files.extend(gen_subst_files(table,def_ioc_column=-1))
#    for subst_file in subst_files:
#        if options.flip:
#            screen = Vacuum(subst_file.subst,filename,flipped_paths=".")
#        else:
#            screen = Vacuum(subst_file.subst,filename)
#        open(filename,"w").write(screen.read())
#        print "Vacuum screen written to: "+filename
#
# if __name__=="__main__":
#    cl_vacuum()
