#!/usr/bin/env python

import os, sys, re, random, glob
import urllib, urllib2, cookielib
import copy, Queue
from threading import Thread
from optparse import OptionParser
from lxml import etree
from lib import MultipartPostHandler

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
			,'quote':QuotePost
			,'photo':PhotoPost
			,'conversation':ConversationPost
			,'audio':AudioPost
			,'video':VideoPost
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
		posts=[]
		for filename in os.listdir(self.posts_dir):
			xml_string=self.extract_xml_string(self.posts_dir+"/"+filename)
			postelement=etree.fromstring(xml_string)
			posttype=postelement.get('type')
			if self.post_types.has_key(posttype):
				posts.append(self.post_types[posttype](postelement,self.options))
		self.tumblog.post_many(posts)

class Tumblog(object):
	def __init__(self,options):
		self.options=options
		self.parameters={
			'email':self.options.email
			,'password':options.password
			,'generator':'github.com/hughsaunders/Tumblr-Restore'
			,'group':options.tumblog
		}
		self.post_chunk=50
	
	def get_existing_posts(self):
		posts=[]
		while True:
			chunk=self.get_chunk_of_posts(len(posts))
			posts+=chunk
			if len(chunk)<self.post_chunk:
				break
		self.options.ui.message(str(len(posts))+' existing posts')
		return posts
			
	def get_chunk_of_posts(self,start):
		existing_posts=urllib.urlopen("http://"+self.options.tumblog+"/api/read?num="+str(self.post_chunk)+"&start="+str(start)+"&random="+str(int(random.random()*10000000000000000)))
		existing_posts=etree.parse(existing_posts)
		return [element.get('id') for element in existing_posts.xpath('posts/post')]

	def delete_post(self,post_id):
		local_parameters=copy.copy(self.parameters)
		local_parameters['post-id']=post_id
		result = urllib.urlopen(self.options.api_base+'/delete',urllib.urlencode(local_parameters))
		self.options.ui.message("Deleteing "+str(post_id))

	def worker(self,q,task):
		while q._qsize()>0:
			item=q.get()
			task(item)
			q.task_done()

	def do_parallel(self,q,task):
		self.options.ui.message("Starting parallel task: "+str(task)+" "+str(q._qsize())+" items")
		for i in range(self.options.num_threads):
			thread=Thread(target=self.worker, args=(q,task))
			thread.start()
		q.join()
		self.options.ui.message("Parallel Task Complete")
	
	def delete_all_posts(self):
		q=Queue.Queue()
		for post_id in self.get_existing_posts():
			q.put(post_id)
		self.do_parallel(q,self.delete_post)
		

	def post_many(self,posts):
		q=Queue.Queue()
		for post in posts:
			q.put(post)
		self.do_parallel(q,self.post)

	def post(self,post):
		post.add_specific_parameters()
		post.parameters.update(self.parameters)
		cookies=cookielib.CookieJar()
		opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
				MultipartPostHandler.MultipartPostHandler)
		self.options.ui.message("starting upload")
		result=opener.open(self.options.api_base+'/write',(post.parameters))
		self.options.ui.message("upload done")
		self.options.ui.message("Post Creation Result: "+str(result.getcode())+' new post id: '+result.readline())

class Post(object):
	"""Base Class for Post Creating Classes"""
	def __init__(self,postelement,options):
		self.postelement=postelement
		self.options=options
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
	
	def download_file(self,url):
		return urllib.urlopen(url).read()	

	
class RegularPost(Post):
	def __init__(self,postelement,options):
		super(RegularPost,self).__init__(postelement,options)

	def add_specific_parameters(self):
		self.add_param('regular-title','title')
		self.add_param('regular-body','body')

class LinkPost(Post):
	def __init__(self,postelement,options):
		super(LinkPost,self).__init__(postelement,options)

	def add_specific_parameters(self):
		self.add_param('link-text','name')
		self.add_param('link-url','url')
		self.add_param('link-description','description')

class PhotoPost(Post):
	def __init__(self,postelement,options):
		super(PhotoPost,self).__init__(postelement,options)
		self.photos=[]	

	def add_specific_parameters(self):
		self.add_param('photo-caption','caption')
		self.add_param('photo-link-url','click-through-url')
		postid=self.postelement.get('id')
		self.parameters['data']=open(glob.glob(self.options.backup_dir+'/images/'+postid+'*')[0],'rb').read()
		

class QuotePost(Post):
	def __init__(self,postelement,options):
		super(QuotePost,self).__init__(postelement,options)

	def add_specific_parameters(self):
		self.add_param('quote-text','quote')
		self.add_param('quote-source','source')

class ConversationPost(Post):
	def __init__(self,postelement,options):
		super(ConversationPost,self).__init__(postelement,options)

	def add_specific_parameters(self):
		self.add_param('conversation-title','title')
		self.add_param('conversation-text','conversation')

class AudioPost(Post):
	def __init__(self,postelement,options):
		super(AudioPost,self).__init__(postelement,options)

	def add_specific_parameters(self):
		self.add_param('audio-caption','caption')
		postid=self.postelement.get('id')
		self.parameters['data']=open(glob.glob(self.options.backup_dir+'/audio/'+postid+'*')[0],'rb').read()

class VideoPost(Post):
	def __init__(self,postelement,options):
		super(VideoPost,self).__init__(postelement,options)

	def add_specific_parameters(self):
		self.add_param('video-caption','caption')
		self.add_param('video-source','embed')

class UI(object):
	"""Base class for UIs"""

	def __init__(self):
		pass

	def start(self):
		self.message("Tumblr Restore")
		self.options=self.get_options()
		self.options.ui=self
		tumblog=Tumblog(self.options)
		if self.options.delete: 
			tumblog.delete_all_posts()
		bp=BackupParser(self.options,tumblog)
		bp.parse()
		self.message("Tumblr Restore Complete")
	
	def get_options(self):
		pass	

	def message(self,message):
		pass

class CLI(UI):
	"""Command Line Interface"""
	def get_options(self):
		parser=OptionParser()
		parser.add_option("-b","--backupdir",dest="backup_dir",help="Path to directory which contains your tumblr backup. Should include index.html and a 'posts' subdirectory",metavar="DIR")
		parser.add_option("-p","--password",dest="password",help="Tumblr password")
		parser.add_option("-e","--email",dest="email",help="Tumblr email")
		parser.add_option("-t","--tumblog",dest="tumblog",help="Tumblog to act on.",metavar="foo.tumblr.com")
		parser.add_option("-d","--delete",dest="delete",action="store_true",help="clear existing posts before uploading")
		parser.add_option("-a","--api",dest="api_base",help="Base of Api url (default=http://www.tumblr.com/api)",default="http://www.tumblr.com/api")
		parser.add_option("-n","--numthreads",dest="num_threads",help="Number of items to upload/delete simultaneously. Default=5, 10 causes API rate limit errors for me.",default=5)
		options,args=parser.parse_args()
		if not (options.password and options.email and options.backup_dir and options.tumblog):
			parser.print_help()
			sys.exit(1)
		return options
	
	def message(self,message):
		print message
	

if __name__=="__main__":
	cli=CLI()
	cli.start()
