import os
import sys
import struct
import shutil
import tools
from subprocess import call

HEADER_SIZE = 16 * tools.KB # Header size is always 16KB
DRAM_BUF_ADDR = '20200000'
MAGIC_FOOTER = '12345678'

tmpDir = 'tmp'
outputFile = 'LetvUpgrade928.bin'
headerPart = os.path.join(tmpDir, '~header')
binPart = os.path.join(tmpDir, '~bin') 
footerPart = os.path.join(tmpDir, '~footer') 

# Parse args
if len(sys.argv) == 1: 
	print "Usage: pack-partition.py <partition name> <image file> [<lzo> <chunk size KB,MB,GB>]"
	print "Example: pack-partition.py system unpacked/system.img lzo 150MB"
	quit()

if len(sys.argv) == 2:
	print "Image file name cannot be empty"
	quit()

partName = sys.argv[1]
imageFile = sys.argv[2]
lzo = False
chunkSize = 0

# Non required params
# pack-partition.py system unpacked/system.img lzo
# pack-partition.py system unpacked/system.img 200
if len(sys.argv) == 4:
	lzo = (sys.argv[3] == 'lzo')
	if sys.argv[3] != 'lzo':
		chunkSize = tools.sizeInt(sys.argv[3])

# pack-partition.py system unpacked/system.img lzo 150
if len(sys.argv) == 5:
	lzo = (sys.argv[3] == 'lzo')
	chunkSize = tools.sizeInt(sys.argv[4])


print '[i] Partition name: %s' % partName
print '[i] Image file: %s' % imageFile
print '[i] LZO: %s' % lzo
print '[i] Chunk size: %s' % tools.sizeStr(chunkSize)


# Create working directory
tools.createDirectory(tmpDir)

# Split (if needed)
print '[i] Splitting ...'
chunks = tools.splitFile(imageFile, tmpDir, chunksize = chunkSize)


'''
	Header structure
	-------
	Multi-line script which contains MBOOT commands
	The header script ends with line: '% <- this is end of file symbol'
	Line separator is '\n'
	The header is filled by 0xFF to 16KB
	The header size is always 16KB
'''

'''
	Bin structure
	-------
	Basically it's merged parts:

	[part 1]
	[part 2]
	....
	[part n]

	Each part is 4 byte aligned (filled by 0xFF)
'''

# Header and bin
print '[i] Total chunks: %d' % len(chunks)
print '[i] Generating header and bin ...'
# Initial empty bin to store merged parts
open(binPart, 'w').close()
with open(headerPart, 'wb') as header:
	header.write('dont_overwrite_init\n')
	header.write('mmc erase.p %s\n' % partName)

	for index, inputChunk in enumerate(chunks):
		print '[i] Processing chunk: %s' % inputChunk
		(name, ext) = os.path.splitext(inputChunk)
		if lzo:
			outputChunk = name + '.lzo'
			print '[i]     LZO: %s -> %s' % (inputChunk, outputChunk)
			call(['./bin/lzop', '-o',  outputChunk, '-1', inputChunk])
		else:
			outputChunk = inputChunk

		size = os.path.getsize(outputChunk)
		offset = os.path.getsize(binPart) + HEADER_SIZE 
		header.write('filepartload %s %s %x %x\n' % (DRAM_BUF_ADDR, outputFile, offset, size))

		print '[i]     Align chunk'
		tools.alignFile(outputChunk)

		print '[i]     Append: %s -> %s' % (outputChunk, binPart)
		tools.appendFile(outputChunk, binPart)

		
		if lzo:
			if index == 0:
				header.write('mmc unlzo %s %x %s 1\n' % (DRAM_BUF_ADDR, size, partName))
			else:
				header.write('mmc unlzo.cont %s %x %s 1\n' % (DRAM_BUF_ADDR, size, partName))
		else:
			if len(chunks) == 1:
				header.write('mmc write.p %s %s %x 1\n' % (DRAM_BUF_ADDR, partName, size))
			else:
				# filepartload 50000000 MstarUpgrade.bin e04000 c800000
				# mmc write.p.continue 50000000 system 0 c800000 1

				# filepartload 50000000 MstarUpgrade.bin d604000 c800000
				# mmc write.p.continue 50000000 system 64000 c800000 1
				# Why offset is 64000 but not c800000 ???
				print '[!] UNSUPPORTED: mmc write.p.continue'
				quit()
	

#	header.write('setenv LetvUpgrade_complete 1\n')
#	header.write('setenv ResetAfterUpgrade 1\n')
#	header.write('setenv ForcePowerOn 1\n')
#	header.write('saveenv\n')
	header.write('% <- this is end of file symbol\n')
	header.flush()

	print '[i] Fill header script to 16KB'	
	header.write('\xff' * (HEADER_SIZE - os.path.getsize(headerPart)))

'''
	Footer structure
	|MAGIC|SWAPPED HEADER CRC32|SWAPPED BIN CRC32|FIRST 16 BYTES OF HEADER|
'''

print '[i] Generating footer ...'
headerCRC = tools.crc32(headerPart)
binCRC = tools.crc32(binPart)
header16bytes = tools.loadPart(headerPart, 0, 16)
with open(footerPart, 'wb') as footer:
	print '[i]     Magic: %s' % MAGIC_FOOTER
	footer.write(MAGIC_FOOTER)
	print '[i]     Header CRC: 0x%x' % headerCRC
	footer.write(struct.pack('L', headerCRC)) # struct.pack('L', data) <- returns byte swapped data
	print '[i]     Bin CRC: 0x%x' % binCRC
	footer.write(struct.pack('L', binCRC))
	print '[i]     First 16 bytes of header: %s' % header16bytes
	footer.write(header16bytes)

print '[i] Merging header, bin, footer ...'
open(outputFile, 'w').close()
tools.appendFile(headerPart, outputFile)
tools.appendFile(binPart, outputFile)
tools.appendFile(footerPart, outputFile)

shutil.rmtree(tmpDir)
print '[i] Done'