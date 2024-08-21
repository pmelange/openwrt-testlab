# openwrt-testlab

The idea behind the openwrt-testlab is to provide a way to programtically test new OpenWrt based firmwares and firmware features on multiple hardware tagets.  These tests may include interactions between OpenWrt devices (such has meshing) requiring multiple devices to be flashed and configured simultaneously.

Future plans include adding smartphones and other devices to test WiFi connectivity with the attached OpenWrt devices.

![Testlab](https://github.com/user-attachments/assets/342c0612-ab7b-4b83-ad80-b10386c611cb)
![patchpanel](https://github.com/user-attachments/assets/a955a3a7-a62a-4301-84dc-18d35c71b239)

---

## Hardware Setup

The openwrt-testlab is built using a Raspberry Pi 4 as the controlling mechanism for all the attached OpenWrt devices.  Attched to the Raspberry Pi are multiple Serial Expansion HATs and relays.  The additional UARTs provided by the Serial Expansion HATs provide a serial TTY interface to each of the attached OpenWrt devices while the relays control the power and simulate pressing the reset button of the addached OpenWrt devices.

In addition, there are two auxillary power sockets controled with relays.  The idea behind these power sockets is for other types of devices which do not necessarily need to be tested but which would be used by the tested devices such as a managed switch.

Each attached OpenWrt device has a network socket positioned next to it's power socket.  The sockets are then connected to a patch panel where a managed switch can be attached.  This is to reduce cable clutter.

### Connecting a Device to the openwrt-testlab

![testdev1](https://github.com/user-attachments/assets/495f7078-c43f-448b-be26-f172b0fad3ab)

For each attached OpenWrt device, there is a power socket, a network socket, a TTY serial interface terminal and a reset button terminal.  

The power socket and network socket should be self explanatory. 

**Pinout for the Reset/TTY Terminals**
Rst | Rst | | Vcc | Gnd | Tx | Rx
--- | --- | --- | --- | --- | --- | ---
Connect to Reset | Connect to Reset | | Not normally needed | Connect to Gnd | Connect to Rx | Connect to Tx

The reset button pins on the terminal are to be connected to additional jumper cables on the attached OpenWrt device.

The TTY serial interface of the attached OpenWrt device must be connected to the terminal such that the TX line of the OpenWrt device is connected to the RX pin on the terminal and the RX line of the OpenWrt device is connected to the RX pin on the terminal.  Ground is always connected to ground.  In addition the Vcc terminal pin is provided but in almost all cases this will not be needed.  For this, the attached OpenWrt device needs to be modified so that jumper cables from the devices TTY serial interface are easily available.

** Documentation on how to modify and wire various OpenWrt devices can be found under [Documendtation/Devices](Documentation/Devices).

### Building the openwrt-testlab

For detailed information about building the openwrt-testlab, see the documenation under [Documentation/Hardware](Documentation/Hardware).

---

## Test Control Software

**This is a work in progress***
The idea is to integrate [labgrid](https://labgrid.readthedocs.io/en/latest/) with the openwrt-testlab as it provides a ready-made set of features.

---

## Installing and Configuring the Operating System on the Raspberry Pi

The Raspberry Pi runs Raspbery Pi OS (based on Debian) with additional changes and potentially a small patch to the Linux kernel.  Detailed information about installing and configuring the operating system can be found under [Documentation/RaspiOS](Documentation/RaspiOS)
