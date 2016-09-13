import sys
import os
import re
import shutil
from subprocess import call

import tools

DEBUG = False
HEADER_SIZE = 16 * tools.KB # Header size is always 16KB

# Vars
headerScript = ""
headerScriptFound = False
counter = {};

# Parse args
if len(sys.argv) == 1: 
	print "Usage: unpack.py <Firmware> <Output folder [default: ./unpacked/]>"
	quit()

inputFile = sys.argv[1]
if not os.path.exists(inputFile):
	print "No such file: %s" % inputFile
	quit()

if len(sys.argv) == 3:
	outputDirectory = sys.argv[2]
else:
	outputDirectory = 'unpacked'

# Create output directory
tools.createDirectory(outputDirectory)

# Find header script
# Header size is 16KB
# Non used part is filled by 0xFF
print "[i] Analizing header ..."
header = tools.loadPart(inputFile, 0, HEADER_SIZE)
tools.copyPart(inputFile, os.path.join(outputDirectory, "~header"), 0, HEADER_SIZE)

offset = header.find('\xff')
if offset != -1:
	headerScript = header[:offset]
	headerScriptFound = True

if not headerScriptFound:
	print "[!] Could not find header script!"
	quit()
	
if DEBUG:
	print headerScript

# Save the script
print "[i] Saving header script to " + os.path.join(outputDirectory, "~header_script") + " ..."
with open(os.path.join(outputDirectory, "~header_script"), "w") as f:
	f.write(headerScript)

# Parse script
print "[i] Parsing script ..."
# Supporting filepartload, mmc, store_secure_info, store_nuttx_config
for line in headerScript.splitlines():

	if DEBUG:
		print line

	if re.match("^filepartload", line):
		params = tools.processFilePartLoad(line)
		offset =  params["offset"]
		size =  params["size"]

	if re.match("^store_secure_info", line):		
	 	params = tools.processStoreSecureInfo(line)
	 	outputFile = os.path.join(outputDirectory, params["partition_name"])
	 	tools.copyPart(inputFile, outputFile, int(offset, 16), int(size, 16))

	if re.match("^store_nuttx_config", line):
	 	params = tools.processStoreNuttxConfig(line)
	 	outputFile = os.path.join(outputDirectory, params["partition_name"])
	 	tools.copyPart(inputFile, outputFile, int(offset, 16), int(size, 16))

	if re.match("^mmc", line):
		params = tools.processMmc(line)

		if params:

			# if params["action"] == "create":
			# 	nothing here

			if params["action"] == "write.boot":
				outputFile = tools.generateFileName(outputDirectory, params, ".img")
				tools.copyPart(inputFile, outputFile, int(offset, 16), int(size, 16))
				print "[i] Partition: %s\tOffset: %s\tSize %s (%s) -> %s" % (params["partition_name"], offset, size, tools.sizeStr(int(size, 16)), outputFile)

			if params["action"] == "write.p":
				outputFile = os.path.join(outputDirectory, params["partition_name"] + ".img")
				tools.copyPart(inputFile, outputFile, int(offset, 16), int(size, 16))
				print "[i] Partition: %s\tOffset: %s\tSize %s (%s) -> %s" % (params["partition_name"], offset, size, tools.sizeStr(int(size, 16)), outputFile)

			if params["action"] == "write.p.continue":
				outputFile = os.path.join(outputDirectory, params["partition_name"] + ".img")	
				tools.copyPart(inputFile, outputFile, int(offset, 16), int(size, 16), append = True)
				print "[i] Partition: %s\tOffset: %s\tSize %s (%s) append to %s" % (params["partition_name"], offset, size, tools.sizeStr(int(size, 16)), outputFile)

			if params["action"] == "unlzo":
				outputLzoFile = tools.generateFileName(outputDirectory, params, ".lzo")
				outputImgFile = tools.generateFileName(outputDirectory, params, ".img")
				# save .lzo
				print "[i] Partition: %s\tOffset: %s\tSize %s (%s) -> %s" % (params["partition_name"], offset, size, tools.sizeStr(int(size, 16)), outputLzoFile)
				tools.copyPart(inputFile, outputLzoFile, int(offset, 16), int(size, 16))
				# unpack .lzo -> .img
				print "[i]     Unpacking LZO (Please be patient) %s -> %s" % (outputLzoFile, outputImgFile)
				call(["./bin/lzop", "-o",  outputImgFile, "-d", outputLzoFile])
				# delete .lzo
				os.remove(outputLzoFile)

			if params["action"] == "unlzo.continue":
				if not params["partition_name"] in counter:
					counter[params["partition_name"]] = 0
				counter[params["partition_name"]] += 1

				outputImgFile = os.path.join(outputDirectory, params["partition_name"] + ".img")
				outputChunkLzoFile = os.path.join(outputDirectory, params["partition_name"] + str(counter[params["partition_name"]]) + ".lzo")
				outputChunkImgFile = os.path.join(outputDirectory, params["partition_name"] + str(counter[params["partition_name"]]) + ".img")
				# save .lzo
				print "[i] Partition: %s\tOffset: %s\tSize %s (%s) -> %s" % (params["partition_name"], offset, size, tools.sizeStr(int(size, 16)), outputChunkLzoFile)
				tools.copyPart(inputFile, outputChunkLzoFile, int(offset, 16), int(size, 16))
				# unpack chunk .lzo -> .img
				print "[i]     Unpacking LZO (Please be patient) %s -> %s" % (outputChunkLzoFile, outputChunkImgFile)
				call(["./bin/lzop", "-o",  outputChunkImgFile, "-x", outputChunkLzoFile])
				# append the chunk to main .img
				print "[i]     %s append to %s" % (outputChunkImgFile, outputImgFile)
				tools.appendFile(outputChunkImgFile, outputImgFile)
				# delete chunk
				#os.remove(outputChunkLzoFile)
				#os.remove(outputChunkImgFile)




