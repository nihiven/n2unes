# TODO: save options to file

# imports
import os
import fnmatch
import sys
import subprocess
import ntpath
import time
import json

## config
# paths
foobar_path = 'C:\\Program Files (x86)\\foobar2000\\foobar2000.exe'
music_paths = ['e:\\mp3','e:\\downloads\\torrents\\music']

music = [] # global list of indexed music
matches = [] # global list of matches from the latest query

## O P T I O N S
queue_clear = True # clear queue for each search
queue_matches = True # queue multiple seaerch results
queue_matches_MAX = 50 # max number of results to queue
display_matches = True # display multiple search results
display_matches_MAX = 50 # max number of results to display
display_matches_totals = True # display total number of matches if more than MAX
display_matches_fullpath = False # display filename's full path
display_matches_line_numbers = True # display line number in match results
play_matches_mode = 'random' # first, random # TODO: implement
play_matches_type = 'flac' # filetype to prefer or False # TODO: implement

options = [	['queue_clear', 'True/False', 'Clear queue after each search'],
						['queue_matches', 'True/False', 'If a search has multiple results, queue them'],
						['queue_matches_MAX', 'Int', 'The maximum number of matches to queue'], 
						['display_matches', 'True/False',''],
						['display_matches_MAX','Int','The total number of matches to display'],
						['display_matches_totals','True/False','Display the total number of matches if more than display_matches_MAX'],
						['display_matches_fullpath','True/False','Display a the full path when showing file matches'],
						['display_matches_line_numbers','True/False','Display line numbers when showing matches'],
						['play_matches_mode','first/random',''],
						['play_matches_type','filetype extension','Prefer the given file type when there are multiple matches']
						]


## NOW FOR SOME FUNCTIONS
def queue_file(file):
	foobar('/add',file)


def queue_list(list):
	l = len(list)
	if (l > 0):
		#if (queue_clear):
		#	foobar('/command:Clear','')

		# always queue the first item
		if (queue_clear):
			foobar('/immediate',list[0]) # /immediate clears the queue
		else:
			queue_file(list[0])

		#wait a little bit
		time.sleep(1)

		# queue the rest of the matches
		if (queue_matches):
			i = 1
			while (i < queue_matches_MAX and i < l):
				queue_file(list[i])
				i = i + 1
#queue_list()

# display a list of files using defined options
def display_list(list):
	l = len(list)
	if (display_matches and l > 0):
		if (display_matches_totals and display_matches_MAX < l):
			print 'Top', display_matches_MAX, 'of', str(l), 'matches'

		i = 0 # current index in list
		while (i < display_matches_MAX and i < l):

			# generate zero padded line number
			if (display_matches_line_numbers):
				output_string = '[' + str(i+1).rjust(len(str(l)), '0') + '] '
			else:
				output_string = ''

			# add file to output
			if (display_matches_fullpath):
				output_string = output_string + list[i]
			else:
				output_string = output_string + ntpath.basename(list[i])

			# print output and set vars
			print output_string
			i = i + 1
#display_list()


# run foor bar, pass data on command line
def foobar(cmd, arg):
	subprocess.Popen([foobar_path,cmd,arg])


# index files from given paths into global music[]
def index_files():
	global music
	music = []

	print 'indexing files in', len(music_paths), 'directories'
	for path in music_paths:
		i = 0
		for root, dirs, files in os.walk(path):
			for file in files:
				if file.endswith(('.mp3','.mpc','ogg','.m4a','.aac','.m3u','.fpl','.flac','.wav')):
					music.append(os.path.join(root, file))
					i = i + 1
		print ' ' + path + ':', i, 'files'
#index_files()


def save_index():
	try:
		global music
		# save list to disk
		f = open('music.idx', 'w')
		encoded = json.dump(music, f, encoding="latin-1")
		f.close()
		print 'wrote index to disk'
		return True
	except IOError, e:
		print 'failed to write index to disk'
		return False
#save_index()

def load_index():
	try:
		global music
		# load list to disk
		f = open('music.idx', 'r')
		music = json.load(f, encoding="latin-1")
		f.close()
		print 'loaded index from file'
		return True
	except IOError, e:
		return False
#load_index()


# takes given command and routes to other internal functions
def parse_command(command):
	if (command[0] == '/'):
		args = command.split()
		cmd = args[0]
		args.pop(0)

		# playlist
		if (cmd == '/playlist'):
			if (args[0] == 'clear'):
				foobar('/command:Clear','')

			if (args[0] == 'sort'):
				foobar('/command:Sort by title','')
		#if

		if (cmd == '/info'):
			command_info()

		if (cmd == '/index'):
			index_files()
			save_index()

		if (cmd == '/set'):
			command_set(args)

		if (cmd == '/exit'):
			return False

		if (cmd == '/match'):
			command_match(args[0])

		# control
		control_commands = ['/play', '/stop', '/pause', '/next', '/prev']
		if any(cmd in s for s in control_commands):
			foobar(cmd, '')
	#if

	else: # if it's not a command, assume it's a query
		command_query(command)
#parse_command()


# searches music indext for files matches the given query
def command_query(data):
	query = data.replace(' ','*')
	query = '*' + query + '*'

	global matches 
	matches = fnmatch.filter(music, query)

	if (len(matches) > 0):
		queue_list(matches)
		display_list(matches)
	else:
		print 'No matches for:', query
#command_query()


def command_info():
	print music_paths
	print str(len(music)), 'files indexed'
	print str(len(matches)), 'matches in memory'
#command_info()


# play the given index from the last set of matches
def command_match(index):
	global matches
	index = int(index)
	if (index < len(matches)):
		print matches[index] # TODO: implement
	else:
		error('match',['No such index',index])
#command_match()


# sets internal variables
def command_set(args):
	# missing item and value
	if (len(args) == 0):
		error('/set', '[item] [value]')
		return

	# missing value
	if (len(args) == 1):
		error('/set', args[0] + ' [' + command_set_values(args[0]) + ']')
		return

	# ok to go
	item = args[0]
	value = args[1]

	# queue_clear : True/False
	if (item == 'queue_clear'):
		if (value == 'True' or value == 'False'):
			global queue_clear
			queue_clear = bool(value)
		else:
			error('/set', 'invalid value for queue_clear: ' + value)
#command_set()


# TODO: we're going to use the global options for this function
def command_set_values(item):
	if (item == 'queue_clear'):
		return 'True/False'
#command_set_values


# we'll fix this up later
def error(cmd, data):
	print 'Error'
	print cmd, data
#error()


## let's go to work
# welcome
subprocess.call("cls", shell=True)

if (load_index() == False): # try to load index from disk
	index_files() # create a new one if it fails
	save_index()

print ''

## main loop, read input and process
while (1):
	command = str(raw_input("n2unes: "))
	if (parse_command(command) == False):
		break
	print ''
