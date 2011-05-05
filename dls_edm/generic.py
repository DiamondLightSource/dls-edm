import sys, re, os, math
from optparse import OptionParser
from edmObject import *                                # edm screen object
from edmTable import *                                # edm table object
from common import embed

def Generic(ob_list,auto_x_y_string=None,ideal_a_r=None):
    """Try to make a sensible sized screen from a list of objects and return it.
    Screen has no titlebar or exit button"""
    big_x_border, big_y_border = 15,10
    small_x_border, small_y_border = 10,10
    display_w, display_h = 1280, 1024
    screen = EdmObject("Screen")
    base_layout = EdmTable(xborder=big_x_border,yborder=big_y_border)
    screen.addObject(base_layout)
    # 1st attempt, sort the objects by size, and place groups in according to
    # how they fit it with the size of the largest object
    ob_dict = {}
    for ob in ob_list:
        # make a dict of objects sorted by size
        w,h = ob.getDimensions()
        if ob_dict.has_key((w*h,w,h)):
            ob_dict[(w*h,w,h)].append(ob)
        else:
            ob_dict[(w*h,w,h)]=[ob]
    keys = ob_dict.keys()
    keys.sort()
    keys.reverse()
    junk,max_w,max_h = keys[0] 
    counter = 0
    for (junk,w,h) in keys:
        # count the number of boxes needed
        obs = ob_dict[(junk,w,h)]
        num_w = (max_w + small_x_border) / (w + small_x_border)
        num_h = (max_h + small_y_border) / (h + small_y_border) 
        num = num_w*num_h
        assert num, "Zero size objects found in %s" % ob_list
        counter += (len(obs)+num-1)/num
    # fudge factors for producing nice screens
    a_r = float(max_w)/float(max_h)
    # fudge factors for producing nice screens
    if ideal_a_r is None:
        if a_r < 2 and counter > 3:
            ideal_a_r = 2
        else:
            ideal_a_r = 3.5
    max_y = math.sqrt(counter*a_r/ideal_a_r)
    new_layout = None
    num_remaining = 0
    num_h = 0
    for (junk,w,h) in keys:
        obs = ob_dict[(junk,w,h)]
        num_w = (max_w + small_x_border) / (w + small_x_border)
        num_h = (max_h + small_y_border) / (h + small_y_border) 
        num = num_w*num_h
        if num > 1:
            num_groups = (len(obs)+num-1)/num
            groups = [obs[i:i+num] for i in [i*num for i in range(num_groups)]]
            # if there's only a few, see if they fit in the last table
            if len(groups) == 1 and new_layout and num_remaining > len(groups[0]):
                for ob in groups[0]:
                    new_layout.addObject(ob)
                    new_layout.nextCell(max_y = num_h -1 )                    
                num_remaining -= len(groups[0])
            else:
                for group in groups:
                    new_layout = EdmTable(xborder=small_x_border,\
                                          yborder=small_y_border)
                    base_layout.addObject(new_layout)
                    for ob in group:
                        new_layout.addObject(ob)
                        new_layout.nextCell(max_y = num_h -1 )
                    base_layout.nextCell(max_y = max_y -1)
                    new_layout.setDimensions(max_w,max_h)        
                num_remaining = num - len(obs)
        else:
            for ob in obs:
                base_layout.addObject(ob)
                base_layout.nextCell(max_y = max_y -1 )
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
                
