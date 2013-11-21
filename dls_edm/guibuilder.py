from optparse import OptionParser
from xml.dom import minidom
from copy import copy
import sys, re, os
from substitute_embed import Substitute_embed
from generic import Generic
from edmObject import EdmObject, quoteString
from edmTable import EdmTable
from flip_horizontal import Flip_horizontal
from titlebar import Titlebar
from common import embed, rd_visible, label, colour_changing_rd, lines
from math import sqrt

class GBObject(object):
    def __init__(self, name, macrodict = None, children = None):
        self.name = name
        if macrodict:
            self.macrodict = macrodict.copy()
        else:
            self.macrodict = {}            
        self.macrodict["NAME"] = self.name
        self.macrodict["FILE"] = ""
        self.macrodict["EDM_MACROS"] = ""
        if children:
            self.children = children
        else:
            self.children = {}                    
        self.screens, self.shells, self.records = ([], [], [])

    def addScreen(self, filename, macros = "", embedded = False, tab = False):
        macros = macros.replace(",undefined)", ")").rstrip("\r")    
        mdict = {}
        # make sure edm gets '' for empty macros
        for k,v in [x.split("=") for x in macros.split(",") if x]:
            if not v.strip(): 
                v = "''"
            mdict[k.strip()] = v.strip()     
        macros = ','.join(["%s=%s" %x for x in mdict.items()])            
        self.screens.append(GBScreen(filename, macros, embedded, tab))  
        if embedded == False and tab == False:
            for k,v in [x.split("=") for x in macros.split(",") if x]:
                self.macrodict[k.strip()] = v.strip()        
            self.macrodict["NAME"] = self.name
            self.macrodict["FILE"] = os.path.basename(filename)
            self.macrodict["EDM_MACROS"] = macros    
                                    
    def addShell(self, command):
        self.shells.append(GBShell(command))                                           
        
    def addRecord(self, pv, sevr = False):
        self.records.append(GBRecord(pv, sevr))
    
class GBScreen(object):    
    def __init__(self, filename, macros, embedded, tab):
        self.__dict__.update(locals())
        
class GBShell(object):
    def __init__(self, command):
        self.__dict__.update(locals())

class GBRecord(object):
    def __init__(self, pv, sevr):
        self.__dict__.update(locals())      

SILENT = 0
WARN = 1
ERROR = 2

class GuiBuilder:
    def __init__(self, dom = "", errors = ERROR):
        # setup our list of objects
        self.objects = []    
        self.dom = dom
        self.errors = errors        
        # initialise paths
        self.paths = []      
        self.devpaths = []
        self.RELEASE = None
        # initialise record text
        self.dbtext = ""        
        
    def parseArgs(self):        
        # first parse the args
        parser = OptionParser("%prog [options] <BLxxI-gui.xml> <RELEASE>\n" \
            "Builds gui files by parsing xml file")
        parser.add_option("--db", dest="db", default="",
                  help='Write status records to this db file')
        (options, args) = parser.parse_args()
        if len(args) != 2:
            parser.error("Invalid number of arguments, run with -h to see usage")            
        # store options
        self.db = options.db
        self.parseRelease(os.path.abspath(args[1]))
        self.parseXml(args[0])
        
    def parseRelease(self, RELEASE):
        # now parse the tree
        from dls_dependency_tree import dependency_tree        
        self.RELEASE = RELEASE
        tree = dependency_tree(None, self.RELEASE)
        if "BLGui" not in [x.name for x in tree.leaves]:
            prefix = os.path.join(tree.e.prodArea(), "BLGui")
            p = os.path.join(prefix, tree.e.sortReleases(os.listdir(prefix))[-1])
            tree.leaves.append(dependency_tree(tree, module_path = p))
        self.paths = tree.paths()            
        self.devpaths = tree.paths(["/*App/op*/edl","/*App/op*/symbol"])    
        
    def parseXml(self, xml):
        self.xml = xml               
        # open the xml file
        xml_root = minidom.parse(self.xml)        
        # find the root node
        c_node = self._elements(xml_root)[0]
        # populate them from our elements        
        for node in self._elements(c_node):
            name = str(node.nodeName)
            gob = self.object(name)
            # for each object name, populate screens shells and records
            for ob in self._elements(node):
                typ = str(ob.nodeName)
                if typ in ["edm", "edmembed", "edmtab"]:                
                    args = dict()                
                    if typ == "edmembed":
                        args["embedded"] = True
                    elif typ == "edmtab":
                        args["tab"] = True                        
                    # now make a GBScreen out of it                    
                    for k,v in ob.attributes.items():
                        args[str(k)] = str(v)
                    gob.addScreen(**args)
                elif typ in ["shell"]:
                    # now make a GBShell out of it
                    gob.addShell(str(ob.getAttribute("command")))
                elif typ in ["sevr", "status"]:
                    if typ == "sevr":
                        sevr = True
                    else:
                        sevr = False
                    # now make a GBRecord out of it
                    gob.addRecord(str(ob.getAttribute("pv")), sevr)
                else:
                    raise TypeError, "%s is not a valid element type" % typ                     

    def _elements(self, xml):
        return [n for n in xml.childNodes if n.nodeType == n.ELEMENT_NODE]        

    def get(self, name, glob = True, without = None):
        '''Gets all GBObjects with names matching name. If glob then do simple 
        wildcard * expansion, otherwise do regex expansion'''   
        orig_name = name 
        if glob:
            name = name.replace(".", r"\.").replace("*", r"[^\.]*")
        # filter the list of available objects
        if without == None:
            without = []
        ret = [o for o in self.objects if re.match(name, o.name) and re.match(name, o.name).end() == len(o.name) and o.name not in without]
        return ret

    def error(self, text):
        if self.errors == ERROR:
            raise AssertionError, text
        elif self.errors == WARN:
            print >> sys.stderr, "***Warning: " + text
    
    def object(self, name, desc="", P="", obs = [], filename = None, macrodict = None, 
            preferEmbed = True, preferTab = True, substituteEmbed = True, ar = None, d = ".", max_y = None):
        '''Associate a group of objects with a name, prefix and filename. 
        If filename is None then an autogenerated screen will be produced.
        Status records will be produced if writeRecords is called.
        This information  will also be used to autofill icons if autofilled is 
        called on an overview screen.'''    
        # first make an object to fill in  
        if macrodict is None:
            macrodict = {}  
        macrodict["NAME"] = name
        macrodict["DESCRIPTION"] = desc   
        if P:
            macrodict["P"] = P             
        ob = GBObject(name, macrodict, obs)
        self.objects.append(ob)

        # if we are given a P, this means we should write records for it
        if P:
            self.__writeRecord(ob, obs)
            
        # if we are not given a filename, we should make a screen for it
        macros = ",".join("%s=%s" % x for x in macrodict.items())
        if filename is None and obs:
            filename = d + "/" + name + ".edl"
            if self.errors:
                print "Creating screen for %s" % name
            screenobs = self.__screenObs(name, obs, preferEmbed, preferTab)
            if screenobs:
                # only one display which is not embedded, so just add launch this screen
                if len(screenobs) == 1 and screenobs[0].Type == "Group" and screenobs[0].Objects[0].Type == "Related Display":
                    filename = screenobs[0].Objects[0]["displayFileName"][0].strip('"')       
                    if "symbols" in screenobs[0].Objects[0].keys():             
                        macros = screenobs[0].Objects[0]["symbols"][0].strip('"')
                    else:
                        macros = ""
                else:
                    screen = Generic(screenobs, auto_x_y_string=P, ideal_a_r=ar, max_y=max_y)
                    macros = ""
                    screen = Titlebar(screen, button_text = name,
                        header_text = desc, title = "Device - %s" % name)
                    if substituteEmbed:
                        Substitute_embed(screen,[],{},ungroup=True)
                    open(filename, "w").write(screen.read())
            else:
                filename = None    
                
        # if there is a filename of some kind then add a screen to the object                
        if filename:       
            ob.addScreen(filename, macros)
        return ob
    
    def __screenObs(self, name, obs, preferEmbed = True, preferTab = True):
        zero = r"LOC\dummy0=i:0"    
        # create the actual screen obs
        out = []
        tabobs = []
        for ob in obs:
            # First calculate the status and severity Pvs
            StatusPv = [r.pv for r in ob.records if not r.sevr]       
            SevrPv = [r.pv for r in ob.records if r.sevr]
            # now create a combined pv            
            args = dict()
            for attr in ["StatusPv","SevrPv"]:
                pvs = locals()[attr]
                # now work out the combined pvs
                if len(pvs) == 0:
                    pv = zero
                elif len(pvs) == 1:
                    pv = pvs[0]
                else:
                    letters = "|".join(chr(65+j) for j in range(len(pvs)))
                    if attr == "StatusPv":
                        pv = r"CALC\{(%s)>0?1:0}(%s)" % (letters, ",".join(pvs))
                    else:
                        pv = r"CALC\{%s}(%s.SEVR)" % (letters, ".SEVR,".join(pvs))                        
                args[attr] = pv
            # now work out a reasonable label            
            label = ob.name.replace(name + ".", "").replace(name.split(".")[0] + ".", "")
            # now create rds for shells
            for shell in ob.shells:
                out.append(colour_changing_rd(0, 0, 90, 20, name = label, 
                    edl = False, filename = shell.command, symbols = "", \
                    **args))
            # filter the screens for embedded and related displays
            embeds = [s for s in ob.screens if s.embedded]
            tabs = [s for s in ob.screens if s.tab]
            rds = [s for s in ob.screens if not s.embedded and not s.tab]                                                
            # if preferEmbed then filter out rds
            if preferTab and len(tabs) > 0:
                rds = []
                embeds = []
            elif preferEmbed and len(embeds) > 0:
                rds = []                              
                tabs = []
            elif len(rds) > 0:
                embeds = []
                tabs = []
            # now add the rds          
            for rd in rds:
                out.append(colour_changing_rd(0, 0, 90, 20, name = label, 
                    edl = True, filename = os.path.basename(rd.filename), symbols = rd.macros, 
                    **args))
            # then embedded screens             
            for e in embeds:
                filename = e.filename
                self.__load_screen(filename)
                eob = embed(0,0,0,0,os.path.basename(filename),",".join([e.macros, "label="+label]))
                eob.setDimensions(\
                    *Substitute_embed.in_screens[filename].getDimensions())                
                out.append(eob)
            # finally create tab widgets
            for e in tabs:
                filename = e.filename
                self.__load_screen(filename)             
                w, h = Substitute_embed.in_screens[filename].getDimensions()
                tabobs.append((label, os.path.basename(filename), e.macros, w, h))
        if tabobs:
            grp = EdmObject("Group")
            buttons = EdmObject("Choice Button")
            maxw = max([x[3] for x in tabobs])
            maxh = max([x[4] for x in tabobs])  
            labs = ",".join(["0"] + [x[0] for x in tabobs])
            pv = r"LOC\$(!W)tab"
            buttons["controlPv"] = quoteString("%s=e:%s" % (pv, labs))
            buttons.setPosition(4,3)            
            buttons.setDimensions(maxw + 1,25)
            buttons["orientation"] = quoteString("horizontal")
            buttons["font"] = quoteString("arial-bold-r-12.0")
            buttons.setShadows()            
            buttons["selectColor"] = buttons.Colour["Button: On"]
            grp.addObject(buttons)
            grp.addObject(lines([(4,maxh+30), (maxw+6,maxh+30), (maxw+6, 29)], "Top Shadow"))
            grp.addObject(lines([(4,maxh+30), (4,29), (maxw+6, 29)], "Bottom Shadow"))            
            filename, label, macros, w, h = tabobs[0]
            eob = EdmObject("Embedded Window")
            eob.setPosition(5,29)
            eob.setDimensions(maxw,maxh)
            eob["filePv"]=quoteString(pv)
            eob["noScroll"]= True     
            eob["numDsps"] = len(tabobs)
            eob["displaySource"] = quoteString("menu")
            eob["displayFileName"] = dict((i,quoteString(x[1])) for (i,x) in enumerate(tabobs))
            eob["symbols"] = dict((i,quoteString(",".join([x[2], "label="+x[0]]))) for (i,x) in enumerate(tabobs))  
            grp.addObject(eob)
            grp.setDimensions(maxw+10,maxh+30,resize_objects=False)
            out.append(grp)    
        return out
    
    def __load_screen(self, filename):
        if filename not in Substitute_embed.in_screens:
            paths = [ os.path.join(p,filename) for p in self.paths \
                        if os.path.isfile(os.path.join(p,filename)) ]          
            assert paths, "Cannot find file %s in paths %s" % \
                (filename, self.paths)
            screen = EdmObject("Screen")
            screen.write(open(paths[0],"r").read())                
            Substitute_embed.in_screens[filename] = screen.copy()                   
               
    def __safe_filename(self, filename):
        return filename.replace(" ", "-")        
    
    def __filter_screens(self, filename, obs, destFilename = None, \
            embedded = None):
        # return a list of objects with screens filtered and modified for
        # summary screen generation
        objects = []
        for ob in obs:
            newscreens = []
            for s in ob.screens:
                if s.filename == filename:
                    s = copy(s)
                    if destFilename is not None:
                        s.filename = destFilename
                    if embedded is not None:
                        s.embedded = embedded
                    else:
                        embedded = s.embedded
                    newscreens.append(s)
            if newscreens:
                ob = copy(ob)
                ob.screens = newscreens
                objects.append(ob)
        return objects, embedded
                            
    def summary(self, typ, srcFilename, destFilename = None, 
            embedded = None, group = True, groupByName = False, ar = 1.5):
        '''Take a GBScreen object srcOb, find all like it, and display them all
        in a summary screen. If obFilename then use obFilename instead. If 
        embedded then use embedded instead'''
        # this is the filename of the generated screen
        filename = self.__safe_filename(self.dom + "-" + typ.lower() + ".edl")
        if self.errors:        
            print "Creating %s" % filename
        # this is the filename for each object put on screens
        if destFilename is None:
            destFilename = srcFilename
        # this is the screen we will return
        screen = EdmObject("Screen")
        table = EdmTable(yborder=5)
        screen.addObject(table)
        headerText = "%s Summary" % typ   
        # objects is a list of list of screen objects to add
        screen_objects = []
        if group:
            if groupByName:
                # make a tree heirarachy according to . in names
                groupObjects = []
                for o in self.objects:
                    if len(o.name.split(".", 1)) == 1:
                        groupObjects.append(copy(o))
                        groupObjects[-1].children = []
                for o in self.objects:
                    if len(o.name.split(".", 1)) == 2:
                        parent = [x for x in groupObjects if x.name == o.name.split(".", 1)[0]]
                        if parent:
                            parent[0].children.append(o)
            else:
                groupObjects = self.objects        
            # group by parent object
            for o in groupObjects:
                # if no child objects then don't need to do anything
                if not o.children:
                    continue
                # first make a new object list
                objects, embedded = self.__filter_screens(srcFilename, o.children, \
                    destFilename, embedded)
                # now make the list of screen objects out of it
                if objects:
                    sobs = self.__screenObs(o.name, objects, embedded)
                    buttons = self.__screenObs("", [o], preferEmbed = False, preferTab = False)
                    if buttons:
                        # if there is a screen for this already, add a button for it                    
                        title_button = buttons[0]
                        title_button.setDimensions(sobs[-1]["w"], 20)                        
                    else:
                        # otherwise just make a label
                        title_button = label(0,0,sobs[-1]["w"],20,o.name)
                    screen_objects.append([title_button] + sobs)
        else:
            objects, embedded = self.__filter_screens(srcFilename, self.objects, \
                destFilename, embedded)
            if objects:
                screen_objects.append(self.__screenObs("", objects, embedded))          
        if screen_objects:              
            w,h = screen_objects[0][-1].getDimensions()          
            numobs = sum([len(o) for o in screen_objects])
            nrows = int(sqrt(numobs*w/(ar*h))+1)                                    
            for oblist in screen_objects:
                # if entire component doesn't fit in column, create a new one
                if len(oblist) + table["__def_y"] > nrows:
                    table.nextCol()
                for ob in oblist:
                    table.addObject(ob)
                    table.nextCell(max_y=nrows)
            screen.autofitDimensions()
            table.ungroup()
            Titlebar(screen, button = "text", 
                     button_text = self.dom, header = "text", 
                     header_text = headerText, tooltip = "generic-tooltip",
                     title = headerText)
            Substitute_embed(screen,[],{})  
        open(filename, "w").write(screen.read())  

    def __concat(self, l):
        return [x for y in l for x in y]

    def motorHomedSummary(self):
        '''Create a motor homed summary <dom>-motor-homed.edl'''
        self.summary("Motor Homed", "motor.edl", "motor-embed-homed.edl", \
                embedded = True, groupByName = True)

    def interlockSummary(self):
        '''Create an interlock summary <dom>-interlocks.edl'''
        self.summary("Interlocks", "interlock-embed-small.edl", group = False, embedded = True)        

    def temperatureSummary(self):
        '''Create an interlock summary <dom>-interlocks.edl'''
        self.summary("Temperatures", "temperature-embed.edl", embedded = True)        

    def flowSummary(self):
        '''Create an interlock summary <dom>-interlocks.edl'''
        self.summary("Water Flows", "flow-embed.edl", embedded = True)        

    def autofilled(self, screen):
        '''Return a filled version of screen. Any top level group will have tags
        replaced as following:
            visPv tag: #<A=1>##<S1>#
        This means that all instances of #<A># will be replaced by 1 in the
        group, and the component S1 will be used to find values of #<P>#, 
        #<NAME>#, #<DESCRIPTION>#, #<EDM_MACROS># and #<FILE># as defined by
        the relevant call to GuiBuilder.component()'''
        # first open the screen if we've been given a filename
        if type(screen) == str:
            filename = screen
            screen = EdmObject("Screen")
            screen.write(open(filename).read())
        # now autofill all groups in the screens
        groups = [ ob for ob in screen.Objects if ob.Type=="Group" ]
        for group in groups:
            # the vis PV is checked for tags
            if group.has_key("visPv"):
                visPv = group["visPv"].strip('"')
            else:
                visPv=""
            if visPv.startswith('#<'):
                # we need to do something with the group
                args = visPv.replace("#<","").split(">#")[:-1]
                assignment_args = [ a for a in args if "=" in a ]
                device_args = [ a for a in args if not "=" in a ]
                if len(device_args) > 1:
                    self.error("Looks like you're trying to autofill from " \
                    "two components in this visPv: '%s'" % visPv)
                for arg in assignment_args:
                    # if there is an = in the tag, split it into a list and
                    # replace tags from this list instead
                    group.substitute("#<"+arg.split("=")[0].strip()+">#",\
                                        arg.split("=")[1].strip())
                    group["visPv"] = group["visPv"].replace("#<"+arg+">#", "")
                if device_args:
                    # if there is a component tag, use it to get P, NAME, etc..
                    device_name = device_args[0]
                    if device_name in ["AXIS_LEFT","AXIS_RIGHT"]:
                        # These are axes, only tagged for flipping
                        continue
                    # if we have a component then all is fine
                    dicts = [x.macrodict for x in self.objects \
                        if x.name == device_name]
                    if len(dicts) == 0:                    
                        # and it's not an axis group (this isn't a real tag)
                        if device_name not in ["AXIS_LEFT","AXIS_RIGHT"]:
                            self.error("Cannot find component %s. Group has " \
                                "not been autofilled." % device_name)
                        continue
                    for key, val in dicts[0].items():
                        group.substitute("#<"+key+">#",val)
                    group["visPv"] = group["visPv"].replace( \
                        "#<"+device_name+">#", "")
        return screen          
        
    def flipped(self, screen):
        '''Returns a flipped version of screen'''
        if type(screen) == str:
            filename = screen
            screen = EdmObject("Screen")
            screen.write(open(filename).read())
        return Flip_horizontal(screen, self.paths)

    def writeScreen(self, screen, filename):
        '''Writes screen object screen to filename'''
        filename = self.__safe_filename(filename)
        open(filename, "w").write(screen.read())        

    def __writeCalc(self, name, **args):
        '''Write a calc record'''
        self.dbtext += 'record(calc, "%s")\n' % name
        self.dbtext += '{\n'
        for k, v in sorted(args.items()):
            self.dbtext += '    field(%s, "%s")\n' % (k, v)
        self.dbtext += '}\n\n'

    def __writeRecord(self, ob, obs):
        records = self.__concat(o.records for o in obs)
        recordName = ob.macrodict["P"] + ":DEVSTA"             
        if len(records) == 0:
            self.__writeCalc(recordName,CALC=0,PINI="YES")
            return
        # first make a set of all severities and stats
        sevrs = [r.pv.split(".")[0] for r in records if r.sevr]
        stats = [r.pv for r in records if not r.sevr]
        stripped_stats = [pv.split(".")[0] for pv in stats]
        # now create inputs
        # inps = (pv,inCalc)
        inps  = [(pv+" NMS",True) \
            for pv in stats if pv.split(".")[0] not in sevrs ]
        inps += [(pv+" MS",True) \
            for pv in stats if pv.split(".")[0] in sevrs ]
        inps += [(pv+".SEVR MS",False) \
            for pv in sevrs if pv not in stripped_stats ]
        inps = sorted(set(inps))
        # now work out how many calcs we need
        ncalcs = max((len(inps)+11)/12,1)      
        # if we need more than one, then sum them
        if ncalcs>1:
            letters = [chr(65+j) for j in range(ncalcs)]      
            CALC = "(%s)>0?1:0"%("|".join(letters))  
            cargs = dict(("INP%s"%l,"%s%s MS"%(recordName,j+1)) \
                for j,l in enumerate(letters))            
            self.__writeCalc(recordName,SCAN="1 second",CALC=CALC,PHAS=3,ACKT="NO",**cargs)  
        # create the calc records          
        for i in range(ncalcs):
            subset = inps[12*i:12*i+12]
            letters = [chr(65+j) for j,(pv,inCalc) \
                in enumerate(subset) if inCalc]
            if letters:                
                CALC = "(%s)>0?1:0"%("|".join(letters))
            else:
                CALC = "0"
            cargs = dict(("INP%s"%(chr(65+j)),pv) \
                for j,(pv,inCalc) in enumerate(subset))
            if ncalcs>1:
                self.__writeCalc(recordName+str(i+1),SCAN="1 second",CALC=CALC,PHAS=2,ACKT="NO",**cargs)
            else:
                self.__writeCalc(recordName,SCAN="1 second",CALC=CALC,PHAS=2,ACKT="NO",**cargs)
        ob.addRecord(recordName)
        if sevrs:                          
            ob.addRecord(recordName, True)                                        
                                
    def writeRecords(self):
        open(self.db, "w").write(self.dbtext)

    def startupScript(self, filename = None, edl = None, macros = None, 
            setPath = True, setPort = True):
        '''Create an edm startup script using the paths stripped from 
        configure/RELEASE. If filename is None default to st<dom>-gui. If edl
        is None default to <dom>-synoptic.edl. If macros is None default to
        dom=<dom>'''
        # get default values
        if filename is None:
            filename = "st" + self.dom + "-gui"
        filename = self.__safe_filename(filename)
        if edl is None:
            edl = self.dom + "-synoptic.edl"
        if macros is None:
            macros = "dom="+self.dom
        # find paths for current module
        BLdevpath = self.RELEASE.replace("configure/RELEASE", \
            self.dom+"App/opi/edl")            
        BLpath = self.RELEASE.replace("configure/RELEASE","data")
        # format paths for release tree
        devpaths = "".join(['    export EDMDATAFILES="${EDMDATAFILES}%s:"\n'%x \
            for x in self.devpaths])
        paths = "".join(['export EDMDATAFILES="${EDMDATAFILES}:%s"\n'%x \
            for x in self.paths])
        # open the file
        f = open(filename, "w")
        # work out epics version
        epics_ver = re.findall(r"(R\d(?:\.\d+)+)", os.path.abspath(filename))
        if epics_ver:            
            epics_ver = epics_ver[0]
        else:
            epics_ver = "R3.14.11"
        # first put the header in
        f.write(Header % locals())
        # now prepend EDMDATAFILES onto the PATH
        if setPath:
            f.write(SetPath)
        # now popup a gui prompting for the port
        if setPort:
            f.write(SetPort)
        # finally run edm
        if macros:
            macros = '-m "%s" ' % macros
        f.write('edm ${OPTS} %(macros)s %(edl)s' % locals())
        # write the file out
        f.close()

    def __writeBLScript(self, name, text):
        filename = self.__safe_filename("st%s-%s" % (self.dom, name))
        open(filename, "w").write(text)

    def blScripts(self, fe = True, alh = True, burt = True):
        '''Create the standard set of beamline scripts to run alh, FE, etc'''
        dom = self.dom
        if fe:
            FEdom = dom.replace("BL","FE")
            self.__writeBLScript("fe", Fe % locals())
        if alh:
            alhLogPath = "/dls/%s/epics/alh" % (dom[4].lower() + dom[2:4])
            self.__writeBLScript("alh", Alh % locals())
            self.__writeBLScript("alhserver", Alhserver % locals())
        if burt:
            self.__writeBLScript("burt", Burt % locals())
                                                                                                       
Header = """#!/bin/sh
# Make sure edm is on our path
if [[ $(cat /etc/redhat-release) =~ 'release 5' ]]; then
    # Legacy RHEL5 machines use old EDM
    export DLS_EPICS_RELEASE=R3.14.11
else    
    export DLS_EPICS_RELEASE=%(epics_ver)s
fi
source /dls_sw/etc/profile
TOP="$(cd $(dirname "$0")/../..; pwd)"

# first load the paths. These have been generated from the configure/RELEASE
# tree. If we have a -d arg then load the opi/edl paths first
unset EDMDATAFILES
if [ "$1" = "-d" ]; then
    if ls ${TOP}/*App/opi/edl > /dev/null 2>&1; then
        for d in ${TOP}/*App/opi/edl; do
            export EDMDATAFILES="${EDMDATAFILES}${d}:"
        done
    fi
    export EDMDATAFILES="${EDMDATAFILES}${TOP}/data:"
%(devpaths)s
    OPTS="-x -eolc"
else
    OPTS="-x -eolc -noedit"
fi
export EDMDATAFILES="${EDMDATAFILES}${TOP}/data"
%(paths)s
"""

SetPath = """
# Set the path to include any scripts in data dirs
export PATH=${EDMDATAFILES}:${PATH}
"""    

SetPort = r"""
# Prompt for the server port if it isn't already set
if [ "$EPICS_CA_SERVER_PORT" = "" ]
then
    xmessage -nearmouse -buttons '5064 - Machine Mode,'\
'6064 - Prod Simulation,6164 - Work Simulation,6764 - Local Simulation' \
'Which port would you like to run the edm display on?'\
'                                      '
    case $? in
    101) export EPICS_CA_SERVER_PORT=5064
         export EPICS_CA_REPEATER_PORT=5065 ;;
    102) export EPICS_CA_SERVER_PORT=6064
         export EPICS_CA_REPEATER_PORT=6065 ;;
    103) export EPICS_CA_SERVER_PORT=6164
         export EPICS_CA_REPEATER_PORT=6165 ;;
    104) export EPICS_CA_SERVER_PORT=6764
         export EPICS_CA_REPEATER_PORT=6765 ;;
    esac    
fi
"""    

Alh = """#!/bin/sh
alh -D -S $(dirname $0)/%(dom)s.alhConfig
"""

Alhserver = r"""#!/bin/sh
if [ ! -d %(alhLogPath)s ]; then
    mkdir -m 775 -p %(alhLogPath)s
fi
alh -m 0 -T \
    -a %(alhLogPath)s/%(dom)s-alarm-log.alhAlarm \
    -o %(alhLogPath)s/%(dom)s-alarm-log.alhOpmod \
    $(dirname $0)/%(dom)s.alhConfig &
"""

Fe = "/dls_sw/prod/etc/Launcher/FrontEnd_QT.sh %(FEdom)s"

Burt = "if [ -d $1 ]; then cd $1; fi; burtgooey"
