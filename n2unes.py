# NOTE: This is written for Python 3
# NOTE: Set your foorbar2000 and music paths before running
# TODO: save options to file

# imports
import os
import fnmatch
import sys
import subprocess
import ntpath
import time
import sqlite3
import config

matches = [] # global list of matches from the latest query

# Configuration metadata for help/validation
CONFIG_OPTIONS = [
    ["QUEUE_CLEAR", "True/False", "Clear queue after each search"],
    ["QUEUE_MATCHES", "True/False", "If a search has multiple results, queue them"],
    ["QUEUE_MATCHES_MAX", "Int", "The maximum number of matches to queue"],
    ["DISPLAY_MATCHES", "True/False", ""],
    ["DISPLAY_MATCHES_MAX", "Int", "The total number of matches to display"],
    [
        "DISPLAY_MATCHES_TOTALS",
        "True/False",
        "Display the total number of matches if more than display_matches_MAX",
    ],
    [
        "DISPLAY_MATCHES_FULLPATH",
        "True/False",
        "Display a the full path when showing file matches",
    ],
    [
        "DISPLAY_MATCHES_LINE_NUMBERS",
        "True/False",
        "Display line numbers when showing matches",
    ],
    ["PLAY_MATCHES_MODE", "first/random", ""],
    [
        "PLAY_MATCHES_TYPE",
        "filetype extension",
        "Prefer the given file type when there are multiple matches",
    ],
]

def init_database():
	conn = sqlite3.connect(config.DATABASE_FILE)
	cursor = conn.cursor()
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS music_files (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			filepath TEXT UNIQUE NOT NULL,
			filename TEXT NOT NULL,
			directory TEXT NOT NULL,
			extension TEXT NOT NULL,
			date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	''')
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS cue_tracks (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			cue_file TEXT NOT NULL,
			audio_file TEXT NOT NULL,
			track_number INTEGER NOT NULL,
			title TEXT,
			performer TEXT,
			start_time TEXT,
			end_time TEXT,
			date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	''')
	conn.commit()
	conn.close()


def parse_cue_file(cue_path):
	"""Parse a CUE file and return track information."""
	tracks = []
	current_track = {}
	audio_file = ""
	
	try:
		with open(cue_path, 'r', encoding='utf-8', errors='ignore') as f:
			lines = f.readlines()
	except UnicodeDecodeError:
		# Try with latin-1 encoding if utf-8 fails
		try:
			with open(cue_path, 'r', encoding='latin-1') as f:
				lines = f.readlines()
		except:
			return []
	except:
		return []
	
	for line in lines:
		line = line.strip()
		
		if line.startswith('FILE '):
			# Extract audio filename, removing quotes
			parts = line.split(None, 2)
			if len(parts) >= 2:
				audio_file = parts[1].strip('"')
				# Make it relative to the CUE file's directory
				audio_file = os.path.join(os.path.dirname(cue_path), audio_file)
		
		elif line.startswith('TRACK '):
			# Save previous track if exists
			if current_track and 'track_number' in current_track:
				tracks.append(current_track.copy())
			
			# Start new track
			parts = line.split()
			if len(parts) >= 2:
				current_track = {
					'track_number': int(parts[1]),
					'audio_file': audio_file,
					'cue_file': cue_path
				}
		
		elif line.startswith('TITLE '):
			title = line[6:].strip('"')
			current_track['title'] = title
		
		elif line.startswith('PERFORMER '):
			performer = line[10:].strip('"')
			current_track['performer'] = performer
		
		elif line.startswith('INDEX 01 '):
			time_str = line[9:].strip()
			current_track['start_time'] = time_str
	
	# Don't forget the last track
	if current_track and 'track_number' in current_track:
		tracks.append(current_track)
	
	return tracks


def save_cue_tracks(tracks):
	"""Save CUE track information to database."""
	try:
		conn = sqlite3.connect(config.DATABASE_FILE)
		cursor = conn.cursor()
		
		for track in tracks:
			cursor.execute('''
				INSERT OR REPLACE INTO cue_tracks 
				(cue_file, audio_file, track_number, title, performer, start_time)
				VALUES (?, ?, ?, ?, ?, ?)
			''', (
				track.get('cue_file', ''),
				track.get('audio_file', ''),
				track.get('track_number', 0),
				track.get('title', ''),
				track.get('performer', ''),
				track.get('start_time', '')
			))
		
		conn.commit()
		conn.close()
		return True
	except Exception as e:
		print(f'Failed to save CUE tracks: {e}')
		return False


## NOW FOR SOME FUNCTIONS
def queue_file(file):
	# Check if this is a CUE track (format: audio_file#track_number#start_time#display_info)
	if '#' in file:
		parts = file.split('#', 3)
		if len(parts) >= 3:
			audio_file = parts[0]
			track_num = parts[1]
			start_time = parts[2]
			
			# Look for corresponding CUE file
			audio_dir = os.path.dirname(audio_file)
			audio_name = os.path.splitext(os.path.basename(audio_file))[0]
			
			# Try to find the CUE file (common naming patterns)
			possible_cue_files = [
				os.path.join(audio_dir, audio_name + '.cue'),
				os.path.join(audio_dir, audio_name.lower() + '.cue'),
				os.path.join(audio_dir, audio_name.upper() + '.cue')
			]
			
			cue_file = None
			for cue_path in possible_cue_files:
				if os.path.exists(cue_path):
					cue_file = cue_path
					break
			
			if cue_file:
				# Foobar2000 can handle CUE files directly
				# Load the CUE file, it will show individual tracks
				foobar('/add', cue_file)
			else:
				# Fallback: just play the audio file
				# Note: User will need to manually seek to the track
				foobar('/add', audio_file)
				print(f'Note: Seek to {start_time} for track {track_num}')
		else:
			foobar('/add', file)
	else:
		foobar('/add', file)


def queue_list(list):
	l = len(list)
	if (l > 0):
		#if (config.QUEUE_CLEAR):
		#	foobar('/command:Clear','')

		# always queue the first item
		if (config.QUEUE_CLEAR):
			foobar('/immediate',list[0]) # /immediate clears the queue
		else:
			queue_file(list[0])

		#wait a little bit
		time.sleep(1)

		# queue the rest of the matches
		if (config.QUEUE_MATCHES):
			i = 1
			while (i < config.QUEUE_MATCHES_MAX and i < l):
				queue_file(list[i])
				i = i + 1
#queue_list()

# display a list of files using defined options
def display_list(list):
	l = len(list)
	if (config.DISPLAY_MATCHES and l > 0):
		if (config.DISPLAY_MATCHES_TOTALS and config.DISPLAY_MATCHES_MAX < l):
			print('Top', config.DISPLAY_MATCHES_MAX, 'of', str(l), 'matches')

		i = 0 # current index in list
		while (i < config.DISPLAY_MATCHES_MAX and i < l):

			# generate zero padded line number
			if (config.DISPLAY_MATCHES_LINE_NUMBERS):
				output_string = '[' + str(i+1).rjust(len(str(l)), '0') + '] '
			else:
				output_string = ''

			# add file to output
			current_file = list[i]
			if '#' in current_file and current_file.count('#') >= 3:
				# This is a CUE track, format nicely
				parts = current_file.split('#', 3)
				if len(parts) >= 4:
					display_info = parts[3]  # This contains "title - performer"
					if config.DISPLAY_MATCHES_FULLPATH:
						output_string = output_string + f"[CUE] {display_info} ({parts[0]})"
					else:
						output_string = output_string + f"[CUE] {display_info}"
				else:
					output_string = output_string + current_file
			else:
				# Regular file
				if config.DISPLAY_MATCHES_FULLPATH:
					output_string = output_string + current_file
				else:
					output_string = output_string + ntpath.basename(current_file)

			# print output and set vars
			print(output_string)
			i = i + 1
#display_list()


# run foor bar, pass data on command line
def foobar(cmd, arg):
	subprocess.Popen([config.FOOBAR_PATH,cmd,arg])


# index files from given paths and save to database
def index_files():
	temp_music = []
	cue_count = 0

	print('indexing files in', len(config.MUSIC_PATHS), 'directories')
	for path in config.MUSIC_PATHS:
		i = 0
		for root, dirs, files in os.walk(path):
			for file in files:
				full_path = os.path.join(root, file)
				
				if file.endswith(config.AUDIO_EXTENSIONS):
					temp_music.append(full_path)
					i = i + 1
				elif file.lower().endswith('.cue'):
					# Parse CUE file and save track information
					tracks = parse_cue_file(full_path)
					if tracks:
						save_cue_tracks(tracks)
						cue_count += len(tracks)
		print(' ' + path + ':', i, 'audio files')
	
	if cue_count > 0:
		print('processed', cue_count, 'CUE tracks')
	
	# Save directly to database
	save_to_db(temp_music)
#index_files()


def save_to_db(file_list):
	try:
		conn = sqlite3.connect(config.DATABASE_FILE)
		cursor = conn.cursor()
		
		for filepath in file_list:
			filename = ntpath.basename(filepath)
			directory = ntpath.dirname(filepath)
			extension = os.path.splitext(filename)[1].lower()
			
			cursor.execute('''
				INSERT OR REPLACE INTO music_files (filepath, filename, directory, extension)
				VALUES (?, ?, ?, ?)
			''', (filepath, filename, directory, extension))
		
		conn.commit()
		conn.close()
		print('wrote index to database')
		return True
	except Exception as e:
		print(f'failed to write index to database: {e}')
		return False
#save_to_db()

def get_total_files():
	try:
		conn = sqlite3.connect(config.DATABASE_FILE)
		cursor = conn.cursor()
		
		cursor.execute('SELECT COUNT(*) FROM music_files')
		count = cursor.fetchone()[0]
		
		conn.close()
		return count
	except Exception as e:
		print(f'failed to get file count: {e}')
		return 0
#get_total_files()


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


# searches music database for files matches the given query
def command_query(data):
	# For LIKE patterns, we want to match each word separately
	words = data.strip().split()
	
	global matches
	try:
		conn = sqlite3.connect(config.DATABASE_FILE)
		cursor = conn.cursor()
		
		file_matches = []
		cue_matches = []
		
		if len(words) == 1:
			# Single word search
			pattern = f'%{words[0]}%'
			
			# Search regular files
			cursor.execute('''
				SELECT filepath FROM music_files 
				WHERE filename LIKE ? OR filepath LIKE ?
			''', (pattern, pattern))
			file_matches = [row[0] for row in cursor.fetchall()]
			
			# Search CUE tracks
			cursor.execute('''
				SELECT audio_file, title, performer, track_number, start_time FROM cue_tracks
				WHERE title LIKE ? OR performer LIKE ?
			''', (pattern, pattern))
			cue_results = cursor.fetchall()
			
		else:
			# Multi-word search - all words must be present
			file_conditions = []
			file_params = []
			for word in words:
				file_conditions.append('(filename LIKE ? OR filepath LIKE ?)')
				file_params.extend([f'%{word}%', f'%{word}%'])
			
			file_query_sql = f'''
				SELECT filepath FROM music_files 
				WHERE {' AND '.join(file_conditions)}
			'''
			cursor.execute(file_query_sql, file_params)
			file_matches = [row[0] for row in cursor.fetchall()]
			
			# Search CUE tracks
			cue_conditions = []
			cue_params = []
			for word in words:
				cue_conditions.append('(title LIKE ? OR performer LIKE ?)')
				cue_params.extend([f'%{word}%', f'%{word}%'])
			
			cue_query_sql = f'''
				SELECT audio_file, title, performer, track_number, start_time FROM cue_tracks
				WHERE {' AND '.join(cue_conditions)}
			'''
			cursor.execute(cue_query_sql, cue_params)
			cue_results = cursor.fetchall()
		
		# Format CUE results as "audio_file#track_number" for playback
		for audio_file, title, performer, track_num, start_time in cue_results:
			cue_entry = f"{audio_file}#{track_num}#{start_time}#{title} - {performer}"
			cue_matches.append(cue_entry)
		
		matches = file_matches + cue_matches
		
		conn.close()
		
		if (len(matches) > 0):
			queue_list(matches)
			display_list(matches)
		else:
			print('No matches for:', data)
	except Exception as e:
		print(f'Database search failed: {e}')
		matches = []
#command_query()


def command_info():
	print(config.MUSIC_PATHS)
	print(str(get_total_files()), 'files indexed')
	print(str(len(matches)), 'matches in memory')
#command_info()


# play the given index from the last set of matches
def command_match(index):
	global matches
	index = int(index) - 1  # Convert from 1-based user input to 0-based array index
	if (index >= 0 and index < len(matches)):
		queue_file(matches[index])
		print('Queued:', matches[index])
	else:
		error('match',['No such index',int(index) + 1])  # Show 1-based index in error
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
			config.QUEUE_CLEAR = (value == 'True')
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
	print('Error')
	print(cmd, data)
#error()


## let's go to work
# welcome
subprocess.call("cls", shell=True)

init_database() # initialize database
if (get_total_files() == 0): # check if database has files
	index_files() # create index if database is empty

print('')

## main loop, read input and process
while (1):
	command = str(input("n2unes: "))
	if (parse_command(command) == False):
		break
	print('')
