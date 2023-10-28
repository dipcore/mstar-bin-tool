import sys
import os
import re
import shutil
import subprocess

import utils

# Vars
DEBUG = False

# Parse args
if len(sys.argv) == 1: 
	print ("Usage: extract.py <firmware> <output folder [default: ./unpacked/]>")
	quit()

inputFile = sys.argv[1]
if not os.path.exists(inputFile):
	print ("No such file: {}".format(inputFile))
	quit()

if len(sys.argv) == 3:
	outputDirectory = sys.argv[2]
else:
	outputDirectory = 'unpacked'

subprocess.run("unpack.py {} {}".format(inputFile, outputDirectory), shell=True)

if not os.path.exists(outputDirectory):
	print ("No such folder: {}".format(outputDirectory))
	quit()

files = os.listdir(outputDirectory) 
images = filter(lambda x: x.endswith('.img'), files)
for img in images:
	path = os.path.join(outputDirectory, os.path.splitext(img)[0])
	os.mkdir(path)
	utils.unpackImg(os.path.join(outputDirectory, img), path)
