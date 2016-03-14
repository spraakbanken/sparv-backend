#!/bin/bash

#
# This script is only for local testing. A proper installation uses some wsgi
# handler, such as mod_wsgi for apache.
#
# If eventlet is installed, it will be used and handle concurrent requests.
#

while true
do
	python index.wsgi &
	PID=$!
	inotifywait * -e modify
	kill $PID
done
