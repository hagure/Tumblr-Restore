#!/usr/bin/env python

import os
import sys
import re
import urllib
from optparse import OptionParser
from lxml import etree

class BackupParser(object):
	def __init__(self,options):
		self.options=options
		if not os.path.exists(options.backup_dir+"/index.html"):
			raise ValueError("Specified Backup Directory Doesn't Exist")
		self.posts_dir=options.backup_dir+"/posts"

	def extract_xml_string(self,filename):
		file = open(filename,'r')
		lines=file.readlines()
		begin_line=0
		end_line=0
		begin_re=re.compile("<\?xml version=.* encoding=\"UTF-8\"")
		end_re=re.compile("END TUMBLR XML")
		for i in range(0,len(lines)):
			line=lines[i]
			if begin_re.search(line):
				begin_line=i+1
				continue
			if end_re.search(line):
				end_line=i
				break
		lines[begin_line]=lines[begin_line].lstrip()
		return "\n".join(lines[begin_line:end_line])
		
	def parse(self):
		for filename in os.listdir(self.posts_dir):
			xml_string=self.extract_xml_string(self.posts_dir+"/"+filename)
			postelement=etree.fromstring(xml_string)
			posttype=postelement.get('type')
			if posttype == "regular":
				poster=RegularPoster(postelement,self.options)
				poster.post()
			else:
				continue
			
			#print postelement.get("id"),postelement.get("type")
			#for element in postelement.xpath("tag"):
			#	print "",element.text,element.tag
			


class PosterBase(object):
	"""Base Class for Post Creating Classes"""
	def __init__(self,postelement,options):
		self.postelement=postelement
		self.api_base="http://www.tumblr.com/api/write"
		self.parameters={	
			'email':options.email,
			'password':options.password,
			'date':postelement.get('date'),
			'format':postelement.get('format'),
			'tags':",".join([tag.text for tag in postelement.xpath('tag')]),
			'send-to-twitter':'no',
			'generator':'github.com/hughsaunders/Tumblr-Restore'
		}
		if options.group:
			self.parameters['group']=options.group
	
	def post(self):
		self.add_specific_parameters()
		print self.parameters

		result=urllib.urlopen(self.api_base,urllib.urlencode(self.parameters))
		print result.getcode()
		for line in result:
			print line
		

class RegularPoster(PosterBase):
	def __init__(self,postelement,options):
		super(RegularPoster,self).__init__(postelement,options)

	def add_specific_parameters(self):
		title_elements=self.postelement.xpath('regular-title')
		if len(title_elements) > 0:
			self.parameters['title']=title_elements[0].text.encode('utf-8')
		self.parameters['body']=self.postelement.xpath('regular-body')[0].text.encode('utf-8')
		self.parameters['type']="regular"

if __name__=="__main__":
	parser=OptionParser()
	parser.add_option("-b","--backupdir",dest="backup_dir",help="Path to directory which contains your tumblr backup. Should include index.html and a 'posts' subdirectory",metavar="DIR")
	parser.add_option("-p","--password",dest="password",help="Tumblr password")
	parser.add_option("-u","--email",dest="email",help="Tumblr email")
	parser.add_option("-g","--group",dest="group",help="Tumblr group blog to post to")
	options,args=parser.parse_args()
	if not (options.password and options.email and options.backup_dir):
		parser.print_help()
		sys.exit(1)
	bp=BackupParser(options)
	bp.parse()

