#!/bin/env python2.4

"""Author: Tom Cobb

This file contains a python representation of an edm object with associated
useful functions."""

import os, re, sys, shutil, pickle, copy

class EdmObject:

    """EdmObject(type)

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
    
    def __init__(self, type = "Invalid", defaults = True):
        # initialise variables
        self.Properties = {}
        self.Colour = {}
        self.Objects = []
        self.Parent = None
        self.Type = "Invalid"
        # set the type
        self.setType(type, defaults = defaults)

    # make item look like a dict
    def __setitem__(self, key, value):
        return self.Properties.__setitem__(key, value)

    def __getitem__(self, key):
        return self.Properties.__getitem__(key)

    def __delitem__(self, key):
        return self.Properties.__delitem__(key)

    def __contains__(self, key):
        return self.Properties.__contains__(key)

    def items(self):
        return self.Properties.items()

    def keys(self):
        return self.Properties.keys()

    def values(self):
        return self.Properties.values()

    def setType(self,type,defaults = True):
        """setType(type) -> None
        Set the Type of self to be type, and attempt to populate self.Properties
        with default values and self.Colours with the index lookup table"""
        self.Type = type
        if PROPERTIES:
            self.Colour = COLOUR
            try:
                default_dict = PROPERTIES[type]
                if defaults:
                    self.Properties.update(default_dict)
                return
            except:
                pass
        if type!="Screen":
            self['object'] = 'active' + type.replace(" ","") + 'Class'
        # If PROPERTIES isn't defined, set some sensible values
        self['major'],self['minor'],self['release']=(4,0,0) 
        self['x'],self['y'],self['w'],self['h']=(0,0,100,100)   

    def copy(self):
        """copy() -> EdmObject
        Return a copy of self complete with copies of its child objects. This
        copy does not have a Parent defined."""
        new_ob = EdmObject(self.Type,defaults=False)
        # need to explicitly copy some properties
        for k,v in self.items():
            if v.__class__=={}.__class__:
                new_ob[k]=v.copy()
            elif v.__class__==[].__class__:
                new_ob[k]=v[:]
            else:
                new_ob[k]=v
        # add copies of child objects
        for ob in self.Objects:
            new_ob.addObject(ob.copy())
        return new_ob

    def write(self,text,expect="type"):
        """write(text) -> None
        Populate the object's properties with the selected text. This should be
        either the entire text from a .edl file for a screen, or the section
        from '# (Type)' to 'endObjectProperties' for any other object. The text
        can either be a string or a list of lines"""
        if [].__class__ == text.__class__:
            lines = text
        else:
            # if we are being passed text, we must be the top level object
            lines = text.strip().splitlines()
            # we must now clear all our properties to avoid junk tags
            self.Properties = {}
        if self.Type == "Screen":
            expect = None
        ignore_list = [ "4 0 1","beginScreenProperties","endScreenProperties",\
                        "beginObjectProperties","beginGroup","endGroup"]
        key = None
        value = None
        # basic parser
        for i,line in enumerate(lines):
            if not line or line in ignore_list:
                pass
            # see if we're expecting # (type)
            elif expect == "type":
                assert line.startswith("# ("), "Expected '# (Type)', got "+line
                self.Type = line[3:line.find(")")]
                expect = None
            # see if we're expecting a property spanning multiple lines
            elif expect == "multiline":
                if line=="}":
                    self[key]=value
                    key = None
                    value = None
                    expect = None
                else:
                    # replace quotes with a tag, then split the line
                    temp_list = line.replace('\\"',"*&q").strip().split('"')
                    list = []
                    in_quotes = False
                    for t in temp_list:
                        if not in_quotes:
                            list.extend(t.strip().split())
                        else:
                            list.append('"'+t.replace("*&q",'\\"')+'"')
                        in_quotes = not in_quotes
                    # use a list to represent a list of lines
                    if len(list)==1:
                        if not value: value = []
                        assert value.__class__==[].__class__, \
                            "Expected '  x', got "+line
                        value.append(list[0])
                    # use a dict to represent key,val pairs
                    else:
                        if not value: value = {}
                        assert value.__class__=={}.__class__, \
                            "Expected '  x x', got "+line
                        value[list[0]]=" ".join(list[1:])
            # if we aren't expecting a type, it must be a new object
            elif line.startswith("# ("):
                ob = EdmObject(defaults=False)
                more_lines = ob.write(lines[i:])
                self.addObject(ob)
                return self.write(more_lines,None)
            # return the unparsed lines to parent object's write method
            elif line=="endObjectProperties":
                return lines[i+1:]
            # set the property in self
            else:
                list = line.strip().split()
                if len(list)==1:
                    self[list[0]] = True
                elif list[1]=="{":
                    key = list[0]
                    expect = "multiline"
                else:
                    self[list[0]]=line[line.find(list[0])+len(list[0]):].strip()
                    if list[0] in ['x','y','w','h']:
                        self[list[0]] = int(self[list[0]])

    def flatten(self,include_groups=True):
        """flatten(include_groups=True) -> [ EdmObjects ]
        Flatten the tree of objects, and return it as a list. If
        include_groups==False, don't include groups, just their contents."""
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
            assert filter_set <= key_set, \
            'Some required keys not defined: '+str(list(filter_set - key_set))
        # Make sure related displays with no filenames have the right numDsps
        if self.Type=="Related Display":
            if "displayFileName" in list(self.keys()) and len(list(self["displayFileName"].keys())) == 1 and self["displayFileName"][list(self["displayFileName"].keys())[0]] == '""':
                self["displayFileName"] = {}
                self["symbols"] = {}
                self["numDsps"] = 0
        # print the keys                
        for key in sorted(filter_keys):
            if key in keys and not key=="object" and not key[:2]=="__":
                value = self[key]
                if value is True:
                    # output a flag
                    lines.append(key)               
                elif not value is False:
                    if value.__class__ == [].__class__:
                        # output a multiline string
                        text_vals = ['  %s\n' % str(v) for v in value]
                        if text_vals:
                            lines.append(key + ' {\n' + ''.join(text_vals) + '}')
                    elif value.__class__ == {}.__class__:
                        # output a multiline dict
                        vals = list(value.keys())
                        vals.sort()
                        text_vals = ['  %s %s\n' % (str(k), str(value[k])) \
                                     for k in vals]
                        if text_vals:
                            lines.append(key + ' {\n' + ''.join(text_vals) + '}')
                    else:
                        # output a string value
                        lines.append(str(key)+" "+str(value))
        return "\n".join(lines)


    def raiseObject(self):
        """raiseObject() -> None
        Raise self to the front of its Parent's list of objects, so item is at
        the front of the group or screen"""
        assert self.Parent, "Cannot raise, object: "+str(self)+\
               " doesn't have a Parent"
        self.Parent.Objects.remove(self)
        self.Parent.Objects.append(self)

    def lowerObject(self):
        """lowerObject() -> None
        Lower self to the back of its Parent's list of objects, so item is at
        the back of the group or screen"""
        assert self.Parent, "Cannot lower, object: "+str(self)+\
               " doesn't have a Parent"
        self.Parent.Objects.remove(self)
        self.Parent.Objects.insert(0,self)      
        
    def setShadows(self):
        """setShadows() -> None
        Set the top and bottom shadows of self to be reasonable values"""
        self["topShadowColor"] = self.Colour["Top Shadow"]
        self["botShadowColor"] = self.Colour["Bottom Shadow"]       

    def replaceObject(self,ob,new_ob):
        """replaceObject(old_object,new_object) -> None
        Replace the first instance of old_object in self.Objects by
        new_object"""
        assert ob in self.Objects, "Cannot replace, object: "+\
               str(ob)+" not in self"
        self.Objects[self.Objects.index(ob)] = new_ob
        new_ob.Parent = self
        ob.Parent = None

    def removeObject(self,ob):
        """removeObject(object) -> None
        Remove the first instance of object from self.Objects"""
        assert ob in self.Objects, "Cannot remove, object: "+\
               str(ob)+" not in self"
        del(self.Objects[self.Objects.index(ob)])
        
    def read(self):
        """read() -> string
        Read the edm properties set in this object, and output the text in a
        format readable to edm. Keys are exported in a random order apart from
        the keys which are always defined at the beginning or end of the object
        text"""
        first_keys = ['major', 'minor', 'release', 'x', 'y', 'w', 'h']
        last_keys = ['visPv', 'visInvert', 'visMin', 'visMax']
        lines = []
        if self.Type=="Screen":
            lines.append('4 0 1')
            lines.append('beginScreenProperties')
            lines.append(self.__readKeys(first_keys))
            lines.append(self.__readKeys(list(set(self.keys()) - \
                                              set(first_keys))))
            lines.append('endScreenProperties')
            lines.append('')
            for ob in self.Objects:
                lines.append(ob.read())
        else:   
            lines.append('# (%s)' % self.Type)
            lines.append('object %s' % self["object"])
            lines.append('beginObjectProperties')
            lines.append(self.__readKeys(first_keys))
            if self.Type == "Group":
                lines.append(self.__readKeys(list(set(self.keys()) -\
                                              set(first_keys)-set(last_keys))))
                lines.append('')
                lines.append('beginGroup')
                lines.append('')
                for ob in self.Objects:
                    lines.append(ob.read())
                lines.append('endGroup')
                lines.append('')
                lines.append(self.__readKeys(last_keys,assert_existence=False))
            else:
                lines.append(self.__readKeys(list(set(self.keys())-\
                                                  set(first_keys))))
            lines.append('endObjectProperties')
            lines.append('')
        return "\n".join(lines)

                
    def addObject(self,ob):
        """addObject(object) -> None
        Add another EdmObject to self. Fails if self.Type is not a Group or a
        Screen"""
        assert self.Type in ['Group','Screen'], \
            'Trying to add object to a '+str(self.Type)
        assert ob.Type!='Screen', "Can't add a Screen to a "+str(self.Type)
        self.Objects.append(ob)
        ob.Parent = self

    
    def __repr__(self,level=0):
        # make "print self" produce a useful output
        output =  " |"*level+"-"+self.Type+" at ("+str(self["x"])+","+\
                 str(self["y"])+")\n"
        for ob in self.Objects:
            output+=ob.__repr__(level+1)
        return output

    def autofitDimensions(self,xborder=10,yborder=10):
        """autofitDimensions(xborder=10,yborder=10) -> None
        If self.Type is a Group or a Screen, then autofit all children. Next, if
        self.Type is Lines or Group, resize position and dimensions to enclose
        its contents. Alternatively if self.Type is Screen, resize to fit
        contents, adding an x and y border (default 10 pixels each)"""
        maxx = 0
        minx = 100000
        maxy = 0
        miny = 100000
        for ob in self.Objects:
            if not ob.Type=="Menu Mux PV":
                ob.autofitDimensions()
                x,y = ob.getPosition()
                w,h = ob.getDimensions()
                maxx = max(maxx,x+w)
                maxy = max(maxy,y+h)
                minx = min(minx,x)
                miny = min(miny,y)
        if self.Type=="Screen":
            # if any objects are inside borders, move them
            if xborder-minx > 0:
                deltax = xborder - minx
            else:
                deltax = 0
            if yborder-miny > 0:
                deltay = yborder - miny
            else:
                deltay = 0
            if deltax+deltay>0:
                for ob in self.Objects:
                    ob.setPosition(deltax,deltay,relative=True)
            self.setDimensions(maxx+deltax+xborder,maxy+deltay+yborder,\
                               resize_objects=False)
        elif self.Type=="Group":
            self.setDimensions(maxx-minx,maxy-miny,resize_objects=False)
            self.setPosition(minx,miny,move_objects=False)
        elif self.Type=="Lines" and "xPoints" in self and self["xPoints"]:
            xpts = [ int(self["xPoints"][x]) for x in list(self["xPoints"].keys()) ]
            ypts = [ int(self["yPoints"][y]) for y in list(self["yPoints"].keys()) ]
            self["x"],self["y"] = min(xpts),min(ypts)
            self["w"],self["h"] = max(xpts)-min(xpts),max(ypts)-min(ypts)
                        
                                                
    def getDimensions(self):
        """getDimensions() -> (w,h)
        Return a tuple of the width and height of self as integers"""
        return self["w"],self["h"]
            
    def setDimensions(self,w,h,factors=False,resize_objects=True):
        """setDimensions(w,h,factors=False,resize_objects=True) -> None
        Set the dimensions of self to be w,h. If factors, new_width,new_height=
        width*w,height*h. If resize_objects, then resize children
        proportionally"""
        if factors:
            neww = int(w*int(self["w"]))
            newh = int(h*int(self["h"]))
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
        if self.Type=="Screen":
            x,y = (0,0)
        else:
            x,y=self.getPosition()
        if (self.Type=="Group" or self.Type=="Screen") and resize_objects:
            for ob in self.Objects:
                obx,oby = ob.getPosition()
                ob.setPosition(int(factorw*(obx-x)+x),int(factorh*(oby-y)+y))
                ob.setDimensions(factorw,factorh,factors=True)
        elif self.Type=="Lines" and "xPoints" in self and \
                  self["xPoints"] and resize_objects:
            for point in list(self["xPoints"].keys()):
                self["xPoints"][point]=str(int( factorw*(int(\
                                                self["xPoints"][point] )-x)+x ))
            for point in list(self["yPoints"].keys()):
                self["yPoints"][point]=str(int( factorh*(int(\
                                                self["yPoints"][point] )-y)+y ))
        elif "Image" in self.Type and resize_objects:
            print("***Warning: EDM Image container for "+\
                  self["file"]+" has been resized. "+\
                  "Image may not display properly", file=sys.stderr)
        self["w"] = neww
        self["h"] = newh
    
    def getPosition(self):
        """getPosition() -> (x,y)
        Return a tuple of the x position and y position of self as integers"""
        return self["x"],self["y"]
    
    def toint(self, s):
        return int("".join(x for x in str(s) if x.isdigit()))
    
    def setPosition(self,x,y,relative=False,move_objects=True):
        """setPosition(x,y,relative=False,move_objects=True) -> None
        Set the position of self to be x,y. If relative, new_x,new_y = 
        old_x*x,old_y*y. If move_objects, then move children proportionally"""
        if relative:
            newx = x + self["x"]
            newy = y + self["y"]
            deltax = x
            deltay = y
        else:
            newx = x
            newy = y
            deltax = x-self["x"]
            deltay = y-self["y"]
        if self.Type=="Group" and move_objects:
            for ob in self.Objects:
                ob.setPosition(deltax,deltay,relative=True)
        elif self.Type=="Lines" and "xPoints" in self and self["xPoints"]:
            for point in list(self["xPoints"].keys()):
                self["xPoints"][point]=str(self.toint(self["xPoints"][point])+deltax)
            for point in list(self["yPoints"].keys()):
                self["yPoints"][point]=str(self.toint(self["yPoints"][point])+deltay)
        self["x"] = newx
        self["y"] = newy

    def substitute(self,old,rep):
        """substitute(old_text,new_text) -> None Replace each instance of
        old_text with new_text in every property value, and every child
        object"""
        for key,value in list(self.items()):            
            if rep == "''":
                new = ""            
            else:
                new = rep
            if type(value) == list:
                self[key] = [ o.replace(old,new) for o in value ]
            elif type(value) == dict:
                # output a multiline dict
                for k,v in list(value.items()):
                    try:
                        result = v.replace(old,new)
                        # if we are in a symbols dict then take care that we
                        # leave '' values for empty substitutions                        
                        if key == "symbols":                            
                            bits = [x.split("=") for x in unquoteString(result).split(",")]
                            for i, b in enumerate(bits):
                                if len(b) > 1 and b[1] == "":
                                    bits[i] = (b[0], "''")
                            result = quoteString(",".join("=".join(x) for x in bits))
                        value[k] = result                        
                    except AttributeError:
                        pass
            else:
                try:
                    self[key]=value.replace(old,new)
                except AttributeError:
                    pass
        for ob in self.Objects:
            ob.substitute(old,rep)

    def ungroup(self):
        """ungroup() -> None
        Ungroup this Group and add its contents directly to the parent object"""
        assert self.Parent, "Can't ungroup an object with no parent: "+str(self)
        index = self.Parent.Objects.index(self)
        for ob in self.Objects:
            ob.Parent = self.Parent
        self.Parent.Objects = self.Parent.Objects[:index]+\
                              self.Objects+self.Parent.Objects[index+1:]        
                                        

def quoteString(string):
    """quoteString(string) -> String
    Helper function to make a fully quoted and escaped string."""
    assert "\n" not in string, "Cannot process a string with newlines in it "+\
           "using quoteString, try quoteListString" 
    escape_list = ["\\","{","}",'"']
    for e in escape_list:
        string = string.replace(e,"\\"+e) 
    return '"'+string+'"'

def unquoteString(string):
    """unquoteString(string) -> String
    Helper function to reverse quoteString."""
    escape_list = ["\\","{","}",'"']
    for e in escape_list:
        string = string.replace("\\"+e, e) 
    return string.strip('"')
    
def quoteListString(string):
    """quoteListString(string) -> List
    Like quoteString, but split the list by newlines before quoting and
    escaping it"""
    # return a string converted to a list for edm
    return [ quoteString(x) for x in string.split("\n") ]


def write_helper():
    """write_helper() -> None
    Helper function that imports every edm object available and for each object
    builds a dict of default properties. It also builds a dict of colour names
    to indexes. It then pickles these dictionaries, writing them to file. When
    EdmObject in imported again, these dictionaries are read and imported, and
    used to provide some sensible options for a default object."""
    print("Building helper object...")
    cwd = os.getcwd()
    build_dir = os.path.abspath(os.path.dirname(__file__))
    # load the environment so we can find the epics location
    epics_dir = os.path.join(os.environ["EPICS_BASE"], "..")
    edm_dir = os.path.join(epics_dir,"extensions","src","edm")
    # create the COLOUR dictionary
    COLOUR = { "White" : "index 0" }
    file = open(os.path.join(edm_dir,"setup","colors.list"),"r")
    lines = file.readlines()
    file.close()
    for line in lines:
        # read each line in colors.list into the dict
        if line.startswith("static"):
            index = line.split()[1]
            name = line[line.find('"'):line.find('"',line.find('"')+1)+1\
                        ].replace('"',"")
            COLOUR[name] = "index "+index
        elif line.startswith("rule"):
            index = line.split()[1]
            name = line.split()[2]
            COLOUR[name] = "index "+index
    cwd = os.getcwd()
    build_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(edm_dir)
    # build up a list of include dirs to pass to g++
    dirs =  ["-I"+os.path.join(edm_dir,x) for x in os.listdir(".")\
             if os.path.isdir(x) ]
    dirs += ["-I"+os.path.join(edm_dir,"util",x) \
             for x in ["sys/os/Linux","avl","thread/os/Linux"] ]
    dirs += ["-I"+os.path.join(epics_dir,"base","include") ]
    lib_path = os.path.join(epics_dir,"extensions","lib","linux-x86")
    dirs += ["-L"+lib_path ]
    os.chdir(build_dir)
    # build act_save.so, the program for creating a file of all edm objects
    line = "g++ -fPIC "+" ".join(dirs)+\
              " -shared act_save.cc -o act_save.so -Wl,-rpath="+lib_path+\
              " -L"+lib_path+" -lEdmBase"
    print(line)              
    os.system(line)              
    # run it
    os.system("env LD_PRELOAD=./act_save.so edm -crawl dummy.edl")
    file = open("allwidgets.edl","r")
    # get rid of the junk output by one widget
    screen_text = file.read().replace( \
      "# Additional properties\nbeginObjectProperties\nendObjectProperties","")
    file.close()
    os.chdir(cwd)
    # the output of the program isn't a proper screen, so make it so
    all_obs = EdmObject("Screen")
    # fix some code, then add a header
    all_obs.write(all_obs.read()+"\n"+screen_text)
    screen_properties = {}
    # write the default screen properties
    screen_properties["major"]=4
    screen_properties["minor"]=0
    screen_properties["release"]=1
    screen_properties["w"]=500
    screen_properties["h"]=600
    screen_properties["x"]=0
    screen_properties["y"]=0
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
    PROPERTIES = { "Screen": screen_properties}
    for ob in all_obs.Objects:
        # write the default properties for each object
        ob["w"]=100
        ob["h"]=100
        ob["x"]=0
        ob["y"]=0
        for key in ["font","fgColor","bgColor"]:
            if key in ob:
                ob[key] = screen_properties[key]
        if ob.Type=="Lines":
            del(ob["xPoints"])
            del(ob["yPoints"])
        for key,item in list(ob.items()):
            # remove anything that edm regards as a flag
            # this avoids 
            if item==True:
                ob[key]=False
            elif "TYP" in key.upper():
                del(ob[key])
        PROPERTIES[ob.Type] = ob.Properties.copy()
    os.chdir(build_dir)
    output = open("helper.pkl","wb")
    pickle.dump((COLOUR,PROPERTIES),output,-1)
    output.close()
    os.chdir(cwd)
    print("Done")

# code to load the stored dictionaries      
cwd = os.getcwd()
try:
    build_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(build_dir)
    file = open('helper.pkl', 'rb')
    (COLOUR,PROPERTIES) = pickle.load(file)
except IOError:
    (COLOUR,PROPERTIES) = ({},{})
os.chdir(cwd)

if __name__ == '__main__':
    write_helper()
