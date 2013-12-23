#!/usr/bin/python

# Copyright 2013 inBloom, Inc. and its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and

import json, sys, csv, re
import glob
import argparse
import cStringIO
import datetime
import md5
import time
import os

# Known date formats, add any format you encounter in inputs
# http://docs.python.org/2/library/datetime.html
date_formats = ["%m/%d/%y", "%m-%d-%y"]

def write_json_file(json_string, file_path):
	"""
	Write json string to file
	"""
	print file_path
	try:
		f = open(file_path, 'w+')
		f.write(json_string)
	except IOError, e:
		print >>sys.stderr,e
		exit(e.errno)

def strip_list_values(array):
	"""
	trims all values in a list
	"""
	for index in range(len(array)):
		try:
			array[index] = array[index].strip()
		except:
			array[index] = strip_list_values(array[index])
	return array


def process_json_list(array):
	"""
	transforms values to lists
	"""
	for index in range(len(array)):
		array[index] = array[index].split(',')
	return array

def process_multi_level_field(string):
	return string.split('_')

"""Format dates"""
def format_date(value):
	if value == '':
		return value
	new_date = False
	for i, format in enumerate(date_formats):
		try:
			ts = time.mktime(datetime.datetime.strptime(str(value), format).timetuple())
			new_date = datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d')
			# Found! return it
			return new_date
		except:
			pass
	# Cannot convert! return original value
	return value

def make_json(row, heading, ignored, context=True):
	"""
	converts a string line into JSON
	"""
	row = process_json_list(row)
	row = strip_list_values(row)

	"""Computes the entry key"""
	m = md5.new()
	m.update(row[0][0])
	filekey = m.hexdigest()

	"""Initialize JSON Object"""
	json_dict = {\
		"@context": [
			{ 
			"url": { "@type": "@id" },
			"@vocab": "http://schema.org/"
			},
			{
				"lrmi": "http://lrmi.net/the-specification#",
				"useRightsUrl": { "@id": "lrmi:useRightsUrl", "@type": "@id" }
			},
		],
		"@type": "CreativeWork",\
	}
	if not context:
		json_dict = {}

	"""Browse fields"""
	for i, field_name in enumerate(heading):
		"""Simple elements"""
		if len(row[i]) == 1:
			row[i] = row[i][0]
			if re.search('date', field_name, flags=re.IGNORECASE):
				row[i] = format_date(row[i])
		if hasattr(row[i], '__iter__') and field_name in ignored:
			row[i] = ','.join(row[i])
		"""Do not output anything if heading or value is empty"""
		if field_name == "" or row[i] == "":
			continue
		if field_name.find('_') != -1:
			field_list = process_multi_level_field(field_name)
			if field_list[0] not in json_dict:
				json_dict[field_list[0]] = {}
			json_dict[field_list[0]][field_list[1]] = row[i]
		else:
			"""Append element"""
			json_dict[field_name] = row[i]
	
	return [filekey, json_dict]
	
			
def append_standards(row, heading, json_file, ignored):
	"""
	parses "row" and appends it as an educationalAlignment object in appropriate file" if exists!
	"""
	
	"""Parse the Json file"""
	json_data = open(json_file)
	json_dict = json.load(json_data)
	json_data.close()	
	
	"""make the AlignmentObject json object"""
	
	ao_json = make_json(row, heading, ignored, False)[1]
	ao_json['@type'] = "AlignmentObject"
	del ao_json['url']
	
	"""Insert the object"""
	if "AlignmentObject" not in json_dict:
		json_dict["AlignmentObject"] = []
	json_dict["AlignmentObject"].append(ao_json)
	
	write_json_file(json.dumps(json_dict, indent=4, sort_keys=True), json_file)


def csv2json(csvfile, ignored):
	"""
	creates JSON files from a given CSV file
	"""
	try:
		file_handle = open(csvfile,'rU')
		reader = csv.reader(file_handle, dialect='excel')
		
		try:
			for i, row in enumerate(reader):
				"""get heading"""
				if i == 0:
					heading = row
				else:
					try:
						json_list = make_json(row, heading, ignored)
						json_dict = json_list[1]
						file_path = json_list[0]+".json"
						directory = 'data'
						if not os.path.exists(directory):
							os.makedirs(directory)
						file_path = os.path.join(directory,file_path)
						write_json_file(json.dumps(json_dict, indent=4, sort_keys=True), file_path)
					except IndexError, e:
						print >>sys.stderr,"Invalid row:",i
						print >>sys.stderr,e
		except IOError, e:
			print >>sys.stderr, e
			
			exit(-1)
			

	except IOError, e:
		print >>sys.stderr,e
		exit(e.errno)

def find_json_file_from_standard(key_field, value, json_files):
	"""
	Given a link key for a standard, the appropriate json file name is returned
	returns false if no file matches
	"""
	for index, json_file in enumerate(json_files):
		try:
			json_data = open(json_file)
			json_dict = json.load(json_data)
			json_data.close()	
		except IOError, e:
			print >>sys.stderr, e
		if json_dict[key_field] == value:
			return json_file
	
	return False


def addstandards(standards, ignored):
	"""
	import a CSV file with standards to fill the educationalAlignment object 
	in the already created JSON files using the -f command"
	"""
	
	"""index all output JSON files"""
	json_files={}
	json_files = glob.glob(os.path.join("data", "*.json"))
		
	try:
		file_handle = open(standards,'rU')
		reader = csv.reader(file_handle, dialect='excel')
		
		try:
			for i, row in enumerate(reader):
				"""get heading"""
				if i == 0:
					heading = row
				else:
					try:
						found_json = find_json_file_from_standard(heading[0], row[0], json_files)
						if found_json:
							append_standards(row, heading, found_json, ignored)
					except IndexError, e:
						print >>sys.stderr,"Invalid row:",i
						print >>sys.stderr,e
		except IOError, e:
			print >>sys.stderr, e
			

	except IOError, e:
		print >>sys.stderr,e
		exit(e.errno)

if __name__ == '__main__':
	"""Parse command line"""
	parser = argparse.ArgumentParser(description='CSV to JSON LD.')
	parser.add_argument('-i', '--items', dest='csvfile', help="import a CSV file into separate JSON files named file1, file2, ....")
	parser.add_argument('-s', '--standards', dest='standards', help="import a CSV file with standards to fill the educationalAlignment object in the already created JSON files using the -f command")
	parser.add_argument('-g', '--ignore-columns', dest='columns', nargs='+', help="Ignore field level comma delimited array creation for given fields (separated by a space)")

	try:
		args = parser.parse_args()
	except Exception as e:
		print >>sys.stderr, '', e
		exit(-2)

	"""Ignore field level comma delimited array creation for given fields"""
	if args.columns:
		ignored = args.columns
	else:
		ignored = []
		
	if args.csvfile and not args.standards:
		csv2json(args.csvfile, ignored)
	elif not args.csvfile and args.standards:
		addstandards(args.standards, ignored)
	else:
		print >>sys.stderr, 'Either -c OR -s has to be specified!\n',
		parser.print_help()

