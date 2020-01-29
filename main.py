# launch gpib_config before
# used with AGILENT 34970A QAQ

import RPi.GPIO as GPIO
import smbus
import pyvisa
import time
import asyncio
from utils.asynchelpers import start_timer, show_timer
from utils.timer import Timer

try:
    i2c = smbus.SMBus(1) # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
except:
    raise IOError("Could not find i2c device")

# ADC Config
ADDRESS = 0x48
REG_READ = 0x00
REG_CONFIG = 0x01

# Write config register to the ADC
bytes = [0xC2, 0x83]
i2c.write_i2c_block_data(ADDRESS, REG_CONFIG, bytes)
# Wait
time.sleep(1)

# DAQ
rm = pyvisa.ResourceManager()
# print(rm.list_resources())

daq = rm.open_resource("GPIB0::1::INSTR")
# print(daq.query('*IDN?'))

# Loop
start_timer()
loop = asyncio.get_event_loop()

#IO Config
OPEN = GPIO.LOW
CLOSE = GPIO.HIGH
Float = 23
FillingValve = 17
waterLevel = False

async def FloatHighRebound_callback():
    show_timer(f"Flag Float.timerHighRebound_callback")
    global waterLevel
    waterLevel = True

timerHighRebound = Timer('timerHighRebound', 3, FloatHighRebound_callback)

def onFloatEvent(channel):
    if GPIO.input(channel):
        # Negative Edge detected
        show_timer("Float is up")
        asyncio.run_coroutine_threadsafe(timerHighRebound.start(), loop)
    else:
        # Positive Edge detected
        show_timer("Float is down")
        asyncio.run_coroutine_threadsafe(timerHighRebound.cancel(), loop)

async def main():
    # Define I/O
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(Float, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(Float, GPIO.BOTH, callback=onFloatEvent)

    GPIO.setup(FillingValve, GPIO.OUT, initial=CLOSE)

    # Filling
    print("Start filling")
    GPIO.output(FillingValve, OPEN)

    while (not waterLevel):
        await asyncio.sleep(0.2)  # each 200ms

    print("Tank is now filled")
    GPIO.output(FillingValve, CLOSE)

    fichier = open("data.csv", "w")
    fichier.write("#;ANA;T_Out;T_In\n")
    fichier.close()
    for i in range (0,3600):
        # Read DAQ
        daq.write('MEAS:TEMP? TC,T,(@105)')
        t1 = float("{0:.2f}".format(float(daq.read())))

        daq.write('MEAS:TEMP? TC,K,(@106)')
        t2 = float("{0:.2f}".format(float(daq.read())))

        # Read the conversion results
        result = i2c.read_i2c_block_data(ADDRESS, REG_READ, 2)
        val = (result[0] << 8) | (result[1])
        if val > 0x7FFF:
            val = (val - 0xFFFF)
        else:
            val = (result[0] << 8) | (result[1])

        print(f"{i};{val};{t1};{t2}")
        fichier = open("data.csv", "a")
        fichier.write(f"{i};{val};{t1};{t2}\n")
        fichier.close()
        time.sleep(1)

try:
    asyncio.ensure_future(main())
    loop.run_forever()
except KeyboardInterrupt:
    GPIO.cleanup()  # clean up GPIO
    print("clean up done")