#
#  main.py
#  TumblrRestoreXcode
#
#  Created by Hugh & Maddie on 20/06/2011.
#  Copyright __MyCompanyName__ 2011. All rights reserved.
#

#import modules required by application
import objc
import Foundation
import AppKit
import controller

from PyObjCTools import AppHelper

# import modules containing classes required to start application and load MainMenu.nib
import TumblrRestoreXcodeAppDelegate

import tumblrRestore

# pass control to AppKit
AppHelper.runEventLoop()
