#!/bin/env python2.4

author = "Tom Cobb"
usage = """%prog [options] <input_screen> <output_screen>

This script takes an edm screen and flips it horizontally, keeping groups intact. It also replaces symbols and images with their flipped counterparts if they exist"""

import os,sys
from optparse import OptionParser
from edmObject import *
from common import flip_axis

def Flip_horizontal(screen,paths,flip_group_contents=False):
    """Flip the screen object, and return it with changes applied. paths gives the
    list of paths to look for flipped symbols or pngs. If flip_group_contacts:
    flip the contents of groups, otherwise keep them intact when flipping."""
    screenw,screenh = screen.getDimensions()
    files = []
    for p in paths:
        files.extend([ f for f in os.listdir(p) if f.endswith(".png") or \
                       "symbol" in f ])
    for ob in screen.Objects:
        # check groups' dimensions exactly enclose their contents
        ob.autofitDimensions()
        if ob.has_key("visPv"):
            visPv = ob["visPv"].strip('"')
        else:
            visPv = ""
        x,y = ob.getPosition()
        w,h = ob.getDimensions()
        if ob.Type == "Group":
            symbols = [ o for o in ob.Objects if o.Type=="Symbol" ]
            if visPv.startswith("#<AXIS_"):
                # replace AXIS with the reverse object
                if visPv.startswith("#<AXIS_RIGHT"):
                    new_ob=flip_axis("left")
                else:
                    new_ob=flip_axis("right")
                new_ob.setPosition(screenw-x-w,y)
                screen.replaceObject(ob,new_ob)
            elif visPv.startswith("#<"):
                for ob2 in [ o for o in ob.flatten() if o.Type == "Symbol" ]:
                    # replace symbols with their flipped version if applicable
                    filename = ob2["file"].strip('"').replace(\
                        "-symbol","-flipped-symbol")
                    if filename[-4:] != ".edl":
                        filename += ".edl"
                    if filename in files:           
                        ob2["file"] = quoteString(filename.replace(".edl",""))
            if flip_group_contents or not symbols or\
                (symbols and "filter" in symbols[0]["file"]):
                # if it is the beam object then reverse the order and positions
                # of the components
                for ob2 in ob.Objects:
                    ob2x,ob2y = ob2.getPosition()
                    ob2w,ob2h = ob2.getDimensions()
                    ob2.setPosition(x+w-(ob2x-x+ob2w),ob2y)
                    if (not symbols or flip_group_contents) and ob2.Type=="Lines":
                        flip_lines(ob2)
        elif ob.Type=="Lines" and ob["lineColor"]==ob.Colour["Controller"]:
            # flip lines in symbols
            flip_lines(ob)
        elif (ob.Type == "PNG Image" or ob.Type == "Image"):
            # replace images with their flipped version if applicable
            filename = ob["file"].strip('"').replace(".png","")+"-flipped.png"
            if filename in files:           
                ob["file"] = quoteString(filename.replace(".png",""))
        # mirror the group on the other side of the screen
        ob.setPosition(screenw-(x+w),y)
    return screen

def flip_lines(ob):
    if ob.has_key("xPoints") and ob["xPoints"]:
        ob2x,ob2y = ob.getPosition()
        ob2w,ob2h = ob.getDimensions()
        for key in ob["xPoints"].keys():
            px = int(ob["xPoints"][key])
            ob["xPoints"][key] = str(ob2x+ob2w-(px-ob2x))
                                    
def cl_flip_horizontal():
    parser = OptionParser(usage)
    paths="."
    parser.add_option("-p", "--paths", dest="paths", \
                      metavar="COLON_SEPARATED_LIST", \
                      help="Set the list of paths to look for the symbols "+\
                      "and images to flip. Default is "+paths)
    (options, args) = parser.parse_args()
    if len(args)!=2:
        parser.error("Incorrect number of arguments")
    if options.paths:
        paths = options.paths.split(":")
    screen = EdmObject("Screen")
    screen.write(open(args[0],"r").read())
    Flip_horizontal(screen,paths)
    open(args[1],"w").write(screen.read())
    print args[0]+ " has been flipped. Output written to: "+args[1]

if __name__ == "__main__":
    cl_flip_horizontal()


