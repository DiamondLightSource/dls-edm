"""
A python representation of an edm object with associated useful functions.

Author: Tom Cobb
Updated to Python3 by: Oliver Copping
"""

import codecs
import os
import pickle
import sys
from pathlib import Path
from typing import Dict, ItemsView, KeysView, List, Optional, Tuple, Union, ValuesView

ignore_list = [
    "4 0 1",
    "beginScreenProperties",
    "endScreenProperties",
    "beginObjectProperties",
    "beginGroup",
    "endGroup",
]


def get_dicts() -> (
    Tuple[Dict[str, str], Dict[str, Union[str, bool, int, List[str], Dict]]]
):
    COLOUR: Dict[str, str] = {}
    PROPERTIES: Dict[str, Union[str, bool, int, List[str], Dict]] = {}
    # code to load the stored dictionaries
    try:
        file_path = Path.absolute(Path(__file__).parent)  # + "/helper.pkl")
        file_path = file_path.joinpath("helper.pkl")
        file = file_path.open("rb")
        pkl = pickle.load(file)
        (COLOUR, PROPERTIES) = pkl
    except IOError as e:
        print(f"IOError: \n{e}")
        (COLOUR, PROPERTIES) = ({}, {})

    return COLOUR, PROPERTIES


class EdmObject:
    """
    A python representation of an Edm Object.

    Attributes:
    Type - Type of self, like 'Group', 'Screen' or 'Embedded Window'
    Properties - Dictionary containing edm properties like w, h, font
    Objects - List of child EdmObjects if self.Type=='Group' or 'Screen'
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
    # can either use the index numbers, or look them up from self.Colour
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
        self.Type: str = "Invalid"
        self.Properties: Dict[str, Union[str, bool, int, List[str], Dict]] = {}
        self.Objects: List[EdmObject] = []
        self.Colour: Dict[str, str] = {}
        self.Parent: Optional[EdmObject] = None
        # set the type
        self.setType(obj_type)

        self.setProperties(defaults=defaults)

    # make item look like a dict
    def __setitem__(self, key: str, value: Union[str, int, List[str], Dict]) -> None:
        return self.Properties.__setitem__(key, value)

    def __getitem__(self, key: str) -> Union[str, int, List[str], Dict]:
        return self.Properties.__getitem__(key)

    def __delitem__(self, key: str) -> None:
        return self.Properties.__delitem__(key)

    def __contains__(self, key: str) -> bool:
        return self.Properties.__contains__(key)

    def items(
        self,
    ) -> ItemsView[str, Union[str, bool, int, List[str], Dict]]:
        return self.Properties.items()

    def keys(self) -> KeysView[str]:
        # assert self.Properties.keys().__class__ == {}.keys().__class__
        return self.Properties.keys()

    def values(self) -> ValuesView[Union[str, bool, int, List[str], Dict]]:
        # assert self.Properties.values().__class__ == {}.values().__class__
        return self.Properties.values()

    def setType(self, obj_type: str) -> None:
        """
        Set EdmObject Type.

        Set the Type of self to be obj_type.

        Args:
            obj_type (str): Type of self, like 'Group', 'Screen' or
                'Embedded Window'. Defaults to "Invalid".
        """
        self.Type = obj_type

        if obj_type != "Screen":
            self["object"] = "active" + obj_type.replace(" ", "") + "Class"
        # If PROPERTIES isn't defined, set some sensible values
        self["major"], self["minor"], self["release"] = (4, 0, 0)
        self["x"], self["y"], self["w"], self["h"] = (0, 0, 100, 100)

    def setProperties(self, defaults: bool = True):
        """
        Set EdmObject Properties.

        Attempt to populate self.Properties with default values and
        self.Colours with the index lookup table.

        Args:
            defaults (bool, optional): Flag to use default values for Type.
                Defaults to True.
        """
        COLOUR, PROPERTIES = get_dicts()

        if PROPERTIES:
            self.Colour = COLOUR
            try:
                default_dict = PROPERTIES[self.Type]
                if defaults:
                    self.Properties.update(default_dict)
            except Exception as e:
                print(
                    f"Exception caught when attempting to set default properties:\n {e}"
                )

    def copy(self) -> "EdmObject":
        """
        Return a copy of self.

        Return a copy of self complete with copies of its child objects. This copy does
        not have a Parent defined.

        Returns:
            EdmObject: A python representation of an Edm Object.
        """
        new_ob: EdmObject = EdmObject(self.Type, defaults=False)
        # need to explicitly copy some properties
        for k, v in self.__dict__.items():
            if v.__class__ == {}.__class__:
                new_ob[k] = v.copy()
            elif v.__class__ == [].__class__:
                new_ob[k] = v[:]
            else:
                new_ob[k] = v
        # add copies of child objects
        for ob in self.Objects:
            new_ob.addObject(ob.copy())
        return new_ob

    def write(
        self, text: Union[str, List[str]], expect: Optional[str] = "type"
    ) -> Optional[Union[str, List[str]]]:
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

        if [].__class__ == text.__class__:
            # make sure all elements are of type str
            assert all(isinstance(x, str) for x in text)
            lines = text
        else:
            assert isinstance(text, str)
            # if we are being passed text, we must be the top level object
            lines = text.strip().splitlines()
            # we must now clear all our properties to avoid junk tags
            self.Properties = {}

        if self.Type == "Screen":
            expect = None

        while True:
            # If the lines list is now empty, or only 1 empty line, we are now at the
            # end of the file
            if len(lines) == 0 or (len(lines) == 1 and lines[0] == ""):
                break

            # Reset at beginning of new search
            obj_lines = []
            obj_start_line = -1
            obj_end_line = -1

            # Need to find the start and end of an object
            for i, line in enumerate(lines):
                # If line empty or in ignore list, go to next line
                if not line or line in ignore_list:
                    pass
                if line[0].startswith("# ("):
                    obj_start_line = i
                elif line == "endObjectProperites" and obj_start_line != -1:
                    obj_end_line = i
                    obj_lines = lines[obj_start_line : obj_end_line + 1]
                    break

            obj_dict = self._get_edl_object_from_lines(obj_lines, expect)

            # k: str
            # v: Union[str, bool, int, List[Union[str, int]]]

            for k, v in obj_dict.items():
                if k == "Type":
                    assert isinstance(v, str)
                    self.Type = v
                else:
                    self[k] = v

            # Discard previous object lines
            lines = lines[obj_end_line + 1 :]

        return None

    def _get_edl_object_from_lines(
        self, obj_lines: List[str], expect: Optional[str]
    ) -> Dict[str, Union[str, bool, int, List[str]]]:
        #  Set up empty dictionary
        # object_dict: Dict[str, Union[str, bool, int, List[Union[str, int]]]] = {}
        object_dict: Dict = {}
        key: str = ""
        # value: Union[Dict[str, Union[str, int]], List[Union[str, int]]] = []
        value: Union[Dict, List] = []
        # multiline_dict: Dict[str, Union[str, bool, int]] = {}

        # First line of object should always include type
        object_dict["Type"] = self._get_edl_object_type(obj_lines[0])

        expect = None
        # Pop first line from list as no longer needed to be parsed
        obj_lines = obj_lines[1:]

        # basic object parser
        for i, line in enumerate(obj_lines):
            # Attempt to split line into parts, if there are multiple on the line
            parts = line.split()

            # see if we're expecting a property spanning multiple lines
            if expect == "multiline":
                # If the line is a '}' it's the end of the multiline
                if line == "}":
                    object_dict[key] = value
                    key = ""
                    value = []
                    expect = None
                # Otherwise, construct the multiline list
                else:
                    value = self._write_edl_multiline(line, value)

            # If only one part, set to True
            elif len(parts) == 1:
                object_dict[parts[0]] = True
            # If '{' in second part, it's the start of a multiline
            elif parts[1] == "{":
                key = parts[0]
                expect = "multiline"
            elif line == "endObjectProperties":
                # obj_end_line = i
                break
            else:
                object_dict[parts[0]] = line[
                    line.find(parts[0]) + len([parts][0]) :
                ].strip()
                if parts[0] in ["x", "y", "w", "h"]:
                    obj_part = object_dict[parts[0]]
                    assert isinstance(obj_part, str)
                    object_dict[parts[0]] = int(obj_part)

        return object_dict

    def _get_edl_object_type(self, line: str) -> str:
        assert line.startswith("# ("), "Expected '# (Type)', got " + line
        # self.Type = line[3 : line.find(")")]
        return line[3 : line.find(")")]

    def _write_edl_multiline(
        self, line: str, value: Union[List, Dict]
    ) -> Union[Dict[str, Union[str, int]], List[Union[str, int]]]:
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

    # def _write_new_edm_object(
    #     self, lines: str, index: int
    # ) -> Optional[Union[str, List[str]]]:
    #     more_lines: List[str]

    #     ob = EdmObject(defaults=False)
    #     more_lines = ob.write(lines[index:])
    #     assert isinstance(more_lines, List[str])
    #     self.addObject(ob)
    #     return self.write(more_lines, None)

    def flatten(self, include_groups: bool = True) -> List["EdmObject"]:
        """Flatten the tree of objects, and return it as a list.

        If include_groups==False, don't include groups, just their contents.

        Returns:
            List[EdmObject]: A list of EdmObjects in the tree
        """
        if not include_groups and self.Type == "Group":
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
        keys = list(self.keys())
        key_set = set(keys)
        # filter_set is the set of keys to filter against
        filter_set = set(filter_keys)
        # if we need to assert that all keys in filter_keys exist, do so here
        if assert_existence:
            assert filter_set <= key_set, "Some required keys not defined: " + str(
                list(filter_set - key_set)
            )
        # Make sure related displays with no filenames have the right numDsps
        if self.Type == "Related Display":
            if (
                "displayFileName" in list(self.keys())
                and len(list(self["displayFileName"].keys())) == 1
                and self["displayFileName"][list(self["displayFileName"].keys())[0]]
                == '""'
            ):
                self["displayFileName"] = {}
                self["symbols"] = {}
                self["numDsps"] = 0
        # print the keys
        for key in sorted(filter_keys):
            if key in keys and not key == "object" and not key[:2] == "__":
                value = self[key]
                if value is True:
                    # output a flag
                    lines.append(key)
                elif value is not False:
                    if value.__class__ == [].__class__:
                        # output a multiline string
                        text_vals = ["  %s\n" % str(v) for v in value]
                        if text_vals:
                            lines.append(key + " {\n" + "".join(text_vals) + "}")
                    elif value.__class__ == {}.__class__:
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
        self["topShadowColor"] = self.Colour["Top Shadow"]
        self["botShadowColor"] = self.Colour["Bottom Shadow"]

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
        if self.Type == "Screen":
            lines.append("4 0 1")
            lines.append("beginScreenProperties")
            lines.append(self.__readKeys(first_keys))
            lines.append(self.__readKeys(list(set(self.keys()) - set(first_keys))))
            lines.append("endScreenProperties")
            lines.append("")
            for ob in self.Objects:
                lines.append(ob.read())
        else:
            lines.append("# (%s)" % self.Type)
            lines.append("object %s" % self["object"])
            lines.append("beginObjectProperties")
            lines.append(self.__readKeys(first_keys))
            if self.Type == "Group":
                lines.append(
                    self.__readKeys(
                        list(set(self.keys()) - set(first_keys) - set(last_keys))
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
                lines.append(self.__readKeys(list(set(self.keys()) - set(first_keys))))
            lines.append("endObjectProperties")
            lines.append("")
        return "\n".join(lines)

    def addObject(self, ob: "EdmObject") -> None:
        """
        Add another EdmObject to self. Fails if self.Type is not a Group or a Screen.

        Args:
            ob (EdmObject): EdmObject to add to self
        """
        assert self.Type in ["Group", "Screen"], "Trying to add object to a " + str(
            self.Type
        )
        assert ob.Type != "Screen", "Can't add a Screen to a " + str(self.Type)
        self.Objects.append(ob)
        ob.Parent = self

    def __repr__(self, level=0):
        """Make "print self" produce a useful output."""
        output = (
            " |" * level
            + "-"
            + self.Type
            + " at ("
            + str(self["x"])
            + ","
            + str(self["y"])
            + ")\n"
        )
        for ob in self.Objects:
            output += ob.__repr__(level + 1)
        return output

    def autofitDimensions(self, xborder: int = 10, yborder: int = 10) -> None:
        """
        Autofit dimensions of objects.

        If self.Type is a Group or a Screen, then autofit all children. Next, if
        self.Type is Lines or Group, resize position and dimensions to enclose
        its contents. Alternatively if self.Type is Screen, resize to fit
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
            if not ob.Type == "Menu Mux PV":
                ob.autofitDimensions()
                x, y = ob.getPosition()
                w, h = ob.getDimensions()
                maxx = max(maxx, x + w)
                maxy = max(maxy, y + h)
                minx = min(minx, x)
                miny = min(miny, y)
        if self.Type == "Screen":
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
        elif self.Type == "Group":
            self.setDimensions(maxx - minx, maxy - miny, resize_objects=False)
            self.setPosition(minx, miny, move_objects=False)
        elif self.Type == "Lines" and "xPoints" in self and self["xPoints"]:
            # Make sure self is a EdmObject due to __getitem__ and __setitem__ overloading
            assert isinstance(self, EdmObject)

            xpts = [int(self["xPoints"][x]) for x in list(self["xPoints"].keys())]
            ypts = [int(self["yPoints"][y]) for y in list(self["yPoints"].keys())]
            self["x"], self["y"] = min(xpts), min(ypts)
            self["w"], self["h"] = max(xpts) - min(xpts), max(ypts) - min(ypts)

    def getDimensions(self) -> Tuple[int, int]:
        """Return a tuple of the width and height of self as integers."""
        # Make sure self is a EdmObject due to __getitem__ and __setitem__ overloading
        assert isinstance(self, EdmObject)
        return self["w"], self["h"]

    def setDimensions(
        self, w: int, h: int, factors: bool = False, resize_objects: bool = True
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
        # Make sure self is a EdmObject due to __getitem__ and __setitem__ overloading
        assert isinstance(self, EdmObject)

        if factors:
            neww = int(w * int(self["w"]))
            newh = int(h * int(self["h"]))
            factorw = w
            factorh = h
        else:
            neww = w
            newh = h
            factorw = 1
            factorh = 1
            if int(self["w"]) != 0:
                factorw = float(w) / float(self["w"])
            if int(self["h"]) != 0:
                factorh = float(h) / float(self["h"])
        if self.Type == "Screen":
            x, y = (0, 0)
        else:
            x, y = self.getPosition()
        if (self.Type == "Group" or self.Type == "Screen") and resize_objects:
            for ob in self.Objects:
                obx, oby = ob.getPosition()
                ob.setPosition(
                    int(factorw * (obx - x) + x), int(factorh * (oby - y) + y)
                )
                ob.setDimensions(factorw, factorh, factors=True)
        elif (
            self.Type == "Lines"
            and "xPoints" in self
            and self["xPoints"]
            and resize_objects
        ):
            for point in list(self["xPoints"].keys()):
                self["xPoints"][point] = str(
                    int(factorw * (int(self["xPoints"][point]) - x) + x)
                )
            for point in list(self["yPoints"].keys()):
                self["yPoints"][point] = str(
                    int(factorh * (int(self["yPoints"][point]) - y) + y)
                )
        elif "Image" in self.Type and resize_objects:
            print(
                "***Warning: EDM Image container for "
                + self["file"]
                + " has been resized. "
                + "Image may not display properly",
                file=sys.stderr,
            )
        self["w"] = neww
        self["h"] = newh

    def getPosition(self) -> Tuple[int, int]:
        """Return a tuple of the x position and y position of self as integers.

        Returns:
            Tuple[int, int]: A tuple of the X and Y positions
        """
        # Make sure self is a EdmObject due to __getitem__ and __setitem__ overloading
        assert isinstance(self, EdmObject)
        return self["x"], self["y"]

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
        # Make sure self is a EdmObject due to __getitem__ and __setitem__ overloading
        assert isinstance(self, EdmObject)
        if relative:
            newx = x + self["x"]
            newy = y + self["y"]
            deltax = x
            deltay = y
        else:
            newx = x
            newy = y
            deltax = x - self["x"]
            deltay = y - self["y"]
        if self.Type == "Group" and move_objects:
            for ob in self.Objects:
                ob.setPosition(deltax, deltay, relative=True)
        elif self.Type == "Lines" and "xPoints" in self and self["xPoints"]:
            for point in list(self["xPoints"].keys()):
                self["xPoints"][point] = str(
                    self.toint(self["xPoints"][point]) + deltax
                )
            for point in list(self["yPoints"].keys()):
                self["yPoints"][point] = str(
                    self.toint(self["yPoints"][point]) + deltay
                )
        self["x"] = newx
        self["y"] = newy

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
        # value: Union[List[str], Dict]

        for key, value in self.items():
            if new_text == "''":
                new = ""
            else:
                new = new_text
            if type(value) == list:

                def process_string(x: str) -> str:
                    assert isinstance(x, str)
                    return x.replace(old_text, new)

                self[key] = list(map(process_string, value))
            elif type(value) == dict:
                # output a multiline dict
                for k, v in value.items():
                    try:
                        result = v.replace(old_text, new)
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
                    self[key] = value.replace(old_text, new)
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
    to indexes. It then pickles these dictionaries, writing them to file. When
    EdmObject in imported again, these dictionaries are read and imported, and
    used to provide some sensible options for a default object.
    """
    get_dicts()
    print("Building helper object...")

    build_dir = Path.absolute(Path(__file__).parent)

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

    # build act_save.so, the program for creating a file of all edm objects
    line = f"g++ -fPIC {' '.join(dirs)} \
        -shared act_save.cc -o act_save.so -Wl,-rpath={lib_path} -L {lib_path} -L {edm_dir}"

    os.system(line)
    # run it
    os.system("env LD_PRELOAD=./act_save.so edm -crawl dummy.edl")

    # get rid of the junk output by one widget
    # For some reason if the codec isn't 'latin-1' this line fails most of the time???
    screen_text = codecs.open("allwidgets.edl", "r", encoding="latin-1").read()
    print("-- screen_text read --")
    screen_text = screen_text.replace(
        "# Additional properties\nbeginObjectProperties\nendObjectProperties", ""
    )

    # the output of the program isn't a proper screen, so make it so
    all_obs = EdmObject("Screen")
    # fix some code, then add a header
    all_obs.write(all_obs.read() + "\n" + screen_text)

    print("-- Setting up screen properties --")

    screen_properties: Dict[str, Union[str, bool, int, List[str], Dict]] = {}
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
    for ob in all_obs.Objects:
        # write the default properties for each object
        ob["w"] = 100
        ob["h"] = 100
        ob["x"] = 0
        ob["y"] = 0
        for key in ["font", "fgColor", "bgColor"]:
            if key in ob:
                ob[key] = screen_properties[key]
        if ob.Type == "Lines":
            del ob["xPoints"]
            del ob["yPoints"]
        for key, item in list(ob.items()):
            # remove anything that edm regards as a flag
            # this avoids
            if item is True:
                ob[key] = False
            elif "TYP" in key.upper():
                del ob[key]
        PROPERTIES[ob.Type] = ob.Properties.copy()
    pkl_file = build_dir.joinpath(Path("helper.pkl"))
    pkl_file.touch()
    with pkl_file.open("wb") as f:
        pickle.dump((COLOUR, PROPERTIES), f, 0)
    print("Done")


if __name__ == "__main__":
    write_helper()
