#!/bin/env python2.4

author = "Tom Cobb"
usage = """%prog [options] <input_screen> <output_screen> <width> <height>

This script resizes an edm screen <input_screen> to size (<width>,<height>).
It also resizes fonts, then prints the resulting screen to <output_screen>"""

import os, sys
from optparse import OptionParser
from edmObject import *

def new_font_size(factor,font):
    # finds the closest size for a font
    sizes = [80,100,120,140,160,180,200,240,280,320,360,420,480,600,720,960,\
             1200,1680,2160,3120,4080,5040]
    size = int(font.split("-")[-1].replace('.0"',""))
    # work out the difference between the desired size and available sizes
    new_size = min(sizes, key=lambda x:abs(x-int(size*factor*10)))
    new_font = font.replace("-"+str(size),"-"+str(int(new_size/10.0)))
    return new_font


def Resize(screen,width,height):
    """Resize screen dimensions to be (width,height). Resize fonts proportionally.
    Modify the original object, and return it with changes applied."""
    old_width,old_height = screen.getDimensions()
    factor =  float(width)/float(old_width)
    screen.setDimensions(width,height,resize_objects=True)
    for ob in screen.flatten():
        if ob.has_key("font"):
            font = ob["font"]
            ob["font"] = new_font_size(factor,font)
    return screen

def cl_resize():
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    if len(args)!=4:
        parser.error("Incorrect number of arguments")
    screen = EdmObject("Screen")
    screen.write(open(args[0],"r").read())
    Resize(screen,int(args[2]),int(args[3]))
    open(args[1],"w").write(screen.read())
    print args[0]+ " has been resized. Output written to: "+args[1]

if __name__ == "__main__":
    cl_resize()

