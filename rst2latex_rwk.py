#!/usr/bin/env python
import os
from optparse import OptionParser

import rwkos

if rwkos.amiLinux():
    basecmd = 'rst2latexmath.py'
else:
    basecmd = 'rst2latex.py'

basecmd += ' --use-latex-citations'

usage = 'usage: %prog [options] inputfile.rst'
parser = OptionParser(usage)

parser.add_option("-r", "--runlatex", dest="runlatex", \
                  help="Run LaTeX after presentation is converted to tex.", \
                  default=1, type="int")

parser.add_option("-o", "--output", dest="output", \
                  help="Desired output path or filename.", \
                  default='', type="string")

parser.add_option("-f", "--fontsize", dest="fontsize", \
                  help="Fontsize in document options (in points).", \
                  default='12', type="string")

parser.add_option("-n", "--number", dest="number",\
                  help="Number sections and subsections (as opposed to using seciton*)", \
                  default=1, type="int")

parser.add_option('-s','--stylesheet',dest='stylesheet', \
                  help='path to latex style sheet', \
                  default='', type=str)

parser.add_option('-c','--clean',dest='clean', \
                  help='clean up files generated by pdflatex and rst:' + \
                  '\n 0: leave all' + '\n 1: delete .log, .aux, .out' + \
                  '\n 2: delete .tex and all level 1 files (leaving only rst and pdf)', \
                  default=1, type=int)

#rst2latex --section-numbering --use-latex-toc proposal_format.rst proposal_format.tex


## parser.add_option("-t", "--theme", dest="theme", \
##                   help="Beamer theme to be used.", \
##                   default="ryan_Warsaw_no_subs", type="string")
##                   #default="ryan_Warsaw", type="string")
##                   #default="CambridgeUS", type="string")

## parser.add_option("-i", "--use-latex-docinfo", dest="info", \
##                   help='Should the option "--use-latex-docinfo" be passed to rst2beamer', \
##                   default=0, type=int)

                  
(options, args) = parser.parse_args()

print('args = %s' % args)
print('options = %s' % options)

inputfile = args[0]

outputfile = options.output

if options.number:
    basecmd += ' --section-numbering --use-latex-toc'

if options.stylesheet:
    basecmd += ' --stylesheet='+str(options.stylesheet)
    #basecmd += ' --stylesheet-path='+str(options.stylesheet)
    
if not outputfile:
    fno, ext = os.path.splitext(inputfile)
    outputfile = fno+'.tex'

fontsize = options.fontsize
mydocopts = '"%spt,letterpaper"' % fontsize

## if options.info:
##     basecmd += ' --use-latex-docinfo'
cmd = basecmd + ' --documentoptions=%s %s %s' % \
      (mydocopts, inputfile, outputfile)
print(cmd)

os.system(cmd)

if options.runlatex:
    curdir = os.getcwd()
    outfolder, outfile = os.path.split(outputfile)
    try:
        os.chdir(outfolder)
        lcmd = 'pdflatex %s' % outfile
        print(lcmd)
        os.system(lcmd)

        if options.clean > 0:
            exts = ['.out','.log']
            if options.clean > 1:
                exts.extend(['.tex','.aux'])
            basename, ext = os.path.splitext(outfile)
            for ext in exts:
                curname = basename + ext
                if os.path.exists(curname):
                    os.remove(curname)
    finally:
        os.chdir(curdir)
        
            