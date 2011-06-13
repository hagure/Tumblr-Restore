#!/usr/bin/env python

import os
import sys
import re
from lxml import etree

class BackupParser:
	def __init__(self,backup_dir):
		self.backup_dir=backup_dir
		if not os.path.exists(backup_dir+"/index.html"):
			raise ValueError("Specified Backup Directory Doesn't Exist")
		self.posts_dir=backup_dir+"/posts"

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
				poster=RegularPoster(postelement)
				poster.post()
			else:
				continue
			
			#print postelement.get("id"),postelement.get("type")
			#for element in postelement.xpath("tag"):
			#	print "",element.text,element.tag
			


class PosterBase(object):
	"""Base Class for Post Creating Classes"""
	def __init__(self,postelement):
		self.postelement=postelement
		self.api_base="http://www.tumblr.com/api/write"
		self.parameters={
			'group':'wherenow-gruoptest.tumblr.com',
			'date':postelement.get('date'),
			'format':postelement.get('format'),
			'tags':",".join([tag.text for tag in postelement.xpath('tag')]),
			'send-to-twitter':'no'
		}
	
	def post(self):
		self.add_specific_parameters()
		#result=urllib.urlopen(self.api_base,self.parameters).getcode()
		#print result
		print self.parameters
		

class RegularPoster(PosterBase):
	def __init__(self,postelement):
		super(RegularPoster,self).__init__(postelement)

	def add_specific_parameters(self):
		#self.parameters['title']=self.postelement.xpath('regular-title')[0].text
		self.parameters['body']=self.postelement.xpath('regular-body')[0].text

if __name__=="__main__":
	bp=BackupParser(sys.argv[1])
	bp.parse()

