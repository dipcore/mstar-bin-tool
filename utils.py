import re
import os
import shutil
import string
import binascii
import math
import ctypes

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

def str2bool(v):
	return v.lower() in ("yes", "true", "True", "1")

def bool2int(v):
	return  1 if v else 0

def getConfigValue(config, name, defValue):
	try:
		value = config[name]
	except Exception as e:
		value = defValue
	return value

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
			except e:
				print (e)

def splitFile(file, destdir, chunksize):
	(name, ext) = os.path.splitext(os.path.basename(file))
	chunks = []

	# Just copy file if its size is less than chunk size
	if os.path.getsize(file) < chunksize or chunksize == 0:
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
	
def sparse_split(file, destdir, chunksize):
	(name, ext) = os.path.splitext(os.path.basename(file))
	chunks = []

	# Just return file if its size is less than chunk size
	if os.path.getsize(file) < chunksize or chunksize == 0:
		return [file]
		
	# Split to chunks
	src = os.path.join(destdir, name + ext)
	dest = os.path.join(destdir, name + "_sparse")
	os.system('bin\\sparse\\simg2simg.exe' + ' {} {} {}'.format(src, dest, chunksize))
	namesList = list(filter(lambda s: s.startswith(name + '_sparse'), os.listdir(destdir)))
	for name in namesList:
		chunks.append(os.path.join(destdir, name))
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
			f.write(('\xff' * result).encode(encoding='iso-8859-1'))

# unlzo
# if NT then use ./bin/lzo.exe
def unlzo(src, dest):
	lzop = 'bin\\win32\\lzop.exe' if os.name == 'nt' else 'bin/linux-x86/lzop'
	os.system(lzop + ' -o {} -d {}'.format(dest, src))

# lzo
# if NT then use ./bin/lzo.exe
def lzo(src, dest):
	lzop = 'bin\\win32\\lzop.exe' if os.name == 'nt' else 'bin/linux-x86/lzop'
	os.system(lzop + ' -o {} -1 {}'.format(dest, src))
	
def sparse_to_img (src, dest):
	os.system('bin\\sparse\\simg2img.exe' + ' {} {}'.format(src, dest))
	
def img_to_sparse (src, dest):
	os.system('bin\\sparse\\img2simg.exe' + ' {} {}'.format(src, dest))

# Calculate crc32
# file - filename of a file to calculate
def crc32(file):
    buf = open(file,'rb').read()
    buf = (binascii.crc32(buf) & 0xFFFFFFFF)
    return buf

# Apply env variable to line, i.e.
# setenv imageSize 0x13800
# setenv imageOffset 0x4000
# filepartload 0x20200000 LetvUpgrade938.bin $(imageOffset) $(imageSize)
# So we replace it to filepartload 0x20200000 LetvUpgrade938.bin 0x4000 0x13800
def applyEnv(line, env):
	keys = re.findall('\$\((\w+)\)', line)
	for key in keys:
		if key in env and env[key]:
			line = line.replace("$({})".format(key), env[key])
	return line

def processSetEnv(line):
	args = re.findall('([^\s]+)\s+([^\s]+)\s*(.*)', line)
	args = args[0]
	if len(args) == 3:
		return {'cmd': args[0], 'key': args[1], 'value': args[2]}
	else:
		return {'cmd': args[0], 'key': args[1]}

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
	
def processSparseWrite(line):
	args = parceArgs(line)
	return {'cmd': args[0], 'action': args[1], 'addr': args[2], 'partition_name': args[3], 'size': args[4]}

def processMmc(line):
	args = parceArgs(line)

	if args[1] == 'create':
		# mmc create [name] [size]- create/change mmc partition [name]
		return {'cmd': args[0], 'action': args[1], 'partition_name': args[2], 'size': args[3]}

	if args[1] == 'erase.p':
		# mmc erase.p partition_name
		return {'cmd': args[0], 'action': args[1], 'partition_name': args[2]}
		# TODO Add support:
		# mmc create.gp part_no size enh_attr ext_attr relwr_attr - create/change eMMC GP partition No.[part_no(0~3)] with size and enhance/extended/reliable_write attribute
		# mmc create.enhusr start_addr size enha_attr relwr_atrr - create/change eMMC enhance user partition(slc mode) from start_addr with size and enhance/reliable_write attribute
		# mmc create.complete - complete eMMC gp, enhance user, reliable write partition setting


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


# TODO rewrite it
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
	
fileExtCounter = {}
def generateFileNameSparse(outputDirectory, part):
	fileName = os.path.join(outputDirectory, part['partition_name'] + '_sparse.0')
	if os.path.exists(fileName):
		try:
			fileExtCounter[part['partition_name']] += 1
		except:
			fileExtCounter[part['partition_name']] = 1
		fileName = os.path.join(outputDirectory, part['partition_name'] + '_sparse.' + str(fileExtCounter[part['partition_name']]))
	return fileName
	
def convertInputSparseName(filename):
	filename = filename.replace("\\", "/");
	return filename

def directive(header, dramBufAddr, useHexValuesPrefix):

	def filepartload(filename, offset, size, memoryOffset=dramBufAddr):
		if (useHexValuesPrefix):
			header.write('filepartload 0x{} {} 0x{} 0x{}\n'.format(memoryOffset, filename, offset, size).encode())
		else:
			header.write('filepartload {} {} {} {}\n'.format(memoryOffset, filename, offset, size).encode())

	# Create directive always uses 0x format
	def create(name, size):
		#if (useHexValuesPrefix):
		header.write('mmc create {} 0x{}\n'.format(name, size).encode())
		#else:
		#	header.write('mmc create {} {}\n'.format(name, size).encode())

	def erase_p(name):
		header.write('mmc erase.p {}\n'.format(name).encode())

	# mmc unlzo[.continue|.cont] addr size partition_name [empty_skip:0-disable,1-enable]- decompress lzo file and write to mmc partition
	def unlzo(name, size, memoryOffset=dramBufAddr, emptySkip = 1):
		if (useHexValuesPrefix):
			header.write('mmc unlzo 0x{} 0x{} {} {}\n'.format(memoryOffset, size, name, emptySkip).encode())
		else:
			header.write('mmc unlzo {} {} {} {}\n'.format(memoryOffset, size, name, emptySkip).encode())

	# mmc unlzo[.continue|.cont] addr size partition_name [empty_skip:0-disable,1-enable]- decompress lzo file and write to mmc partition
	def unlzo_cont(name, size, memoryOffset=dramBufAddr, emptySkip = 1):
		if (useHexValuesPrefix):
			header.write('mmc unlzo.cont 0x{} 0x{} {} {}\n'.format(memoryOffset, size, name, emptySkip).encode())
		else:
			header.write('mmc unlzo.cont {} {} {} {}\n'.format(memoryOffset, size, name, emptySkip).encode())

	# mmc write.p addr partition_name size [empty_skip:0-disable,1-enable]
	def write_p(name, size, memoryOffset=dramBufAddr, emptySkip = 1):
		if (useHexValuesPrefix):
			header.write('mmc write.p 0x{} {} 0x{} {}\n'.format(memoryOffset, name, size, emptySkip).encode())
		else:
			header.write('mmc write.p {} {} {} {}\n'.format(memoryOffset, name, size, emptySkip).encode())

	# TODO Add support 
	# mmc write.p(.continue|.cont) addr partition_name offset size [empty_skip:0-disable,1-enable]

	def store_secure_info(name, memoryOffset=dramBufAddr):
		if (useHexValuesPrefix):
			header.write('store_secure_info {} 0x{}\n'.format(name, memoryOffset).encode())
		else:
			header.write('store_secure_info {} {}\n'.format(name, memoryOffset).encode())

	def store_nuttx_config(name, memoryOffset=dramBufAddr):
		if (useHexValuesPrefix):
			header.write('store_nuttx_config {} 0x{}\n'.format(name, memoryOffset).encode())
		else:
			header.write('store_nuttx_config {} {}\n'.format(name, memoryOffset).encode())

	# mmc write[.boot|.gp] [bootpart|gppart] addr blk# size [empty_skip:0-disable,1-enable]
	def write_boot(size, memoryOffset=dramBufAddr, emptySkip = 0):
		if (useHexValuesPrefix):
			header.write('mmc write.boot 1 0x{} 0 0x{} {}\n'.format(memoryOffset, size, emptySkip).encode())
		else:
			header.write('mmc write.boot 1 {} 0 {} {}\n'.format(memoryOffset, size, emptySkip).encode())

	#####
	def sparse_write(name, memoryOffset=dramBufAddr):
		if (useHexValuesPrefix):
			header.write('sparse_write mmc 0x{} {} $(filesize)\n'.format(memoryOffset, name).encode())
		else:
			header.write('sparse_write mmc {} {} $(filesize)\n'.format(memoryOffset, name).encode())
			
	directive.filepartload = filepartload	
	directive.create = create	
	directive.erase_p = erase_p	
	directive.unlzo = unlzo	
	directive.unlzo_cont = unlzo_cont	
	directive.write_p = write_p	
	directive.store_secure_info = store_secure_info	
	directive.store_nuttx_config = store_nuttx_config	
	directive.write_boot = write_boot	
	directive.sparse_write = sparse_write
	return directive

def hexString(v, delimiter = ' '):
	return (delimiter.join([format(i, '02X') for i in v]))

def unpackStructure(s, b):
	result = s()
	ctypes.memmove(ctypes.addressof(result), b, ctypes.sizeof(s))
	return result

def writeFile(file, data):
	with open(file, 'wb') as f:
		f.write(data)

def writeRSAPublicKey(file, key):
	writeFile(file, 
		str.encode( "N = {}\nE = {}".format(hexString(key.N, ''), hexString(key.E, '')) ))