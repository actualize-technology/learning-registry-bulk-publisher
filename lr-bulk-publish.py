#!/usr/bin/python

import argparse
import datetime
import glob
import json
import oauth2 as oauth
import os
import re
import sys
import time
import urllib
 
# Sample publish to LR Sandbox using OAuth
 
_netloc = "sandbox.learningregistry.org"
_testing_url = "https://%s/auth/oauth_verify" % _netloc
_publish_url = "https://%s/publish" % _netloc
_obtain_url = "https://%s/obtain?by_doc_ID=true&request_ID=%s"
 
# Go to https://sandbox.learningregistry.org/auth to create a publishing account,
# Replace the Consumer and Token keys and secrets below with the ones generated there.

# *** NOTE:  Also modify Learning Registry submitter information near Line 95 below

_consumer = {
	"key": "CONSUMER_KEY",
	"secret": "CONSUMER_SECRET"
}
 
_token = {
	"key": "TOKEN_KEY",
	"secret": "TOKEN_SECRET"
}

"""To disable STDERR and STDOUT"""
class NullDevice():
    def write(self, s):
        pass

"""To copy STDOUT to a file"""
class Logger(object):
    def __init__(self):
        self.file = open(str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))+'.log', 'a')
        self.stdout = sys.stdout
        sys.stdout = self
    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

"""Retuns keywords if file is JSON"""
def get_json_keywords(json_dict):
	try:
		if 'keywords' in json_dict:
			return json_dict['keywords']
	except Exception, e:
		return False
		
	return False

"""Test oauth using creds,
return oauth cleint object if success, False else"""
def oauth_creds(no_check_certificate = True):
	# Create your consumer with the proper key/secret.
	consumer = oauth.Consumer(key=_consumer["key"], secret=_consumer["secret"])
	token = oauth.Token(key=_token["key"], secret=_token["secret"])
	# Create our client.
	client = oauth.Client(consumer, token=token)
	# we only need to do this because Sandbox uses a self-signed SSL cert that is untrusted. This should not be needed on production.
	client.disable_ssl_certificate_validation = no_check_certificate
	try:
		print >>sys.stderr, "Authenticating..."
		resp, content = client.request(
							_testing_url, 
							"POST", 
							body="", 
							headers={"Content-Type": "application/json"}
						)
		content_json = json.loads(content)
		if content_json['status'] == 'Okay':
			print >>sys.stderr, "status : Okay"
			return client
		else:
			print >>sys.stderr, "Error authenticating with the Learning Registry."
			print >>sys.stderr, "status:", content_json['status']
			if 'detail' in content_json:
				print >>sys.stderr, "detail:", content_json['detail']
			return False
	except Exception, e:
		print >>sys.stderr, e
		return False
	

"""Publish document using OAuth node signing"""
def publish_document(client, file_handle):
	# Resource data document templete
	rdt = {
		"doc_type": "resource_data",
		"doc_version": "0.23.0",
		"active": True,
		"resource_data_type": "metadata",
		"resource_locator": "http://example.com/oauth-sample/resource",
		"keys": [ ],
		"payload_placement": "inline",
		"payload_schema": [ "LRMI", "JSON-LD" ],
		"resource_data": "",
		"TOS": {
			"submission_TOS": "http://www.learningregistry.org/information-assurances/open-information-assurances-1-0"
		},
		"identity": { 
			"signer": "Person or Organization",
			"submitter": "Person or Organization",
			"submitter_type": "user"
		}
	}
	resource_doc = rdt

	try:
		with file_handle as fh:
			data = json.load(fh)
			resource_doc['resource_data'] = data
			keywords = get_json_keywords(data)
	except Exception as e:
		message = ['failure', 'NULL', os.path.basename(file_handle.name), 'NULL', 'NULL', str(e)]
		print ','.join(message)
		return False

	#print >>sys.stderr, "*******", keywords, "*******" # Debug
	if keywords:
		if "keys" not in resource_doc:
			resource_doc['keys'] = []
		resource_doc['keys'].extend(keywords)
	
	resp, content = client.request(
						_publish_url, 
						"POST", 
						body=json.dumps({"documents": [resource_doc]}), 
						headers={"Content-Type": "application/json"}
					)
	content_json = json.loads(content)

	if content_json['document_results'][0]['OK']:
		doc_ID = content_json['document_results'][0]['doc_ID']
		message = ['success', doc_ID, os.path.basename(file_handle.name), _obtain_url%(_netloc, doc_ID), data['url']]
	else:
		message = ['failure', 'NULL', os.path.basename(file_handle.name), 'NULL', 'NULL', content_json['document_results'][0]['error']]

	print ','.join(message)	
	return False

 
if __name__ == '__main__':
	"""Parse command line"""
	parser = argparse.ArgumentParser(description='JSON File Bulk Submission Script')
	requiredarguments = parser.add_argument_group('Required Arguments', '')
	requiredarguments.add_argument('-i', '--input-files' , dest='files', nargs='+', type=file, required=True, help="List of input files, wildcards accepted")
	parser.add_argument('-q', '--quiet', dest='quiet', action='store_true', help="Silent mode")
	#parser.add_argument('-n', '--no-check-certificate', dest='no_check_certificate', action='store_true', help="Don't check the server certificate against the available certificate authorities. Also don't require the URL host name to match the common name presented by the certificate.")

	try:
		args = parser.parse_args()
	except Exception as e:
		print >>sys.stderr, '', e
		exit(-2)
	"""Quiet mode"""
	if args.quiet:
		sys.stdout = NullDevice()
		sys.stderr = NullDevice()
	"""Initialize logging"""
	sys.stdout = Logger()
	"""Preauthenticate"""
	client = oauth_creds()
	if client:
		print >>sys.stderr, "Publishing input files..."
		for i, fh in enumerate(args.files):
			publish_document(client,fh)



