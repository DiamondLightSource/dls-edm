#!/bin/env python2.4

author = "Tom Cobb"
"""
This script contains EdmTable, a virtual EdmObject that can expand and contract as neccessary, resizing its components
"""

import os, re, sys, shutil
from .edmObject import *

class EdmTable(EdmObject):

    """EdmTable(x=0,y=0,xoff=0,yoff=0,xborder=10,yborder=10,xjustify="c",\
                 yjustify="c")
    A virtual EdmObject that can expand and contract and generally behave like a
    gridlayout of cells. x,y are the default cell x and y positions (numbered
    from top left) that the next object will be placed into. Using the
    nextCell() and nextCol() methods modifies these. xoff and yoff are the
    default x and y offsets (local to the cell objects will be placed in).
    xborder and yborder are the spacing between cells. xjustify and yjustify
    are the justification in the cell (choose from "l","c","r","t","m","b":
    they stand for left, centre, right, top, middle, bottom)"""

    def __init__(self,x=0,y=0,xoff=0,yoff=0,xborder=10,yborder=10,xjustify="l",\
                 yjustify="t"):
        EdmObject.__init__(self,type="EdmTable")
        for attr in ["x","y","xoff","yoff","xborder","yborder","xjustify","yjustify"]:
            self["__def_"+attr]=eval(attr)

    def write(self,text):
        """write(text) -> Error
        You cannot write text into an EdmTable, try creating an EdmObject and
        writing text into that instead"""
        raise IOError("This is an EdmTable, you cannot write text into it")

    def read(self):
        """read() -> text
        Read the text of this object by exporting a group and reading that."""
        return self.exportGroup().read()        
    
    def autofitDimensions(self):
        """autofitDimensions() -> None
        Position objects globally so that they appear to be in the grid layout.
        If width and height are smaller that the miniumum space needed for this,
        make them larger. If they are larger already, stretch the cells to
        fit this size"""
        ws,hs = self.__dimLists()
        minw = sum(ws)+(len(ws)-1)*self["__def_xborder"]
        minh = sum(hs)+(len(hs)-1)*self["__def_yborder"]
        # if widths and heights are bigger than their minimums, resize cells uniformly
        if self["w"] > minw and self["__def_xjustify"] != "l":
            wratio = float(self["w"] - minw)/sum(ws)+1
            ws = [ int(0.5+w*wratio) for w in ws ]
        else:
            self["w"] = minw
        if self["h"] > minh and self["__def_yjustify"] != "t":
            hratio = float(self["h"] - minh)/sum(hs)+1
            hs = [ int(0.5+h*hratio) for h in hs ]
        else:
            self["h"] = minh
        # for each object, set its correct x and y value
        for ob in self.Objects:
            ob.autofitDimensions()
            axis_dict = {}
            for axis_str,dim_str,list in [("x","w",ws),("y","h",hs)]:
                axis = ob["__EdmTable_"+axis_str]
                # find value in cell
                val = ob["__EdmTable_"+axis_str+"off"]
                # find diff between avail dim, and object size + offset
                deltaval = list[axis] - val - ob[dim_str]
                if ob["__EdmTable_"+axis_str+"justify"] in ["l","t"]:
                    # objects are already left/top justified
                    pass
                elif ob["__EdmTable_"+axis_str+"justify"] in ["r","b"]:
                    # to right justfy, 
                    val += deltaval
                else:
                    val += deltaval/2
                # now we work out val relative to the screen and set it in the object
                val += self[axis_str]+sum(list[:axis])+axis*self["__def_"+axis_str+"border"]
                axis_dict[axis_str] = val
            ob.setPosition(axis_dict["x"],axis_dict["y"])
    
    def setPosition(self,x,y,relative=False,move_objects=True):
        """setPosition(x,y,relative=False,move_objects=True)
        Set the position of self to be x,y. If relative, new_x,new_y = 
        old_x*x,old_y*y. If move_objects, then move children proportionally"""
        if relative:
            newx = x + self["x"]
            newy = y + self["y"]
            deltax,deltay = (x,y)
        else:
            newx = x
            newy = y
            deltax = x-self["x"]
            deltay = y-self["y"]
        self["x"] = newx
        self["y"] = newy
        for ob in self.Objects:
            ob.setPosition(deltax,deltay,relative=True)
    
    def exportGroup(self):
        """exportGroup() -> EdmObject
        Return the group representation of self. This involved autofitDimensions
        followed by a copy of all children into a new group"""
        copy = self.copy()
        for ob in copy.Objects:
            if ob.Type == "EdmTable":
                copy.replaceObject(ob,ob.exportGroup())
        copy.autofitDimensions()
        group = EdmObject("Group")
        for key in list(copy.keys()):
            if "__EdmTable" in key:
                group[key] = copy[key]
        for ob in copy.Objects:
            group.addObject(ob)
        group.autofitDimensions()
        return group


    def __dimLists(self):
    # generate lists of max widths and heights for each column and each row
        # max_height[y_val] gives max height of row y, and the cells in it
        max_height = {}
        # max_width[x_val] gives max width of column x, and the cells in it
        max_width = {}
        for ob in self.Objects:
            # first make sure the object's dimensions reflect its contents
            ob.autofitDimensions()
            for axis_str,dim_str in [("x","w"),("y","h")]:
                # for each axis, find the min height/width
                axis = ob["__EdmTable_"+axis_str]
                val = ob[dim_str]+ob["__EdmTable_"+axis_str+"off"]
                if axis_str=="x":
                    dim_dict = max_width
                else:
                    dim_dict = max_height
                if axis in dim_dict:
                    dim_dict[axis]=max(dim_dict[axis],val)
                else:
                    dim_dict[axis]=val
        # calculate the max or each row and column
        if max_width:
            ws = [0]*( max( max_width.keys() )+1 )
            for key in list(max_width.keys()):
                ws[key] = max_width[key]
        else:
            ws = [0]
        if max_height:
            hs = [0]*( max( max_height.keys())+1 )
            for key in list(max_height.keys()):
                hs[key] = max_height[key]
        else:
            hs = [0]
        return ws,hs

                                
    def addObject(self,ob,x=None,y=None,yoff=None,xoff=None,\
                  xjustify=None,yjustify=None):
        """addObject(ob,x=None,y=None,yoff=None,xoff=None,\
                            xjustify=None,yjustify=None) -> None
        Add ob to the current cell of the grid layout. Use x,y,xoff,yoff,
        xjustify,yjustify to override their default values (no changes are
        made to the default values themselves)"""
        assert ob.Type!='Screen', "Can't add a Screen to a "+str(self.Type)
        # set the attributes needed to store this object
        for attr in ["x","y","xoff","yoff","xjustify","yjustify"]:
            if eval(attr)!=None:
                ob["__EdmTable_"+attr]=eval(attr)
            else:
                ob["__EdmTable_"+attr]=self["__def_"+attr]
        self.Objects.append(ob)
        ob.Parent = self

        
    def nextCell(self,max_y = -1):
        """nextCell(max_y = -1) -> None
        Move to the next cell, if max_y > -1, don't go further down that this
        cell, change columns if necessary"""
        if max_y > -1 and not self["__def_y"] < max_y:
            # if we have defined a max y to add to, and 
            self.nextCol()
        else:
            # move to next cell
            self["__def_y"]+=1
        
    def nextCol(self):
        """nextCol() -> None
        Move to the first cell in the next column"""
        self["__def_y"]=0
        self["__def_x"]+=1
        
        
if __name__=="__main__":
    a = EdmTable()
    counter = 10
    for size in [100,35,20,44,74,24,22,60,30,5,80,40,25,60,4,4,23,9,30,20,7,18]:
        r = EdmObject("Rectangle")
        r.setDimensions(size,size)
        r["lineColor"]="index "+str(2*counter)
        r["fillColor"]="index "+str(counter)
        r["fill"]=True
        a.addObject(r,xjustify=["l","r","c"][counter%3],yjustify=["t","b","c"][counter%3])
        if counter%2 and size%2:
            a.nextCol()
        elif counter%2:
            a.nextCell()
        counter += 1
    s = EdmObject("Screen")
    s.addObject(a)
    s.autofitDimensions()
    file = open("testEdmTable.edl","w")
    file.write(s.read())
