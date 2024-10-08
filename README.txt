# STEP-0: update credentials file
[credentials]

# STEP-1: install and start Docker
https://www.docker.com/get-started/

# STEP-2: build docker image from Dockerfile
docker build . -t picklebot

# STEP-3: start docker containers as desired
docker run --rm --name="picklebot-1" -e --run=07:00:00 -e day=3 -e time=20:00:00 -e duration="2 Hours" -e court="John Simpson 1" picklebot
docker run --rm --name="picklebot-2" -e --run=07:00:05 -e day=3 -e time=20:00:00 -e duration="2 Hours" -e court="John Simpson 2" picklebot

# OPTIONS:
-e --run	: What time to run (3 days prior)(HH:MM:SS)(24 Hour Format)(default="07:00:00")
-e --day	: What day to reserve (Mon(0) - Sun(6))(default=3)
-e --time	: What time to reserve (HH:MM:SS)(24 Hour Format)(default="20:00:00")
-e --duration	: Duration to reserve (30 Minutes, 60 Minutes, 90 Minutes, 2 Hours)(default="2 Hours")
-e --court	: What court to reserve (default="John Simpson 1")

# NOTES:
* containers can be viewed in docker desktop (logs, files, etc) while running
* add --rm to delete container after completion (if not you will have to manually delete or restart the container to run again)
* add -d to run in background

# APPENDIX-A: run picklepot.py locally
python3 picklebot.py -r=07:00:00 -d=3 -t=20:00:00 -u="2 Hours" -c="John Simpson 1"
python3 picklebot.py -r=07:00:05 -d=3 -t=20:00:00 -u="2 Hours" -c="John Simpson 2"

# APPENDIX-B: copy picklebot.py changes to desired container
docker cp .\picklebot.py picklebot-1:/app
docker cp .\picklebot.py picklebot-2:/app

# APPENDIX-C: export contents of container to view logs, screenshots, etc.
docker export -o picklebot-1.tar picklebot-1
docker export -o picklebot-2.tar picklebot-2
