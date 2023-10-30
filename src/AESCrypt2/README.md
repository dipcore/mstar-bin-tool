## AESCrypt2

The original tarball came from here [packetstormsecurity.com][2].

### Get Fiber and the Huawei HG8245

This router is used with Fiber customers in Oslo, Norway that are using        [Get][3] as their ISP.

In typical ISP fashion they can't just hand you an Ethernet jack and get out of your way, they want to give you a router that NATs and provides WiFi. In this case they've adopted the Huawei HG8245 which is large and provides terrible WiFi coverage within the apartment. Funny that they'll sell you 500/500Mbps Internet service on a router that cannot possibly deliver it to the majority of modern devices. They're at least nice enough to turn off the WiFi and set Bridge mode, but the box still takes over most of the electrical box in my apartment. Everytime I've had them make any change to my service-level they have turned off bridge-mode and then I have to make yet another call to turn it back on. So in summary I really wish they would replace the big box with a [Ubiquiti Nano G][4] and get out of the business of trying to do things they're terrible at.

### Exploring the device

I began the exploration of the unit to be able to manage it myself. A bit of searching came up with a page that included a binary tool for Linux and Windows to encrypt/decrypt the configuration on the device [aescrypt2_huawei][1] and how to trick the router into allowing you to download the configuration. 

### Get the Get configuration file

The configuration from Get prevents you from downloading the config. To trick the router you'll do the following:

 1) Unplug the fiber cable
 2) Perform a factory reset in the web interface
 3) Wait for it to reboot
 4) Log back in using root/admin and you'll see your access level provides full access
 5) Plug the fiber cable back in 
 6) And then download the config when the WAN light goes solid green
 
### Decrypting the configuration

The configuration is stored as an encrypted XML file. Finding a decryption tool was easy enough, but unfortunately it was provided for Linux and Windows and not for Mac. So I really wanted to know what the encryption key being used was and be able to use it directly on my Mac. So I started looking at the binary with [IDA Pro][5].

Based upon the analysis of the program:
   
   Huawei's encryption key is `hex:13395537D2730554A176799F6D56A239`

To recreate the functionality of the `aescrypt2_huawei` tool you need to compile the source code in this repo and do the following:

   1) `echo -n 'hex:13395537D2730554A176799F6D56A239' > key.txt`
   2) `dd if=config.encrypted of=config_no_header.encrypted bs=1 skip=8`
   3) `./aescrypt2 1 config_no_header.encrypted config.decrypted.gz key.txt`
   4) `gunzip config.decrypted.gz`

After getting the encryption key and searching for it I found a spanish speaking forum that says they got the encryption key from a file found on the device in `/etc/wap/aes_string`.

### Looking at the config

The config is pretty long but the main thing needed was to allow you to add a new user with super-user privileges or change the root/admin account to have the same access as Get provides themselves. In summary, passwords are hashed using

`SHA256(MD5(admin))` which in this example yields  `465c194afb65670f38322df087f0a9bb225cc257e43eb4ac5a0c98ef5b3173ac`. 

on the bash command-line this is accomplished like this:

    echo -n admin | md5 | tr -d '\n' | shasum -a 256

You'll find this user in the config from Get and it has been given reduced privileges (level 1).

### Get user

As defined in the configuration file Get added a user called 'getaccess' and with level 0 privileges (the highest) 

    <X_HW_WebUserInfoInstance InstanceID="2" UserName="getaccess" Password="fc0fe4711c0263f37013e423fde0a8be0d64d45f231c924952327052db50b66f" UserLevel="0" Enable="1" ModifyPasswordFlag="1" PassMode="2"/>

So you can modify the root user UserLevel to 0 and you're really root again. However, it probably makes more sense to add a new user since the root/admin combination is well known.

### One more thing

The astute reader might have noticed I skipped the first 8-bytes before decrypting the file. The properly encrypted Huawei config file has some sort of header (4 bytes) and checksum (4 bytes) and I just ignored it. If you plan on uploading a modified config back to the router you'd need to recreate that header, so in that case I'd use the Linux and Windows tool to be safe. 

### What about replacing the router?

I replaced the Huawei box with a [Ubiquiti Nano G][6]. Get is using the Serial Number of the Huawei router as the method of authentication. This is a relatively common practice. So essentially, the OLT sees the Serial Number and lets it connect. So in the web interface set [Profile 2][9] for Huawei and then the device will reboot. Then SSH to the box and change the Serial Number. Username and password are `ubnt` by default.

On the Nano G you issue the following commands discussed on [this website][7]:

    $ ssh ubnt@192.168.1.1

    > sh

    # cd bin
    # ./gponctl stop

    Stop ONU without sending dying gasp messages

    # ./gponctl setSnPwd --sn 41-4c-43-4c-xx-xx-xx-xx

    ======== Serial Number & Password ========

    Serial Number: 41-4C-43-4C-xx-xx-xx-xx
    Password : 20-20-20-20-20-20-20-20-20-20

    ==========================================

    # ./gponctl init
    # ./gponctl start

    Start ONU with operational state: INIT (01)

    # ./gponctl getSnPwd

    ======== Serial Number & Password =======

    Serial Number: 41-4C-43-4C-xx-xx-xx-xx
    Password : 20-20-20-20-20-20-20-20-20-20

    ==========================================

This will not persist across reboots.

### Persisting the serial number by rewriting firmware

It is pretty easy to rewrite the NVRAM and persist the change. Another security researcher wrote this up

[Rewrite the Serial Number][10]

Lastly, I bought the Nano G from [Senetic][8].



[1]: https://zedt.eu/tech/hardware/obtaining-administrator-access-huawei-hg8247h/
[2]: https://packetstormsecurity.com/files/35655/aescrypt2-1.0.tgz.html
[3]: https://www.get.no
[4]: https://www.ubnt.com/ufiber/ufiber-nano-g/
[5]: https://www.hex-rays.com
[6]: https://www.ubnt.com/ufiber/ufiber-nano-g/
[7]: https://blog.onedefence.com/changing-the-gpon-serial-on-the-ubiquiti-ufiber-nano-g-part-one
[8]: https://www.senetic.no/product/UF-NANO
[9]: https://help.ubnt.com/hc/en-us/articles/115009335068-UFiber-GPON-Supported-Third-Party-OLTs
[10]: https://blog.onedefence.com/changing-the-gpon-serial-on-the-ubiquiti-ufiber-nano-g-part-two/
