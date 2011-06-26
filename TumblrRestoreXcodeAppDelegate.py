#
#  TumblrRestoreXcodeAppDelegate.py
#  TumblrRestoreXcode
#
#  Created by Hugh & Maddie on 20/06/2011.
#  Copyright __MyCompanyName__ 2011. All rights reserved.
#

from Foundation import *
from AppKit import *

class TumblrRestoreXcodeAppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, sender):
        NSLog("Application did finish launching.")
