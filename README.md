# mstar-bin-tool
## Unpack MStar bin firmware files

```
Usage: unpack.py <Firmware> <Output folder [default: ./unpacked/]>
```
## Pack a single partition and create MStar bin firmware 
```
Usage: pack-partition.py <partition name> <image file> [<lzo> <chunk size KB,MB,GB>]
Example: pack-partition.py system unpacked/system.img lzo 150MB
```
