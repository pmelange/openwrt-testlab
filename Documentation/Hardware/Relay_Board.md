# The Realy Board

The [RPi Relay Boards](https://www.waveshare.com/rpi-relay-board.htm) created by Waveshare adds the needed Power Supply relays needed to turn on and off the attached test devices.  Normally these relay boards would be controlled via interrupts lines 25, 28 and 29.  Since multiple of these boards will be attached, then the default interrupt controls will interfere with each other accross all the boards.

Since the [Serial Expansion HATs](Serial_Expansion_HAT.md) provides 8 additional GPIO pins, they provide an easy to understand method for enabling and disabling the power relays.  NOTE: The relays are "active low"

Remove the three jumpers from positions CH1, CH2 and CH3.  In addition, add stacking headers to the relay boards to provide the needed distance to be able to stack the boards.

![Realy Board](https://github.com/user-attachments/assets/510122e1-f792-4ee9-8ffc-6c61451e90ba)

