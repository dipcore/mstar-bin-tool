# mstar-bin-tool

Command line tools for manipulating MStar bin firmware files.

Currently awailable tools:
 - **unpack.py** - unpack MStar bin firmware
 - **pack-partition.py** - pack a single partition to MStar bin firmware


## Unpack MStar bin firmware files

```
Usage: unpack.py <firmware> <output folder [default: ./unpacked/]>
        <firmware> - MStar bin firmware to unpack
        <output folder> - directory to store unpacked stuff. Default value: ./unpacked/
```


## Pack a single partition and create MStar bin firmware 
```
Usage: pack-partition.py <firmware> <partition name> <image file> [<lzo> <chunk size KB,MB,GB>]
Example: pack-partition.py system unpacked/system.img lzo 150MB
		<firmware> - Firmware file name to create. Ex. MstarUpdate.bin
        <partition name> - Partition name. Important: The partition is not creating, 
                            so make sure it already exists on your device. Check ./unpacked/~header_script 
                            file for 'mmc create <partition name>' line.
        <image file> - Image or bin file to pack.
        <lzo> - Enable LZO packing. Non required param.
        <chunk size KB,MB,GB> - Chunk size. Ex: 150MB. 
                                Non required param, by default whole image file is used as a sinle chunk.
```
