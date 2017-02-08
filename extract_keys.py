'''
	Tool to extract security keys from the MBOOT

	That tool can be used only if you have Mstar.Key.Bank section in the mboot
	To check that you need to enable debug mode in the mboot console, 
	and check for next lines during the boot:
		[DEBUG] isCustomerKeyBankCipher:926: keyBankOffset=0x168e00
		[DEBUG] isCustomerKeyBankCipher:927: keyBankSize=0x450

	keyBankOffset - is an offset of the key bank section in the mboot
	keyBankSize - section size

	There will be similar lines for the key bank backup.

	Another way to check it is to open MBOOT binary in the hex editor and
	do search for u8MagicID, which is most of the time equals to "Mstar.Key.Bank" string. 
	You should get two equal sections, the key bank and the key bank backup.

	==== Key bank structures ===

	#define AES_IV_LEN 		16
	#define AES_KEY_LEN 	16
	#define HMAC_KEY_LEN 	32

	#define SIGNATURE_LEN        	256
	#define RSA_PUBLIC_KEY_N_LEN 	256
	#define RSA_PUBLIC_KEY_E_LEN 	4
	#define RSA_PUBLIC_KEY_LEN   	(RSA_PUBLIC_KEY_N_LEN+RSA_PUBLIC_KEY_E_LEN)

	typedef struct
	{
	    U32 u32Num;
	    U32 u32Size;
	}IMAGE_INFO;

	typedef struct
	{
	  U8 u8SecIdentify[8]; 
	  IMAGE_INFO info;
	  U8 u8Signature[SIGNATURE_LEN];
	}_SUB_SECURE_INFO;

	typedef struct
	{
	  U8 N[RSA_PUBLIC_KEY_N_LEN];
	  U8 E[RSA_PUBLIC_KEY_E_LEN];
	}RSA_PUBLIC_KEY;

	typedef struct
	{
	    _SUB_SECURE_INFO customer;
	    RSA_PUBLIC_KEY u8RSABootPublicKey;
	    RSA_PUBLIC_KEY u8RSAUpgradePublicKey;
	    RSA_PUBLIC_KEY u8RSAImagePublicKey;
	    U8 u8AESBootKey[AES_KEY_LEN];   
	    U8 u8AESUpgradeKey[AES_KEY_LEN];       
	    U8 u8MagicID[16];
	    U8 crc[4];
	}CUSTOMER_KEY_BANK;

	==== End Key bank structures ===

'''

from ctypes import *
import os
import sys
import utils

DEBUG = False

# Default values
defOutFolder = "keys"
defOffet = "0x168e00"
defSize = "0x450"
#defKey="hex:E01001FF0FAA55FC924D535441FF0700"

# Structures
AES_IV_LEN 		= 16
AES_KEY_LEN 	= 16
HMAC_KEY_LEN 	= 32

SIGNATURE_LEN        	= 256
RSA_PUBLIC_KEY_N_LEN 	= 256
RSA_PUBLIC_KEY_E_LEN 	= 4
RSA_PUBLIC_KEY_LEN   	= RSA_PUBLIC_KEY_N_LEN + RSA_PUBLIC_KEY_E_LEN

class IMAGE_INFO(Structure):
	_fields_ = [("u32Num", c_uint32),
				("u32Size", c_uint32)]

class SUB_SECURE_INFO(Structure):
	_fields_ = [("u8SecIdentify", c_uint8 * 8),
				("info", IMAGE_INFO),
				("u8Signature", c_uint8 * SIGNATURE_LEN)]

class RSA_PUBLIC_KEY(Structure):
	_fields_ = [("N", c_uint8 * RSA_PUBLIC_KEY_N_LEN),
				("E", c_uint8 * RSA_PUBLIC_KEY_E_LEN)]

class CUSTOMER_KEY_BANK(Structure):
	_fields_ = [("customer", SUB_SECURE_INFO),
				("u8RSABootPublicKey", RSA_PUBLIC_KEY),
				("u8RSAUpgradePublicKey", RSA_PUBLIC_KEY),
				("u8RSAImagePublicKey", RSA_PUBLIC_KEY),
				("u8AESBootKey", c_uint8 * AES_KEY_LEN),
				("u8AESUpgradeKey", c_uint8 * AES_KEY_LEN),
				("u8MagicID", c_uint8 * 16),
				("crc", c_uint8 * 4)]


# Command line args
if len(sys.argv) == 1: 
	print ("Usage: extract_keys.py <path to mboot> [<folder to store keys>] [<key bank offset>] [<key bank size>]")
	print ("Defaults: ")
	print ("          <folder to store keys> 	keys")
	print ("          <key bank offset> 		0x168e00")
	print ("          <key bank size> 			0x450")
	#print ("          <custom decription key> 	Efuse Key")
	print ("Example: extract_keys.py ./unpacked/MBOOT.img")
	print ("Example: extract_keys.py ./unpacked/MBOOT.img ./keys 0x169e00 0x450")
	quit()


mboot = sys.argv[1]
outFolder = sys.argv[2] if len(sys.argv) >= 3 else defOutFolder
offestStr = sys.argv[3] if len(sys.argv) >= 4 else defOffet
sizeStr = sys.argv[4] if len(sys.argv) >= 5 else defSize
#hwKey = sys.argv[5] if len(sys.argv) >= 6 else defKey

offset = int(offestStr, 16)
size = int(sizeStr, 16)

# Create out directory 
print ("[i] Create output directory")
utils.createDirectory(outFolder)

# Get the key bank section and store it
outEncKeyBankFile = os.path.join(outFolder, 'key_bank.bin')
print ("[i] Save mstar key bank to {}".format(outEncKeyBankFile))
utils.copyPart(mboot, outEncKeyBankFile, offset, size)

# Unpack the key bank to key bank structure
print ("[i] Unpack key bank structure")
keyBankBytes = utils.loadPart(outEncKeyBankFile, 0, size)
keyBank = utils.unpackStructure(CUSTOMER_KEY_BANK, keyBankBytes)

if (DEBUG):
	# Print all
	print ( "[i] u8SecIdentify:\n{}".format( utils.hexString(keyBank.customer.u8SecIdentify) ) )
	print ( "[i] u32Num: 0x{:08x}".format( keyBank.customer.info.u32Num ) )
	print ( "[i] u32Size: 0x{:08x}".format( keyBank.customer.info.u32Size ) )
	print ( "[i] u8Signature:\n{}".format( utils.hexString(keyBank.customer.u8Signature) ) )

	print ( "[i] u8RSABootPublicKey N:\n{}".format( utils.hexString(keyBank.u8RSABootPublicKey.N) ) )
	print ( "[i] u8RSABootPublicKey E:\n{}".format( utils.hexString(keyBank.u8RSABootPublicKey.E) ) )
	print ( "[i] u8RSAUpgradePublicKey N:\n{}".format( utils.hexString(keyBank.u8RSAUpgradePublicKey.N) ) )
	print ( "[i] u8RSAUpgradePublicKey E:\n{}".format( utils.hexString(keyBank.u8RSAUpgradePublicKey.E) ) )
	print ( "[i] u8RSAImagePublicKey N:\n{}".format( utils.hexString(keyBank.u8RSAImagePublicKey.N) ) )
	print ( "[i] u8RSAImagePublicKey E:\n{}".format( utils.hexString(keyBank.u8RSAImagePublicKey.E) ) )
	print ( "[i] u8AESBootKey:\n{}".format( utils.hexString(keyBank.u8AESBootKey) ) )
	print ( "[i] u8AESUpgradeKey:\n{}".format( utils.hexString(keyBank.u8AESUpgradeKey) ) )

	print ( "[i] u8MagicID:\n{}".format( utils.hexString(keyBank.u8MagicID) ) )
	print ( "[i] CRC:\n{}".format( utils.hexString(keyBank.crc) ) )

# Save keys
print ("[i] Save keys")

# RSA Boot
utils.writeFile(os.path.join(outFolder, 'RSAboot_pub.bin'), keyBank.u8RSABootPublicKey)
utils.writeRSAPublicKey(os.path.join(outFolder, 'RSAboot_pub.txt'), keyBank.u8RSABootPublicKey)

# RSA Upgrade
utils.writeFile(os.path.join(outFolder, 'RSAupgrade_pub.bin'), keyBank.u8RSAUpgradePublicKey)
utils.writeRSAPublicKey(os.path.join(outFolder, 'RSAupgrade_pub.txt'), keyBank.u8RSAUpgradePublicKey)

# RSA Image
utils.writeFile(os.path.join(outFolder, 'RSAimage_pub.bin'), keyBank.u8RSAImagePublicKey)
utils.writeRSAPublicKey(os.path.join(outFolder, 'RSAimage_pub.txt'), keyBank.u8RSAImagePublicKey)

# AES
utils.writeFile(os.path.join(outFolder, 'AESBoot.bin'), keyBank.u8AESBootKey)
utils.writeFile(os.path.join(outFolder, 'AESUpgrade.bin'), keyBank.u8AESUpgradeKey)

print ("Done")