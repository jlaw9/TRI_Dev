#! /usr/bin/env python

import sys
import os
import re
import json
from optparse import OptionParser
import ast

def runCommandLine(systemCall):
	#run the call and return the status
	print 'Starting %s' % (systemCall)
	status = os.system(systemCall)
	return(status)

# Set up the parser
parser = OptionParser()

parser.add_option('-j', '--json', dest='json', help="The name of the .json file to add info to.")
parser.add_option('-m', '--metric', dest='metrics', action="append", help="info to add to a json file. string is loaded into json so must use JSON format. (See push_Data.sh for an example)")
parser.add_option('-a', '--add_run_to_sample', dest='add_run', action="store_true", help="the run's json file has the path to it's sample's json file. It will copy the sample's json file from the other server and add the run to it.")
parser.add_option('-p', '--push_sample_json', dest='push_sample_json', action="store_true", help="push the sample's json file to the server because it hasn't been copied yet.")
parser.add_option('-s', '--server', dest='server', help="server where the sample's json file is located")

(options, args) = parser.parse_args()

# check to make sure the inputs are valid
if not options.json:
	print "--USAGE-ERROR-- --json is required"
	parser.print_help()
	sys.exit(1)
if not os.path.isfile(options.json): 
	print "--USAGE-ERROR-- %s not found"%options.json
	parser.print_help()
	sys.exit(1)

if options.push_sample_json:
	# load the given json file
	jsonData = json.load(open(options.json))
	# get the name of the sample's json file which should be the last item in the list.
	sample_json_name = jsonData["sample_json"].split("/")[-1]

	# copy the sample's json file here and check if the copy was successful
	copy_command = "scp Json_Files/%s %s:%s "%(sample_json_name, options.server, jsonData["sample_json"])
	if runCommandLine(copy_command) == 0:
		print "Json file copied successfully"
	else:
		print "ERROR: Unable to copy the sample's json file"	
		sys.exit(1)

elif options.add_run:
	# load the given json file
	runJsonData = json.load(open(options.json))
	# get the name of the sample's json file which should be the last item in the list.
	sample_json_name = runJsonData["sample_json"].split("/")[-1]

	# copy the sample's json file here and check if the copy was successful
	copy_command = "scp %s:%s Json_Files/"%(options.server, runJsonData["sample_json"])
	if runCommandLine(copy_command) == 0:
		sampleJsonData = json.load(open("Json_Files/"+sample_json_name))

		# append the current run to this sample's list of runs.
		sampleJsonData['runs'].append(runJsonData['json_file'])
		
		# set the status to 'pending' so that the runs will be QCd together.
		sampleJsonData['status'] = 'pending'
		
		# dump the json file
		with open("Json_Files/"+sample_json_name, 'w') as out:
			json.dump(sampleJsonData, out, sort_keys=True, indent = 2)

		# copy the edited sample's json file back to the server
		copy_command = "scp Json_Files/%s %s:%s "%(sample_json_name, options.server, runJsonData["sample_json"])
		runCommandLine(copy_command)	
	else:
		print "ERROR: Unable to copy the sample's json file"	
		sys.exit(1)
	

elif options.metrics:
	# load the given json file
	jsonData = json.load(open(options.json))
	for metric in options.metrics:
		print "Adding/updating " + metric + " to the json data."
		# Union the two dictionaries together. If a field is found in both dictionaries, then whatever's in extraJson will overwrite what is in jsonData.
		# Example: dict1 = { "a":1, "b": 2}		dict2 = { "b":3, "c": 4}  dict(dict1.items() + dict2.items()) 	{'a': 1, 'c': 4, 'b': 3}
		try:
			newData = json.loads(metric)
			jsonData = dict(jsonData.items() + newData.items())
		except ValueError:
			print "Unable to load the string %s into JSON"%metric

	# dump the json file
	with open(options.json, 'w') as out:
		json.dump(jsonData, out, sort_keys=True, indent = 2)
