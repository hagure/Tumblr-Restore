#
#  controller.py
#  TumblrRestoreXcode
#
#  Created by Hugh Saunders on 22/06/2011.
#  Copyright (c) 2011. All rights reserved.
#

from objc import YES, NO, IBAction, IBOutlet
from Foundation import *
from AppKit import *
from tumblrRestore.tumblrRestore import *

class Options:pass

class CocoaUI(UI):
	pass


class controller(NSWindowController):
	def __init__(self):
		options=Options()
		options.api_base="http://www.tumblr.com/api"
		options.num_threads=5
		options.u


	
	#Outlets are variables that are directly linked to GUI controls.
	email=IBOutlet()
	password=IBOutlet()
	delete_existing=IBOutlet()
	log=IBOutlet()
			
	@IBAction
	def selectBackupDir_(self,sender):
		panel = NSOpenPanel.openPanel()
		panel.setCanChooseFiles_(NO)
		panel.setCanChooseDirectories_(YES)
		panel.setAllowsMultipleSelection_(NO)
		panel.runModal()
		self.dir=panel.filename()
		print "Backup Dir Selected",self.dir
		
	@IBAction
	def login_(self,sender):
		print "Username:",self.email.stringValue()
		print "Password:",self.password.stringValue()
		print self.log.setString_(self.log.textStorage().mutableString()+"foo\n")
	
	@IBAction
	def restore_(self,sender):
		print "Delete existing?",self.delete_existing.stringValue()
