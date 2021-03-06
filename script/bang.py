#!/usr/bin/python

# Have someone who knows python rewrite this !eventually


import os, uploader, sys

import simplejson as json
from pythonExtractor import PythonExtractor
from cExtractor import CstyleExtractor
from tag import Tag

def writeConfigFile(symbol, language, suffixes, dirs, cwd):
    config = {
        'symbol': symbol,
        'language': language,
        'dirs': dirs,
        'suffixes': suffixes,
        'projectName': os.path.basename(cwd)
    }
    file(cwd + '/.bangconfig', 'write').write(json.dumps(config))


def readConfigFile(path):
    fileContents = file(path).read()
    return json.loads(fileContents);


def listFiles(rootDir, suffixes):
    fileList = []
    for root, subFolders, files in os.walk(rootDir):
        for file in files:
            for suffix in suffixes:
                if file.endswith(suffix):
                    fileList.append(os.path.join(root, file))
    return fileList;

# Add a ruby extractor !r2
extracters = {
    'js': CstyleExtractor,
    'java': CstyleExtractor,
    'c': CstyleExtractor,
    'cpp': CstyleExtractor,
    'c++': CstyleExtractor,
    'c#': CstyleExtractor,
    'php': CstyleExtractor,
    'py': PythonExtractor
}

languageSuffixes = {

    'python': ['py'],
    'java': ['java'],
    'php': ['php', 'inc','module'],
    'py': ['py'],
    'js': ['js', 'html'],
    'c': ['c', 'h'],
    'cpp': ['c++', 'cpp', 'cxx', 'h', 'cc'],
    'c++': ['c++', 'cpp', 'cxx', 'h', 'cc'],
    }

defaultSymbols = {
    'python': '!',
    'py': '!',
    'php': '!',
    'java': '!',
    'js': '!',
    'c': '!',
    'cpp': '!',
    'c++': '!',
    }

# Main Script


import argparse, os

language = 'py'
symbol = '!'
files = []
globalConfigs = {}
openCommand = 'xdg-open'
# Determine the 'open' command to open a new browser window

if sys.platform == 'darwin':
    openCommand = 'open'
elif sys.platform == 'cygwin':
    openCommand = 'cygstart'



# Now we read the config files, a global one, and a project based one
cwd = os.getcwd()
globalConfigFile = os.getenv("HOME") + "/.bangconfig";
projectConfigFile = cwd + "/.bangconfig";

if os.path.exists(projectConfigFile):
    globalConfigs = readConfigFile(projectConfigFile)
elif os.path.exists(globalConfigFile):
    globalConfigs = readConfigFile(globalConfigFile)


# Now we parse the command line arguments

parser = argparse.ArgumentParser(description='\n')
parser.add_argument('dirs', metavar='directory', nargs='+',
                    help='Directories to parse')

# Beef up -v verbose mode !r2 
# Add an -x exclude option to exclude things like jquery, ext, anything minified.  Use globs ? !r2 ^9

parser.add_argument('-l', dest='language', action='store',
                    help='The language type to parse, options are [php,py(thon),js,java,c,cpp')
parser.add_argument('-c', help='A custom list of file suffixes you want to use for  your language', action='store',
                    dest='languageSuffixes')
parser.add_argument('-s', dest='symbol', action='store', help='The symbol type to search for, common uses are !,#,~')
parser.add_argument('-i', dest='includeLongLines', action='store_const', const='True',
                    help='Include files whose length is > 1000, this is recommended, js users will see a lot of false hits in minified code')
parser.add_argument('-v', dest='verbose', action='store_const', const='True', help='Verbose mode')
parser.add_argument('-q', dest='dontOpen', action='store_const', const='True',
                    help='Dont open the link after the report')
parser.add_argument('-text', dest='text', action='store_const', const='True', help='Add this to use text only display')

args = parser.parse_args()



# Setup some defaults , and some logic here figuring out which defaults to u se 

if args.language:
    language = args.language
elif globalConfigs and 'language' in globalConfigs:
    language = globalConfigs["language"]

if args.symbol:
    symbol = args.symbol
elif globalConfigs:
    symbol = globalConfigs["symbol"]
else:
    symbol = defaultSymbols[language]

if args.languageSuffixes:
    suffixes = args.languageSuffixes.split(',');
elif globalConfigFile and 'suffixes' in globalConfigs:
    suffixes = globalConfigs["suffixes"]
else:
    suffixes = languageSuffixes[language]

if args.verbose: sys.stdout.write(
    "\nCalling bang with language = '" + language + "', symbol = '" + symbol + "', dirs=" + str(args.dirs) + ", suffixes=" + str(suffixes) + "\n")

# Parse all the files for the right file extension


if args.verbose: sys.stdout.write("Using suffixes " + str(suffixes) + "\n")

for d in args.dirs:
    if os.path.isfile(d):
        files.append(d)
    else:
        files.extend(listFiles(d, suffixes))

if args.verbose: sys.stdout.write("Found " + str(len(files)) + " files for parsing\n")
if not len(files):
    sys.stdout.write(
        "Oops, I didn't find any files to parse so I'm quitting.  Using language='" + language + "' , symbol='" + symbol + "', dirs=" + str(
            args.dirs) + ",suffixes=" + str(suffixes) + "\n")
    sys.exit()

#run the extractor
extractorType = extracters[language]
extractor = extractorType(files, symbol, args.includeLongLines)
categories = extractor.run()


# if text only, print the output
if args.text:
    print '\n\nBANG.\n=====\n\n'

    for k, v in categories.iteritems():
        print k, '\n\t'
        tagList = sorted(v, key=lambda v: v.priority, reverse=True)
        for tag in tagList:
            print '\t' + str(tag)
        print '\n\n'

#otherwise upload the report
else:
    reportDict = {
        'tags': categories,
        'project': os.path.basename(cwd)
    }
    report = json.dumps(reportDict, default=Tag.toJson)
    url = uploader.uploadReport(report)
    print url
    if not args.dontOpen:
        #rewrite this to use non deprecated popoen !r2
        os.popen(openCommand + ' ' + url)




# Now , if the symbols or language is different from there ~/.bang file, we ask if they want to save it to a local file
if (('symbol' in globalConfigs and globalConfigs['symbol'] != symbol ) or (
'language' in globalConfigs and globalConfigs['language'] != language ))\
or ( 'symbol' not in globalConfigs and 'language' not in globalConfigs)\
and ( args.language or args.symbol):
    answer = raw_input(
        "\n\nYour defaults have changed, would you like to create a config file for this directory? (y\N)");
    if answer == 'y' or answer == 'Y':
        writeConfigFile(symbol, language, suffixes, args.dirs, cwd)
        sys.stdout.write(
            "\nGreat! Your commmand line arguments have been saved.\n\nNow, to run the report, simply type 'bang [ directories ] '\n");
    else:
        sys.stdout.write("Ok bye!\n");

    
