import math
import os
import re
import sys
import string
import binascii

B  = 2**00
KB = 2**10
MB = 2**20
GB = 2**30

def sizeInt(s):

	value = int(s.strip(string.ascii_letters))
	unit = s.strip(string.digits)
	if not unit:
		unit = 'B'
	return value * globals()[unit]

def sizeStr(s):
	if (s == 0):
		return '0B'
	size_name = ('B', 'KB', 'MB', 'GB')
	i = int(math.floor(math.log(s, 1024)))
	p = math.pow(1024 ,i)
	s = round(s / p, 2)
	return '%s %s' % (s,size_name[i])

def createDirectory(dir):
	if not os.path.exists(dir): # if the directory does not exist
		os.makedirs(dir) # make the directory
	else: # the directory exists
		#removes all files in a folder
		for the_file in os.listdir(dir):
			file_path = os.path.join(dir, the_file)
			try:
				if os.path.isfile(file_path):
					os.unlink(file_path) # unlink (delete) the file
			except Exception, e:
				print e

def splitFile(file, destdir, chunksize):
	(name, ext) = os.path.splitext(os.path.basename(file))
	chunks = []

	# Just copy file if its size is less than chunk size
	if os.path.getsize(file) < chunksize:
		chunk = os.path.join(destdir, name + ext)
		shutil.copyfile(file, chunk)
		return [chunk]

	# Split in chunks and copy
	data = True
	while data:
		data = loadPart(file, len(chunks) * chunksize, chunksize)
		if data:
			chunk = os.path.join(destdir, ('%s.%04d%s' % (name, len(chunks), ext)))
			chunks.append(chunk)
			with open(chunk, 'wb') as f2:
				f2.write(data)	

	assert len(chunks) <= 9999			
	return chunks

# Append src file to dest file
# bufsize - chunk size
def appendFile(src, dest, bufsize = 16 * MB):
	with open(src, 'rb') as f1:
		with open(dest, 'ab') as f2:
			data = True
			while data:
				data = f1.read(bufsize)
				f2.write(data)
	
# Copy part of src file to dest file. 
# offset - beginning of the part to copy
# size - length of the part to copy
# bufsize - chunk size
# append - if True then append to dest file
# if dest file does not exist it will be created
def copyPart(src, dest, offset, size, bufsize = 16 * MB, append = False):
	if not os.path.exists(dest):
		append = False

	with open(src, 'rb') as f1:
		f1.seek(offset)
		with open(dest, 'ab' if append else 'wb') as f2:
			while size:
				chunk = min(bufsize, size)
				data = f1.read(chunk)
				f2.write(data)
				size -= chunk

# Trim part of src file and save the rest to dest file.
# offset - beginning of the part to trim
# size - length of the part to trim
# bufsize - chunk size
def trimPart(src, dest, offset, size, bufsize = 16 * MB):
	srcSize = os.path.getsize(src)
	copyPart(src, dest, 0, offset, bufsize)
	copyPart(src, dest, offset + size, srcSize - offset - size, bufsize = bufsize, append = True)

# Load and return part
# file - source file
# offset - beginning of the part
# size - length of the part
def loadPart(file, offset, size):
	with open(file, 'rb') as f:
		f.seek(offset)
		return f.read(size)

# Align file
# file - input file to align
# base - alignment base
def alignFile(file, base = 0x1000):
	result = base - os.path.getsize(file) % base
	if result:
		with open(file, 'ab') as f:
			f.write('\xff' * result)

# Calculate crc32
# file - filename of a file to calculate
def crc32(file):
    buf = open(file,'rb').read()
    buf = (binascii.crc32(buf) & 0xFFFFFFFF)
    return buf

# unlzo
# if NT then use ./bin/lzo.exe
def unlzo(src, dest):
	lzop = os.path.abspath('.') + '/bin/lzop.exe' if os.name == 'nt' else 'lzop'
	os.system(lzop + ' -o {} -d {}'.format(dest, src))

# unlzo
# if NT then use ./bin/lzo.exe
def lzo(src, dest):
	lzop = os.path.abspath('.') + '/bin/lzop.exe' if os.name == 'nt' else 'lzop'
	os.system(lzop + ' -o {} -1 {}'.format(dest, src))

def parceArgs(string):
	return re.findall('([^\s]+)', string)

def processFilePartLoad(line):
	args = parceArgs(line)
	return {'cmd': args[0], 'addr': args[1], 'sourceFile': args[2], 'offset': args[3], 'size': args[4]}
	
def processStoreSecureInfo(line):
	args = parceArgs(line)
	return {'cmd': args[0], 'partition_name': args[1], 'addr': args[2]}	
	
def processStoreNuttxConfig(line):
	args = parceArgs(line)
	return {'cmd': args[0], 'partition_name': args[1], 'addr': args[2]}

def processMmc(line):
	args = parceArgs(line)

	if args[1] == 'create':
		# mmc erase.p partition_name
		return {'cmd': args[0], 'action': args[1], 'partition_name': args[2], 'size': args[3]}

	if args[1] == 'erase.p':
		# mmc erase.p partition_name
		return {'cmd': args[0], 'action': args[1], 'partition_name': args[2]}

	elif args[1] == 'write.p':
		# mmc write.p addr partition_name size [empty_skip:0-disable,1-enable]
		res = {'cmd': args[0], 'action': args[1], 'addr': args[2], 'partition_name': args[3], 'size': args[4]}
		try:
			res['empty_skip'] = args[5]
		except IndexError:
			res['empty_skip'] = 0
		return res

	elif args[1] == 'write.p.continue' or args[1] == 'write.p.cont':
		# mmc write.p(.continue|.cont) addr partition_name offset size [empty_skip:0-disable,1-enable]\n
		res = {'cmd': args[0], 'action': 'write.p.continue', 'addr': args[2], 'partition_name': args[3], 'offset': args[4], 'size': args[5]}
		try:
			res['empty_skip'] = args[6]
		except IndexError:
			res['empty_skip'] = 0
		return res


	elif args[1] == 'write.boot' or args[1] == 'write':
		# mmc write[.boot] bootpart addr blk# size [empty_skip:0-disable,1-enable]
		res = {'cmd': args[0], 'action': args[1], 'bootpart': args[2], 'addr': args[3], 'blk#': args[4], 'size': args[5], 'partition_name': 'sboot'}
		try:
			res['empty_skip'] = args[6]
		except IndexError:
			res['empty_skip'] = 0
		return res

	elif args[1] == 'unlzo':
		# mmc unlzo[.continue|.cont] addr size partition_name [empty_skip:0-disable,1-enable]- decompress lzo file and write to mmc partition
		res = {'cmd': args[0], 'action': args[1], 'addr': args[2], 'size': args[3], 'partition_name': args[4]}
		try:
			res['empty_skip'] = args[5]
		except IndexError:
			res['empty_skip'] = 0
		return res

	elif args[1] == 'unlzo.continue' or args[1] == 'unlzo.cont':
		# mmc unlzo[.continue|.cont] addr size partition_name [empty_skip:0-disable,1-enable]- decompress lzo file and write to mmc partition
		res = {'cmd': args[0], 'action': 'unlzo.continue', 'addr': args[2], 'size': args[3], 'partition_name': args[4]}
		try:
			res['empty_skip'] = args[5]
		except IndexError:
			res['empty_skip'] = 0
		return res

	# else:
	# 	print 'Unknown mmc action'
	# 	print args

fileNameCounter = {}
def generateFileName(outputDirectory, part, ext):
	fileName = os.path.join(outputDirectory, part['partition_name'] + ext)
	if os.path.exists(fileName):
		try:
			fileNameCounter[part['partition_name']] += 1
		except:
			fileNameCounter[part['partition_name']] = 1
		fileName = os.path.join(outputDirectory, part['partition_name'] + str(fileNameCounter[part['partition_name']]) + ext)
	return fileName
