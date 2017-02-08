'''
This tool is used to sign (aka generate "secureinfo") and encrypt partition

Almost all new Mstar builds I saw have SECURITY_BOOT option enebled. Which means it uses AES to 
encrypt boot.img and recovery.img and RSA to generate signature (Plus multiple internal security updates).

This script will generate two files: encrypted image and signature file

'''

import os
import sys

# Command line args
if len(sys.argv) == 1: 
	print ("Usage: secure_partition.py <file to encrypt> <AES key file> <RSA private key file> <RSA public key file> <output encrypted file> <output signature file>")
	print ("Example: secure_partition.py ./pack/boot.img ./keys/AESbootKey ./keys/RSAboot_priv.txt ./keys/RSAboot_pub.txt ./pack/boot.img.aes ./pack/boot.signature.bin")
	quit()

INPUT_FILE_NAME 			= sys.argv[1]
AES_KEY 					= sys.argv[2]
RSA_PRIVATE_KEY 			= sys.argv[3]
RSA_PUBLIC_KEY 				= sys.argv[4]
OUTPUT_FILE_NAME 			= sys.argv[5]
OUTPUT_SIGNATURE_FILE_NAME	= sys.argv[6]

# Aditional SubSecureInfoGen params
BLOCK_SIZE_FOR_INTERLEAVE  			= 2097152
ENABLE_PARTIAL_AUTHENTICATION 		= 0 	# 0 - disable, 1 - enable
NUMBER_FOR_PARTIAL_AUTHENTICATION 	= 8 	# ???
ENABLE_INTERLEAVE_MODE 				= 1 	# 0 - disable, 1 - enable
DISPLAY_DEBUGGING_INFO 				= 1		# 0 - disable, 1 - enable

# Binary tools
TOOLS_DIR = 'bin\\win32\\' if os.name == 'nt' else 'bin/linux-x86/'
alignment 			= os.path.join(TOOLS_DIR, 'alignment')
SubSecureInfoGen 	= os.path.join(TOOLS_DIR, 'SubSecureInfoGen')
aescrypt2 			= os.path.join(TOOLS_DIR, 'aescrypt2')


# Alignment
os.system(alignment + ' {}'.format(INPUT_FILE_NAME))

# Generate signature
os.system(SubSecureInfoGen + ' {} {} {} {} {} {} {} {} {} {}'.format(
		OUTPUT_SIGNATURE_FILE_NAME, 
		INPUT_FILE_NAME, 
		RSA_PRIVATE_KEY, 
		RSA_PUBLIC_KEY, 
		ENABLE_PARTIAL_AUTHENTICATION, 
		NUMBER_FOR_PARTIAL_AUTHENTICATION, 
		ENABLE_INTERLEAVE_MODE, 
		BLOCK_SIZE_FOR_INTERLEAVE,
		DISPLAY_DEBUGGING_INFO,
		TOOLS_DIR))

print (SubSecureInfoGen + ' {} {} {} {} {} {} {} {} {} {}'.format(
		OUTPUT_SIGNATURE_FILE_NAME, 
		INPUT_FILE_NAME, 
		RSA_PRIVATE_KEY, 
		RSA_PUBLIC_KEY, 
		ENABLE_PARTIAL_AUTHENTICATION, 
		NUMBER_FOR_PARTIAL_AUTHENTICATION, 
		ENABLE_INTERLEAVE_MODE, 
		BLOCK_SIZE_FOR_INTERLEAVE,
		DISPLAY_DEBUGGING_INFO,
		TOOLS_DIR))


# Crypt input image
os.system(aescrypt2 + ' 0 {} {} {}'.format(INPUT_FILE_NAME, OUTPUT_FILE_NAME, AES_KEY))

print ("Done")