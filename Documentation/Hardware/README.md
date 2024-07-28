
# Hardware Developemnt
The hardware for the openwrt-testlab is based on the RaspberryPi, some HATs, some relays, and electric components.

## Hardware List
* [Raspberry Pi 4B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
* 32GB MicroSD Card
* 3.1A Power Supply for the Raspberry Pi
* 4x [RPi Relay Board from Wareshare](https://www.waveshare.com/rpi-relay-board.htm)
* 5x [Serial Expansion HAT for Raspberry Pi from Waveshare](https://www.waveshare.com/serial-expansion-hat.htm)
* 10x [Relay Module 5 V: 1 Channel Relay Board with Optocoupler](https://www.amazon.de/Vaileal-Relay-Module-Optocoupler-Performance/dp/B0C8JCHT5S?language=en_GB&currency=EUR)
* M2 Spacers Male Female Hex Brass Spacers for Raspberry Pi Motherboard
* 1.5mm electrical wire
* 1.5mm DIN Wire End Ferrules/Twin Insulated
* 1.5mm DIN Wire End Ferrules/Single Insulated
* 3x Terminal Block Set, 12 Positions, Dual Row Screw Terminals Strip with cover
* 50x 1.5mm Insulated Wire Connectors
* 13x Surface Mount Power Sockets (Schuko for Europe)
* 1.5mm Flexible Power Cable
* 12 Port RJ45 Patch Panel
* 10x RJ45 Keystome Modules
* Cat 6 S/FTP Cable
* Prototyping Circuit Boards
* 2.54mm Pin Headers
* 2x20 (40 Pin) Stacking Headers
* Jumper Cables in various lengths
* 3x Chandelier Clamp
* 4x20 Screws
* A Mounting Surface

## Tool List
* Soldering Iron
* Solder
* Screwdrivers
* LSA Tool
* Cabel Insulation Remover
* Cable Cutter
* Digital Multimeter
* Electrician Crimping Tool
* Hot Glue Gun w/ Glue Sticks
* Label Printer

## Building the Pi
In order to build the HATs onto the Pi, some modifications need to be done to the Serial Expansion HAT when more than one of these boards are used.  Specifically modifiying the I2C Address and Interrupt.  In addition, solder 90° Pin Headers to the GPIO sockets.

![Serial Extension HAT](https://github.com/user-attachments/assets/d1c62465-310c-4b4b-ad27-f8b3c85a7727)

In this example, 5 Serial Expansion HATs are used.  They are configured with the following settings
* Board 1: INT 24, I2C Address 0x48 (A1 -> 3V3, A0 -> 3V3) _Default Configuration_
* Board 2: INT 23, I2C Address 0x49 (A1 -> 3V3, A0 -> GND)
* Board 3: INT 22, I2C Address 0x4A (A1 -> 3V3, A0 -> SCL)
* Board 4: INT 21, I2C Address 0x4B (A1 -> 3V3, A0 -> SDA)
* Board 5: INT 20, I2C Address 0x4C (A1 -> GND, A0 -> 3V3)

Above each of the Relay Boards install a Stacking Header.  The reason for this is because the screw terminals on the Realy Board are too high to stack the HATs without them.  In addition, remove the jumpers from the Realy Boards as we will be wiring them directly to the GPIO pins on the Serial Extension HATs.

![Realy Board](https://github.com/user-attachments/assets/510122e1-f792-4ee9-8ffc-6c61451e90ba)

Optional: Create a Prototype Board which has a Stacking Header on one end to stack on top of the Raspberry Pi and expands the number of 5V and GND pins to power the additional Relay Modules.  While creating this board, it was not yet clear if 3.3V or 5V would be used.  In addition the IRQ Pins 25 and 26 were added for convenience as these are used to control the power relays for power sockets AUX1 and AUX2.

![ProtoBoard](https://github.com/user-attachments/assets/80ed4984-d909-45bd-9e1c-f44c3c19fe2a)
![ProtoBoardBack](https://github.com/user-attachments/assets/f82671d1-707d-44c5-8f1e-25a2e171cf16)
