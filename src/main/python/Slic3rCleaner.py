#ZSDavidson
#/Users/zoeydavidson/Documents/Results/buckledDEA/BucklingActuator/2019-11-12_mm_buckler_newscript/buckler_multi_solid_v2.gcode
#/Users/zoeydavidson/Documents/Code/mecode/20191016_buckler_fix/buckler1_v4.gcode
import sys
import argparse
import re

class Slic3rCleaner(object):
    """
    Class object to keep track of parameters for cleaning Slic3r output
    """

    def __init__(self,tool_dict,infile,outfile):

        self.init_extrude_retract = re.compile(r'(G(?:0|1|2|3|28).*)(E([-\+]?[\d\.\d]*))(.*)retract',
                                            flags=re.IGNORECASE)

        self.current_tool = None
        self.toggle_count = 0
        #self.set_press_line = False ## has the set pressure line been done?
        self.current_tool_toggle_state = False #is the current tool on or off?
        self.infile = infile
        self.outfile = outfile


        self.tool_dict = tool_dict#self.tool_replacements(tool_list)

        self.regMatch = self.compile_generic_replacements(tool_dict)
        self.tool_setups = self.setup_tools()
        #[r'(G(?:0|1|2|3|28).*)(E([-\+]?[\d\.\d]*))(.*)',r'\1\4'], # need these to check for toggling

    def handle_toggles(self,line):
        extrude_line = re.match(r'(G(?:0|1|2|3|28) )(X)(\d+\.\d*)(\sY)(\d+\.\d*) (E[-\+]?[\d\.\d]*)(.*)',line)
        writeline=line
        toggleline=''
        if extrude_line and self.current_tool_toggle_state:
            #write line without E command
            writeline = extrude_line.group(1)+ \
                        extrude_line.group(2)+ \
                        extrude_line.group(3)+ \
                        extrude_line.group(4)+ \
                        extrude_line.group(5)+\
                        extrude_line.group(7)+'\n'
            self.current_tool_toggle_state = True # not needed but hey
        elif (extrude_line) and (not self.current_tool_toggle_state):
            self.current_tool_toggle_state = True
            #toggle pressure and write line without E command
            toggleline = 'Call togglePress P'+str(self.current_tool.comport)+'; toggle on\n'
            #print('toggle on!')
            writeline = extrude_line.group(1)+ \
                        extrude_line.group(2)+ \
                        extrude_line.group(3)+ \
                        extrude_line.group(4)+ \
                        extrude_line.group(5)+ \
                        extrude_line.group(7)+ '\n'
            self.toggle_count += 1
            return (toggleline,writeline)
        elif (not extrude_line) and self.current_tool_toggle_state:
            #toggle pressure off and write the line, whatever it is
            toggleline = '\nCall togglePress P'+str(self.current_tool.comport)+'; toggle off\n'
            writeline = line+'\n'
            self.toggle_count += 1
            self.current_tool_toggle_state = False
            #print('toggle off!')

        return (toggleline,writeline)
#/Users/zoeydavidson/Documents/Results/buckledDEA/BucklingActuator/2019-11-18_buckling_mm_gui_test/buckler_multi_solid_v3_0pt5wall.gcode
    def compile_generic_replacements(self,tools):
        """
        creates the regular expression pairs to handle the majority
        of replacements in the *.gcode text for creating aerotech *.pgm.
        """
        regMatch = []
        replacements = [
            [r'(G(?:92).*)(?:E0)',r''], #remove reset extruders
            [r'G21',r''], # remove G21 codes
            [r'M82.*',''], ## remove absolute distances for extrusion
            [r'M10(?:4|6|7|8|9).*',''], ## remove fan and temperature commands
            [r'(G1 )(E[-\+]?[\d\.\d]*)(.*)',''],
            [r'(G1 )(-?(\d*\.\d*))(.*)','']
        ]

        for regexString, replacement in replacements:
            regex = re.compile(regexString)
            regMatch.append([regex, replacement])

        return regMatch

    def setup_tools(self):
        """
        set pressures and make sure everything is in absolute coords and mm/minute
        """
        tool_setups =''
        for tool in self.tool_dict:
            #pressure_toggles += ([[r'(:?.*)(retract)(:?.*)'+str(tool[0]),
            #                        '\n']])
            tool_setups += (r'Call setPress P'+str(self.tool_dict[tool].comport)+
                            r' Q'+str(self.tool_dict[tool].pressure)+
                            r' ; tool '+str(self.tool_dict[tool].tool_number))+'\n'

        if len(self.tool_dict)==1:
            self.current_tool = next(iter(self.tool_dict.values()))

        tool_setups += '\nG90 ;use absolute coordinates \n'+'MINUTES\n'
        return tool_setups

    def do_replacements(self,line):
        """
        Search the line and sub in replacements if found make a new line.
        Otherwise, return the original line.
        """
        for regex, replacement in self.regMatch:
            line = regex.sub(replacement, line)
        return line

    def handle_tool_offsets(self,line):
        tool_move = re.search('(G(?:1).)(X)(\d+\.\d*)(\sY)(\d+\.\d*)(.*)',line)
        newline = line
        if tool_move:
            newline=str(tool_move.group(1))+str(tool_move.group(2))+\
                    '{0:.4f}'.format(float(tool_move.group(3))+float(self.current_tool.xoffset))+\
                    str(tool_move.group(4))+\
                    '{0:.4f}'.format(float(tool_move.group(5))+float(self.current_tool.yoffset))+\
                    tool_move.group(6)+'\n'
        return newline


    def handle_tool_change(self,line):
        tool_change = re.search('T(\d) ; change extruder',line)
        newline = line
        if tool_change:
            newline = r';'+line
            #self.current_tool_toggle_state = False
            try:
                self.current_tool = self.tool_dict[int(tool_change.group(1))]
            except Exception as e:
                raise
            if self.current_tool.velocity:
                newline +='\n VELOCITY ON\n'
            else:
                newline +='\n VELOCITY OFF\n'
        return newline
            # except KeyError:
            #     print('Tool in file not found in user entered tools. Tool: '+
            #             str(self.current_tool) +'\n Exiting...')
            #     return

    def handle_z_moves(self,line):
        """
        Be sure to toggle the pressure when moving in z
        """
        newline = line
        z_move = re.search('(G1 )(Z)(\d*\.\d*)(.*)',line)
        if (z_move and (self.current_tool is not None)):
            newline = z_move.group(1)+str(self.current_tool.aeroaxis)+z_move.group(3)+z_move.group(4)+'\n'
        return newline

    def run_lines(self):
        main_description = '''
        This application converts RepRap flavour GCode to AeroTech flavour GCode.
        This version is for multiple materials and assumes you correctly configured
        Slic3r to produce readily translatable GCode. See readme for details.
        Slic3r must be set to produce verbose GCode.
        '''

        with open(self.infile, 'r') as inFile, open(self.outfile, 'w') as outFile:
            outFile.write(starting_string+'\n') #dVars etc from start of mecode output
            outFile.write(self.tool_setups+'\n')
            for line in inFile:
                #do not write this line for first time
                # if (not set_press_line) and init_extrude_retract.match(line):
                #     set_press_line = True
                #     continue ## sorry for the ugly
                    #### needs fixing. must happen for every tool change.
                newline = self.do_replacements(line) #uses sub to replace text in line if match
                newline = self.handle_tool_change(newline) #handle tool_change
                newline = self.handle_z_moves(newline)
                toggleline,newline = self.handle_toggles(newline)
                newline = self.handle_tool_offsets(newline)
                outFile.write(toggleline+newline)

            outFile.write("SECONDS\n") # restore machine for other users
            outFile.write(ending_string) #functions for aerotech, see below

            #inFile.close()
            #outFile.close()

        return self.toggle_count
        #exit(0)

starting_string = """
DVAR $hFile
DVAR $cCheck
DVAR $press
DVAR $length
DVAR $lame
DVAR $comport
DVAR $vacpress

$DO0.0=0
$DO1.0=0
$DO2.0=0
$DO3.0=0

Primary ; sets primary units mm and s
G65 F2000; accel speed mm/s^2
G66 F2000;accel speed mm/s^2
"""

ending_string = """
;#################################### Code ##########################################

M2

;##########Nordson Pressure Box Functions############;
DFS setPress        
         
        $strtask1 = DBLTOSTR( $P, 0 )            
        $strtask1 = "COM" + $strtask1
        $hFile = FILEOPEN $strtask1, 2
        COMMINIT $hFile, "baud=115200 parity=N data=8 stop=1"
        COMMSETTIMEOUT $hFile, -1, -1, 1000
                             
        $press = $Q * 10.0                             
        $strtask2 = DBLTOSTR( $press , 0 )  
      
      
        $length = STRLEN( $strtask2 )      
        WHILE $length < 4.0
                $strtask2 = "0" + $strtask2    
                $length = STRLEN( $strtask2 ) 
        ENDWHILE


        $strtask2 = "08PS  " + $strtask2
                                    
        $cCheck = 0.00     
        $lame = STRTOASCII ($strtask2, 0)
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 1) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 2) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 3) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 4)
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 5) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 6) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 7) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 8) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 9)  
        $cCheck = $cCheck - $lame
                        
        WHILE( $cCheck) < 0
                $cCheck = $cCheck + 256
        ENDWHILE                        


        $strtask3 = makestring "{#H}" $cCheck   
        $strtask3 = STRUPR( $strtask3 )
        $strtask2 = "\x02" + $strtask2 + $strtask3 + "\x03"
            
        FILEWRITE $hFile "\x05"
        FILEWRITE $hFile $strtask2
        FILEWRITE $hFile "\x04"


        FILECLOSE $hFile


ENDDFS

DFS setVac      
         
        $strtask1 = DBLTOSTR( $P, 0 )            
        $strtask1 = "COM" + $strtask1
        $hFile = FILEOPEN $strtask1, 2
        COMMINIT $hFile, "baud=115200 parity=N data=8 stop=1"
        COMMSETTIMEOUT $hFile, -1, -1, 1000
                             
        $vacpress = $Q * 10.0                             
        $strtask2 = DBLTOSTR( $vacpress , 0 )  
      
      
        $length = STRLEN( $strtask2 )      
        WHILE $length < 4.0
                $strtask2 = "0" + $strtask2    
                $length = STRLEN( $strtask2 ) 
        ENDWHILE


        $strtask2 = "08VS  " + $strtask2
                                    
        $cCheck = 0.00     
        $lame = STRTOASCII ($strtask2, 0)
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 1) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 2) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 3) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 4)
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 5) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 6) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 7) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 8) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 9)  
        $cCheck = $cCheck - $lame
                        
        WHILE( $cCheck) < 0
                $cCheck = $cCheck + 256
        ENDWHILE                        


        $strtask3 = makestring "{#H}" $cCheck   
        $strtask3 = STRUPR( $strtask3 )
        $strtask2 = "\x02" + $strtask2 + $strtask3 + "\x03"
            
        FILEWRITE $hFile "\x05"
        FILEWRITE $hFile $strtask2
        FILEWRITE $hFile "\x04"


        FILECLOSE $hFile


ENDDFS

DFS togglePress        
         
        $strtask1 = DBLTOSTR( $P, 0 )            
        $strtask1 = "COM" + $strtask1
        $hFile = FILEOPEN $strtask1, 2
        COMMINIT $hFile, "baud=115200 parity=N data=8 stop=1"
        COMMSETTIMEOUT $hFile, -1, -1, 1000


        $strtask2 = "04DI  "
                                    
        $cCheck = 0.00     
        $lame = STRTOASCII ($strtask2, 0)
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 1) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 2) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 3) 
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 4)
        $cCheck = $cCheck - $lame
        $lame = STRTOASCII( $strtask2, 5) 
        $cCheck = $cCheck - $lame
                        
        WHILE( $cCheck) < 0
                $cCheck = $cCheck + 256
        ENDWHILE                        


        $strtask3 = makestring "{#H}" $cCheck   
        $strtask3 = STRUPR( $strtask3 )
        $strtask2 = "\x02" + $strtask2 + $strtask3 + "\x03"
                  
        FILEWRITE $hFile "\x05"
        FILEWRITE $hFile $strtask2
        FILEWRITE $hFile "\x04"


        FILECLOSE $hFile
        G4 P0.15

ENDDFS

;##########Omnicure Functions############;
DFS omniOn

        $strtask1 = DBLTOSTR( $P, 0 )
        $strtask1 = "COM" + $strtask1
        $hFile = FILEOPEN $strtask1, 2
        COMMINIT $hFile, "baud=19200 parity=N data=8 stop=1"
        COMMSETTIMEOUT $hFile, -1, -1, 1000
                
        FILEWRITENOTERM $hFile "CONN18\x0D"
        FILEREAD $hFile, 0, $strtask2
        WHILE STRCMP($strtask2,"READY0A",0)
                FILEWRITENOTERM $hFile "CONN18\x0D"
                FILEREAD $hFile, 0, $strtask2
        ENDWHILE
        
        FILEWRITENOTERM $hFile "OPN40\x0D"
        FILEREAD $hFile, 0, $strtask2
        WHILE STRCMP($strtask2,"ReceivedBF",0)
                FILEWRITENOTERM $hFile "OPN40\x0D"
                FILEREAD $hFile, 0, $strtask2
        ENDWHILE
        
        FILEWRITENOTERM $hFile "DCONE1\x0D"
        FILEREAD $hFile, 0, $strtask2
        WHILE STRCMP($strtask2,"CLOSED42",0)
                FILEWRITENOTERM $hFile "DCONE1\x0D"
                FILEREAD $hFile, 0, $strtask2
        ENDWHILE
        FILECLOSE $hFile

ENDDFS

DFS omniOff

        $strtask1 = DBLTOSTR( $P, 0 )
        $strtask1 = "COM" + $strtask1
        $hFile = FILEOPEN $strtask1, 2
        COMMINIT $hFile, "baud=19200 parity=N data=8 stop=1"
        COMMSETTIMEOUT $hFile, -1, -1, 1000
                
        FILEWRITENOTERM $hFile "CONN18\x0D"
        FILEREAD $hFile, 0, $strtask2
        WHILE STRCMP($strtask2,"READY0A",0)
                FILEWRITENOTERM $hFile "CONN18\x0D"
                FILEREAD $hFile, 0, $strtask2
        ENDWHILE
        
        FILEWRITENOTERM $hFile "CLS3A\x0D"
        FILEREAD $hFile, 0, $strtask2
        WHILE STRCMP($strtask2,"ReceivedBF",0)
                FILEWRITENOTERM $hFile "CLS3A\x0D"
                FILEREAD $hFile, 0, $strtask2
        ENDWHILE
        
        FILEWRITENOTERM $hFile "DCONE1\x0D"
        FILEREAD $hFile, 0, $strtask2
        WHILE STRCMP($strtask2,"CLOSED42",0)
                FILEWRITENOTERM $hFile "DCONE1\x0D"
                FILEREAD $hFile, 0, $strtask2
        ENDWHILE
        FILECLOSE $hFile
        
ENDDFS

DFS omniSetInt

        $strtask1 = DBLTOSTR( $P, 0 )
        $strtask1 = "COM" + $strtask1
        $hFile = FILEOPEN $strtask1, 2
        COMMINIT $hFile, "baud=19200 parity=N data=8 stop=1"
        COMMSETTIMEOUT $hFile, -1, -1, 1000

        FILEWRITENOTERM $hFile "CONN18\x0D"
        FILEREAD $hFile, 0, $strtask2
        WHILE STRCMP($strtask2,"READY0A",0)
                FILEWRITENOTERM $hFile "CONN18\x0D"
                FILEREAD $hFile, 0, $strtask2
        ENDWHILE

        $strtask4 = $strtask4 + "\x0D"
        FILEWRITENOTERM $hFile $strtask4
        FILEREAD $hFile, 0, $strtask2
        WHILE STRCMP($strtask2,"ReceivedBF",0)
                FILEWRITENOTERM $hFile $strtask4
                FILEREAD $hFile, 0, $strtask2
        ENDWHILE

        FILEWRITENOTERM $hFile "DCONE1\x0D"
        FILEREAD $hFile, 0, $strtask2
        WHILE STRCMP($strtask2,"CLOSED42",0)
                FILEWRITENOTERM $hFile "DCONE1\x0D"
                FILEREAD $hFile, 0, $strtask2
        ENDWHILE
        FILECLOSE $hFile

ENDDFS

;##########Alicat Functions############;
DFS setAlicatPress

        $strtask1 = DBLTOSTR( $P, 0 )
        $strtask1 = "COM" + $strtask1
        $hFile = FILEOPEN $strtask1, 2
        COMMINIT $hFile, "baud=19200 parity=N data=8 stop=1"
        COMMSETTIMEOUT $hFile, -1, -1, 1000
                
        $strtask2 = DBLTOSTR($Q,2)
        $strtask3 = "AS" + $strtask2 + "\x0D"
        FILEWRITENOTERM $hFile $strtask3
        FILECLOSE $hFile

ENDDFS
"""
