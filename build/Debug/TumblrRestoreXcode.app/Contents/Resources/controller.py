#
#  controller.py
#  TumblrRestoreXcode
#
#  Created by Hugh & Maddie on 22/06/2011.
#  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
#

from objc import YES, NO, IBAction, IBOutlet
from Foundation import *
from AppKit import *

class controller(NSWindowController):
	
	#Outlets are variables that are directly linked to GUI controls.
	email=IBOutlet()
	password=IBOutlet()
	delete_existing=IBOutlet()
			
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
	
	@IBAction
	def restore_(self,sender):
		print "Delete existing?",self.delete_existing.stringValue()
