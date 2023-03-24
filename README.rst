=========
FPV Robot
=========

.. image:: photo01.jpg
   :width: 100%

.. image:: screenshot01.jpg
   :align: center

This repository contains schematic and software to build 4WD FPV robot/car
based on Raspberry Pi and Arduino. The robot is controlled via a web interface
using Wi-Fi.

Hardware
========

The 4WD robot car platform is used as chassis. The Raspberry Pi with camera
module is used to run web server and stream video. The Arduino Pro Mini is used
to control motors, servos, lighting and read batteries voltage level. Arduino
is connected with Raspberry Pi via serial connection (UART).

Schematic in `schematic.pdf <schematic.pdf>`_.

Supplies:

* 4WD Mobile Platform for Arduino Smart Robot Car
  [https://www.elecrow.com/4wd-mobile-platform-for-arduino-smart-robot-car-p-1531.html]
* Raspberry Pi 3 Model B+
* Raspberry Pi Camera Module
* Micro SD memory card
* Arduino Pro Mini 3.3v ATmega328P
* MX1508 Dual DC Motor Driver Module
* Pan and Tilt Stand
  [https://www.electromaker.io/shop/product/assemb-mini-pan-tilt-kit-wmicro-servos]
* 2 x SG90 Servo
* LM2596S Step Down DC-DC Converter
* MP1584EN Step Down DC-DC Converter
* AMS1117 5.0V Voltage Regulator (module or single chip)
* AMS1117 3.3V Voltage Regulator (module or single chip)
* 3S 18650 Batteries Holder Case
* 3 x 18650 Li-Ion Batteries
* Switch like SS12D07
* 30K resistor
* 10K resistor
* 3K resistor
* 2N2222A NPN Transistor
* 2 x 10uF tantalum capacitor (if using AMS1117 as single chip)
* 2 x 22uF tantalum capacitor (if using AMS1117 as single chip)
* 5 x 3mm white LEDs
* Wires, screws, PCB protoboards, etc.

Software
========

* The ``ard1`` directory contains Arduino sketch
* The ``fpvrobotrpiserver`` directory contains web server application written
  in Python/aiohttp to run on Raspberry Pi

Arduino sketch
--------------

The Arduino sketch requires `servo library
<https://www.arduino.cc/reference/en/libraries/servo/>`_.

Web server
----------

To run web server application on Raspberry Pi firstly download and install
`Raspberry Pi OS <https://www.raspberrypi.com/software/>`_ to memory card. Then
configure Wi-Fi and enable SSH. Determine Raspberry Pi IP address using ``sudo
ip addr``. Connect via SSH and install these packages:

.. code::

   sudo apt install git \
                    python3-aiohttp \
                    python3-aiohttp-jinja2 \
                    python3-picamera2 \
                    python3-pip \
                    python3-serial

Then install aioserial:

.. code::

   sudo pip3 install aioserial

Optionally for HTTP basic authentication install aiohttp-basicauth

.. code::

   sudo pip3 install aiohttp_basicauth

Clone this repository:

.. code::

   git clone git@github.com:lostclus/FPVRobot.git 


Run application:

.. code::

   cd FPVRobot
   python3 -m fpvrobotrpiserver


Then in other device that connected to same local network open web browser and
go to http://<IP>:8080

Configuration
-------------

Web server application can be configured using environment variables.

.. table:: Environment variables
   :widths: auto

   ======================= =============================== =============
   Variable                Description                     Default value
   ======================= =============================== =============
   ARD1_PORT               Serial port to communicate with /dev/serial0
                           Arduino
   ARD1_BAUDRATE           Boud rate of serial connection  9600
   ARD1_TIMEOUT            Timeout of serial connection    0.1
   DEFAULT_CAMERA_SIZE     Default camera resolution       640x480
   DEFAULT_CAMERA_QUALITY  Default camera quality          2
   CAMERA_TRANSFORM        Camera transformation           hflip,vflip
   AUTH_USER               User name for authentication
   AUTH_PASSWORD           Password for authentication
   ======================= =============================== =============

User Interface
----------------

Robot movement, camera movement and lighting control can be via keyboard, mouse
or touchscreen.

.. table:: Keyboard control
   :widths: auto

   =========== =================
   Key         Action
   =========== =================
   W           Move forward
   S           Move backward
   A           Turn left
   D           Turn right
   Space       Stop motors
   Up arrow    Turn camera up
   Down arrow  Turn camera down
   Left arrow  Turn camera left
   Right arrow Turn camera right
   Home        Center camera
   L           Toggle lighting
   =========== =================


.. table:: Top pannel
   :widths: auto

   ============== ============================ =====================
   Icon           Description                  Click Action
   ============== ============================ =====================
   |level slider| Camera settings              Toggle settings view
   |ok hand|      Session is active            Make session not active
   |locked|       Session is not active        Make session active
   |battery|      Normal battery voltage level Power off Raspberry Pi
   |low battery|  Low battery voltage level    Power off Raspberry Pi
   ============== ============================ =====================

.. |level slider| unicode:: 0x1f39a
.. |ok hand| unicode:: 0x1f44c
.. |locked| unicode:: 0x1f512
.. |battery| unicode:: 0x1f50b
.. |low battery| unicode:: 0x1faab
   :trim:
