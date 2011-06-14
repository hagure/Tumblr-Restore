#!/usr/bin/env python

import os
import sys
import re
import urllib
import copy
from optparse import OptionParser
from lxml import etree

class BackupParser(object):
	def __init__(self,options,tumblog):
		self.options=options
		self.tumblog=tumblog
		if not os.path.exists(options.backup_dir+"/index.html"):
			raise ValueError("Specified Backup Directory Doesn't Exist")
		self.posts_dir=options.backup_dir+"/posts"
		self.post_types={
			'link':LinkPost
			,'regular':RegularPost
		}

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
			if self.post_types.has_key(posttype):
				self.tumblog.post(self.post_types[posttype](postelement))

class Tumblog(object):
	def __init__(self,options):
		self.options=options
		self.parameters={
			'email':self.options.email
			,'password':options.password
			,'generator':'github.com/hughsaunders/Tumblr-Restore'
			,'group':options.tumblog
		}
	
	def get_existing_posts(self):
		existing_posts=urllib.urlopen("http://"+self.options.tumblog+"/api/read")
		existing_posts=etree.parse(existing_posts)
		return [element.get('id') for element in existing_posts.xpath('posts/post')]

	def delete_post(self,post_id):
		local_parameters=copy.copy(self.parameters)
		local_parameters['post-id']=post_id
		result = urllib.urlopen(self.options.api_base+'/delete',urllib.urlencode(local_parameters))
		print "Deleteing",post_id,result
	
	def delete_all_posts(self):
		for post_id in self.get_existing_posts():
			self.delete_post(post_id)

	def post(self,post):
		post.add_specific_parameters()
		post.parameters.update(self.parameters)
		result=urllib.urlopen(self.options.api_base+'/write',urllib.urlencode(post.parameters))
		print result.getcode()
		for line in result:
			print line

class Post(object):
	"""Base Class for Post Creating Classes"""
	def __init__(self,postelement):
		self.postelement=postelement
		self.parameters={	
			'date':postelement.get('date')
			,'format' : postelement.get('format')
			,'slug' : postelement.get('slug')
			,'tags' : ",".join([tag.text for tag in postelement.xpath('tag')])
			,'type' :  postelement.get('type')
			,'send-to-twitter' : 'no'
		}

	def add_param(self,xpath,parameter):
		elements=self.postelement.xpath(xpath)
		if len(elements)>0:
			self.parameters[parameter]=elements[0].text.encode('utf-8')

	
class RegularPost(Post):
	def __init__(self,postelement):
		super(RegularPost,self).__init__(postelement)

	def add_specific_parameters(self):
		print self.postelement.get("type")
		title_elements=self.postelement.xpath('regular-title')
		if len(title_elements) > 0:
			self.parameters['title']=title_elements[0].text.encode('utf-8')
		self.parameters['body']=self.postelement.xpath('regular-body')[0].text.encode('utf-8')

class LinkPost(Post):
	def __init__(self,postelement):
		super(LinkPost,self).__init__(postelement)

	def add_specific_parameters(self):
		self.add_param('link-text','name')
		self.add_param('link-url','url')
		self.add_param('link-description','description')

if __name__=="__main__":
	parser=OptionParser()
	parser.add_option("-b","--backupdir",dest="backup_dir",help="Path to directory which contains your tumblr backup. Should include index.html and a 'posts' subdirectory",metavar="DIR")
	parser.add_option("-p","--password",dest="password",help="Tumblr password")
	parser.add_option("-u","--email",dest="email",help="Tumblr email")
	parser.add_option("-t","--tumblog",dest="tumblog",help="Tumblog to act on eg foo.tumblr.com")
	parser.add_option("-d","--delete",dest="delete",action="store_true",help="clear existing posts before uploading")
	parser.add_option("-a","--api",dest="api_base",help="Base of Api url (default=http://www.tumblr.com/api)",default="http://www.tumblr.com/api")
	options,args=parser.parse_args()
	if not (options.password and options.email and options.backup_dir and options.tumblog):
		parser.print_help()
		sys.exit(1)
	tumblog=Tumblog(options)
	if options.delete: tumblog.delete_all_posts()
	bp=BackupParser(options,tumblog)
	bp.parse()

