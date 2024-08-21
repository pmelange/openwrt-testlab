
The hardware for the openwrt-testlab is based on the RaspberryPi, some HATs, some relays, and electric components.

![Testlab](https://github.com/user-attachments/assets/342c0612-ab7b-4b83-ad80-b10386c611cb)

# Hardware List
* [Raspberry Pi 4B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
* 32GB MicroSD Card
* 3.1A Power Supply for the Raspberry Pi
* 5x [Serial Expansion HAT](Serial_Expansion_HAT.md) from Waveshare
* 4x [Relay Board](Relay_Board.md) from Waveshare
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

# Tool List
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

# Building/Stacking the Pi

In order to build the HATs onto the Pi, some modifications first need to be done to the [Serial Expansion HATs](Serial_Expansion_HAT.md) and the [Relay Boards](Relay_Board.md).  In addition, an _optional_ [Prototype Board](#protoype-board) can be created to provide easier access to the 5V and Ground as well as IRQ Pins 25 and 26 while leaving the a full Stacking Header exposed for future expansion if needed.

On the Raspberry Pi, add the Relay Boards including adding any necessary extra Stacking Headers to ensure that the pieces fit properly.  Above the Relay Boards, add the Serial Expansion HATs with the optional Prototype Board on the top.

## Power Relay GPIO Control

For each of the Serial Expansion HATs, run a jumper from GPIO pins 0 and 1 to the [Relay Board](Relay_Board.md) pins CH1, CH2 or CH3 as appropriate.  These GPIO pins will be used to control the power supplies connected to the relays.

![Realy Board CH](https://github.com/user-attachments/assets/df63b494-1ff3-4716-b063-a60a13f9666a)
![Realy Board Jumper](https://github.com/user-attachments/assets/50991b40-8272-404c-9b35-8ec8b01f0f85)

## Power Relay Terminal Block Electric Wiring

The enabling/disabling of the GPIO pins on the Serial Expansion HATs control the power sockets for each test position.  The center terminal of each terminal block provides the power input for all the relays to switch on and off.  Wire all of the central terminals together.  To do this, cut the wire to the proper length and add insulated ferrules to the ends (use double ferrules when needed).  In this example, these are the brown wires.

In addition, add wires with insulated ferrules to the "normally open" side of the terminal blocks.  These will be "switched on" when the relays is activated, thus providing power to the power sockets.  In this example, these are the red wires.

![Relay_power_wiring](https://github.com/user-attachments/assets/9ec21159-defd-429c-a6eb-89ce80406098)

### Protoype Board

Optional: Create a Prototype Board which has a Stacking Header on one end to stack on top of the Raspberry Pi and expands the number of 5V and GND pins to power the additional Relay Modules.  While creating this board, it was not yet clear if 3.3V or 5V would be used.  Having the voltage selectable is not required.

In addition the IRQ Pins 25 and 26 were added for convenience as these are used to control the power relays for power sockets AUX1 and AUX2.

![ProtoBoard](https://github.com/user-attachments/assets/80ed4984-d909-45bd-9e1c-f44c3c19fe2a)
![ProtoBoardBack](https://github.com/user-attachments/assets/f82671d1-707d-44c5-8f1e-25a2e171cf16)

# Reset Button Relays

The [Relay Module 5 V: 1 Channel Relay Board with Optocoupler](https://www.amazon.de/Vaileal-Relay-Module-Optocoupler-Performance/dp/B0C8JCHT5S?language=en_GB&currency=EUR) are used to simulate pressing the reset button (or any other button) on the test devices.  Other relay modules can be used, but their electrontical properties may be different from what is used here.  The following information is specific to this model.

Connect all the DC+ terminals to 5V (on the prototype board) and DC- terminals to Ground.  In addition, connect GPIO pins 2 or 3 (as needed and logical) from the differnt Serial Expansion HATs to the IN1 terminals.  Leave jumper "High/Low Level Trigger" at "H".  The COM and NO terminals are to be connected to the reset button of the test device.

# Electrical Wiring

Using the Terminal Block Set-12 Positions, bridge the connections needed for the Earth connections (yellow) and the neutral connections (blue).  In addition, attach the output from the power relays (red wires) to a third 12P terminal block.  From these terminal blocks, run power to each of the power sockets using the Insulated Wire Connectors.  Make sure that the plastic cover is installed on the P12 Terminals to protect the user.

Install the power sockets

NOTE: When connected to power, make sure that the orientation of the plug is such that the Line(L) is connected to the Relay Boards and Neutral(N) is connected to the blue P12 Terminal.

# Serial and Reset Headers

Using protoype boards, create 10 "Searial & Reset Headers".  These provide easy access to the UARTs and Reset Relays in a convenient spot.  The left pair of pins provide the "reset" button press (order does not matter) from the [Reset Button Relays](#reset-button-relays).  The right set of pins provide, from left to right, Vcc Gnd Tx Rx which are connected to the UARTs on the Serial Expansion HATs.

![Serial Reset Header](https://github.com/user-attachments/assets/2b6183d1-012e-4ac5-91b3-6ca089b6fc43)

# RJ45 Ethernet Ports

Connect RJ45 Keystone modules from the test locations to a patch panel to provide a more manageable network setup.  In this example, a 12 port patch panel is used whereby port 1-10 are for the 10 test locations and port 12 is connected to the Raspberry Pi.  The idea is that a switch shall be connected to these ports and programtically controlled to provide access to multiple VLANs and networks.

# Additional/Optional

* Add a power cable to the entire setup, connecting to the Ground P12 Termninal, the Neutral P12 Terminal and the Line to the Relay Boards' input (center terminal).
* Add an always-on power socket to supply the Raspberry Pi. 
