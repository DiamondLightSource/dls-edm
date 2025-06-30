"""
A python representation of an edm object with associated useful functions.

Author: Tom Cobb
Updated to Python3 by: Oliver Copping
"""

import codecs
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import dill

from dls_edm.edmProperties import EdmProperties
from dls_edm.utils import write_colour_helper

ignore_list = [
    "4 0 1",
    "beginScreenProperties",
    "endScreenProperties",
    "beginObjectProperties",
    "beginGroup",
    "endGroup",
]


class EdmObject:
    """
    A python representation of an Edm Object.

    Attributes:
    Type - Type of self, like 'Group', 'Screen' or 'Embedded Window'
    Properties - Dictionary containing edm properties like w, h, font
    Objects - List of child EdmObjects if self.Properties.Type=='Group' or 'Screen'
    Parent - Pointer to parent if self is a child of an EdmObject
    Colour - Colour index lookup dictionary eg Colour['White']='index 0'

    The easiest way to make a valid EdmObject is to work from the .edl file.
    Take for instance this edm representation of a rectangle:

    # (Rectangle)
    object activeRectangleClass
    beginObjectProperties
    major 4
    minor 0
    release 0
    x 57
    y 95
    w 167
    h 161
    lineColor index 14
    fillColor index 0
    endObjectProperties

    To create this we would use the following code:

    # the type is enclosed in round brackets in the line: '# (Rectangle)'
    o = EdmObject("Rectangle")
    # object,major,minor,release are predicted from the type
    # beginObjectProperties and endObjectProperties are not needed
    o.setPosition(57,95)
    o.setDimensions(167,161)
    # can either use the index numbers, or look them up from self.Properties.Colour
    o["lineColor"] = "index 14"
    o["fillColor"] = o.Colour["White"]
    """

    def __init__(self, obj_type: str = "Invalid", defaults: bool = True) -> None:
        """
        Edm Object constructor.

        Args:
            obj_type (str, optional): Type of self, like 'Group', 'Screen' or
                'Embedded Window'. Defaults to "Invalid".
            defaults (bool, optional): Flag to use default values for Type.
                Defaults to True.
        """
        # initialise variables
        self.Objects: List[EdmObject] = []
        self.Parent: EdmObject | None = None

        self.Properties: EdmProperties = EdmProperties(obj_type, defaults=defaults)

    def copy(self) -> "EdmObject":
        """
        Return a copy of self.

        Return a copy of self complete with copies of its child objects. This copy does
        not have a Parent defined.

        Returns:
            EdmObject: A python representation of an Edm Object.
        """
        # print("Copy, type:", self.Properties.Type)
        assert self.Properties.Type is not None
        new_ob: EdmObject = EdmObject(self.Properties.Type, defaults=False)
        # need to explicitly copy some properties
        for k, v in self.Properties.items():
            if isinstance(v, Dict):
                new_ob.Properties[k] = v.copy()
            elif isinstance(v, List):
                new_ob.Properties[k] = v[:]
            else:
                new_ob.Properties[k] = v
        # add copies of child objects
        for ob in self.Objects:
            new_ob.addObject(ob.copy())
        return new_ob

    def write(
        self, text: str | List[str], expect: str | None = "type"
    ) -> str | List[str] | None:
        """
        Populate the object's properties with the selected text.

        This should be either the entire text from a .edl file for a screen, or
        the section from '# (Type)' to 'endObjectProperties' for any other object.
        The text can either be a string or a list of lines.

        Args:
            text (str): The entire text from a .edl file for a screen, or
                the section from '# (Type)' to 'endObjectProperties' for
                any other object.
            expect (str, optional): The contents of text. Defaults to "type".

        Returns:
            _type_: _description_
        """
        lines: List[str]

        if isinstance(text, List):
            # make sure all elements are of type str
            assert all(isinstance(x, str) for x in text)
            lines = text
        else:
            assert isinstance(text, str)
            # if we are being passed text, we must be the top level object
            lines = text.strip().splitlines()
            # we must now clear all our properties to avoid junk tags
            self.Properties.clear_properties()

        if self.Properties.Type == "Screen":
            expect = None

        key: str | None = ""
        value: Dict[str, str | int] | List[str | int] | None = []
        # multiline_dict: Dict[str, str | bool | int] = {}

        # Need to find the start and end of an object
        for i, line in enumerate(lines):
            if not line or line in ignore_list:
                pass
            elif expect in ["type", "multiline"]:
                match expect:
                    case "type":
                        if self.Properties.Type is None:
                            self.Properties.Type = self._get_edl_object_type(line)
                        expect = None
                    case "multiline":
                        # value = self._write_edl_multiline(line)
                        if line == "}":
                            assert isinstance(key, str)
                            self.Properties[key] = value
                            key = None
                            value = None
                            expect = None
                        else:
                            value = self._write_edl_multiline(line, value)

            elif line.startswith("# ("):
                return self._write_new_edm_object(lines[i:])
            # return the unparsed lines to parent object's write method
            elif line == "endObjectProperties":
                return lines[i + 1 :]
            # set the property in self
            else:
                list_ = line.strip().split()
                if len(list_) == 1:
                    self.Properties[list_[0]] = True
                elif list_[1] == "{":
                    key = list_[0]
                    expect = "multiline"
                else:
                    self.Properties[list_[0]] = (
                        line[line.find(list_[0]) + len(list_[0]) :].strip().strip('"')
                    )
                    if list_[0] in ["x", "y", "w", "h"]:
                        tmp = self.Properties[list_[0]]
                        assert isinstance(tmp, str)
                        assert tmp.lstrip("-").isdecimal()
                        self.Properties[list_[0]] = int(tmp)

        return None

    def _get_edl_object_type(self, line: str) -> str:
        assert line.startswith("# ("), "Expected '# (Type)', got " + line
        # self.Properties.Type = line[3 : line.find(")")]
        return line[line.find("(") + 1 : line.find(")")]

    def _write_edl_multiline(
        self, line: str, value: Dict[str, str | int] | List[str | int] | None
    ) -> Dict[str, str | int] | List[str | int]:
        list_ = []
        in_quotes = False

        # replace quotes with a tag, then split the line
        temp_list = line.replace('\\"', "*&q").strip().split('"')

        for t in temp_list:
            if not in_quotes:
                list_.extend(t.strip().split())
            else:
                list_.append('"' + t.replace("*&q", '\\"') + '"')
            in_quotes = not in_quotes
        # use a list to represent a list of lines
        if len(list_) == 1:
            if not value:
                value = []
            assert isinstance(value, List), "Expected '  x', got " + line
            value.append(list_[0])
        # use a dict to represent key,val pairs
        else:
            if not value:
                value = {}
            assert isinstance(value, Dict), "Expected '  x x', got " + line
            value[list_[0]] = " ".join(list_[1:])
        return value

    def _write_new_edm_object(self, lines: List[str]) -> str | List[str] | None:
        more_lines: List[str]

        obj_type = self._get_edl_object_type(lines[0])
        ob = EdmObject(obj_type, defaults=False)
        more_lines = ob.write(lines)
        assert isinstance(more_lines, List)
        self.addObject(ob)
        return self.write(more_lines, None)

    def flatten(self, include_groups: bool = True) -> List["EdmObject"]:
        """Flatten the tree of objects, and return it as a list.

        If include_groups==False, don't include groups, just their contents.

        Returns:
            List[EdmObject]: A list of EdmObjects in the tree
        """
        if not include_groups and self.Properties.Type == "Group":
            output = []
        else:
            output = [self]
        for ob in self.Objects:
            output.extend(ob.flatten(include_groups))
        return output

    def __readKeys(self, filter_keys, assert_existence=True):
        # internal function to export values of filter_keys if they exist
        lines = []
        # key_set is the set of all property keys
        keys = self.Properties.keys()
        key_set = set(keys)
        # filter_set is the set of keys to filter against
        filter_set = set(filter_keys)
        # if we need to assert that all keys in filter_keys exist, do so here
        if assert_existence:
            assert (
                filter_set <= key_set
            ), f"Some required keys not defined: {list(filter_set - key_set)}"
        # Make sure related displays with no filenames have the right numDsps
        if self.Properties.Type == "Related Display":
            tmp = self.Properties["displayFileName"]
            assert isinstance(tmp, Dict)
            if (
                "displayFileName" in self.Properties.keys()
                and len(tmp.keys()) == 1
                and tmp[list(tmp.keys())[0]] == '""'
            ):
                self.Properties["displayFileName"] = {}
                self.Properties["symbols"] = {}
                self.Properties["numDsps"] = 0
        # print the keys
        for key in sorted(filter_set):
            if key in keys and not key == "object" and not key[:2] == "__":
                value = self.Properties[key]
                # If the value is literally True
                if value is True:
                    # output a flag
                    lines.append(key)
                # If it has a value that isn't literally True
                elif value is not False:
                    if isinstance(value, List):
                        # output a multiline string
                        text_vals = ["  %s\n" % str(v) for v in value]
                        if text_vals:
                            lines.append(key + " {\n" + "".join(text_vals) + "}")
                    elif isinstance(value, Dict):
                        # output a multiline dict
                        vals = list(value.keys())
                        vals.sort()
                        text_vals = [
                            "  %s %s\n" % (str(k), str(value[k])) for k in vals
                        ]
                        if text_vals:
                            lines.append(key + " {\n" + "".join(text_vals) + "}")
                    else:
                        # output a string value
                        lines.append(str(key) + " " + str(value))
        return "\n".join(lines)

    def raiseObject(self) -> None:
        """
        Raise self to the front of its Parent's list of objects.

        Raise self to the front of its Parent's list of objects, so item is at
        the front of the group or screen.
        """
        assert self.Parent, (
            "Cannot raise, object: " + str(self) + " doesn't have a Parent"
        )
        self.Parent.Objects.remove(self)
        self.Parent.Objects.append(self)

    def lowerObject(self) -> None:
        """
        Lower self to the back of its Parent's list of objects.

        Lower self to the back of its Parent's list of objects, so item is at
        the back of the group or screen.
        """
        assert self.Parent, (
            "Cannot lower, object: " + str(self) + " doesn't have a Parent"
        )
        self.Parent.Objects.remove(self)
        self.Parent.Objects.insert(0, self)

    def setShadows(self) -> None:
        """Set the top and bottom shadows of self to be reasonable value."""
        self.Properties["topShadowColor"] = self.Properties.Colour["Top Shadow"]
        self.Properties["botShadowColor"] = self.Properties.Colour["Bottom Shadow"]

    def replaceObject(self, ob: "EdmObject", new_ob: "EdmObject"):
        """Replace the first instance of old_object in self.Objects by new_object.

        Args:
            ob (EdmObject): The old EdmObject to replace
            new_ob (EdmObject): The new EdmObject
        """
        assert ob in self.Objects, "Cannot replace, object: " + str(ob) + " not in self"
        self.Objects[self.Objects.index(ob)] = new_ob
        new_ob.Parent = self
        ob.Parent = None

    def removeObject(self, ob: "EdmObject") -> None:
        """Remove the first instance of object from self.Objects.

        Args:
            ob (EdmObject): The EdmObject to remove
        """
        assert ob in self.Objects, "Cannot remove, object: " + str(ob) + " not in self"
        del self.Objects[self.Objects.index(ob)]

    def read(self) -> str:
        """
        Read the edm properties set in this object.

        Read the edm properties set in this object, and output the text in a
        format readable to edm. Keys are exported in a random order apart from
        the keys which are always defined at the beginning or end of the object
        text

        Returns:
            str: the edm properties set in this object
        """
        first_keys = ["major", "minor", "release", "x", "y", "w", "h"]
        last_keys = ["visPv", "visInvert", "visMin", "visMax"]
        lines = []
        if self.Properties.Type == "Screen":
            lines.append("4 0 1")
            lines.append("beginScreenProperties")
            lines.append(self.__readKeys(first_keys))
            lines.append(
                self.__readKeys(list(set(self.Properties.keys()) - set(first_keys)))
            )
            lines.append("endScreenProperties")
            lines.append("")
            for ob in self.Objects:
                lines.append(ob.read())
        else:
            lines.append("# (%s)" % self.Properties.Type)
            lines.append("object %s" % self.Properties["object"])
            lines.append("beginObjectProperties")
            lines.append(self.__readKeys(first_keys))
            if self.Properties.Type == "Group":
                lines.append(
                    self.__readKeys(
                        list(
                            set(self.Properties.keys())
                            - set(first_keys)
                            - set(last_keys)
                        )
                    )
                )
                lines.append("")
                lines.append("beginGroup")
                lines.append("")
                for ob in self.Objects:
                    lines.append(ob.read())
                lines.append("endGroup")
                lines.append("")
                lines.append(self.__readKeys(last_keys, assert_existence=False))
            else:
                lines.append(
                    self.__readKeys(list(set(self.Properties.keys()) - set(first_keys)))
                )
            lines.append("endObjectProperties")
            lines.append("")
        return "\n".join(lines)

    def addObject(self, ob: "EdmObject") -> None:
        """
        Add another EdmObject to self. Fails if self.Properties.Type is not a Group, Screen or EdmTable.

        Args:
            ob (EdmObject): EdmObject to add to self
        """
        assert self.Properties.Type in [
            "Group",
            "Screen",
            "EdmTable",
        ], f"Trying to add {ob.Properties.Type} to a {self.Properties.Type}"
        assert ob.Properties.Type != "Screen", "Can't add a Screen to a " + str(
            self.Properties.Type
        )
        self.Objects.append(ob)
        ob.Parent = self

    def __repr__(self, level=0):
        """Make "print self" produce a useful output."""
        output = f' |{level}-{self.Properties.Type} at ({str(self.Properties["x"])},{str(self.Properties["y"])}\n'
        for ob in self.Objects:
            output += ob.__repr__(level + 1)
        return output

    def autofitDimensions(self, xborder: int = 10, yborder: int = 10) -> None:
        """
        Autofit dimensions of objects.

        If self.Properties.Type is a Group or a Screen, then autofit all children. Next, if
        self.Properties.Type is Lines or Group, resize position and dimensions to enclose
        its contents. Alternatively if self.Properties.Type is Screen, resize to fit
        contents, adding an x and y border (default 10 pixels each)

        Args:
            xborder (int, optional): X spacing between cells. Defaults to 10.
            yborder (int, optional): Y spacing between cells. Defaults to 10.
        """
        maxx = 0
        minx = 100000
        maxy = 0
        miny = 100000
        for ob in self.Objects:
            if not ob.Properties.Type == "Menu Mux PV":
                ob.autofitDimensions()
                x, y = ob.getPosition()
                w, h = ob.getDimensions()
                maxx = max(maxx, x + w)
                maxy = max(maxy, y + h)
                minx = min(minx, x)
                miny = min(miny, y)
        if self.Properties.Type == "Screen":
            # if any objects are inside borders, move them
            if xborder - minx > 0:
                deltax = xborder - minx
            else:
                deltax = 0
            if yborder - miny > 0:
                deltay = yborder - miny
            else:
                deltay = 0
            if deltax + deltay > 0:
                for ob in self.Objects:
                    ob.setPosition(deltax, deltay, relative=True)
            self.setDimensions(
                maxx + deltax + xborder, maxy + deltay + yborder, resize_objects=False
            )
        elif self.Properties.Type == "Group":
            self.setDimensions(maxx - minx, maxy - miny, resize_objects=False)
            self.setPosition(minx, miny, move_objects=False)
        elif (
            self.Properties.Type == "Lines"
            and "xPoints" in self.Properties
            and self.Properties["xPoints"]
        ):
            xtmp = self.Properties["xPoints"]
            assert isinstance(xtmp, Dict)
            xpts = [int(xtmp[x]) for x in xtmp.keys()]

            ytmp = self.Properties["yPoints"]
            assert isinstance(ytmp, Dict)
            ypts = [int(ytmp[y]) for y in ytmp.keys()]
            self.Properties["x"], self.Properties["y"] = min(xpts), min(ypts)
            self.Properties["w"], self.Properties["h"] = (
                max(xpts) - min(xpts),
                max(ypts) - min(ypts),
            )

    def getDimensions(self) -> Tuple[int, int]:
        """Return a tuple of the width and height of self as integers."""
        wtmp, htmp = self.Properties["w"], self.Properties["h"]
        assert isinstance(wtmp, int)
        assert isinstance(htmp, int)
        return wtmp, htmp

    def setDimensions(
        self,
        w: int | float,
        h: int | float,
        factors: bool = False,
        resize_objects: bool = True,
    ) -> None:
        """Set the dimensions of self.

        Set the dimensions of self to be w,h.
        If factors, new_width,new_height=width*w,height*h.
        If resize_objects, then resize children proportionally.

        Args:
            w (int): The width of self
            h (int): The height of self
            factors (bool, optional): Flag to determine if w and h are to be multiplied
                by their respective factors. Defaults to False.
            resize_objects (bool, optional): Flag to determine if children object need
                resizing proprotionally. Defaults to True.
        """
        wtmp, htmp = self.Properties["w"], self.Properties["h"]
        assert isinstance(wtmp, int)
        assert isinstance(htmp, int)
        if factors:
            neww = int(w * int(wtmp))
            newh = int(h * int(htmp))
            factorw = w
            factorh = h
        else:
            neww = int(w)
            newh = int(h)
            factorw = 1
            factorh = 1
            if int(wtmp) != 0:
                factorw = float(w) / float(wtmp)
            if int(htmp) != 0:
                factorh = float(h) / float(htmp)
        if self.Properties.Type == "Screen":
            x, y = (0, 0)
        else:
            x, y = self.getPosition()
        if (
            self.Properties.Type == "Group" or self.Properties.Type == "Screen"
        ) and resize_objects:
            for ob in self.Objects:
                obx, oby = ob.getPosition()
                ob.setPosition(
                    int(factorw * (obx - x) + x), int(factorh * (oby - y) + y)
                )
                ob.setDimensions(factorw, factorh, factors=True)
        elif (
            self.Properties.Type == "Lines"
            and "xPoints" in self.Properties
            and self.Properties["xPoints"]
            and resize_objects
        ):
            xtmp, ytmp = self.Properties["xPoints"], self.Properties["yPoints"]
            assert isinstance(xtmp, Dict)
            assert isinstance(ytmp, Dict)

            for point in list(xtmp.keys()):
                self.Properties["xPoints"][point] = str(
                    int(factorw * (int(xtmp[point]) - x) + x)
                )
            for point in list(ytmp.keys()):
                self.Properties["yPoints"][point] = str(
                    int(factorh * (int(ytmp[point]) - y) + y)
                )
        elif "Image" in self.Properties.Type and resize_objects:
            print(
                f'***Warning: EDM Image container for {self.Properties["file"]} has been resized. Image may not display properly',
                file=sys.stderr,
            )
        self.Properties["w"] = neww
        self.Properties["h"] = newh

    def getPosition(self) -> Tuple[int, int]:
        """Return a tuple of the x position and y position of self as integers.

        Returns:
            Tuple[int, int]: A tuple of the X and Y positions
        """
        xtmp, ytmp = self.Properties["x"], self.Properties["y"]
        assert isinstance(xtmp, int)
        assert isinstance(ytmp, int)
        return xtmp, ytmp

    def toint(self, s):
        """Convert elements in s to int if they are a digit."""
        return int("".join(x for x in str(s) if x.isdigit()))

    def setPosition(
        self, x: int, y: int, relative: bool = False, move_objects: bool = True
    ) -> None:
        """
        Set the position of self to be x,y.

        If relative, new_x,new_y = old_x*x,old_y*y.
        If move_objects, then move children proportionally.

        Args:
            x (int): X position of self
            y (int): Y position of self
            relative (bool, optional): Flag to detemine if new position should be
                relative to old position. Defaults to False.
            move_objects (bool, optional): Flag to determine if children should be
                moved proporionally. Defaults to True.
        """
        xtmp, ytmp = self.Properties["x"], self.Properties["y"]
        assert isinstance(xtmp, int)
        assert isinstance(ytmp, int)
        if relative:
            newx = x + xtmp
            newy = y + ytmp
            deltax = x
            deltay = y
        else:
            newx = x
            newy = y
            deltax = x - xtmp
            deltay = y - ytmp
        if self.Properties.Type == "Group" and move_objects:
            for ob in self.Objects:
                ob.setPosition(deltax, deltay, relative=True)
        elif (
            self.Properties.Type == "Lines"
            and "xPoints" in self.Properties
            and self.Properties["xPoints"]
        ):
            for point in self.Properties["xPoints"]:
                self.Properties["xPoints"][point] = str(
                    self.toint(self.Properties["xPoints"][point]) + deltax
                )
            for point in self.Properties["yPoints"]:
                self.Properties["yPoints"][point] = str(
                    self.toint(self.Properties["yPoints"][point]) + deltay
                )
        self.Properties["x"] = newx
        self.Properties["y"] = newy

    def substitute(self, old_text: str, new_text: str) -> None:
        """
        Replace old_text with new_text.

        Replace each instance of old_text with new_text in every property value,
        and every child object.

        Args:
            old_text (str): Text to replace with new_text
            new_text (str): Text to replace old_text with
        """
        # key: str
        # value: List[str] | Dict

        for key, value in self.Properties.items():
            if new_text == "''":
                new = ""
            else:
                new = new_text
            if isinstance(value, list):

                def process_string(x: str) -> str:
                    assert isinstance(x, str)
                    return x.replace(old_text, new)

                self.Properties[key] = list(map(process_string, value))
            elif isinstance(value, dict):
                # output a multiline dict
                for k, v in value.items():
                    try:
                        result = v.replace(old_text, new).replace('"', '')
                        # if we are in a symbols dict then take care that we
                        # leave '' values for empty substitutions
                        if key == "symbols":
                            bits = [
                                x.split("=") for x in unquoteString(result).split(",")
                            ]
                            for i, b in enumerate(bits):
                                if len(b) > 1 and b[1] == "":
                                    bits[i] = [b[0], "''"]
                            result = quoteString(",".join("=".join(x) for x in bits))
                        value[k] = result
                    except AttributeError:
                        pass
            else:
                try:
                    assert isinstance(value, str)
                    self.Properties[key] = value.replace(old_text, new)
                except AssertionError:
                    pass
        for ob in self.Objects:
            ob.substitute(old_text, new_text)

    def ungroup(self) -> None:
        """Ungroup this Group and add its contents directly to the parent object."""
        assert self.Parent, "Can't ungroup an object with no parent: " + str(self)
        index = self.Parent.Objects.index(self)
        for ob in self.Objects:
            ob.Parent = self.Parent
        self.Parent.Objects = (
            self.Parent.Objects[:index]
            + self.Objects
            + self.Parent.Objects[index + 1 :]
        )


def quoteString(string: str) -> str:
    """Fully quoted and escaped string helper function."""
    assert "\n" not in string, (
        "Cannot process a string with newlines in it "
        + "using quoteString, try quoteListString"
    )
    escape_list = ["\\", "{", "}", '"']
    for e in escape_list:
        string = string.replace(e, "\\" + e)
    return '"' + string + '"'


def unquoteString(string: str) -> str:
    """Reverse quoteString helper function."""
    escape_list = ["\\", "{", "}", '"']
    for e in escape_list:
        string = string.replace("\\" + e, e)
    return string.strip('"')


def quoteListString(string: str) -> List[str]:
    """Split list by newlines before quoting and escaping it."""
    # return a string converted to a list for edm
    return [quoteString(x) for x in string.split("\n")]


def write_helper() -> None:
    """
    Build dict of every available object with dict of default properties.

    Helper function that imports every edm object available and for each object
    builds a dict of default properties. It also builds a dict of colour names
    to indexes. It then dills these dictionaries, writing them to file. When
    EdmObject in imported again, these dictionaries are read and imported, and
    used to provide some sensible options for a default object.
    """
    print("Building helper object...")

    build_dir = Path.absolute(Path(__file__).parent)

    # load the environment so we can find the epics location
    edm_path = Path("/dls_sw/prod/tools/RHEL7-x86_64/defaults/bin/edm")
    while edm_path.is_symlink():
        edm_path = edm_path.readlink()
    edm_dir = Path.joinpath(edm_path.parent, "..", "..", "src", "edm")

    COLOUR = write_colour_helper()
    assert isinstance(COLOUR, Dict)

    # build up a list of include dirs to pass to g++
    dirs = [
        f"-I {Path.joinpath(edm_dir, x)}"
        for x in Path(edm_dir).iterdir()
        if Path.is_dir(x)
    ]
    dirs += [
        f"-I {Path.joinpath(edm_dir, 'util', x)}"
        for x in ["sys/os/Linux", "avl", "thread/os/Linux"]
    ]
    epics_base_dir = Path(os.environ["EPICS_BASE"])
    dirs += [f"-I {Path.joinpath(epics_base_dir, 'include')}"]
    lib_path = Path.joinpath(epics_base_dir, "lib", "linux-x86")
    dirs += [f"-L {lib_path}"]

    act_save = build_dir.joinpath("act_save.cc")
    act_save_so = build_dir.joinpath("act_save.so")

    print(build_dir)
    # build act_save.so, the program for creating a file of all edm objects
    line = f"g++ -fPIC {' '.join(dirs)} \
        -shared {act_save} -DBUILD_DIR={build_dir} -o {act_save_so} -Wl,-rpath={lib_path} -L {lib_path} -L {edm_dir}"
    os.system(line)
    print(line)
    # run it
    os.system(f"env LD_PRELOAD={act_save_so} edm -crawl dummy.edl")
    print(f"env LD_PRELOAD={act_save_so} edm -crawl dummy.edl")

    # get rid of the junk output by one widget
    with codecs.open(
        str(build_dir.joinpath("allwidgets.edl")), "r", encoding="latin-1"
    ) as f:
        # For some reason if the codec isn't 'latin-1' this line fails most of the time???
        all_widgets = f.read()
    print("-- all_widgets read --")
    all_widgets = all_widgets.replace(
        "# Additional properties\nbeginObjectProperties\nendObjectProperties", ""
    )

    # the output of the program isn't a proper screen, so make it so
    # defaults needs to be False as properties_helper.pkl may not exist and cause an error
    screen_obj = EdmObject("Screen", defaults=True)
    # fix some code, then add a header
    screen_obj.write(screen_obj.read() + "\n" + all_widgets)

    print("-- Setting up screen properties --")

    screen_properties: Dict[str, str | bool | int | List[str] | Dict] = {}
    # write the default screen properties
    screen_properties["major"] = 4
    screen_properties["minor"] = 0
    screen_properties["release"] = 1
    screen_properties["w"] = 500
    screen_properties["h"] = 600
    screen_properties["x"] = 0
    screen_properties["y"] = 0
    screen_properties["font"] = quoteString("arial-medium-r-14.0")
    screen_properties["ctlFont"] = quoteString("arial-bold-r-14.0")
    screen_properties["btnFont"] = quoteString("arial-bold-r-14.0")
    screen_properties["fgColor"] = COLOUR["Black"]
    screen_properties["bgColor"] = COLOUR["Canvas"]
    screen_properties["textColor"] = COLOUR["Black"]
    screen_properties["ctlFgColor1"] = COLOUR["Controller"]
    screen_properties["ctlFgColor2"] = COLOUR["White"]
    screen_properties["ctlBgColor1"] = COLOUR["Canvas"]
    screen_properties["ctlBgColor2"] = COLOUR["Black"]
    screen_properties["topShadowColor"] = COLOUR["Top Shadow"]
    screen_properties["botShadowColor"] = COLOUR["Bottom Shadow"]
    screen_properties["showGrid"] = True
    screen_properties["snapToGrid"] = True
    screen_properties["disableScroll"] = False
    PROPERTIES = {"Screen": screen_properties}
    for ob in screen_obj.Objects:
        # write the default properties for each object
        ob.Properties["w"] = 100
        ob.Properties["h"] = 100
        ob.Properties["x"] = 0
        ob.Properties["y"] = 0
        for key in ["font", "fgColor", "bgColor"]:
            if key in ob.Properties:
                ob.Properties[key] = screen_properties[key]
        if ob.Properties.Type == "Lines":
            del ob.Properties["xPoints"]
            del ob.Properties["yPoints"]
        for key, item in list(ob.Properties.items()):
            # remove anything that edm regards as a flag
            # this avoids
            if item is True:
                ob.Properties[key] = False
            elif key.upper() == "TYPE":
                del ob.Properties[key]
        # print(ob.__dict__)
        PROPERTIES[ob.Properties.Type] = ob.copy().Properties

    prop_pkl_file = build_dir.joinpath("properties_helper.pkl")
    prop_pkl_file.touch()
    with prop_pkl_file.open("wb") as f:
        # print(PROPERTIES)
        dill.dump(PROPERTIES, f, -1, byref=True)
    print("Done")


if __name__ == "__main__":
    write_helper()
