#ZSDavidson
#borrowing heavily from https://github.com/machinekoder

import sys
import argparse
import re


regMatch = []
toolMatch = []

endCode = '; end of program'
endTerm = r';END gcode for filament'

init_extrude_retract = re.compile(r'(G(?:0|1|2|3|28).*)(E([-\+]?[\d\.\d]*))(.*)retract',
                                    flags=re.IGNORECASE)


def compile_replacements(tools):
    pressure_toggles = []
    for tool in tools:
        #pressure_toggles += ([[r'(:?.*)(retract)(:?.*)'+str(tool[0]),
        #                        r'Call togglePress P'+str(tool[2])+' ;']])
        pressure_toggles += ([[r'(:?.*)(retract)(:?.*)'+str(tool[0]),
                                '\n']])
        #pressure_toggles += ([[r'(G(?:92).*)(?:E0)',r'Call togglePress P'+str(tool[2])+' ;\n']])
        #pressure_toggles += ([[r'(G(?:0|1|2|3|28).*)(E([-\+]?[\d\.\d]*))(.*retract extruder.*)'+str(tool[0]),
        #                        r'Call togglePress P'+str(tool[1])+' ;']])
        pressure_toggles += ([[r'(?:M109 S[\d]* T)'+str(tool[0])+r'(?:.*)',
                                r'Call setPress P'+str(tool[2])+r' Q'+str(tool[3])+
                                r' ; tool '+str(tool[0])+
                                r'\nG90 ;use absolute coordinates \n'+
                                r'MINUTES\n']])

    replacements = [
        [r'(G(?:92).*)(?:E0)',r''], #remove reset extruders
        [r'G21',r''], # remove G21 codes
        [r'(G(?:0|1|2|3|28).*)(E([-\+]?[\d\.\d]*))(.*)',r'\1\4'], # remove extruder commands before feedrate
        [r'M82.*',''], ## remove absolute distances for extrusion
        [r'M10(?:4|6|7).*',''], ## remove fan and temperature commands
    ]

    replacements += pressure_toggles

    for regexString, replacement in replacements:
        regex = re.compile(regexString)
        regMatch.append([regex, replacement])


def tool_replacements(tools):
    tool_dict = {}
    for tool in tools:
        regex = re.compile(r'(G(?:1).)(Z)(.*)')
        tool_dict[tool[0]]=[regex,r'\1 '+str(tool[1])+r'\3',tool[2],tool[3],tool[4],tool[5],tool[6]]
    return tool_dict

def do_replacements(line):
    for regex, replacement in regMatch:
        line = regex.sub(replacement, line)
    return line

def sanitised_input(prompt, type_=None, min_=None, max_=None, range_=None):
    """
    https://stackoverflow.com/questions/23294658/asking-the-user-for-input-until-they-give-a-valid-response
    """
    if min_ is not None and max_ is not None and max_ < min_:
        raise ValueError("min_ must be less than or equal to max_.")
    while True:
        ui = input(prompt)
        if type_ is not None:
            try:
                ui = type_(ui)
            except ValueError:
                print("Input type must be {0}.".format(type_.__name__))
                continue
        if max_ is not None and ui > max_:
            print("Input must be less than or equal to {0}.".format(max_))
        elif min_ is not None and ui < min_:
            print("Input must be greater than or equal to {0}.".format(min_))
        elif range_ is not None and ui not in range_:
            if isinstance(range_, range):
                template = "Input must be between {0.start} and {0.stop}."
                print(template.format(range_))
            else:
                template = "Input must be {0}."
                if len(range_) == 1:
                    print(template.format(*range_))
                else:
                    print(template.format(" or ".join((", ".join(map(str,
                                                                     range_[:-1])),
                                                       str(range_[-1])))))
        else:
            return ui

def get_tool_info(num_tools):
    tools=[]
    for input_num in range(num_tools):
        tnumstr = 'What is the tool number in Slic3r? '+str(input_num+1)+'/'+str(num_tools) + ' ... '
        tnum = sanitised_input(tnumstr,str)
        axisstr = 'What AeroTech axis is the tool on? '+str(input_num+1)+'/'+str(num_tools) + ' ... '
        axis = sanitised_input(axisstr,str)
        comportstr='What is the comport of the tool? '+str(input_num+1)+'/'+str(num_tools) + ' ... '
        comport = sanitised_input(comportstr,int)
        pressurestr = 'What pressure do you want to run at? '+str(input_num+1)+'/'+str(num_tools) + ' ... '
        pressure = sanitised_input(pressurestr,int)
        xoffsetstr = 'What is the x offset for the tool? '+str(input_num+1)+'/'+str(num_tools) + ' ... '
        xoffset = sanitised_input(xoffsetstr,float)
        yoffsetstr = 'What is the y offset for the tool? '+str(input_num+1)+'/'+str(num_tools) + ' ... '
        yoffset = sanitised_input(yoffsetstr,float)
        velocitystr = 'VELOCITY ON for the tool? 1=Yes, 0=No'+str(input_num+1)+'/'+str(num_tools) + ' ... '
        velocity = sanitised_input(velocitystr,int,min_=0,max_=1)
        tools+=[[tnum,axis,comport,pressure,xoffset,yoffset,int(velocity)]]
    return tools


def main():
    main_description = '''
    This application converts RepRap flavour GCode to AeroTech flavour GCode.
    This version is for multiple materials and assumes you correctly configured
    Slic3r to produce readily translatable GCode. See readme for details.
    Slic3r must be set to produce verbose GCode.
    '''
    parser = argparse.ArgumentParser(description=main_description)
    parser.add_argument('-i','--infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin, help='input file, takes input from stdin if not specified',
                        required=True)
    parser.add_argument('-o','--outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout, help='output file, prints output to stdout of not specified',
                        required=True)
    parser.add_argument('-T','--tool', nargs=6, metavar=('toolx','axis','comport','pressure','xoffset','yoffset'),
                        action='append',
                        help='Set tool x comport and pressure, e.g.: -T 1 A 5 30 -35.2, 0.1',
                        required=False, default=None)
    parser.add_argument('-d', '--debug', help='enable debug mode', action='store_true')
    args = parser.parse_args()

    #print(args.tool)
    #return
    if args.tool is None:
        number_of_tools=sanitised_input('Specify number of tools ... ',int,min_=1)
        tool_list = get_tool_info(number_of_tools)
        compile_replacements(tool_list)
        tool_dict = tool_replacements(tool_list)
    else:
        tool_dict = tool_replacements(args.tool)
        tool_list = args.tool
        compile_replacements(args.tool)

    hasProgramEnd = False
    inFile = args.infile
    outFile = args.outfile
    outFile.write(starting_string) #dVars etc from start of  mecode output
    current_tool = None
    toggle_count = 0
    endRegex = re.compile(endTerm, flags=re.IGNORECASE)
    set_press_line = False ## has the set pressure line been done?
    for line in inFile:
        #do not write this line for first time
        if (not set_press_line) and init_extrude_retract.match(line):
            set_press_line = True
            continue ## sorry for the ugly
            #### needs fixing. must happen for every tool change.
        newline = do_replacements(line)
        move_layer = re.search('move to next layer',newline)
        if move_layer :
            newline = r''
        tool_change = re.search('T(\d) ; change extruder',newline)
        if tool_change:
            newline = r';'+newline
            if (current_tool is not None):
                last_tool = int(current_tool)
                current_tool = str(tool_change.group(1))
                #and  add togglePress for last tool
                #newline += '\n Call togglePress P'+str(tool_dict[str(last_tool)][2])+' ;'
            else:
                current_tool = str(tool_change.group(1))
                #don't add togglePress on the first one
            set_press_line = False
            assert ((tool_dict[current_tool][6] == 0) or (tool_dict[current_tool][6] == 1)), 'VELOCITY on must be 1 or 0.'
            if tool_dict[current_tool][6] == 0:
                newline +='\n VELOCITY OFF\n'
            elif tool_dict[current_tool][6] == 1:
                newline +='\n VELOCITY ON\n'

        elif (current_tool is not None):# add the offsets:
            try:
                newline = tool_dict[current_tool][0].sub(tool_dict[current_tool][1],newline)
                tool_move = re.search('(G(?:1).)(X)(\d+\.\d*)(\sY)(\d+\.\d*)(.*)',newline)
                #tool_move = re.search('(G(?:1).)(X)(\d+\.\d+)(\sY)(\d+\.\d+)\s*;',newline)
                if tool_move:
                    #try:
                    newline=str(tool_move.group(1))+str(tool_move.group(2))+\
                            '{0:.4f}'.format(float(tool_move.group(3))+float(tool_dict[current_tool][4]))+\
                            str(tool_move.group(4))+\
                            '{0:.4f}'.format(float(tool_move.group(5))+float(tool_dict[current_tool][5]))+\
                            tool_move.group(6)+'\n'

                    #except:
                    #    return
            except KeyError:
                print('Tool in file not found in user entered tools. Tool: '+
                        str(current_tool) +'\n Exiting...')
                inFile.close()
                outFile.close()
                return
        lift_Z = re.search('lift Z',newline)
        restore_Z = re.search('restore layer Z',newline)
        if (lift_Z and (current_tool is not None)):
            if toggle_count > 0:
                newline = '\nCall togglePress P'+str(tool_dict[str(current_tool)][2])+' ;\n' + newline
                toggle_count +=1
        elif (restore_Z and (current_tool is not None)):
            newline += '\nCall togglePress P'+str(tool_dict[str(current_tool)][2])+' ;\n'
            toggle_count +=1

        outFile.write(newline)
        if (not hasProgramEnd) and endRegex.match(newline):  # check for end of program
            hasProgramEnd = True

    if not hasProgramEnd:
        outFile.write(endCode + "\n")

    outFile.write("SECONDS\n")
    outFile.write(ending_string) #functions for aerotech, see below

    inFile.close()
    outFile.close()

    exit(0)


starting_string = """DVAR $hFile
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
G66 F2000;accel speed mm/s^2 """

ending_string = """
M2

;##########Functions############;
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

"""

if __name__ == "__main__":
    main()
