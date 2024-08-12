# The Serial Expansion HAT

The [Serial Expansion HAT](https://www.waveshare.com/serial-expansion-hat.htm), created by Waveshare adds an SC16IS752 serial controller which brings an additional 2 UARTs and 8 GPIOs.  Multiple of these HATs can be stacked to provide more UARTs and GPIOs.  The UARTs have device names in the format /dev/ttySCX (where X is a number starting at 0).

## Multiple Serial Expansion HATs

When using multiple Serial Expansion HATs, a bit of soldering needs to be done.  Specifically modifiying the I2C Address and Interrupt. In addition, soldering 90° Pin Headers to the GPIO sockets.

![Serial Extension HAT](https://github.com/user-attachments/assets/d1c62465-310c-4b4b-ad27-f8b3c85a7727)

For the testlab, 5 Serial Expansion HATs are used.  They are configured with the following settings
* Board 1: INT 24, I2C Address 0x48 (A1 -> 3V3, A0 -> 3V3) _Default Configuration_
* Board 2: INT 23, I2C Address 0x49 (A1 -> 3V3, A0 -> GND)
* Board 3: INT 22, I2C Address 0x4A (A1 -> 3V3, A0 -> SCL)
* Board 4: INT 21, I2C Address 0x4B (A1 -> 3V3, A0 -> SDA)
* Board 5: INT 20, I2C Address 0x4C (A1 -> GND, A0 -> 3V3)

## The GPIO Pins

One row of GPIO pins is used in connection with each of the attached UARTs.  For UART "a", GPIO pins 0, 2, 4, and 6 are reserved, while for UART "b" GPIO pins 1, 3, 5, and 7 are reserved.  GPIO pins 0 and 1 are used to control the power relays for their power sockets while GPIO pins 2 and 3 are used to control the reset button relays.

## The Linux Kernel

The Linux kernel is hard coded with a maximum of 8 UARTs controlled via connected SC16IS752 chips.  The reason for this limit is not clear and is probably a case of "8 should be enough".  With a small modification to the kernel, this can be easily increased to 16.  A patch can be seen [here](https://github.com/pmelange/raspi-linux/commit/3ed315a591d3fe72dc2cf187ba897a87ea06bf11).  For more information about how to compile and install the Linux kernel, please take a look at the documentation at raspberrypi.com page [The Linux kernel](https://www.raspberrypi.com/documentation/computers/linux_kernel.html)

## Device Tree overlay for the SC16IS752

To install the kernel module for the Serial Expansion HAT, the file ```/boot/firmware/config.txt``` needs to be edited to add the following _(modify the interrupt pin and address as needed)_.  

NOTE: the oder of the ```dtoverlay``` entries seems to be important in so far as to the ordering of ```/dev/ttySCX``` and which gpiochipY is assigned to which HAT.   In this example, the HAT with address 0x48 is assigned ```/dev/ttySC0``` and ```/dev/ttySC1``` along with gpiochip2 while the HAT with address 0x4c is assigned ```/dev/ttySC8``` ```/dev/ttySC9``` and gpiochip6.

```
dtoverlay=sc16is752-i2c,int_pin=20,addr=0x4c
dtoverlay=sc16is752-i2c,int_pin=21,addr=0x4b
dtoverlay=sc16is752-i2c,int_pin=22,addr=0x4a
dtoverlay=sc16is752-i2c,int_pin=23,addr=0x49
dtoverlay=sc16is752-i2c,int_pin=24,addr=0x48
```
