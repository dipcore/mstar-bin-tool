# mstar-bin-tool

Command line tools to pack/unpack MStar bin firmware

Currently available tools:
 - **unpack.py** - unpack MStar bin firmware
 - **pack.py** - pack MStar bin firmware
 - **extract_keys.py** - extract AES and RSA-public keys from MBOOT binary
 - **secure_partition.py** - encrypt image and generate signature file


## Unpack MStar bin firmware files

```
Usage: unpack.py <firmware> <output folder [default: ./unpacked/]>
        <firmware> - MStar bin firmware to unpack
        <output folder> - directory to store unpacked stuff. Default value: ./unpacked/
```


## Pack MStar bin firmware 
```
Usage: pack.py <config file>
Example: pack.py configs/letv-x355pro-full.ini
		<config file> - Configuration file. The config file structure will be described later.
                        For now you can take a look at configs/letv-x355pro-full.ini
                        and use it as an example
```


## Extract keys from MBOOT
That tool is used to get AES and public RSA keys from the MBOOT. AES keys are needed to encrypt/decrypt 
boot.img and recovery.img images. aescrypt2 tool is used.

```
Usage: extract_keys.py <path to mboot> [<folder to store keys>] [<key bank offset>] [<key bank size>]
Defaults:
          <folder to store keys>        keys
          <key bank offset>             0x168e00
          <key bank size>               0x450
Example: extract_keys.py ./unpacked/MBOOT.img
Example: extract_keys.py ./unpacked/MBOOT.img ./keys 0x169e00 0x450
```

## Encrypt partition and generate signature
All new MStar builds have SECURE_BOOT option enabled. In that case 
boot.img and recovery.img is encrypted (AES) and signed with RSA priv keys.
That script is used to encrypt image and generate sign file. 

To manually encrypt|decrypt image use aescrypt tool from bin folder.
AES key can be extracted from MBOOT with extract_keys.py script.

```
Usage: secure_partition.py <file to encrypt> <AES key file> <RSA private key file> <RSA public key file> <output encrypted file> <output signature file>
Example: secure_partition.py ./pack/boot.img ./keys/AESbootKey ./keys/RSAboot_priv.txt ./keys/RSAboot_pub.txt ./pack/boot.img.aes ./pack/bootSign
```
