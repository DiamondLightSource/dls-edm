#!/bin/env python2.4

author = "Tom Cobb"
usage = """%prog [options] <input_screen_filename> <output_screen_filename>

Substitutes all embedded windows for their contents in a screen, saving it as
<output_screen_filename>"""

import os, sys, re
from optparse import OptionParser
from edmObject import *

class Substitute_embed:
    """Object that substitutes all embedded windows in a screen for groups
    containing their contents. screen is the source EdmObject. paths is a list
    of paths where the filenames of the embedded windows being substituted may
    be found. dict is an optional dict giving the maximum number of temperature,
    waterflow, and current embedded screens to substitute. additional_macros
    are then substituted in this screen"""
    in_screens = {}
    def __init__(self,screen,paths,dict={"NTEMP":99,"NFLOW":99,"NCURR":99},ungroup=False):
        self.ungroup = ungroup
        self.screen = screen
        self.paths = paths
        self.dict = dict
        self.additional_macros = {}
        self.counter = 0
        outsiders = self.__substitute_recurse(self.screen)
        # combine off screen menu muxes and menu mux pvs
        menu_muxes = []
        menu_mux_pvs = []
        screen_w,screen_h = self.screen.getDimensions()
        for ob in outsiders:
            if ob.Type in ["Menu Mux","Menu Mux PV"] \
               and not (ob.has_key("numItems") and ob["numItems"] and \
                        int(ob["numItems"]) > 1):
                # combine menu muxes and menu mux pvs if they have only 1 state
                x,y = ob.getPosition()
                if x>screen_w or y>screen_h:
                    if ob.Type=="Menu Mux":
                        menu_muxes.append(ob)
                    else:
                        menu_mux_pvs.append(ob)
                else:
                    self.screen.addObject(ob)
            else:
                self.screen.addObject(ob)
        for t,l in [("Menu Mux",menu_muxes),("Menu Mux PV",menu_mux_pvs)]:
            mux = EdmObject(t)
            for ob in l:
                symbols = [ o for o in ob.keys() if o.startswith("symbol") and \
                            len(o)==len("symbol")+1 ]
                symbol_max_num = int(max(symbols)[-1])
                if symbol_max_num>3 or \
                   mux.has_key("symbol"+str(3-symbol_max_num)):
                    screen.addObject(mux)
                    mux = EdmObject(t)
                mux["numItems"]=1
                mux["symbolTag"]= { 0: quoteString(".") }
                x,y = ob.getPosition()
                mux.setPosition(x,y)
                w,h = ob.getDimensions()
                mux.setDimensions(w,h)
                for i in range(3):
                    key = "symbol"+str(i)
                    if ob.has_key(key):
                        while True:
                            if not mux.has_key(key):
                                mux[key] = { 0: ob["symbol"+str(i)]["0"] }
                                for x in ["PV"+str(i),"value"+str(i)]:
                                    if ob.has_key(x):
                                        mux[x[:-1]+key[-1]]= { 0: ob[x]["0"] }
                                break
                            else:
                                key = key[:-1]+str(int(key[-1])+1)
            if mux.has_key("symbol0"):
                screen.addObject(mux)
                    
    def __substitute_recurse(self,root=None):
        # recursive substitute call
        outsiders = []
        for ob in root.flatten():
            if ob.Type == "Embedded Window":
                check = self.__check_embed(ob)
                if check == "replace":
                    i = max(ob["displayFileName"].keys())
                    macros = {}
                    for sub in ob["symbols"][i].split(","):
                        l = [ x.strip() for x in sub.strip('"').split("=") ]
                        if len(l) == 2:
                            macros[l[0]] = l[1]
                    group,new_outsiders = self.__group_from_screen(\
                                                ob["displayFileName"][i],macros)
                    if group:
                        for new_ob in [group]+new_outsiders:
                            x,y= ob.getPosition()
                            new_ob.setPosition(x,y,relative=True)
                        ob.Parent.replaceObject(ob,group)
                        if self.ungroup:
                            group.ungroup()
                        outsiders+=new_outsiders
                elif check == "remove":
                    ob.Parent.removeObject(ob)
        return outsiders

    def __group_from_screen(self,filename,macros):
        # create a group from a screen given by the filename
        filename = filename.strip('"').replace(".edl","")+".edl"
        if self.in_screens.has_key(filename):
            screen = self.in_screens[filename].copy()
        else:
            paths = [ os.path.join(p,filename) for p in self.paths \
                      if os.path.isfile(os.path.join(p,filename)) ]          
            if paths:
                screen = EdmObject("Screen")
                screen.write(open(paths[0],"r").read())                
                self.in_screens[filename] = screen.copy()                
            else:
                return (None,None)
        outsiders = []
        screen_w,screen_h = screen.getDimensions()
        group = EdmObject("Group")
        group.setDimensions(screen_w,screen_h)
        self.counter+=1
        for ob in screen.Objects:
            ob.substitute("auto-label","label%d"%self.counter)
            ob_x,ob_y = ob.getPosition()
            if ob_x<screen_w and ob_y<screen_h:
                group.addObject(ob)
            else:
                outsiders.append(ob)
        new_macros = self.additional_macros.copy()
        new_macros.update(macros)
        for key in new_macros.keys():
            for ob in [group]+outsiders:
                ob.substitute("$("+key+")",new_macros[key])
        return (group,outsiders)

                    
    def __check_embed(self,ob):
        # check for dummy in filePv, or if it is a temp, flow or curr box
        # controlled by $(P):INFO:N<VAR>
        # return replace if it needs to be replaced, remove to remove
        # and nothing to do nothing 
        filePv = ob["filePv"]
        if "dummy" in filePv:
            return "replace"
        else:
            for string in ["ntemp","nflow","ncurr"]:
            # see if the screen is one that we can substitute
                if string.upper() in filePv and "CALC" in filePv:
                    match = re.compile(r"A>=(\d+)\?1:0").search(filePv)
                    if match and match.groups() and int(match.groups()[0]) <= \
                       int(self.dict[string.upper()]):
                        return "replace"
                    else:
                        return "remove"
            return "nothing"

def cl_substitute_embed():
    parser = OptionParser(usage)
    paths="."
    parser.add_option("-p", "--paths", dest="paths", \
                      metavar="COLON_SEPARATED_LIST", \
                      help="Set the list of paths to look for the embedded "+\
                      "screens. Default is "+paths)
    (options, args) = parser.parse_args()
    if len(args)!=2:
        parser.error("Incorrect number of arguments")
    if options.paths:
        paths = options.paths
    paths = paths.split(":")
    screen = EdmObject("Screen")
    screen.write(open(args[0],"r").read())
    Substitute_embed(screen,paths)
    open(args[1],"w").write(screen.read())
    print "Embedded windows substituted in "+args[0]+", output written to "+args[1]

    
if __name__ == "__main__":
    cl_substitute_embed()
