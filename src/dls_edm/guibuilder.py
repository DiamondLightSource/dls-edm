"""
GuiBuilder generator script.

Author: Tom Cobb
Updated to Python3 by: Oliver Copping
"""

import argparse
import re
import sys
from copy import copy
from math import sqrt
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple, TypedDict, Union
from xml.dom import minidom
from xml.dom.minidom import Element

from .common import colour_changing_rd, embed, label, lines
from .edmObject import EdmObject, quoteString
from .edmTable import EdmTable
from .flip_horizontal import Flip_horizontal
from .generic import Generic
from .substitute_embed import Substitute_embed
from .titlebar import Titlebar


class ScreenOptions(TypedDict):
    """TypedDict for Screen arguments."""

    filename: Path
    macros: str
    embedded: bool
    tab: bool


class GBObject(object):
    """GuiBuilder Object class."""

    def __init__(
        self,
        name: str,
        macrodict: Optional[Dict[str, str]] = None,
        children: Optional[List["GBObject"]] = None,
    ) -> None:
        """GuiBuilder constructor.

        Args:
            name (str): Name of screen.
            macrodict (Optional[Dict[str, str]], optional): Dictionary of macros.
                Defaults to None.
            children (Optional[Dict[str, EdmObject]], optional): List of child
                GBObjects. Defaults to None.
        """
        self.name = name
        if macrodict:
            self.macrodict = macrodict.copy()
        else:
            self.macrodict = {}
        self.macrodict["NAME"] = self.name
        self.macrodict["FILE"] = ""
        self.macrodict["EDM_MACROS"] = ""
        if children:
            self.children = children
        else:
            self.children = []

        self.screens: List[GBScreen]
        self.shells: List[GBShell]
        self.records: List[GBRecord]

        self.screens, self.shells, self.records = ([], [], [])

    # @overload
    # def addScreen(**options: Unpack) -> None:
    #     ...

    # @overload
    # def addScreen(self, **options: Options) -> None:
    #     ...

    def addScreen(
        self,
        filename: str,
        macros: str = "",
        embedded: bool = False,
        tab: bool = False,
        # **kwargs: Unpack[ScreenOptions],
    ) -> None:
        """Add screen to GuiBuilder object.

        Args:
            filename (Path): File name of the screen to add.
            macros (str, optional): String of macros for the screen. Defaults to "".
            embedded (bool, optional): Flag to determine if the screen is embedded.
                Defaults to False.
            tab (bool, optional): Flag to determine if there are tab widgets.
                Defaults to False.
        """
        # assert_type(kwargs, ScreenOptions)

        # kws: ScreenOptions = {
        #     "filename": Path(),
        #     "macros": "",
        #     "embedded": False,
        #     "tab": False,
        # }

        # From https://stackoverflow.com/a/65965731
        # In Python 3.12 this probably won't be needed due to PEP 692
        # def kwargs_get(d, *k):
        #     print(d, k)
        #     for i in k:
        #         # yield d[i]
        #         kws[i] = d[i]

        # kwargs_get(kwargs, *kwargs)

        # filename, macros, embedded, tab = kws.values()

        macros = macros.replace(",undefined)", ")").rstrip("\r")
        mdict = {}
        # make sure edm gets '' for empty macros
        for k, v in [x.split("=") for x in macros.split(",") if x]:
            if not v.strip():
                v = "''"
            mdict[k.strip()] = v.strip()
        macros = ",".join([f"{k}={v}" for k, v in mdict.items()])
        self.screens.append(GBScreen(filename, macros, embedded, tab))
        if embedded is False and tab is False:
            for k, v in [x.split("=") for x in macros.split(",") if x]:
                self.macrodict[k.strip()] = v.strip()
            self.macrodict["NAME"] = self.name
            self.macrodict["FILE"] = (
                filename if isinstance(filename, str) else str(filename)
            )
            self.macrodict["EDM_MACROS"] = macros

    def addShell(self, command: str) -> None:
        """Add shell command object.

        Args:
            command (str): Shell command to attach to the object.
        """
        self.shells.append(GBShell(command))

    def addRecord(self, pv: str, sevr: bool = False) -> None:
        """Add record object.

        Args:
            pv (str): PV name for record
            sevr (bool, optional): Flag to detemine if the record has a severity.
                Defaults to False.
        """
        self.records.append(GBRecord(pv, sevr))


class GBScreen(object):
    """GuiBuilder screen object."""

    filename: Path
    macros: str
    embedded: bool
    tab: bool

    def __init__(self, filename: Path, macros: str, embedded: bool, tab: bool) -> None:
        """Guibuilder screen constructor."""
        self.__dict__.update(locals())


class GBShell(object):
    """Guibuilder shell object."""

    command: str

    def __init__(self, command: str) -> None:
        """Guibuilder screen constructor."""
        self.__dict__.update(locals())


class GBRecord(object):
    """GuiBuilder record object."""

    pv: str
    sevr: bool

    def __init__(self, pv: str, sevr: bool) -> None:
        """Guibuilder screen constructor."""
        self.__dict__.update(locals())


SILENT = 0
WARN = 1
ERROR = 2


class GuiBuilder:
    """GuiBuilder class."""

    def __init__(self, dom: str = "", errors: int = ERROR) -> None:
        """Guibuilder class constructor.

        Args:
            dom (str, optional): Beamline domain. Defaults to "".
            errors (int, optional): Debug level. Defaults to ERROR.
        """
        # setup our list of objects, fetched from the xml in parseXml()
        self.objects: List[GBObject] = []
        self.dom = dom
        self.errors = errors
        # initialise paths
        self.paths: List[Path] = []
        self.devpaths: List[Path] = []
        self.RELEASE: Path = Path()
        # initialise record text
        self.dbtext = ""

    def parseArgs(self):
        """Parse the args of the Guibuilder class."""
        # first parse the args
        parser = argparse.ArgumentParser(
            prog="GuiBuilder", description="Builds gui files by parsing xml file"
        )
        parser.add_argument("xml", nargs=1, type=Path)
        parser.add_argument("release", nargs=1, type=Path)
        parser.add_argument(
            "--db", dest="db", default="", help="Write status records to this db file"
        )
        args = parser.parse_args()

        # "%prog [options] <BLxxI-gui.xml> <RELEASE>\n"

        # store options
        self.db = args.db
        self.parseRelease(Path.absolute(args.release[0]))
        self.parseXml(args.xml[0])

    def parseRelease(self, RELEASE: Path) -> None:
        """Parse the release tree.

        Args:
            RELEASE (str): The path to the module root, or the configure/RELEASE
                file.
        """
        # now parse the tree
        from dls_dependency_tree import dependency_tree

        self.RELEASE = RELEASE
        tree = dependency_tree(None, str(self.RELEASE))
        if "BLGui" not in [x.name for x in tree.leaves]:
            prefix = Path(tree.e.prodArea()).joinpath("BLGui")
            p = prefix.joinpath(
                tree.e.sortReleases([str(p) for p in prefix.iterdir()])[-1]
            )
            tree.leaves.append(dependency_tree(tree, module_path=str(p)))
        self.paths = [Path(p) for p in tree.paths()]
        self.devpaths = [
            Path(p) for p in tree.paths(["/*App/op*/edl", "/*App/op*/symbol"])
        ]

    def parseXml(self, xml: Path) -> None:
        """Parse xml of Guibuilder object.

        Args:
            xml (str): XML file in string format.
        """
        self.xml = xml
        # open the xml file
        xml_root: minidom.Document = minidom.parse(str(self.xml))
        # find the root node
        c_node: Element = self._elements(xml_root)[0]
        # populate them from our elements
        for node in self._elements(c_node):
            assert isinstance(node, Element)
            name = str(node.nodeName)
            if name == "Def":
                name = str(node.getAttribute("name"))
            gob = self.object(name)
            # for each object name, populate screens shells and records
            for ob in self._elements(node):
                typ = str(ob.nodeName)
                if typ in ["edm", "edmembed", "edmtab"]:
                    args: ScreenOptions = {
                        "filename": Path(),
                        "macros": "",
                        "embedded": False,
                        "tab": False,
                    }
                    if typ == "edmembed":
                        args["embedded"] = True
                    elif typ == "edmtab":
                        args["tab"] = True
                    # now make a GBScreen out of it
                    for k, v in list(ob.attributes.items()):
                        assert k in ["filename", "macros"]
                        if k == "filename":
                            args["filename"] = Path(v)
                        elif k == "macros":
                            args["macros"] = str(v)
                    gob.addScreen(**args)
                elif typ in ["shell"]:
                    # now make a GBShell out of it
                    gob.addShell(str(ob.getAttribute("command")))
                elif typ in ["sevr", "status"]:
                    if typ == "sevr":
                        sevr = True
                    else:
                        sevr = False
                    # now make a GBRecord out of it
                    gob.addRecord(str(ob.getAttribute("pv")), sevr)

    def _elements(self, xml: Union[minidom.Document, Element]) -> List[Element]:
        assert isinstance(xml, minidom.Document) or (
            isinstance(xml, Element) and xml.hasChildNodes()
        )
        return [n for n in xml.childNodes if n.nodeType == n.ELEMENT_NODE]

    def get(
        self, name: str, glob: bool = True, without: Optional[List[str]] = None
    ) -> List[GBObject]:
        """Get all GBObjects with names matching name.

        If glob then do simple wildcard * expansion, otherwise do regex expansion.

        Args:
            name (str): Name of objects to find.
            glob (bool, optional): Flag to determine whether to do wildcard expansion
                or regex expansion. Defaults to True.
            without (Optional[List[str]], optional): List of object names to filter
                from available objects. Defaults to None.

        Returns:
            List[GBObject]: List of GBObjects with matching names as name
        """

        def _check_objs(objects: List[GBObject]) -> List[GBObject]:
            ret_objs: List = []
            for o in objects:
                assert isinstance(o, GBObject)
                assert without is not None

                matched = re.match(name, o.name)
                if (
                    matched is not None
                    and matched.end() == len(o.name)
                    and o.name not in without
                ):
                    ret_objs.append(o)
            return ret_objs

        if glob:
            name = name.replace(".", r"\.").replace("*", r"[^\.]*")
        # filter the list of available objects
        if without is None:
            without = []

        ret = _check_objs(self.objects)
        return ret

    def error(self, text: str) -> None:
        """Determine the outcome of an error being thrown.

        If self.errors == ERROR, raise an error.
        If self.errors == WARN, print warning message to console.

        Args:
            text (str): Error/warning message

        Raises:
            AssertionError: Error if self.errors == ERROR
        """
        if self.errors == ERROR:
            raise AssertionError(text)
        elif self.errors == WARN:
            print("***Warning: " + text, file=sys.stderr)

    def object(
        self,
        name: str,
        desc: str = "",
        P: str = "",
        obs: List[GBObject] = [],
        filename: Optional[Path | str] = None,
        macrodict: Optional[Dict] = None,
        preferEmbed: bool = True,
        preferTab: bool = True,
        substituteEmbed: bool = False,
        ar: Optional[float] = None,
        d: str = ".",
        max_y: Optional[int] = None,
    ) -> GBObject:
        """Associate a group of objects with a name, prefix and filename.

        If filename is None then an autogenerated screen will be produced.
        Status records will be produced if writeRecords is called.
        This information  will also be used to autofill icons if autofilled is
        called on an overview screen.

        Args:
            name (str): Name of object
            desc (str, optional): Description of object. Defaults to "".
            P (str, optional): Prefix of object. Defaults to "".
            obs (List[GBObject], optional): List of child objects. Defaults to [].
            filename (Optional[Path | str], optional): Screen filename. Defaults to None.
            macrodict (Optional[Dict], optional): Dictionary of macros.
                Defaults to None.
            preferEmbed (bool, optional): Flag to determine if the screen should
                be embedded. Defaults to True.
            preferTab (bool, optional): Flag to determine if the screen should
                be in a tab. Defaults to True.
            substituteEmbed (bool, optional): Flag to determine if embedded windows
                in a screen are substutured for groups containing their contents.
                Defaults to True.
            ar (Optional[float], optional): Aspect ratio. Defaults to None.
            d (str, optional): Directory. Defaults to ".".
            max_y (Optional[int], optional): Max number of cells in Y.
                Defaults to None.

        Returns:
            GBObject: GBObject class
        """

        # first make an object to fill in
        if macrodict is None:
            macrodict = {}
        macrodict["NAME"] = name
        macrodict["DESCRIPTION"] = desc
        if P:
            macrodict["P"] = P

        # Check if object with the same name already exists to avoid duplication
        ob_exists = [o for o in self.objects if o.name == name]
        if ob_exists:
            ob = ob_exists[0]
            # overwrite with new macrodict items
            for k, v in macrodict.items():
                ob.macrodict[k] = v
        else:
            ob = GBObject(name, macrodict, obs)
            self.objects.append(ob)

        # if we are given a P, this means we should write records for it
        if P:
            self.__writeRecord(ob, obs)

        # if we are not given a filename, we should make a screen for it
        macros = ",".join(f"{k}={v}" for k, v in list(macrodict.items()))
        if filename is None and obs:
            filename = Path(f"{d}/{name}.edl")
            if self.errors:
                print(f"Creating screen for {name}")
            screenobs = self.__screenObs(name, obs, preferEmbed, preferTab)
            if screenobs:
                # only one display which is not embedded, so just add launch this screen
                if (
                    len(screenobs) == 1
                    and screenobs[0].Properties.Type == "Group"
                    and screenobs[0].Objects[0].Properties.Type == "Related Display"
                ):
                    screenob = screenobs[0].Objects[0]
                    if "symbols" in screenob.Properties:
                        screenob_macros = screenob.Properties["symbols"]
                        assert isinstance(screenob_macros, Dict)
                        macros = screenob_macros[0].strip('"')
                    else:
                        macros = ""
                else:
                    screen = Generic(
                        screenobs, auto_x_y_string=P, ideal_a_r=ar, max_y=max_y
                    )
                    macros = ""
                    screen = Titlebar(
                        screen,
                        button_text=name,
                        header_text=desc,
                        title="Device - %s" % name,
                    )
                    if substituteEmbed:
                        screen = Substitute_embed(
                            screen, self.paths, {}, ungroup=False
                        ).get_substituted_screen()
                    open(filename, "w").write(screen.read())

        # if there is now a filename of some kind then add a screen to the object
        if filename is not None:
            filename = Path(filename) if isinstance(filename, str) else filename

            args: ScreenOptions = {
                "filename": filename,
                "macros": macros,
                "embedded": False,
                "tab": False,
            }
            ob.addScreen(**args)
        return ob

    def __screenObs(
        self,
        name: str,
        obs: List[GBObject],
        preferEmbed: bool = True,
        preferTab: bool = True,
    ) -> List[EdmObject]:
        zero = r"LOC\dummy0=i:0"
        # create the actual screen obs
        out: list[EdmObject] = []
        tabobs: list[tuple] = []
        for ob in obs:
            # First calculate the status and severity Pvs
            StatusPv = [r.pv for r in ob.records if not r.sevr]
            SevrPv = [r.pv for r in ob.records if r.sevr]
            # now create a combined pv
            args = dict()
            for attr in ["StatusPv", "SevrPv"]:
                pvs = locals()[attr]
                # now work out the combined pvs
                if len(pvs) == 0:
                    pv = zero
                elif len(pvs) == 1:
                    pv = pvs[0]
                else:
                    letters = "|".join(chr(65 + j) for j in range(len(pvs)))
                    if attr == "StatusPv":
                        pv = r"CALC\{(%s)>0?1:0}(%s)" % (letters, ",".join(pvs))
                    else:
                        pv = r"CALC\{%s}(%s.SEVR)" % (letters, ".SEVR,".join(pvs))
                args[attr] = pv
            # now work out a reasonable label
            label = ob.name
            if name:
                label = label.replace(name + ".", "").replace(
                    name.split(".")[0] + ".", ""
                )
            # now create rds for shells
            for shell in ob.shells:
                out.append(
                    colour_changing_rd(
                        0,
                        0,
                        90,
                        20,
                        name=label,
                        edl=False,
                        filename=shell.command,
                        symbols="",
                        **args,
                    )
                )
            # filter the screens for embedded and related displays
            embeds = [s for s in ob.screens if s.embedded]
            tabs = [s for s in ob.screens if s.tab]
            rds = [s for s in ob.screens if not s.embedded and not s.tab]
            # if preferEmbed then filter out rds
            if preferTab and len(tabs) > 0:
                rds = []
                embeds = []
            elif preferEmbed and len(embeds) > 0:
                rds = []
                tabs = []
            elif len(rds) > 0:
                embeds = []
                tabs = []
            # now add the rds
            for rd in rds:
                out.append(
                    colour_changing_rd(
                        0,
                        0,
                        90,
                        20,
                        name=label,
                        edl=True,
                        filename=rd.filename,
                        symbols=rd.macros,
                        **args,
                    )
                )
            # then embedded screens
            for e in embeds:
                try:
                    e_macrodict = {
                        k: v for k, v in [x.split("=") for x in e.macros.split(",")]
                    }
                # If no macrodict is provided, make an empty dict
                except ValueError:
                    e_macrodict = {}
                if str(e.filename) == "." and "filename" in e_macrodict.keys():
                    e.filename = Path(e_macrodict["filename"])
                filename = (
                    Path(e.filename) if isinstance(e.filename, str) else e.filename
                )
                self.__load_screen(filename)

                eob = embed(
                    0,
                    0,
                    0,
                    0,
                    filename,
                    ",".join([e.macros, "label=" + label]),
                )
                eob.setDimensions(
                    *Substitute_embed.in_screens[filename].getDimensions()
                )
                out.append(eob)
            # finally create tab widgets
            for e in tabs:
                filename = e.filename
                self.__load_screen(filename)
                w, h = Substitute_embed.in_screens[filename].getDimensions()
                tabobs.append((label, str(filename), e.macros, w, h))
        if tabobs:
            grp = EdmObject("Group")
            buttons = EdmObject("Choice Button")
            maxw = max([x[3] for x in tabobs])
            maxh = max([x[4] for x in tabobs])
            labs = ",".join(["0"] + [x[0] for x in tabobs])
            pv = r"LOC\$(!W)tab"
            buttons.Properties["controlPv"] = quoteString("%s=e:%s" % (pv, labs))
            buttons.setPosition(4, 3)
            buttons.setDimensions(maxw + 1, 25)
            buttons.Properties["orientation"] = quoteString("horizontal")
            buttons.Properties["font"] = quoteString("arial-bold-r-12.0")
            buttons.setShadows()
            buttons.Properties["selectColor"] = buttons.Properties.Colour["Button: On"]
            grp.addObject(buttons)
            grp.addObject(
                lines(
                    [(4, maxh + 30), (maxw + 6, maxh + 30), (maxw + 6, 29)],
                    "Top Shadow",
                )
            )
            grp.addObject(
                lines([(4, maxh + 30), (4, 29), (maxw + 6, 29)], "Bottom Shadow")
            )
            filename, label, macros, w, h = tabobs[0]
            eob = EdmObject("Embedded Window")
            eob.setPosition(5, 29)
            eob.setDimensions(maxw, maxh)
            eob.Properties["filePv"] = quoteString(pv)
            eob.Properties["noScroll"] = True
            eob.Properties["numDsps"] = len(tabobs)
            eob.Properties["displaySource"] = quoteString("menu")
            eob.Properties["displayFileName"] = dict(
                (i, quoteString(x[1])) for (i, x) in enumerate(tabobs)
            )
            eob.Properties["symbols"] = dict(
                (i, quoteString(",".join([x[2], "label=" + x[0]])))
                for (i, x) in enumerate(tabobs)
            )
            grp.addObject(eob)
            grp.setDimensions(maxw + 10, maxh + 30, resize_objects=False)
            out.append(grp)
        return out

    def __load_screen(self, filename: Path) -> None:
        if filename not in Substitute_embed.in_screens:
            paths = [
                p.joinpath(filename)
                for p in self.paths
                if p.joinpath(filename).is_file()
            ]
            assert paths, (
                f"Cannot find file {filename} in paths:\n[\n- "
                + "\n- ".join([str(path) for path in sorted(self.paths)])
                + "\n]"
            )
            screen = EdmObject("Screen")
            screen.write(open(paths[0], "r").read())
            Substitute_embed.in_screens[filename] = screen.copy()

    def __safe_filename(self, filename: str) -> str:
        return filename.replace(" ", "-")

    def __filter_screens(
        self,
        filename: Path,
        obs: List[GBObject],
        destFilename: Optional[Path] = None,
        embedded: Optional[bool] = None,
    ) -> Tuple[List[GBObject], bool]:
        # return a list of objects with screens filtered and modified for
        # summary screen generation
        objects = []
        for ob in obs:
            newscreens = []
            for s in ob.screens:
                if s.filename == filename:
                    s = copy(s)
                    if destFilename is not None:
                        s.filename = destFilename
                    if embedded is not None:
                        s.embedded = embedded
                    else:
                        embedded = s.embedded
                    newscreens.append(s)
            if newscreens:
                ob = copy(ob)
                ob.screens = newscreens
                objects.append(ob)
        assert embedded is not None
        return objects, embedded

    def makeList(
        self, srcFiles: List[Path], dstFiles: List[Path], group: GBObject
    ) -> Tuple[List[GBObject], bool]:
        """Make a list of GuiBuilder objects.

        Args:
            srcFiles (List[str]): Source filenames
            dstFiles (List[str]): Destination filenames
            group (GBObject): GBObject group

        Returns:
            Tuple[List[GBObject], bool]: Tuple of final list of GBObjects and bool
                of flag to determine if the group is embedded.
        """
        objectList: List[GBObject] = []
        embedded: Optional[bool] = None
        for srcFilename, destFilename in zip(srcFiles, dstFiles):
            objects, embedded = self.__filter_screens(
                srcFilename, group.children, destFilename
            )
            objectList.extend(objects)
        assert embedded is not None
        return objectList, embedded

    def multiFileSummary(
        self,
        typ: str,
        srcFiles: List[Path],
        dstFiles: Optional[List[Path]] = None,
        embedded: Optional[bool] = None,
        group: bool = True,
        groupByName: bool = False,
        aspectRatio: float = 1.5,
    ) -> None:
        """Find objects with screen names as in srcFiles and create a summary screen.

        Optional dstFiles can be used to replace to a different filename used for
        the summary.

        Args:
            typ (str): String describing the type of screen
            srcFiles (List[str]): The source files for the screens.
            dstFiles (Optional[List[str]], optional): Destination files.
                Defaults to None.
            embedded (Optional[bool], optional): Flag to determine if the screen is
                embedded. Defaults to None.
            group (bool, optional): Flag to determine if objects should be grouped.
                Defaults to True.
            groupByName (bool, optional): Flag to determine if objects are grouped
                by name. Defaults to False.
            aspectRatio (float, optional): Aspect ratio of the screen. Defaults to 1.5.
        """
        if dstFiles is None:
            # Generate a list of "" to match srcFiles by length
            dstFiles = []
            assert isinstance(dstFiles, List)
            for i in range(len(srcFiles)):
                dstFiles.append(Path())
        else:
            assert len(dstFiles) == len(
                srcFiles
            ), "len of srcFiles and dstFiles must match"
        filename = self.__safe_filename(f"{self.dom}-{typ.lower()}.edl")
        if self.errors:
            print(f"Creating {filename}")
        screen = EdmObject("Screen")
        table = EdmTable(yborder=5)
        screen.addObject(table)
        headerText = f"{typ} Summary"
        # only group == True case implemented
        assert group, "group == False case not implemented"
        assert not groupByName, "groupByName case not implemented"
        groupObjects = self.objects
        screen_objects = []
        # group by parent object
        for o in groupObjects:
            # if no child objects then don't need to do anything
            if not o.children:
                continue
            # first make a new object list
            objects, embedded = self.makeList(srcFiles, dstFiles, o)
            # now make the list of screen objects out of it
            if objects:
                sobs = self.__screenObs(o.name, objects, embedded)
                buttons = self.__screenObs("", [o], preferEmbed=False, preferTab=False)

                sobs_width = sobs[-1].Properties["w"]
                if not isinstance(sobs_width, int):
                    if isinstance(sobs_width, str) and sobs_width.isdigit():
                        sobs_width = int(sobs_width)
                assert isinstance(sobs_width, int)

                if buttons:
                    # if there is a screen for this already, add a button for it
                    title_button = buttons[0]
                    title_button.setDimensions(sobs_width, 20)
                else:
                    # otherwise just make a label
                    title_button = label(0, 0, sobs_width, 20, o.name)
                screen_objects.append([title_button] + sobs)
        # end of case  "group == True"
        if screen_objects:
            w, h = screen_objects[0][-1].getDimensions()
            numobs = sum([len(o) for o in screen_objects])
            nrows = int(sqrt(numobs * w / (aspectRatio * h)) + 1)
            for oblist in screen_objects:
                # if entire component doesn't fit in column, create a new one
                assert isinstance(table.Properties["__def_y"], int)
                if len(oblist) + table.Properties["__def_y"] > nrows:
                    table.nextCol()
                for ob in oblist:
                    table.addObject(ob)
                    table.nextCell(max_y=nrows)
            screen.autofitDimensions()
            table.ungroup()
            screen = Titlebar(
                screen,
                button="text",
                button_text=self.dom,
                header="text",
                header_text=headerText,
                tooltip="generic-tooltip",
                title=headerText,
            )
            screen = Substitute_embed(screen, [], {}).get_substituted_screen()
        open(filename, "w").write(screen.read())

    def summary(
        self,
        typ: str,
        srcFilename: Path,
        destFilename: Optional[Path] = None,
        embedded: Optional[bool] = None,
        group: bool = True,
        groupByName: bool = False,
        ar: float = 1.5,
        extras: List[GBObject] = [],
    ) -> None:
        """Find all GBScreen objects like srcOb and display them in a summary screen.

        If obFilename then use obFilename instead.
        If embedded then use embedded instead

        Args:
            typ (str): String describing type of screen
            srcFilename (str): Source filename of screen
            destFilename (Optional[str], optional): Destination filename of new screen.
                Defaults to None.
            embedded (Optional[bool], optional): Flag to determine if screen is
                embedded. Defaults to None.
            group (bool, optional): Flag to determine if objects are grouped together.
                Defaults to True.
            groupByName (bool, optional): Flag to determine if objects are grouped
                by name. Defaults to False.
            ar (float, optional): Aspect ratio of screen. Defaults to 1.5.
            extras (List[GBObject], optional): List of extra objects. Defaults to [].
        """
        # this is the filename of the generated screen
        filename = Path(self.__safe_filename(f"{self.dom}-{typ.lower()}.edl"))
        if self.errors:
            print(f"Creating {filename}")
        # this is the filename for each object put on screens
        if destFilename is None:
            destFilename = srcFilename
        # this is the screen we will return
        screen = EdmObject("Screen")
        table = EdmTable(yborder=5)
        screen.addObject(table)
        headerText = f"{typ} Summary"
        # objects is a list of list of screen objects to add
        screen_objects: list[list[EdmObject]] = []
        if group:
            if groupByName:
                # make a tree hierarchy according to . in names
                groupObjects: list[GBObject] = []
                for o in self.objects:
                    if len(o.name.split(".", 1)) == 1:
                        groupObjects.append(copy(o))
                        groupObjects[-1].children = []
                for o in self.objects:
                    if len(o.name.split(".", 1)) == 2:
                        parent = [
                            x for x in groupObjects if x.name == o.name.split(".", 1)[0]
                        ]
                        if parent:
                            parent[0].children.append(o)
            else:
                groupObjects = self.objects
            # group by parent object
            for o in groupObjects:
                # if no child objects then don't need to do anything
                if not o.children:
                    continue
                # first make a new object list
                objects, embedded = self.__filter_screens(
                    srcFilename, o.children, destFilename, embedded
                )
                # now make the list of screen objects out of it
                if objects:
                    sobs = self.__screenObs(o.name, objects, embedded)
                    buttons = self.__screenObs(
                        "", [o], preferEmbed=False, preferTab=False
                    )

                    sobs_width = sobs[-1].Properties["w"]
                    if not isinstance(sobs_width, int):
                        if isinstance(sobs_width, str) and sobs_width.isdigit():
                            sobs_width = int(sobs_width)
                    assert isinstance(sobs_width, int)

                    if buttons:
                        # if there is a screen for this already, add a button for it
                        title_button = buttons[0]
                        title_button.setDimensions(sobs_width, 20)
                    else:
                        # otherwise just make a label
                        title_button = label(0, 0, sobs_width, 20, o.name)
                    screen_objects.append([title_button] + sobs)
        else:
            objects, embedded = self.__filter_screens(
                srcFilename, self.objects, destFilename, embedded
            )
            if objects:
                screen_objects.append(self.__screenObs("", objects, embedded))
        # now add in the extras
        if len(screen_objects) > 0 and len(extras) > 0:
            sobs = self.__screenObs("", extras, preferEmbed=False, preferTab=False)

            scrObs_width = screen_objects[-1][-1].Properties["w"]
            if not isinstance(scrObs_width, int):
                if isinstance(scrObs_width, str) and scrObs_width.isdigit():
                    scrObs_width = int(scrObs_width)
            assert isinstance(scrObs_width, int)

            for s in sobs:
                assert isinstance(s.Properties["h"], int)
                s.setDimensions(scrObs_width, s.Properties["h"])
            screen_objects.append(sobs)
        if screen_objects:
            w, h = screen_objects[0][-1].getDimensions()
            numobs = sum([len(o) for o in screen_objects])
            nrows = int(sqrt(numobs * w / (ar * h)) + 1)
            for oblist in screen_objects:
                # if entire component doesn't fit in column, create a new one
                assert isinstance(table.Properties["__def_y"], int)
                if len(oblist) + table.Properties["__def_y"] > nrows:
                    table.nextCol()
                for ob in oblist:
                    table.addObject(ob)
                    table.nextCell(max_y=nrows)
            screen.autofitDimensions()
            table.ungroup()
            screen = Titlebar(
                screen,
                button="text",
                button_text=self.dom,
                header="text",
                header_text=headerText,
                tooltip="generic-tooltip",
                title=headerText,
            )
            screen = Substitute_embed(screen, [], {}).get_substituted_screen()
        open(filename, "w").write(screen.read())

    def __concat(self, obj_list_gen: Generator[List[GBRecord], None, None]) -> List:
        return [x for gbrecord in obj_list_gen for x in gbrecord]

    def motorHomedSummary(self):
        """Create a motor homed summary <dom>-motor-homed.edl."""
        self.summary(
            "Motor Homed",
            Path("motor.edl"),
            Path("motor-embed-homed.edl"),
            embedded=True,
            groupByName=True,
        )

    def interlockSummary(self):
        """Create an interlock summary <dom>-interlocks.edl."""
        self.summary(
            "Interlocks", Path("interlock-embed-small.edl"), group=False, embedded=True
        )

    def temperatureSummary(self, bms: bool = True):
        """Create a temperatures summary <dom>-temperatures.edl."""
        extras = []
        if bms:
            # First create BMS button objects
            bms_lines = open("/dls_sw/prod/etc/init/BMS_pvs.csv").readlines()
            ids = {}
            for line in bms_lines:
                split = line.split("|")
                # id, desc, ....., pv
                if len(split) > 3 and self.dom.replace("BL", "SV") in split[-1]:
                    ids[split[0].strip('"')] = split[1].strip('"')
            for id, desc in list(ids.items()):
                ob = self.object("%s BMS" % desc)

                args: ScreenOptions = {
                    "filename": Path(f"DLS_dev{id}.edl"),
                    "macros": "",
                    "embedded": False,
                    "tab": False,
                }
                ob.addScreen(**args)
                extras.append(ob)
        self.summary(
            "Temperatures", Path("temperature-embed.edl"), embedded=True, extras=extras
        )

    def flowSummary(self):
        """Create an interlock summary <dom>-interlocks.edl."""
        self.summary("Water Flows", Path("flow-embed.edl"), embedded=True)

    def softiocSummary(self, softiocs: list[tuple[str, str, str]]):
        """
        Create a summary of all softiocs <dom>-softioc-status.edl

        softiocs should be a list of tuples of 3 values:
        (softioc, ioc-detail, ioc-host)
        """

        def macroString(macroHash):
            """transform a hash of key, value string pairs
            to a string that can be passed to edm as comma separated
            macro spec"""
            return ",".join([f"{k}={v}" for k, v in macroHash.items()])

        # this is the filename of the generated screen
        filename = self.__safe_filename(f"{self.dom}-softioc-status.edl")
        embedded_elems: list[GBObject] = []

        count: int = 1
        for softioc, ioc_detail, ioc_host in softiocs:
            count += 1
            name = f"IOC{count}"
            ioc_dict = {
                "softioc": softioc,
                "ioc-host": ioc_host,
                "ioc-detail": ioc_detail,
            }
            assert (
                "=" not in ioc_detail
            ), f"'=' are not allowed in IOC detail.\nLine: {ioc_dict}\n\n{macroString(ioc_dict)}\n"

            if "RSERV" in ioc_host:
                ioc_dict["glocal"] = ""
            else:
                ioc_dict["glocal"] = "-g"

            if "ECSCN" in softioc or "CYC" in softioc:
                embedfile = "BLGui-scanner-embed.edl"
            else:
                embedfile = "BLGui-softiocSummary-embed.edl"

            gob = self.object(
                name,
            )
            gob.addScreen(embedfile, macroString(ioc_dict), embedded=True)
            embedded_elems.append(gob)

        softioc_title = self.object("softioc_title")
        softioc_title.addScreen(
            "BLGui-softiocSummary-title-embed.edl", "", embedded=True
        )

        self.object(
            "IOCSTAT",
            "Soft IOCs",
            "IOCSTAT",
            [softioc_title, *embedded_elems],
            ar=0.2,
            # This needs to be True to help with performance
            substituteEmbed=True,
        )

    def pmacSummary(self, pmacinfo: list[tuple[str, str, str, str, str, str]]):
        """
        Create a summary of all pmacs <dom>-pmac-status.edl

        pmacinfo should be a list of tuples of 6 values:
        (step, step-detail, step-ioc, connection-type, step-ip, step-rack)
        """

        def macroString(macroHash):
            """transform a hash of key, value string pairs
            to a string that can be passed to edm as comma separated
            macro spec"""
            return ",".join([f"{k}={v}" for k, v in macroHash.items()])

        # this is the filename of the generated screen
        filename = self.__safe_filename(f"{self.dom}-pmac-status.edl")
        embedded_elems: list[GBObject] = []

        conn_types = ["ts", "tcpip", "rs232", "ssh"]

        count: int = 1
        for step, step_detail, step_ioc, conn_type, step_ip, step_rack in pmacinfo:
            count += 1
            name = f"PMAC{count}"

            if len(step_ip.split(":")) == 2:
                step_ip, step_port = step_ip.split(":", maxsplit=1)
            else:
                step_port = "1025"

            step_dict = {
                "step": step,
                "desc": step_detail,
                "ioc": step_ioc,
                "connection-type": conn_type if conn_type in conn_types else "tcpip",
                "step-ip": step_ip,
                "step-port": step_port,
                "rack-cia": step_rack if step_rack != "" else "N/A",
            }
            assert (
                "=" not in step_detail
            ), f"'=' are not allowed in STEP detail.\nLine: {step_dict}"

            embedfile = "BLGui-pmacSummary-embed.edl"

            gob = self.object(
                name,
            )
            gob.addScreen(embedfile, macroString(step_dict), embedded=True)
            embedded_elems.append(gob)

        pmac_title = self.object("pmac_title")
        pmac_title.addScreen("BLGui-pmacSummary-title-embed.edl", "", embedded=True)

        self.object(
            "PMACSTAT",
            "PMACs",
            "PMACSTAT",
            [pmac_title, *embedded_elems],
            ar=0.3,
            # This needs to be True to help with performance
            substituteEmbed=True,
        )

    def autofilled(self, screen: Union[str, EdmObject]) -> EdmObject:
        """Return an autofilled version of screen.

        Any top level group will have tags replaced as following:
            visPv tag: #<A=1>##<S1>#
        This means that all instances of #<A># will be replaced by 1 in the
        group, and the component S1 will be used to find values of #<P>#,
        #<NAME>#, #<DESCRIPTION>#, #<EDM_MACROS># and #<FILE># as defined by
        the relevant call to GuiBuilder.component()

        Args:
            screen (Union[str, EdmObject]): The EdmObject of the screen, or the
                filename of the screen.

        Returns:
            EdmObject: The EdmObject of the screen.
        """
        # first open the screen if we've been given a filename
        if isinstance(screen, str):
            filename = screen
            screen = EdmObject("Screen")
            screen.write(open(filename).read())
        # now autofill all groups in the screens
        assert isinstance(screen, EdmObject)
        groups = [ob for ob in screen.Objects if ob.Properties.Type == "Group"]
        for group in groups:
            # the vis PV is checked for tags
            if "visPv" in group.Properties:
                visPv = group.Properties["visPv"]
                assert isinstance(visPv, str)
                # Make sure no leading and trailing ""
                visPv = visPv.strip('"')
            else:
                visPv = ""
            if visPv.startswith("#<"):
                # we need to do something with the group
                args = visPv.replace("#<", "").split(">#")[:-1]
                assignment_args = [a for a in args if "=" in a]
                device_args = [a for a in args if "=" not in a]
                if len(device_args) > 1:
                    self.error(
                        "Looks like you're trying to autofill from "
                        f"two components in this visPv: '{visPv}'"
                    )
                for arg in assignment_args:
                    # if there is an = in the tag, split it into a list and
                    # replace tags from this list instead
                    group.substitute(
                        "#<" + arg.split("=")[0].strip() + ">#",
                        arg.split("=")[1].strip(),
                    )
                    visPv = visPv.replace("#<" + arg + ">#", "")
                if device_args:
                    # if there is a component tag, use it to get P, NAME, etc..
                    device_name = device_args[0]
                    if device_name in ["AXIS_LEFT", "AXIS_RIGHT"]:
                        # These are axes, only tagged for flipping
                        continue
                    # if we have a component then all is fine
                    dicts = [x.macrodict for x in self.objects if x.name == device_name]
                    if len(dicts) == 0:
                        # and it's not an axis group (this isn't a real tag)
                        if device_name not in ["AXIS_LEFT", "AXIS_RIGHT"]:
                            self.error(
                                f"Cannot find component {device_name}. Group has "
                                "not been autofilled."
                            )
                        continue
                    for key, val in list(dicts[0].items()):
                        group.substitute("#<" + key + ">#", val)
                    visPv = visPv.replace("#<" + device_name + ">#", "")
        return screen

    def flipped(self, screen: Union[str, EdmObject]) -> EdmObject:
        """Return a flipped version of screen."""
        if isinstance(screen, str):
            filename = screen
            screen = EdmObject("Screen")
            with open(filename, "r") as f:
                screen.write(f.read())
        assert isinstance(screen, EdmObject)
        return Flip_horizontal(screen, self.paths)

    def writeScreen(self, screen: EdmObject, filename: str):
        """Write screen object screen to filename."""
        filename = self.__safe_filename(filename)
        with open(filename, "w") as f:
            f.write(screen.read())

    def __writeCalc(self, name: str, **args):
        """Write a calc record."""
        self.dbtext += 'record(calc, "%s")\n' % name
        self.dbtext += "{\n"
        for k, v in sorted(args.items()):
            self.dbtext += '    field(%s, "%s")\n' % (k, v)
        self.dbtext += "}\n\n"

    def __writeRecord(self, ob: GBObject, obs: List[GBObject]) -> None:
        records = self.__concat(o.records for o in obs)
        recordName = ob.macrodict["P"] + ":DEVSTA"
        if len(records) == 0:
            self.__writeCalc(recordName, CALC=0, PINI="YES")
            return
        # first make a set of all severities and stats
        sevrs = [r.pv.split(".")[0] for r in records if r.sevr]
        stats = [r.pv for r in records if not r.sevr]
        stripped_stats = [pv.split(".")[0] for pv in stats]
        # now create inputs
        # inps = (pv,inCalc)
        inps = [(pv + " NMS", True) for pv in stats if pv.split(".")[0] not in sevrs]
        inps += [(pv + " MS", True) for pv in stats if pv.split(".")[0] in sevrs]
        inps += [(pv + ".SEVR MS", False) for pv in sevrs if pv not in stripped_stats]
        inps = sorted(set(inps))
        # now work out how many calcs we need
        ncalcs = int(max((len(inps) + 11) / 12, 1))
        # if we need more than one, then sum them
        if ncalcs > 1:
            letters = [chr(65 + j) for j in range(ncalcs)]
            CALC = f"({('|'.join(letters))})>0?1:0"
            cargs = dict(
                (f"INP{letter}", f"{recordName}{j + 1} MS")
                for j, letter in enumerate(letters)
            )
            self.__writeCalc(
                recordName, SCAN="1 second", CALC=CALC, PHAS=3, ACKT="NO", **cargs
            )
        # create the calc records
        for i in range(ncalcs):
            subset = inps[12 * i : 12 * i + 12]
            letters = [chr(65 + j) for j, (pv, inCalc) in enumerate(subset) if inCalc]
            if letters:
                CALC = f"({('|'.join(letters))})>0?1:0"
            else:
                CALC = "0"
            cargs = dict(
                (f"INP{(chr(65 + j))}", pv) for j, (pv, inCalc) in enumerate(subset)
            )
            if ncalcs > 1:
                self.__writeCalc(
                    recordName + str(i + 1),
                    SCAN="1 second",
                    CALC=CALC,
                    PHAS=2,
                    ACKT="NO",
                    **cargs,
                )
            else:
                self.__writeCalc(
                    recordName, SCAN="1 second", CALC=CALC, PHAS=2, ACKT="NO", **cargs
                )
        ob.addRecord(recordName)
        if sevrs:
            ob.addRecord(recordName, True)

    def writeRecords(self):
        """Write records to db file."""
        open(self.db, "w").write(self.dbtext)

    def startupScript(
        self,
        filename: Optional[str] = None,
        edl: Optional[str] = None,
        macros: Optional[str] = None,
        setPath: bool = True,
        setPort: bool = True,
    ) -> None:
        """Create an edm startup script using the paths stripped from configure/RELEASE.

        If filename is None default to st<dom>-gui.
        If edl is None default to <dom>-synoptic.edl.
        If macros is None default to dom=<dom>
        """
        # get default values
        if filename is None:
            filename = "st" + self.dom + "-gui"
        filename = self.__safe_filename(filename)
        if edl is None:
            edl = self.dom + "-synoptic.edl"
        if macros is None:
            macros = "dom=" + self.dom
        # find paths for current moduletop,
        top = Path("../..")
        BLdevpath = self.RELEASE.joinpath(top, self.dom + "App/opi/edl").resolve()
        BLpath = self.RELEASE.joinpath(top, "data")
        # format paths for release tree
        devpaths = "".join(
            ['    EDMDATAFILES="${EDMDATAFILES}%s:"\n' % x for x in self.devpaths]
        )
        paths = "".join(['EDMDATAFILES="${EDMDATAFILES}:%s"\n' % x for x in self.paths])
        # open the file
        f = open(filename, "w")
        # first put the header in
        f.write(Header % locals())
        # now prepend EDMDATAFILES onto the PATH
        if setPath:
            f.write(SetPath)
        # now popup a gui prompting for the port
        if setPort:
            f.write(SetPort)
        # finally run edm
        if macros:
            macros = '-m "%s" ' % macros
        f.write("edm ${OPTS} %(macros)s %(edl)s" % locals())
        # write the file out
        f.close()

    def __writeBLScript(self, name: str, text: str) -> None:
        filename = self.__safe_filename("st%s-%s" % (self.dom, name))
        open(filename, "w").write(text)

    def blScripts(self, fe: bool = True, alh: bool = True, burt: bool = True) -> None:
        """Create the standard set of beamline scripts to run alh, FE, etc."""
        dom = self.dom
        if fe:
            if dom in ("BL07C"):
                FEdom = "FE" + dom[2:4] + "B"
            # The following J beamlines are individual beamlines but share
            # the front end screens of their neighbouring I beamlines
            elif dom in ("BL04J", "BL11J", "BL15J", "BL20J"):
                FEdom = "FE" + dom[2:4] + "I"
            # All other beamlines have their own front end screens
            else:
                FEdom = "FE" + dom[2:5]
            self.__writeBLScript("fe", Fe % locals())
        if alh:
            alhLogPath = "/dls/%s/epics/alh" % (dom[4].lower() + dom[2:4])
            self.__writeBLScript("alh", Alh % locals())
            self.__writeBLScript("alhserver", Alhserver % locals())
        if burt:
            self.__writeBLScript("burt", Burt % locals())


Header = """#!/bin/sh
TOP="$(cd $(dirname "$0")/../..; pwd)"

# first load the paths. These have been generated from the configure/RELEASE
# tree. If we have a -d arg then load the opi/edl paths first
shopt -s nullglob
unset EDMDATAFILES
if [ "$1" = "-d" ]; then
    for d in ${TOP}/*App/opi/edl; do
        EDMDATAFILES="${EDMDATAFILES}${d}:"
    done
    EDMDATAFILES="${EDMDATAFILES}${TOP}/data:"
%(devpaths)s
    OPTS="-x -eolc"
else
    OPTS="-x -eolc -noedit"
fi
EDMDATAFILES="${EDMDATAFILES}${TOP}/data"
%(paths)s
export EDMDATAFILES
"""

SetPath = """
# Set the path to include any scripts in data dirs
export PATH=${EDMDATAFILES}:${PATH}
"""

SetPort = r"""
# Prompt for the server port if it isn't already set
if [ "$EPICS_CA_SERVER_PORT" = "" ]
then
    xmessage -nearmouse -buttons '5064 - Machine Mode,'\
'6064 - Prod Simulation,6164 - Work Simulation,6764 - Local Simulation' \
'Which port would you like to run the edm display on?'\
'                                      '
    case $? in
    101) export EPICS_CA_SERVER_PORT=5064
         export EPICS_CA_REPEATER_PORT=5065 ;;
    102) export EPICS_CA_SERVER_PORT=6064
         export EPICS_CA_REPEATER_PORT=6065 ;;
    103) export EPICS_CA_SERVER_PORT=6164
         export EPICS_CA_REPEATER_PORT=6165 ;;
    104) export EPICS_CA_SERVER_PORT=6764
         export EPICS_CA_REPEATER_PORT=6765 ;;
    esac
fi
"""

Alh = """#!/bin/sh
alh -D -S $(dirname $0)/%(dom)s.alhConfig
"""

Alhserver = r"""#!/bin/sh
source /dls_sw/etc/profile
if [ ! -d %(alhLogPath)s ]; then
    mkdir -m 775 -p %(alhLogPath)s
fi
alh -m 0 -T \
    -a %(alhLogPath)s/%(dom)s-alarm-log.alhAlarm \
    -o %(alhLogPath)s/%(dom)s-alarm-log.alhOpmod \
    $(dirname $0)/%(dom)s.alhConfig &
"""

Fe = (
    "/dls_sw/prod/etc/Launcher/script_from_dir.sh "
    + "$EPICS_CA_SERVER_PORT feqt4-wrapper-gui"
    + " feqt4gui.sh %(FEdom)s\n"
)

Burt = "if [ -d $1 ]; then cd $1; fi; burtgooey"
