"""
EdmTable, a virtual EdmObject.

It can expand and contract as neccessary, resizing its components.

Author: Tom Cobb
Updated to Python3 by: Oliver Copping
"""

from typing import Dict, List, Optional, Tuple, Union

from .edmObject import EdmObject


class EdmTable(EdmObject):
    """A virtual EdmObject.

    A virtual EdmObject that can expand and contract and generally behave like a
    gridlayout of cells.

    x, y are the default cell x and y positions (numbered from top left) that the
    next object will be placed into.
    Using the nextCell() and nextCol() methods modifies these.

    xoff and yoff are the default x and y offsets (local to the cell objects will
    be placed in).

    xborder and yborder are the spacing between cells.

    xjustify and yjustify are the justification in the cell (choose from
    "l","c","r","t","m","b": they stand for left, centre, right, top, middle, bottom)

    EdmTable(x=0,y=0,xoff=0,yoff=0,xborder=10,yborder=10,xjustify="c",\
                 yjustify="c")

    Args:
        EdmObject (EdmObject): The EdmObject class
    """

    def __init__(
        self,
        x=0,
        y=0,
        xoff=0,
        yoff=0,
        xborder=10,
        yborder=10,
        xjustify="l",
        yjustify="t",
    ) -> None:
        """EdmTable constructor.

        Args:
            x (int, optional): Cell x position. Defaults to 0.
            y (int, optional): Cell y position. Defaults to 0.
            xoff (int, optional): Cell x offset. Defaults to 0.
            yoff (int, optional): Cell y offset. Defaults to 0.
            xborder (int, optional): X spacing between cells. Defaults to 10.
            yborder (int, optional): Y spacing between cells. Defaults to 10.
            xjustify (str, optional): X justification in the cell. Defaults to "l".
            yjustify (str, optional): Y justification in the cell. Defaults to "t".
        """
        # Store the entered args into a disctionary
        _args: Dict = locals()
        super().__init__(obj_type="EdmTable", defaults=False)

        # Loop over every argument
        for attr, val in _args.items():
            self.Properties[f"__def_{attr}"] = val

    def write(self, text: Union[str, list[str]], expect: Optional[str] = None) -> None:
        """
        Write method override for EdmObject write method.

        You cannot write text into an EdmTable, try creating an EdmObject and
        writing text into that instead

        Args:
            text (Union[str, list[str]]): Text to write to EdmTable
            expect (Optional[str], optional): Expected type of EdmTable.
                Defaults to None.

        Raises:
            IOError: This is an EdmTable, you cannot write text into it
        """
        raise IOError("This is an EdmTable, you cannot write text into it")

    def read(self) -> str:
        """Read the text of this object by exporting a group and reading that.

        Returns:
            str: The exported representation of self
        """
        return self.exportGroup().read()

    def autofitDimensions(self, xborder: int = 10, yborder: int = 10) -> None:
        """
        Autofit dimensions of objects.

        Position objects globally so that they appear to be in the grid layout.
        If width and height are smaller that the miniumum space needed for this,
        make them larger. If they are larger already, stretch the cells to
        fit this size.

        Args:
            xborder (int, optional): X spacing between cells. Defaults to 10.
            yborder (int, optional): Y spacing between cells. Defaults to 10.
        """
        ws, hs = self.__dimLists()

        assert isinstance(self.Properties["__def_xborder"], int)
        assert isinstance(self.Properties["__def_yborder"], int)

        minw = sum(ws) + (len(ws) - 1) * self.Properties["__def_xborder"]
        minh = sum(hs) + (len(hs) - 1) * self.Properties["__def_yborder"]

        # if widths and heights are bigger than their minimums, resize cells uniformly
        assert isinstance(self.Properties["w"], int)
        if self.Properties["w"] > minw and self.Properties["__def_xjustify"] != "l":
            wratio = float(self.Properties["w"] - minw) / sum(ws) + 1
            ws = [int(0.5 + w * wratio) for w in ws]
        else:
            self.Properties["w"] = minw

        assert isinstance(self.Properties["h"], int)
        if self.Properties["h"] > minh and self.Properties["__def_yjustify"] != "t":
            hratio = float(self.Properties["h"] - minh) / sum(hs) + 1
            hs = [int(0.5 + h * hratio) for h in hs]
        else:
            self.Properties["h"] = minh
        # for each object, set its correct x and y value
        for ob in self.Objects:
            ob.autofitDimensions()
            axis_dict = {}
            for axis_str, dim_str, list in [("x", "w", ws), ("y", "h", hs)]:
                assert isinstance(axis_str, str)
                assert isinstance(dim_str, str)

                axis = ob.Properties["__EdmTable_" + axis_str]
                assert isinstance(axis, int)
                # find value in cell
                val = ob.Properties["__EdmTable_" + axis_str + "off"]
                assert isinstance(val, int)
                # find diff between avail dim, and object size + offset

                ob_dim_str = ob.Properties[dim_str]
                assert isinstance(ob_dim_str, int)
                deltaval = list[axis] - val - ob_dim_str
                if ob.Properties["__EdmTable_" + axis_str + "justify"] in ["l", "t"]:
                    # objects are already left/top justified
                    pass
                elif ob.Properties["__EdmTable_" + axis_str + "justify"] in ["r", "b"]:
                    # to right justfy,
                    val += deltaval
                else:
                    val += int(deltaval / 2)
                # now we work out val relative to the screen and set it in the object
                assert isinstance(val, int)

                border_val = self.Properties["__def_" + axis_str + "border"]
                assert isinstance(border_val, int)

                self_axis_str = self.Properties[axis_str]
                assert isinstance(self_axis_str, int)
                val += self_axis_str + sum(list[:axis]) + axis * border_val
                axis_dict[axis_str] = val

            assert isinstance(axis_dict["x"], int)
            assert isinstance(axis_dict["y"], int)
            ob.setPosition(axis_dict["x"], axis_dict["y"])

    def setPosition(
        self, x: int, y: int, relative: bool = False, move_objects: bool = True
    ) -> None:
        """Set the position of self to be x,y.

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
        assert isinstance(self.Properties["x"], int)
        assert isinstance(self.Properties["y"], int)

        if relative:
            newx = x + self.Properties["x"]
            newy = y + self.Properties["y"]
            deltax, deltay = (x, y)
        else:
            newx = x
            newy = y
            deltax = x - self.Properties["x"]
            deltay = y - self.Properties["y"]
        self.Properties["x"] = newx
        self.Properties["y"] = newy
        for ob in self.Objects:
            ob.setPosition(deltax, deltay, relative=True)

    def exportGroup(self) -> EdmObject:
        """Return the group representation of self.

        This involved autofitDimensions followed by a copy of all children
        into a new group.

        Returns:
            EdmObject: EdmObject class of group
        """
        copy = self.copy()
        for ob in copy.Objects:
            if ob.Properties.Type == "EdmTable":
                assert isinstance(ob, EdmTable)
                copy.replaceObject(ob, ob.exportGroup())
        copy.autofitDimensions()
        group = EdmObject("Group")
        for key in list(copy.Properties.keys()):
            if "__EdmTable" in key:
                group.Properties[key] = copy.Properties[key]
        for ob in copy.Objects:
            group.addObject(ob)
        group.autofitDimensions()
        return group

    def __dimLists(self) -> Tuple[List[int], List[int]]:
        # generate lists of max widths and heights for each column and each row
        # max_height[y_val] gives max height of row y, and the cells in it
        max_height: Dict = {}
        # max_width[x_val] gives max width of column x, and the cells in it
        max_width: Dict = {}
        for ob in self.Objects:
            # first make sure the object's dimensions reflect its contents
            ob.autofitDimensions()
            for axis_str, dim_str in [("x", "w"), ("y", "h")]:
                # for each axis, find the min height/width
                axis = ob.Properties["__EdmTable_" + axis_str]

                ob_dim_str = ob.Properties[dim_str]
                ob_table_axis_offset = ob.Properties["__EdmTable_" + axis_str + "off"]
                assert isinstance(ob_dim_str, int)
                assert isinstance(ob_table_axis_offset, int)
                val = ob_dim_str + ob_table_axis_offset
                if axis_str == "x":
                    dim_dict = max_width
                else:
                    dim_dict = max_height
                if axis in dim_dict:
                    dim_dict[axis] = max(dim_dict[axis], val)
                else:
                    dim_dict[axis] = val
        # calculate the max or each row and column
        if max_width:
            ws = [0] * (max(max_width.keys()) + 1)
            for key in list(max_width.keys()):
                ws[key] = max_width[key]
        else:
            ws = [0]
        if max_height:
            hs = [0] * (max(max_height.keys()) + 1)
            for key in list(max_height.keys()):
                hs[key] = max_height[key]
        else:
            hs = [0]
        return ws, hs

    def addObject(
        self,
        ob: EdmObject,
        x: Optional[int] = None,
        y: Optional[int] = None,
        yoff: Optional[int] = None,
        xoff: Optional[int] = None,
        xjustify: Optional[str] = None,
        yjustify: Optional[str] = None,
    ) -> None:
        """Add ob to the current cell of the grid layout.

        Use x,y,xoff,yoff,xjustify,yjustify to override their default values
        (no changes are made to the default values themselves).

        Args:
            ob (EdmObject): EdmObject to add to current cell
            x (Optional[int], optional): X position override of EdmObject.
                Defaults to None.
            y (Optional[int], optional): Y position override of EdmObject.
                Defaults to None.
            yoff (Optional[int], optional): X offset override of EdmObject.
                Defaults to None.
            xoff (Optional[int], optional): Y offset override of EdmObject.
                Defaults to None.
            xjustify (Optional[str], optional): X alignment. Defaults to None.
            yjustify (Optional[str], optional): Y alignment. Defaults to None.
        """
        _args = locals()
        del _args["self"], _args["ob"]

        assert ob.Properties.Type != "Screen", "Can't add a Screen to a " + str(
            self.Properties.Type
        )
        # Loop over every argument
        for attr, val in _args.items():
            # set the attributes needed to store this object
            if hasattr(ob.Properties, attr) and ob.Properties[attr] is not None:
                ob.Properties[f"__EdmTable_{attr}"] = val
            else:
                ob.Properties[f"__EdmTable_{attr}"] = self.Properties[f"__def_{attr}"]
        self.Objects.append(ob)
        ob.Parent = self

    def nextCell(self, max_y: int = -1) -> None:
        """Move to the next cell.

        If max_y > -1, don't go further down that this cell, change columns if necessary

        Args:
            max_y (int, optional): Max number of cells in Y. Defaults to -1.
        """
        assert isinstance(self.Properties["__def_y"], int)
        if max_y > -1 and not self.Properties["__def_y"] < max_y:
            # if we have defined a max y to add to, and
            self.nextCol()
        else:
            # move to next cell
            self.Properties["__def_y"] += 1

    def nextCol(self) -> None:
        """Move to the first cell in the next column."""
        assert isinstance(self.Properties["__def_y"], int)
        assert isinstance(self.Properties["__def_x"], int)
        self.Properties["__def_y"] = 0
        self.Properties["__def_x"] += 1


if __name__ == "__main__":
    a = EdmTable()
    counter = 10
    for size in [
        100,
        35,
        20,
        44,
        74,
        24,
        22,
        60,
        30,
        5,
        80,
        40,
        25,
        60,
        4,
        4,
        23,
        9,
        30,
        20,
        7,
        18,
    ]:
        r = EdmObject("Rectangle")
        r.setDimensions(size, size)
        r.Properties["lineColor"] = "index " + str(2 * counter)
        r.Properties["fillColor"] = "index " + str(counter)
        r.Properties["fill"] = True
        a.addObject(
            r,
            xjustify=["l", "r", "c"][counter % 3],
            yjustify=["t", "b", "c"][counter % 3],
        )
        if counter % 2 and size % 2:
            a.nextCol()
        elif counter % 2:
            a.nextCell()
        counter += 1
    s = EdmObject("Screen")
    s.addObject(a)
    s.autofitDimensions()
    file = open("testEdmTable.edl", "w")
    file.write(s.read())
