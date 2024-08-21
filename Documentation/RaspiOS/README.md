To install RapianOS on an SD Card and configure it, follow these instructions.

* Download the most recent 64 bit lite version of raspios from [here](https://www.raspberrypi.com/software/operating-systems/) and extract the image from the downloaded file.
* write the image to the SD Card ```sudo dd if=2024-07-04-raspios-bookworm-arm64-lite.img of=/dev/sdb bs=4M conv=fsync status=progress```
* mount the partition "bootfs"
* In the bootfs partition create an empty file named ssh to activate the ssh server ```touch ssh```
* Set a password for the user pi ```echo "pi:"$(echo 'password' | openssl passwd -6 -stdin) > userconf```
* Unmount the SD card from the PC and install it into the Raspberry Pi.
* Connect the Raspberry Pi to the local LAN with a network cable and boot the device.
* Once booted the Raspberry Pi should get an IP address from the local DHCP server.  Now connect to the device with ```ssh pi@raspberrypi```
* Change the password to something better than "password"
* (optional) add your public ssh key to ".ssh/authorized_keys"
* run ```sudo raspi-config```
  * Set up WiFi under "System Options -> Wireless LAN" as the WiFi interface will be the main method used to connect to the openwrt-testlab.  The cabled connection will be used with the attached devices.
  * Set up a hostname, for example "testlab01" under "System Options -> Hostname" for example ```testlab01```
  * Enable I2C under "Interface Options -> I2C"
  * (optional) Enable the Serial Port under "Interface Options -> Serial Port"
  * (optional) Set the localisation under "Localisation Options -> Locale" to en_US-UTF-8
  * Set the timezone under "Localisation Options -> Timezone"
  * Exit rapi-config via "Finish" and reboot (you can now remove the network cable)

Now it should be possible to log into the device with ```ssh pi@hostname``` where hostname is the name you used above.

Upgrade the system with:
```
sudo apt-get update
sudo apt-get --with-new-pkgs upgrade
```
reboot the system.
```
sudo reboot
```
After the reboot, remove old packages
```
auto apt-get autoremove
```

---

Now it is time to patch and build a new linux kernel.  The instructions can be found [here](https://www.raspberrypi.com/documentation/computers/linux_kernel.html) and it is important to apply the patch [0001-sc16is7xx.c-increase-SC16IS7XX_MAX_DEVS-to-16.patch](0001-sc16is7xx.c-increase-SC16IS7XX_MAX_DEVS-to-16.patch) before starting the build.  This patch is needed when more than 4 of the Serial Expansion HATs are used.  With the MAX_DEVS set to 16, up to 8 of the HATs can be used.  If more are needed, adjust the MAX_DEVS accordingly.

```
sudo apt install git
git clone --depth=1 https://github.com/raspberrypi/linux
cd linux
wget -O /tmp/patch https://github.com/pmelange/openwrt-testlab/blob/main/Documentation/RaspiOS/0001-sc16is7xx.c-increase-SC16IS7XX_MAX_DEVS-to-16.patch](https://raw.githubusercontent.com/pmelange/openwrt-testlab/main/Documentation/RaspiOS/0001-sc16is7xx.c-increase-SC16IS7XX_MAX_DEVS-to-16.patch
git apply /tmp/patch
sudo apt install bc bison flex libssl-dev make
KERNEL=kernel8
make bcm2711_defconfig
CONFIG_LOCALVERSION="-v8-TESTLAB"
make -j6 Image.gz modules dtbs
sudo make -j6 modules_install
sudo cp /boot/firmware/$KERNEL.img /boot/firmware/$KERNEL-backup.img
sudo cp arch/arm64/boot/Image.gz /boot/firmware/$KERNEL.img
sudo cp arch/arm64/boot/dts/broadcom/*.dtb /boot/firmware/
sudo cp arch/arm64/boot/dts/overlays/*.dtb* /boot/firmware/overlays/
sudo cp arch/arm64/boot/dts/overlays/README /boot/firmware/overlays/
```
and reboot into the new kernel.
