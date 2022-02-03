#ZSDavidson
#borrowing heavily from https://github.com/machinekoder

import sys
import argparse
import re


regMatch = []

endCode = '; end of program'
endTerm = r';END gcode for filament'

init_extrude_retract = re.compile(r'(G(?:0|1|2|3|28).*)(E([-\+]?[\d\.\d]*))(.*)retract',
                                    flags=re.IGNORECASE)

def compile_replacements(pressure):
    replacements = [
        [r'(G(?:92).*)(?:E0)',r''], #remove reset extruders
        [r'G21',r''], # remove G21 codes
        [r'(G(?:0|1|2|3|28).*)(E([-\+]?[\d\.\d]*))(.*)retract',r'Call togglePress P5 ;'], # toggle pressure.
        #[r'(G(?:0|1|2|3|28).*)((?:E)([-\+]?[\d\.].*))', r'\1'], #remove extruder commands during moves
        [r'(G(?:0|1|2|3|28).*)(E([-\+]?[\d\.\d]*))(.*)',r'\1\4'], # remove extruder commands before feedrate
        #[r'(G(?:0|1|2|3|28|92).*)((?:F)([-\+]?[\d\.].*))', r'\1'],
        [r'M82.*',''], ## remove absolute distances for extrusion
        [r'M104.*',''], ## remove temperature commands
        [r'M10(?:4|6|7).*',''], ## remove fan and temperature commands
        [r'M109.*','G90 ;use absolute coordinates \n'+
                    'Call setPress P5 Q'+str(pressure)+' ;set pressure \n'+
                    'MINUTES ;set to mm/min']
        #[r'',r'Call togglePress P5'] # toggle the pressure before travel or prints
    ]
    for regexString, replacement in replacements:
        #regex = re.compile(regexString, flags=re.IGNORECASE)
        regex = re.compile(regexString)
        regMatch.append([regex, replacement])


def do_replacements(line):
    for regex, replacement in regMatch:
        line = regex.sub(replacement, line)
    return line

def main():
    parser = argparse.ArgumentParser(description='This application converts RepRap flavour GCode to AeroTech flavour GCode')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin, help='input file, takes input from stdin if not specified')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout, help='output file, prints output to stdout of not specified')
    parser.add_argument('-Q','--pressure', help='Set the pressure',type=int, required=True)
    parser.add_argument('-d', '--debug', help='enable debug mode', action='store_true')
    args = parser.parse_args()
    print(args.pressure)

    hasProgramEnd = False
    inFile = args.infile
    outFile = args.outfile
    outFile.write(starting_string) #dVars etc from start of  mecode output

    compile_replacements(args.pressure)
    endRegex = re.compile(endTerm, flags=re.IGNORECASE)
    set_press_line = False ## has the set pressure line been done?
    for line in inFile:
        #do not write this line for first time
        if (not set_press_line) and init_extrude_retract.match(line):
            set_press_line = True
            continue ## sorry for the ugly
        newline = do_replacements(line)
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
