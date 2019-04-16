"Module containing some useful EdmObjects for building dls screens"

from .edmObject import *
__all__=['arrow', 'dummy', 'embed', 'exit_button', 'label',\
         'raised_PV_button_circle', 'raised_PV_circle', \
         'raised_button_circle', 'raised_circle', 'raised_text_button_circle',\
         'raised_text_circle', 'rd', 'rd_visible', 'rectangle', 'symbol',\
         'text_monitor', 'tooltip', 'shell', 'shell_visible', 'can_optimise']
__all__.sort()

def can_optimise(x):
    """can_optimise(x) -> Boolean
    Return True if the item can be optimised (i.e. if it is an autogen screen
    or one of the selected optimisable screens"""
    return ("camera" in x and not "2cam" in x and not "camera"==x) or "autogen"\
             in x or "slit" in x or "mirror" in x 
    
def label(x,y,w,h,text,fontAlign="left"):
    """label(x,y,w,h,text,fontAlign="left") -> EdmObject
    Return a Static Text box with position (x,y) dimensions (w,h). text is the
    display text and fontAlign is how it is aligned. Font is arial medium 10"""
    ob = EdmObject("Static Text")
    ob.setDimensions(w,h)
    ob.setPosition(x,y)
    ob["font"]=quoteString("arial-medium-r-10.0")
    ob["fgColor"]=ob.Colour["Black"]
    ob["useDisplayBg"] = True
    ob["value"] = quoteListString(text) 
    ob["fontAlign"] = quoteString(fontAlign)               
    return ob

def text_monitor(x,y,w,h,pv,showUnits=False,fontAlign="left"):
    """text_monitor(x,y,w,h,pv,showUnits=False,fontAlign="left") -> EdmObject
    Return a Text Monitor with position (x,y) dimensions (w,h). pv is the
    display pv and fontAlign is how it is aligned. Font is arial medium 10.
    If showUnits, then units from the Db are shown."""    
    ob = EdmObject("Text Monitor")
    ob.setDimensions(w,h)
    ob.setPosition(x,y)
    ob["controlPv"]=quoteString(pv)
    ob["font"] = quoteString("arial-medium-r-10.0")
    ob["fgColor"] = ob.Colour["Black"]
    ob["useDisplayBg"] = True
    ob["precision"] = 3
    ob["fontAlign"] = quoteString(fontAlign)    
    ob["smartRefresh"] = True
    ob["fastUpdate"] = True
    ob["showUnits"] = showUnits
    ob["limitsFromDb"] = False
    ob["newPos"] = True
    return ob

def dummy(x,y,w,h):
    """dummy(x,y,w,h) -> EdmObject
    Return a dummy invisible rectangle with position (x,y) dimensions (w,h)"""
    ob = EdmObject("Rectangle")
    ob.setDimensions(w,h)
    ob.setPosition(x,y)
    ob["lineColor"] = ob.Colour["Canvas"]
    ob["invisible"] = True
    return ob

def rectangle(x,y,w,h,lineColour="Black",fillColour="Controller"):
    """rectangle(x,y,w,h,lineColour="Black",fillColour="Controller")\
            -> EdmObject
    Return a filled rectangle with position (x,y) dimensions (w,h). fillColour
    and lineColour are looked up in ob.Colour"""
    ob = EdmObject("Rectangle")
    ob.setDimensions(w,h)
    ob.setPosition(x,y)
    ob["lineColor"] = ob.Colour[lineColour]
    ob["fill"] = True
    ob["fillColor"] = ob.Colour[fillColour]
    return ob

def tooltip(x,y,w,h,text):
    """tooltip(x,y,w,h,text) -> EdmObject
    Return an invisible related display with position (x,y) dimensions (w,h).
    When right clicked, it displays a tooltip with the given text."""    
    ob = EdmObject("Related Display")
    ob.setDimensions(w,h)
    ob.setPosition(x,y)
    ob["yPosOffset"] = max(h,22)+8
    ob["xPosOffset"] = w/2-100
    ob["button3Popup"] = True
    ob["invisible"] = True
    ob["buttonLabel"] = quoteString("tooltip")
    ob["numPvs"] = 4
    ob["numDsps"] = 1
    ob["displayFileName"] = { 0: quoteString("symbols-tooltip-symbol") }
    ob["setPosition"] = { 0: quoteString("button") }
    ob["symbols"] = { 0: quoteString("text="+text) }
    return ob

def rd(x,y,w,h,filename,symbols):
    """rd(x,y,w,h,filename,symbols) -> EdmObject
    Return an invisible related display with position (x,y) dimensions (w,h).
    filename and symbols as defined."""  
    ob = EdmObject("Related Display")
    ob.setDimensions(w,h)
    ob.setPosition(x,y)
    ob["invisible"] = True
    ob["buttonLabel"] = quoteString("device screen")
    ob["numPvs"] = 4
    if filename:
       ob["displayFileName"] = { 0: quoteString(filename) }
       ob["numDsps"] = 1       
       if symbols:
          ob["symbols"] = { 0: quoteString(symbols) }
    else:
       ob["numDsps"] = 0      
    return ob

def shell(x,y,w,h,command):
    """shell(x,y,w,h,filename,symbols) -> EdmObject
    Return an invisible shell command button with position (x,y) dimensions
    (w,h) and command as defined."""  
    ob = EdmObject("Shell Command")
    ob.setDimensions(w,h)
    ob.setPosition(x,y)
    ob["invisible"] = True
    ob["buttonLabel"] = quoteString("Shell Command")
    ob["numCmds"] = 1
    ob["command"] = { 0: quoteString(command) }
    return ob

def shell_visible(x,y,w,h,name,command):
    """shell(x,y,w,h,filename,symbols) -> EdmObject
    Return an invisible shell command button with position (x,y) dimensions
    (w,h) and command as defined."""  
    ob = EdmObject("Shell Command")
    ob.setDimensions(w,h)
    ob.setPosition(x,y)
    ob["buttonLabel"] = quoteString(name)
    ob["numCmds"] = 1
    ob["command"] = { 0: quoteString(command) }
    ob["fgColor"] = ob.Colour["Related display"]
    ob["bgColor"] = ob.Colour["Canvas"]
    ob["font"] = quoteString("arial-bold-r-14.0") 
    ob.setShadows()
    return ob

def rd_visible(x,y,w,h,text,filename,symbols=None):
    """rd_visible(x,y,w,h,text,filename,symbols=None) -> EdmObject
    Return a visible related display button with position (x,y) dimensions (w,h)
    text is the button label and filename and symbols are as defined."""  
    ob = EdmObject("Related Display")
    ob.setDimensions(w,h)
    ob.setPosition(x,y)
    ob["buttonLabel"] = quoteString(text)
    ob["numPvs"] = 4
    ob["numDsps"] = 1
    ob["displayFileName"] = { 0: quoteString(filename) }
    if symbols:
        ob["symbols"] = { 0: quoteString(symbols) }
    ob["fgColor"] = ob.Colour["Related display"]
    ob["bgColor"] = ob.Colour["Canvas"]
    ob["font"] = quoteString("arial-bold-r-14.0") 
    ob.setShadows()       
    return ob

def symbol(x,y,w,h,filename,pv,nstates,truth=False):
    """symbol(x,y,w,h,filename,pv,nstates,truth=False) -> EdmObject
    Return a symbol with position (x,y) dimensions (w,h). for i in nstates:
    connect values i-1 to i to symbol state i. If truth, treat it as a truth
    table."""
    ob = EdmObject("Symbol")
    ob.setDimensions(w,h)
    ob.setPosition(x,y)
    ob["file"] = quoteString(filename)
    ob["truthTable"] = truth
    ob["numStates"] = nstates
    mindict,maxdict = {},{}
    for i in range(1,nstates):
        if i>1:
            mindict[i] = i-1
        maxdict[i]=i
    ob["minValues"] = mindict
    ob["maxValues"] = maxdict
    ob["controlPvs"] = { 0: quoteString(pv) }
    ob["numPvs"] = 1
    ob["useOriginalColors"] = True
    return ob

def raised_circle(x,y,w,h,ta="CO"):
    """raised_circle(x,y,w,h,ta="CO") -> EdmObject
    Return a 3d look circle with position (x,y) dimensions (w,h). ta gives
    the colour, ie CO, MO, DI, VA, etc."""
    group = EdmObject("Group")
    top_shadow = EdmObject("Circle")
    top_shadow.setDimensions(w-2,h-1)
    top_shadow.setPosition(x,y)
    top_shadow["lineColor"]=top_shadow.Colour["Top Shadow"]
    top_shadow["lineWidth"]=2
    group.addObject(top_shadow)
    bottom_shadow = EdmObject("Circle")
    bottom_shadow.setDimensions(w-2,h-1)
    bottom_shadow.setPosition(x+2,y+2)
    bottom_shadow["lineColor"]=bottom_shadow.Colour["Bottom Shadow"]
    bottom_shadow["lineWidth"]=2
    group.addObject(bottom_shadow)
    base = EdmObject("Circle")
    base.setDimensions(w-3,h-3)
    base.setPosition(x+2,y+2)
    base["lineColor"]=base.Colour[ta+" help"]
    base["fillColor"]=base.Colour[ta+" title"]
    base["lineWidth"]=3
    base["fill"]=True
    group.addObject(base)
    sparkle = EdmObject("Circle")
    sparkle.setDimensions(4,3)
    sparkle.setPosition(x+12,y+6)
    sparkle["lineColor"]=sparkle.Colour["Top Shadow"]
    sparkle["fillColor"]=sparkle.Colour["White"]
    sparkle["lineWidth"]=2
    sparkle["fill"]=True
    group.addObject(sparkle)
    group.setPosition(x,y,move_objects=False)
    group.setDimensions(w,h,resize_objects=False)
    return group

def raised_text_circle(x,y,w,h,text,font="arial-bold-r-14.0",\
                       fontAlign="center",ta="CO"):
    """raised_text_circle(x,y,w,h,text,font="arial-bold-r-14.0",\
                          fontAlign="center",ta="CO") -> EdmObject
    Return a 3d look circle with a text label text, position (x,y) dimensions
    (w,h), font and fontAlign. ta gives the colour, ie CO, MO, DI, VA, etc."""
    group = raised_circle(x,y,w,h,ta)
    text_label = label(x,y,w,h,text)
    text_label["fontAlign"]=quoteString(fontAlign)
    text_label["font"]=quoteString(font)
    group.addObject(text_label)
    return group

def raised_button_circle(x,y,w,h,filename,symbols,ta="CO"):
    """raised_button_circle(x,y,w,h,filename,symbols,ta="CO") -> EdmObject
    Return a 3d look circular button with position (x,y) dimensions (w,h)
    filename and symbols. ta gives the colour, ie CO, MO, DI, VA, etc."""
    group = raised_circle(x,y,w,h,ta)
    RD = rd(4,4,42,24,filename,symbols)
    group.addObject(RD)
    RD.lowerObject()
    return group

def raised_text_button_circle(x,y,w,h,text,filename,symbols,\
                          font="arial-bold-r-14.0",fontAlign="center",ta="CO"):
    """raised_text_button_circle(x,y,w,h,text,filename,symbols,\
              font="arial-bold-r-14.0",fontAlign="center",ta="CO") -> EdmObject
    Return a 3d look circular button with a text label text, position (x,y)
    dimensions (w,h) filename and symbols. ta gives the colour, ie CO, MO, DI,
    VA, etc."""
    group = raised_button_circle(x,y,w,h,filename,symbols,ta)
    text_label = label(x,y,w,h,text)
    text_label["fontAlign"]=quoteString(fontAlign)
    text_label["font"]=quoteString(font)
    group.addObject(text_label)
    return group

def raised_PV_circle(x,y,w,h,pv,ta="CO"):
    """raised_PV_circle(x,y,w,h,pv,ta="CO") -> EdmObject
    Return a 3d look circle with a PV monitor pv, position (x,y) dimensions
    (w,h). ta gives the colour, ie CO, MO, DI, VA, etc."""
    group = raised_circle(x,y,w,h,ta)
    PV = text_monitor(x,y,w,h,pv)
    PV["font"]=quoteString("arial-bold-r-14.0")
    PV["fontAlign"]=quoteString("center")
    group.addObject(PV)
    return group    

def raised_PV_button_circle(x,y,w,h,pv,filename="generic-help",\
                        symbols="draw=$(P).png",ta="CO"):
    """raised_PV_button_circle(x,y,w,h,pv,filename="generic-help",\
                        symbols="draw=$(P).png",ta="CO") -> EdmObject
    Return a 3d look circular button with a a PV monitor pv, position (x,y)
    dimensions (w,h) filename and symbols. ta gives the colour, ie CO, MO, DI,
    VA, etc."""
    group = raised_PV_circle(x,y,w,h,pv,ta)
    RD = rd(x+4,y+4,w-8,h-6,filename,symbols)
    group.addObject(RD)
    RD.lowerObject()
    return group

def raised_PV_shell_circle(x,y,w,h,pv,\
             command="firefox $(autogen)/documentation/$(P)-help.html",ta="CO"):
    """raised_PV_button_circle(x,y,w,h,pv,filename="generic-help",\
                        symbols="draw=$(P).png",ta="CO") -> EdmObject
    Return a 3d look circular button with a a PV monitor pv, position (x,y)
    dimensions (w,h) filename and symbols. ta gives the colour, ie CO, MO, DI,
    VA, etc."""
    group = raised_PV_circle(x,y,w,h,pv,ta)
    RD = shell(x+4,y+4,w-8,h-6,command)
    group.addObject(RD)
    RD.lowerObject()
    return group

def embed(x,y,w,h,filename,symbols=None):
    """embed(x,y,w,h,filename,symbols=None) -> EdmObject
    Return an embedded window with position (x,y) dimensions (w,h) filename
    and symbols."""
    ob = EdmObject("Embedded Window")
    ob.setPosition(x,y)
    ob.setDimensions(w,h)
    ob["displaySource"]=quoteString("menu")
    ob["filePv"]=quoteString(r"LOC\dummy=i:0")
    ob["numDsps"]=1
    ob["displayFileName"]= { 0: quoteString(filename) }
    if symbols:
        ob["symbols"]= { 0: quoteString(symbols) }
    ob["noScroll"]= True                
    return ob

def exit_button(x,y,w,h):
    """exit_button(x,y,w,h) -> EdmObject
    Return an exit button with position (x,y) dimensions (w,h)."""
    button = EdmObject("Exit Button")
    button.setPosition(x,y)
    button.setDimensions(w,h)
    button["fgColor"] = button.Colour["Exit/Quit/Kill"]
    button["bgColor"] = button.Colour["Canvas"]
    button.setShadows()
    button["label"] = quoteString("EXIT")
    button["font"] = quoteString("arial-medium-r-16.0")
    button["3d"] = True
    return button

def lines(points,col="Black"):
    ob = EdmObject("Lines")
    ob["lineColor"] = ob.Colour[col]
    ob["numPoints"] = len(points)
    ob["xPoints"] = dict((i,x) for i,(x,y) in enumerate(points) )
    ob["yPoints"] = dict((i,y) for i,(x,y) in enumerate(points) )    
    ob.autofitDimensions()
    return ob    

def arrow(x0,x1,y0,y1,col="Black"):
    """arrow(x0,x1,y0,y1,col="Black") -> EdmObject
    Return an arrow from (x0,y0) to (x1,y1) with colour col."""
    ob = lines([(x0,y0),(x1,y1)],col)
    ob["arrows"] = quoteString("to")
    return ob

def component_symbol(x,y,w,h,StatusPv,SevrPv,filename):
    if not SevrPv.startswith("LOC") and not SevrPv.startswith("CALC"):
        SevrPv = SevrPv.split(".")[0]+".SEVR"    
    ob = EdmObject("Symbol")
    ob.setDimensions(w,h)
    ob.setPosition(x,y)
    ob["file"] = quoteString(filename)
    ob["numStates"] = 5
    ob["minValues"] = {0:6, 1:0, 2:2, 3:4, 4:1}
    ob["maxValues"] = {0:8, 1:1, 2:4, 3:6, 4:2}
    ob["controlPvs"] = {0: quoteString(StatusPv), 1: quoteString(SevrPv)}
    ob["numPvs"] = 2
    ob["shiftCount"] = {1:1}
    ob["useOriginalColors"] = True
    return ob    

def colour_changing_rd(x,y,w,h,name,StatusPv,SevrPv,filename,symbols="",edl=True):
    """Return a symbol with an invisible rd behind it that changes col based on
    sta and sevr pvs"""
    obgroup = EdmObject("Group")
    if edl:
        obgroup.addObject(rd_visible(x,y,w,h,"",filename,symbols))
    else:    
        obgroup.addObject(shell_visible(x,y,w,h,"",filename))        
    obtext = label(x+2,y+2,w-4,h-4,name,fontAlign="center")
    obtext["font"] = quoteString("arial-bold-r-14.0")
    obtext["fgColor"] = obtext.Colour["Related display"]    
    obtext["bgAlarm"] = True
    obtext["alarmPv"] = quoteString(SevrPv)
    obtext["visPv"] = quoteString(StatusPv)
    obtext["visMin"] = quoteString("1")
    obtext["visMax"] = quoteString("2")            
    obtext["useDisplayBg"] = False
    obtext2 = obtext.copy()  
    obtext["visInvert"] = True   
    obtext2["bgColor"] = obtext.Colour["Monitor: NORMAL"]    
    obgroup.addObject(obtext)   
    obgroup.addObject(obtext2)
    obgroup.autofitDimensions()
    return obgroup


def flip_axis(direction):
    # create a set of axis for a beam going left or right
    group = EdmObject("Group")
    if direction=="left":
        zlab=label(50,50,10,20,"Z","center")
        zlab["font"]=quoteString("arial-bold-r-14.0")
        group.addObject(zlab)
        z=arrow(5,45,60,60,"grey-13")
        group.addObject(z)
        y=arrow(5,5,60,20,"grey-13")
        group.addObject(y)  
        ylab=label(0,0,10,16,"Y","center")
        ylab["font"]=quoteString("arial-bold-r-14.0")
        group.addObject(ylab)
        xlab=label(40,20,77,32,"X (into \n    screen)","center")
        xlab["font"]=quoteString("arial-bold-r-14.0")
        group.addObject(xlab)
        x=arrow(5,35,60,45,"Black")
        group.addObject(x)
    else:
        zlab=label(5,25,10,15,"Z","center")
        zlab["font"]=quoteString("arial-bold-r-14.0")
        group.addObject(zlab)
        z=arrow(40,0,45,45,"Black")
        group.addObject(z)
        y=arrow(40,40,45,5,"Black")
        group.addObject(y)  
        ylab=label(15,0,20,20,"Y","center")
        ylab["font"]=quoteString("arial-bold-r-14.0")
        group.addObject(ylab)
        xlab=label(50,30,69,32,"X (out of  \n   screen)","center")
        xlab["font"]=quoteString("arial-bold-r-14.0")
        group.addObject(xlab)
        x=arrow(40,70,45,65,"grey-13")
        group.addObject(x)
    group.autofitDimensions()
    return group    
