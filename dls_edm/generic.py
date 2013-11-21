import sys, re, os, math
from optparse import OptionParser
from edmObject import *                                # edm screen object
from edmTable import *                                # edm table object
from common import embed

# this tries to make a generic screen from a list of objects using the 
# following algorithm:
# - Find the biggest size object big_ob
# - For each size object
#  - Make an EdmTable of size big_ob
#  - Fill it with obs
#  - If there are any spaces left then make a smaller EdmTable and iterate
# - Tile the large layouts to fit aspect ratio

# Return xborder, yborder for level of tiler
def get_borders(level):
    if level == 0:
        return (15, 10)
    elif level == 1:
        return (10, 10)
    else:
        return (5, 5)

class Tiler(EdmTable):
    def __init__(self, tilerw, tilerh, obw, obh, level):
        xborder, yborder = get_borders(level)
        EdmTable.__init__(self, xborder = xborder, yborder = yborder)   
        self._numw = (tilerw + xborder)/(obw + xborder)
        self._numh = (tilerh + yborder)/(obh + yborder)
        self._obw = obw
        self._obh = obh
        self._level = level
        self._t = None
        self._num = 0

    def hasSpace(self, ob):
        w, h = ob.getDimensions()
        if w > self._obw or h > self._obh:
            # Can't add something bigger than our ob width
            return False
        elif self._numw*self._numh - self._num > 0:
            # There is space for another in our layout
            return True
        elif ob.getDimensions() == (self._obw, self._obh):
            # No more space in this layout for one of this size
            return False
        elif self._t:
            # If we have a tiler then ask it if it has a space
            return self._t.hasSpace(ob)
        else:
            # No tiler and no space in us
            return False

    def addObject(self, ob):
        assert self.hasSpace(ob), "No space left"
        if self._t and self._t.hasSpace(ob):
            self._t.addObject(ob)
        else:
            w, h = ob.getDimensions()        
            if w != self._obw or h != self._obh:
                self._t = Tiler(self._obw, self._obh, w, h, self._level + 1)
                self._t.addObject(ob)
                ob = self._t
            EdmTable.addObject(self, ob)
            self.nextCell(max_y = self._numh -1)
            self._num += 1

def Generic(ob_list,auto_x_y_string=None,ideal_a_r=None,max_y=None):
    """Try to make a sensible sized screen from a list of objects and return it.
    Screen has no titlebar or exit button"""
    big_x_border, big_y_border = 15,10
    small_x_border, small_y_border = 10,10
    display_w, display_h = 1280, 1024
    # Sort the object into sized groups
    ob_dict = {}
    for ob in ob_list:
        ob_dict.setdefault(ob.getDimensions(), []).append(ob)    
    # Find the biggest object size
    max_w = max(w for w,h in ob_dict)
    max_h = max(h for w,h in ob_dict)        
    # This is the list of obs that will make up the final screen
    base_obs = []
    # Tile each group
    for w,h in reversed(sorted(ob_dict, key=lambda x: x[0]*x[1])):
        obs = ob_dict[(w,h)]
        while obs:
            ob = obs.pop(0)
            if len(base_obs) == 0 or not base_obs[-1].hasSpace(ob):
                base_obs.append(Tiler(max_w, max_h, w, h, 1))            
            base_obs[-1].addObject(ob)
    # now make the screen
    screen = EdmObject("Screen")
    # work out how high to tile these objects
    if max_y is None:
        a_r = float(max_w)/float(max_h)    
        if ideal_a_r is None:
            if a_r < 2 and len(base_obs) > 3:
                ideal_a_r = 2
            else:
                ideal_a_r = 3.5
        # fudge factors for producing nice screens
        max_y = int(math.sqrt(len(base_obs)*a_r/ideal_a_r))
    else:
        max_y = max_y - 1
    # Tile them
    xborder, yborder = get_borders(0)
    base_layout = EdmTable(xborder = xborder, yborder = yborder)
    screen.addObject(base_layout)
    # Add objects
    for ob in base_obs:
        base_layout.addObject(ob)
        base_layout.nextCell(max_y = max_y)
    # Finish up
    screen.autofitDimensions()
    if auto_x_y_string:
        w,h = screen.getDimensions()
        w,h = display_w - w, display_h - h
        # make a function that will get us a repeatable x,y value based on a str
        f = lambda x: 30*sum([ord(y) for y in x])
        g = lambda x: 53*sum([ord(y) for y in x])
        x,y = g(auto_x_y_string)%w, f(auto_x_y_string)%h
        screen.setPosition(x,y)
    for ob in screen.flatten():
        if ob.Type=="EdmTable":
            ob.ungroup()
    return screen            
                
