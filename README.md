# mstar-bin-tool

Command line tools to pack/unpack MStar bin firmware

Currently available tools:
 - **unpack.py** - unpack MStar bin firmware
 - **pack.py** - pack MStar bin firmware


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
