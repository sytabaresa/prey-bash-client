#!/usr/bin/python2.5
# encoding: utf-8
#######################################################
# Prey Mac Network Trigger - (c) 2011 Fork Ltd.
# Written by Tomas Pollak <tomas@forkhq.com>
# Based on the SysConfig section of crankd.py
# Licensed under the GPLv3
#######################################################

# import signal
import os
import sys
# import logging
import subprocess
from datetime import datetime, timedelta
from PyObjCTools import AppHelper

from SystemConfiguration import \
    SCDynamicStoreCreate, \
    SCDynamicStoreCreateRunLoopSource, \
    SCDynamicStoreSetNotificationKeys

from Cocoa import \
	CFAbsoluteTimeGetCurrent, \
	CFRunLoopAddSource,  \
	CFRunLoopGetCurrent, \
	CFRunLoopAddTimer, \
	CFRunLoopTimerCreate, \
	NSRunLoop, \
	kCFRunLoopCommonModes

min_interval = 2 # minutes
log_file = "/var/log/prey.log"
prey_command = "/usr/share/prey/prey.sh -i"

try:
   log_output = open(log_file, 'wb')
except IOError:
   print "No write access to log file: " + log_file + ". Prey log will go to /dev/null!"
   log_output = open('/dev/null', 'w')

#######################
# helpers
#######################

def connected(interface):
	return subprocess.call(["ipconfig", "getifaddr", interface]) == 0

# only for testing purposes
def log(message):
	# subprocess.call(["/usr/bin/osascript", "-e", "say", message, "using", "Zarvox"])
	if sys.argv[1] and sys.argv[1] == '--debug':
		os.popen("osascript -e 'say \"" + message + "\"' using Zarvox")

def run_prey():
    global run_at
    log("Should we run Prey?")
    two_minutes = timedelta(minutes=min_interval)
    now = datetime.now()
    if (run_at is None) or (now - run_at > two_minutes):
        log("Running Prey")
        subprocess.Popen(prey_command.split(), stdout=log_output, stderr=subprocess.STDOUT, shell=True)
        run_at = datetime.now()


#######################
# event handlers
#######################

def network_state_changed(*args):
	log("Network change detected")
	if connected('en0') or connected('en1'):
		run_prey()

def timer_callback(*args):
	"""Handles the timer events which we use simply to have the runloop run regularly. Currently this logs a timestamp for debugging purposes"""
	# logging.debug("timer callback at %s" % datetime.now())

#######################
# main
#######################

if __name__ == '__main__':
	
	log("Initializing")
	run_at = None
	run_prey()

	sc_keys = [ 
		'State:/Network/Global/IPv4', 
		'State:/Network/Global/IPv6'
	]

	store = SCDynamicStoreCreate(None, "global-network-change", network_state_changed, None)
	SCDynamicStoreSetNotificationKeys(store, None, sc_keys)

	CFRunLoopAddSource(
		# NSRunLoop.currentRunLoop().getCFRunLoop(),
		CFRunLoopGetCurrent(), 
		SCDynamicStoreCreateRunLoopSource(None, store, 0), 
		kCFRunLoopCommonModes
	)

	# signal.signal(signal.SIGINT, stop_loop)
	# signal.signal(signal.SIGHUP, partial(quit, "SIGHUP received"))

	# NOTE: This timer is basically a kludge around the fact that we can't reliably get
	#       signals or Control-C inside a runloop. This wakes us up often enough to
	#       appear tolerably responsive:
	CFRunLoopAddTimer(
	    NSRunLoop.currentRunLoop().getCFRunLoop(),
	    CFRunLoopTimerCreate(None, CFAbsoluteTimeGetCurrent(), 2.0, 0, 0, timer_callback, None),
	    kCFRunLoopCommonModes
	)

	try:
	    AppHelper.runConsoleEventLoop(installInterrupt=True)
	except KeyboardInterrupt:
	    print "KeyboardInterrupt received, exiting"

	sys.exit(0)
