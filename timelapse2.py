# Takes automated timelapses with an interface

import time
import subprocess
import math
import digitalio
import board
import re
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

## Initialize the display

# Setup the hardware buttons
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()
 
# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=240,
    height=240,
    x_offset=0,
    y_offset=80,
)
 
# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90
 
# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
 
# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)

# Prepare the font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
fontSmall = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 1)
redText = "#A00000"
whiteText = "#969696"
greyText = "#777777"
blackText = "#000000"

# Turn on the backlight and prepare the buttons
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input()
buttonB.switch_to_input()


## Test shot?


## User Settings

# Get the end time
startTimeDisp = time.localtime()
endTimeDisp = [startTimeDisp[3],startTimeDisp[4] + 30]
if endTimeDisp[1] >= 60:
    endTimeDisp[0] = endTimeDisp[0] + 1
    endTimeDisp[1] = endTimeDisp[1] - 60
        
endTimeOutput = [" ", " "]
if endTimeDisp[0] < 10:
    endTimeOutput[0] = "0" + str(int(endTimeDisp[0]))
else:
    endTimeOutput[0] = str(int(endTimeDisp[0]))
if endTimeDisp[1] < 10:
    endTimeOutput[1] = "0" + str(int(endTimeDisp[1]))
else:
    endTimeOutput[1] = str(int(endTimeDisp[1]))

# Initial Display
draw.rectangle((0, 210, 119, 240), outline=0, fill=(150, 150, 150))
draw.rectangle((121, 210, 240, 240), outline=0, fill=(150, 150, 150))
draw.text((10,215), "Change", font=font, fill=blackText)
draw.text((130,215), "Next", font=font, fill=blackText)
# draw.text((5,5), "Duration: 30 Minutes", font=font, fill=redText)
draw.text((5,35), "Interval: 1 minute", font=font, fill=whiteText)
draw.text((5,65), "Max Shutter: 20\"", font=font, fill=whiteText)
draw.text((5,95), "Max ISO: 3200", font=font, fill=whiteText)
draw.text((5,125), "Start: 1/30, ISO 100", font=font, fill=whiteText)
draw.text((5,155), "Start", font=font, fill=whiteText)
draw.text((5,185), "30 Shots", font=font, fill=greyText)
draw.text((5,5),"Duration: 30 minutes", font=font, fill=whiteText)

disp.image(image, rotation)

# Variables of options

# Timelapse duration
TLtime = [[300, "5 minutes"],
         [900, "15 minutes"],
         [1800, "30 minutes"],
         [3600, "1 hour"],
         [7200, "2 hours"],
         [14400, "4 hours"],
         [43200, "12 hours"],
         [86400, "24 hours"]]
         
TLtimeIndex = 2

# Timelapse interval
TLintr = [[30, "30 seconds"],
         [60, "1 minute"],
         [120, "2 minutes"],
         [300, "5 minutes"],
         [600, "10 minutes"],
         [1800, "30 minutes"],
         [3600, "1 hour"]]
         
TLintrIndex = 1
numShots = TLtime[TLtimeIndex][0]/TLintr[TLintrIndex][0]

# Get the settings from the camera
subprocess.check_output("bash /home/pi/CameraLogs/getSettings.sh", shell=True)
cameraFile = open('cameraLog.txt', 'r')
cameraText = cameraFile.read()
# print(cameraText)

# Timelapse settings shutter speed
# TLsettingsTime = [[3, "1/2000"],
             # [6, "1/1000"],
             # [9, "1/500"],
             # [12, "1/250"],
             # [16, "1/100"],
             # [19, "1/50"],
             # [21, "1/30"],
             # [23, "1/20"],
             # [25, "1/13"],
             # [27, "1/8"],
             # [29, "1/5"],
             # [31, "1/3"],
             # [33, "1/2"],
             # [35, "1/1.3"],
             # [36, "1\""],
             # [37, "1.3\""],
             # [39, "2\""],
             # [41, "3\""],
             # [43, "5\""],
             # [44, "6\""],
             # [45, "8\""],
             # [46, "10\""],
             # [47, "13\""],
             # [48, "15\""],
             # [49, "20\""],
             # [50, "25\""],
             # [51, "30\""]]
             
# TLsettingsISO = [[3, "100"],
#              [6, "200"],
#              [9, "400"],
#              [12, "800"],
#              [15, "1600"],
#              [18, "3200"],
#              [21, "6400"]]

# Getting the ISO list from camera

loopStoop = 0
TLsettingsISO = []
loopIndex = 0
while loopStoop == 0:
    ISOregex1 = 'ISO[\s\S]*?(?:Choice: (\d+) \d+\s){1,'+str(loopIndex+1)+'}[\s\S]*?END'
    ISOregex2 = 'ISO[\s\S]*?(?:Choice: \d+ (\d+)\s){1,'+str(loopIndex+1)+'}[\s\S]*?END'
    tempISO1 = re.findall(ISOregex1, cameraText)
    tempISO2 = re.findall(ISOregex2, cameraText)
    if loopIndex >= 1:
        if [tempISO1, tempISO2] == TLsettingsISO[-1]:
            loopStoop = 1
        else:
            TLsettingsISO.append([tempISO1, tempISO2])
    else:
        TLsettingsISO.append([tempISO1, tempISO2])
    loopIndex = loopIndex + 1
    
# Getting the Shutter speed list from camera    

loopStoop = 0
TLsettingsTime = []
loopIndex = 0
while loopStoop == 0:
    TimeRegex1 = 'Shutter[\s\S]*?(?:Choice: (\d+) \d+\.\d+s\s){1,'+str(loopIndex+1)+'}[\s\S]*?END'
    TimeRegex2 = 'Shutter[\s\S]*?(?:Choice: \d+ (\d+\.\d+)s\s){1,'+str(loopIndex+1)+'}[\s\S]*?END'
    tempTime1 = re.findall(TimeRegex1, cameraText)
    tempTime2 = re.findall(TimeRegex2, cameraText)
    if loopIndex >= 1:
        if [tempTime1, tempTime2] == TLsettingsTime[-1]:
            loopStoop = 1
        else:
            TLsettingsTime.append([tempTime1, tempTime2])
    else:
        TLsettingsTime.append([tempTime1, tempTime2])
    loopIndex = loopIndex + 1
    
# Getting the Aperture list from camera    

loopStoop = 0
TLsettingsF = []
loopIndex = 0
while loopStoop == 0:
    FRegex1 = 'F-[\s\S]*?(?:Choice: (\d+) f\/\d+\.?\d?\s){1,'+str(loopIndex+1)+'}[\s\S]*?END'
    FRegex2 = 'F-[\s\S]*?(?:Choice: \d+ f\/(\d+\.?\d?)\s){1,'+str(loopIndex+1)+'}[\s\S]*?END'
    tempF1 = re.findall(FRegex1, cameraText)
    tempF2 = re.findall(FRegex2, cameraText)
    if loopIndex >= 1:
        if [tempF1, tempF2] == TLsettingsF[-1]:
            loopStoop = 1
        else:
            TLsettingsF.append([tempF1, tempF2])
    else:
        TLsettingsF.append([tempF1, tempF2])
    loopIndex = loopIndex + 1

print(TLsettingsTime)
print(TLsettingsISO)
print(TLsettingsF)
             
TLsettingsIndex = [6, 0]

maxShutter = 24

maxISO = 5

# loop until user says go
go = 0
while go == 0:

    # Update display
    draw.rectangle((0, 120, 240, 150), outline=0, fill=(0, 0, 0))
    draw.text((5,125), "Start: " + str(TLsettingsTime[TLsettingsIndex[0]][1]) + ", ISO " + str(TLsettingsISO[TLsettingsIndex[1]][1]), font=font, fill=whiteText)
    draw.rectangle((0, 150, 240, 180), outline=0, fill=(0, 0, 0))
    draw.text((5,155), "Start", font=font, fill=redText)
    draw.rectangle((0, 210, 119, 240), outline=0, fill=(150, 150, 150))
    draw.rectangle((121, 210, 240, 240), outline=0, fill=(150, 150, 150))
    draw.text((10,215), "Start", font=font, fill=blackText)
    draw.text((130,215), "Next", font=font, fill=blackText)
    disp.image(image, rotation)
    
    # Start Timelapse
    
    while not buttonB.value:
        time.sleep(0.01)
    while buttonB.value and buttonA.value:
        time.sleep(0.01)
    if not buttonA.value:
        go = 1

    # Update display
    draw.rectangle((0, 150, 240, 180), outline=0, fill=(0, 0, 0))
    draw.text((5,155), "Start", font=font, fill=whiteText)
    draw.rectangle((0, 0, 240, 30), outline=0, fill=(0, 0, 0))
    draw.text((5,5),"Duration: " + str(TLtime[TLtimeIndex][1]), font=font, fill=redText)
    draw.rectangle((0, 210, 119, 240), outline=0, fill=(150, 150, 150))
    draw.rectangle((121, 210, 240, 240), outline=0, fill=(150, 150, 150))
    draw.text((10,215), "Change", font=font, fill=blackText)
    draw.text((130,215), "Next", font=font, fill=blackText)
    
    # Deciding timelapse duration
    while not buttonB.value:
        time.sleep(0.01)
    while buttonB.value and go == 0:
        disp.image(image, rotation)
        if not buttonA.value:
            if TLtimeIndex == 7:
                TLtimeIndex = -1
            TLtimeIndex = TLtimeIndex + 1
            draw.rectangle((0, 0, 240, 30), outline=0, fill=(0, 0, 0))
            draw.text((5,5),"Duration: " + str(TLtime[TLtimeIndex][1]), font=font, fill=redText)
            draw.rectangle((0, 180, 240, 210), outline=0, fill=(0, 0, 0))
            numShots = TLtime[TLtimeIndex][0]/TLintr[TLintrIndex][0]
            draw.text((5,185), str(int(numShots)) + " Shots", font=font, fill=greyText)
            disp.image(image, rotation)
            while not buttonA.value:
                time.sleep(0.01)
        time.sleep(0.01)
        
    # Update display
    draw.rectangle((0, 0, 240, 30), outline=0, fill=(0, 0, 0))
    draw.text((5,5),"Duration: " + str(TLtime[TLtimeIndex][1]), font=font, fill=whiteText)
    draw.rectangle((0, 30, 240, 60), outline=0, fill=(0, 0, 0))
    draw.text((5,35), "Interval: " + str(TLintr[TLintrIndex][1]), font=font, fill=redText)
    
    # Deciding timelapse interval
    while not buttonB.value:
        time.sleep(0.01)
    while buttonB.value and go == 0:
        disp.image(image, rotation)
        if not buttonA.value:
            if TLintrIndex == 6 or TLintr[TLintrIndex+1][0] >= TLtime[TLtimeIndex][0]:
                TLintrIndex = -1
            TLintrIndex = TLintrIndex + 1
            draw.rectangle((0, 30, 240, 60), outline=0, fill=(0, 0, 0))
            draw.text((5,35), "Interval: " + str(TLintr[TLintrIndex][1]), font=font, fill=redText)
            draw.rectangle((0, 180, 240, 210), outline=0, fill=(0, 0, 0))
            numShots = TLtime[TLtimeIndex][0]/TLintr[TLintrIndex][0]
            draw.text((5,185), str(int(numShots)) + " Shots", font=font, fill=greyText)
            disp.image(image, rotation)
            while not buttonA.value:
                time.sleep(0.01)
        time.sleep(0.01)
        
    # Update display
    draw.rectangle((0, 30, 240, 60), outline=0, fill=(0, 0, 0))
    draw.text((5,35), "Interval: " + str(TLintr[TLintrIndex][1]), font=font, fill=whiteText)
    draw.rectangle((0, 60, 240, 90), outline=0, fill=(0, 0, 0))
    draw.text((5,65), "Max Shutter: " + str(TLsettingsTime[maxShutter][1]), font=font, fill=redText)
    
    # Deciding Max Shutter
    while not buttonB.value:
        time.sleep(0.01)
    while buttonB.value and go == 0:
        disp.image(image, rotation)
        if not buttonA.value:
            if maxShutter == 26:
                maxShutter = -1
            maxShutter = maxShutter + 1
            draw.rectangle((0, 60, 240, 90), outline=0, fill=(0, 0, 0))
            draw.text((5,65), "Max Shutter: " + str(TLsettingsTime[maxShutter][1]), font=font, fill=redText)
            disp.image(image, rotation)
            while not buttonA.value:
                time.sleep(0.01)
        time.sleep(0.01)
    
    # Update display
    draw.rectangle((0, 60, 240, 90), outline=0, fill=(0, 0, 0))
    draw.text((5,65), "Max Shutter: " + str(TLsettingsTime[maxShutter][1]), font=font, fill=whiteText)
    draw.rectangle((0, 90, 240, 120), outline=0, fill=(0, 0, 0))
    draw.text((5,95), "Max ISO: " + str(TLsettingsISO[maxISO][1]), font=font, fill=redText)
    
    # Deciding Max ISO
    while not buttonB.value:
        time.sleep(0.01)
    while buttonB.value and go == 0:
        disp.image(image, rotation)
        if not buttonA.value:
            if maxISO == 6:
                maxISO = -1
            maxISO = maxISO + 1
            draw.rectangle((0, 90, 240, 120), outline=0, fill=(0, 0, 0))
            draw.text((5,95), "Max ISO: " + str(TLsettingsISO[maxISO][1]), font=font, fill=redText)
            disp.image(image, rotation)
            while not buttonA.value:
                time.sleep(0.01)
        time.sleep(0.01)
    
    # Update display
    draw.rectangle((0, 90, 240, 120), outline=0, fill=(0, 0, 0))
    draw.text((5,95), "Max ISO: " + str(TLsettingsISO[maxISO][1]), font=font, fill=whiteText)
    draw.rectangle((0, 120, 240, 150), outline=0, fill=(0, 0, 0))
    draw.text((5,125), "Start: " + str(TLsettingsTime[TLsettingsIndex[0]][1]) + ", ISO " + str(TLsettingsISO[TLsettingsIndex[1]][1]), font=font, fill=redText)
    
    # Deciding timelapse initial settings
    while not buttonB.value:
        time.sleep(0.01)
    while buttonB.value and go == 0:
        disp.image(image, rotation)
        if not buttonA.value:
            if TLsettingsIndex[0] < maxShutter:
                TLsettingsIndex[0] = TLsettingsIndex[0] + 1
            elif TLsettingsIndex[1] < maxISO:
                TLsettingsIndex[1] = TLsettingsIndex[1] + 1
            elif TLsettingsIndex[1] == maxISO:
                TLsettingsIndex[0] = 0
                TLsettingsIndex[1] = 0
            draw.rectangle((0, 120, 240, 150), outline=0, fill=(0, 0, 0))
            draw.text((5,125), "Start: " + str(TLsettingsTime[TLsettingsIndex[0]][1]) + ", ISO " + str(TLsettingsISO[TLsettingsIndex[1]][1]), font=font, fill=redText)
            disp.image(image, rotation)
            while not buttonA.value:
                time.sleep(0.01)
        time.sleep(0.01)
        
    
    
## Timelapse

# Reset display
draw.rectangle((0, 0, 240, 240), outline=0, fill=(0, 0, 0))

# put the time in timelapse
startTime = time.time()
startTimeDisp = time.localtime()
endTimeDisp = [startTimeDisp[3],startTimeDisp[4]]
if endTimeDisp[0] + math.floor(TLtime[TLtimeIndex][0] / 3600) > 24:
    endTimeDisp[0] = endTimeDisp[0] + math.floor(TLtime[TLtimeIndex][0] / 3600) - 24
    endTimeDisp[1] = endTimeDisp[1] + math.floor(TLtime[TLtimeIndex][0]/60) - math.floor(TLtime[TLtimeIndex][0] / 3600) * 3600
    if endTimeDisp[1] >= 60:
        endTimeDisp[0] = endTimeDisp[0] + 1
        endTimeDisp[1] = endTimeDisp[1] - 60
else:
    endTimeDisp[0] = endTimeDisp[0] + math.floor(TLtime[TLtimeIndex][0] / 3600)
    endTimeDisp[1] = endTimeDisp[1] + math.floor(TLtime[TLtimeIndex][0]/60) - math.floor(TLtime[TLtimeIndex][0] / 3600) * 3600
    if endTimeDisp[1] >= 60:
        endTimeDisp[0] = endTimeDisp[0] + 1
        endTimeDisp[1] = endTimeDisp[1] - 60
        
endTimeOutput = [" ", " "]
if endTimeDisp[0] < 10:
    endTimeOutput[0] = "0" + str(int(endTimeDisp[0]))
else:
    endTimeOutput[0] = str(int(endTimeDisp[0]))
if endTimeDisp[1] < 10:
    endTimeOutput[1] = "0" + str(int(endTimeDisp[1]))
else:
    endTimeOutput[1] = str(int(endTimeDisp[1]))
currentTime = time.time()
    
lastTime = 0
endTime = startTime + TLtime[TLtimeIndex][0]
currentShot = 0
backLit = True

while not buttonB.value or not buttonA.value:
    time.sleep(0.01)

# Timelapse
while currentShot < numShots:
    draw.rectangle((0, 210, 119, 240), outline=0, fill=(150, 150, 150))
    draw.rectangle((121, 210, 240, 240), outline=0, fill=(150, 150, 150))
    draw.text((10,215), "Cancel", font=font, fill=blackText)
    draw.text((130,215), "Screen Off", font=font, fill=blackText)
    draw.rectangle((0, 180, 240, 210), outline=0, fill="#000000")
    disp.image(image, rotation)
    loadBar = 0
    while currentTime < lastTime + TLintr[TLintrIndex][0]:
        # Backlight switching
        if not buttonB.value:
            if backLit:
                backlight.value = False
                backLit = False
            else:
                backlight.value = True
                backLit = True
            while not buttonB.value:
                time.sleep(0.01)
        
        # Cancel on button press
        if not buttonA.value:
            draw.text((5,155), "Canceled", font=font, fill="#993333")
            disp.image(image, rotation)
            exit()
        time.sleep(0.05)
        currentTime = time.time()
        if int((currentTime - lastTime) / TLintr[TLintrIndex][0] * 240) > loadBar + 5:
            draw.rectangle((0, 190, int((currentTime - lastTime) / TLintr[TLintrIndex][0] * 240), 208), outline=0, fill="#336699")
            disp.image(image, rotation)
            loadBar = int((currentTime - lastTime) / TLintr[TLintrIndex][0] * 240)
        
    # Capture image
    currentShot = currentShot + 1
    lastTime = time.time()
    nefName = "cap" + str(currentShot) + '.nef'
    draw.rectangle((0, 0, 240, 210), outline=0, fill=(0, 0, 0))
    draw.text((5,5), "Shot #" + str(currentShot) + "/" + str(int(numShots)), font=font, fill=whiteText)
    draw.text((5,35), TLsettingsTime[TLsettingsIndex[0]][1] + " - ISO " + TLsettingsISO[TLsettingsIndex[1]][1], font=font, fill=whiteText)
    draw.text((5, 95), "Time Left - " + str(int((numShots - currentShot) * TLintr[TLintrIndex][0] / 3600)) + "h " + str(int((numShots - currentShot) * TLintr[TLintrIndex][0] / 60)) + "m", font=font, fill=whiteText)
    draw.text((5,125), "Taking Picture", font=font, fill=greyText)
    disp.image(image, rotation)
    subprocess.check_output("sudo uhubctl -l 1-1 -p 2 -a 1", shell=True)
    time.sleep(1)
    codeOutput = subprocess.check_output("gphoto2 --set-config shutterspeed=" + str(TLsettingsTime[TLsettingsIndex[0]][0]) + " --set-config iso=" + str(TLsettingsISO[TLsettingsIndex[1]][0]) + " --capture-image-and-download --filename=" + nefName + " --force-overwrite", shell=True)
    subprocess.check_output("sudo uhubctl -l 1-1 -p 2 -a 0", shell=True)
    
    
    # temp jpg to analyze
    draw.rectangle((0, 120, 240, 150), outline=0, fill=(0, 0, 0))
    draw.text((5,125), "Processing", font=font, fill=greyText)
    disp.image(image, rotation)
    subprocess.check_output('exiv2 -e p2 ' + nefName, shell=True)
    jpgName = "cap" + str(currentShot) + '-preview2.jpg'
    
    # Analyze image
    imgLight = subprocess.check_output('identify -format "%[mean]" ' + jpgName, shell=True)
    if float(imgLight) < 10000:
        draw.text((5,65), "Increasing Exposure", font=font, fill=whiteText)
        if TLsettingsIndex[0] < maxShutter:
            TLsettingsIndex[0] = TLsettingsIndex[0] + 1
        elif TLsettingsIndex[1] < maxISO:
            TLsettingsIndex[1] = TLsettingsIndex[1] + 1
    elif float(imgLight) > 30000:
        draw.text((5,65), "Decreasing Exposure", font=font, fill=whiteText)
        if TLsettingsIndex[1] > 0:
            TLsettingsIndex[1] = TLsettingsIndex[1] - 1
        elif TLsettingsIndex[0] > 0:
            TLsettingsIndex[0] = TLsettingsIndex[0] - 1
    else:
        draw.text((5,65), "Maintaining Exposure", font=font, fill=whiteText)
        
    # remove temp file and move image
    subprocess.check_output('rm ' + jpgName, shell=True)
    subprocess.check_output('sudo mv ' + nefName + ' /home/pi/timelapse/shots/' + str(currentShot) + '.nef', shell=True)
    
    draw.rectangle((0, 120, 240, 150), outline=0, fill=(0, 0, 0))
    disp.image(image, rotation)
    
    currentTime = time.time()
    
subprocess.check_output("sudo uhubctl -l 1-1 -p 2 -a 1", shell=True)
draw.text((5,155), "Done", font=font, fill="#339966")
disp.image(image, rotation)
exit()