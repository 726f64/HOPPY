# HOPPY - a smart watering system using MetOffice API
# for E14 Monthly Theme Competition
# by rodders
# 2nd April 2018
# v1.8
#
# feel free to reuse, repurpose and modify this code for your own project.
# an simple acknowledgement would be appreciated :-) as well as keeping the links to original code that I also reused.
#
# Written by a Python novice !

import json
import urllib.request
import time
from datetime import datetime
import argparse
import RPi.GPIO as GPIO

myKey=""

#The functions

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def valid_time(s):
    try:
        return datetime.strptime(s, "%H:%M")
    except ValueError:
        msg = "Not a valid time format: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def checkWateringConstraints():
   result = getMetOfficeData(testValue)
   #work out the tests here...
   if (result == 1):
       print("Passed ALL conditions and starting to water...")
       startWatering()
       return
   else:
       print("Didn't pass tests to water plants today.")
       return

def startWatering():
        timeNow = datetime.now().strftime('%H:%M:%S')
        setValve(1)
        print("Watering valve ON at:",timeNow)
        time.sleep(wateringDuration)
        print("Valve will be on for approx.", wateringDuration, " seconds")

        timeNow = datetime.now().strftime('%H:%M:%S')
        setValve(0)
        print("Watering valve OFF at:", timeNow)

        lastWateredTime = datetime.now()
        return

	
def setValve(valveState):
    if valveState == 0:
        GPIO.output(25, False)
    else:
        GPIO.output(25, True)
    return

def getMetOfficeData(waterPlants):
    waterPlants = 1               #default is that the plants need watering now, unless the algorithm determines that should be held off
    if (debugID == 0):
        print("Obtaining JSON data from MetOffice...")
        jsonrequest = "http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/" + locationID + "?res=3hourly&key=" + myKey
        url = urllib.request.urlopen(jsonrequest)
        #url=urllib2.urlopen(jsonrequest)
        data = json.loads(url.read().decode(url.info().get_param('charset') or 'utf-8'))
        print("Data obtained is:", data)

        for key, value in data.items():
            # today's data
            Pp1=data['SiteRep']['DV']['Location']['Period'][0]['Rep'][RepNo]['Pp']
            print("    Today Precipitation:", Pp1)
            T1=data['SiteRep']['DV']['Location']['Period'][0]['Rep'][RepNo]['T']
            print("    Today's Temperature:",T1)
            W1=data['SiteRep']['DV']['Location']['Period'][0]['Rep'][RepNo]['W']
            print("    Today's Weather:",W1)

            # tomorrow's data
            Pp2=data['SiteRep']['DV']['Location']['Period'][1]['Rep'][RepNo]['Pp']
            print("    Tomorrow Precipitation:", Pp2)
            T2=data['SiteRep']['DV']['Location']['Period'][1]['Rep'][RepNo]['T']
            print("    Tomorrow's Temperature:",T2)
            W2=data['SiteRep']['DV']['Location']['Period'][1]['Rep'][RepNo]['W']
            print("    Tomorrow's Weather:",W2)

            # two days ahead data
            Pp3=data['SiteRep']['DV']['Location']['Period'][2]['Rep'][RepNo]['Pp']
            print("    +2day Precipitation:", Pp3)
            T3=data['SiteRep']['DV']['Location']['Period'][2]['Rep'][RepNo]['T']
            print("    +2day Temperature:",T3)
            W3=data['SiteRep']['DV']['Location']['Period'][2]['Rep'][RepNo]['W']
            print("    +2 day Weather:", W3)


            probWet = 0
            probWet = probWet + int(Pp1) + (int(Pp2)*0.7) + (int(Pp3)*0.5)
            print("    Combined weighting for Prob Rain is:", probWet)           #NB: not true stats etc eg adding/weighting percentages

    else:
        print("Non-API mode...forced to expect DRY weather")
        probWet = 30


    #When was the plants last watered?
    timeElapsed = datetime.now() - lastWateredTime
    sTimeElapsed = (timeElapsed.seconds/3600)

    print("Time elapsed since last water period is:", sTimeElapsed, " hours.")
    if (debugID == 2):
        waterCycle = 0.01
    else:
        waterCycle = 24

    wateredLast24hrs = False
    if sTimeElapsed > waterCycle:
        wateredLast24hrs = True
        print("Was watered in last 24 hours")

    # Now the algorithm - this is the bit that should be adjusted to ensure optimal water usage vs. plant health.
    if ((probWet > 40) and (wateredLast24hrs)):
        print("    Could rain soon. Hold off")
        waterPlants = 0
    elif ((probWet > 90) and (wateredLast24hrs != 1)):
        print("    We held off for the last 24 hrs but here is a high probability of rain; so still hold off watering.")
        waterPlants = 0
    else:
        print("Not high probability of rain and hasn't been watered...so signal for water")

    print("waterPlants value is:", waterPlants)
    return waterPlants

#Module to do a sleep but also monitor the override button.
def hsleep(sleepPeriod):
    sleepMS = sleepPeriod * 1000
    passed = 0
    pressedSW = False

    while ((passed < sleepMS) and not pressedSW):
        time.sleep(0.05)         #50ms sleep
        passed = passed + 50
        if (GPIO.input(23) == 0):
            pressedSW = True
    return pressedSW



######################################################################################################
# The main loop
######################################################################################################
print("***********************************************************")
print("*                                                         *")
print("* Welcome to HOPPY - your smart plant irrigation system   *")
print("* by Rod for Element14, April 2018, v1.8                  *")
print("*                                                         *")
print("***********************************************************")

#get the time from the arguments provided or use a default value set to 8pm when sun has probably gone down
# see https://stackoverflow.com/questions/7427101/simple-argparse-example-wanted-1-argument-3-results#7427376
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", dest="filename",help="write report to FILE", metavar="FILE")
parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", default=True,help="don't print status messages to stdout")
parser.add_argument("-t", "--time", type=valid_time, default="20:00", help="time for watering to start")
parser.add_argument("-d", "--duration", type=int, default="60", help="duration to water in seconds")
parser.add_argument("-l", "--location", type=str, default="3772", help="location ID from MetOffice API list")
parser.add_argument("-a", "--api", type=int, default="0", help="deafult=0, api is called, set 2 to defer")

#Tidy the Time to start watering
parsed = parser.parse_args()
wateringTime = parsed.time
wateringTime = wateringTime.strftime('%H:%M')
print("Time to irrigate is set for: ", wateringTime)

#Tidy the duration of watering
wateringDuration = parsed.duration
if wateringDuration < 1:
    wateringDuration = 1
print("Watering duration set for: ", wateringDuration, " seconds")

#Tidy the required location ID
locationID=parsed.location
print("Location ID is: ", locationID)

#Debug mode
debugID = parsed.api
print("Debug mode is set to: ", debugID)

#Setup I/O
GPIO.setmode(GPIO.BCM)
GPIO.setup(25,GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(23, GPIO.IN)


# Setup data/variables
output_file = open('test.json', 'w')
RepNo = 0
data = {}
testValue = 0
lastWateredTime = datetime.now()
timeNow = 0
timeElapsed = 0
wateredLast24hrs = False            #start with not knowing if watered before - so will force watering to start up

setValve(0)         #otherwise it might default to on for a long time !
override = False
valveStatus = False

#You can sign up free for your own key from MetOffice.
# Just add it as plain text to a file as named below.
API_key_file = open("MyMetOfficeAPIKey.txt",'r')
myKey=API_key_file.read()
API_key_file.close()

print("Starting main loop")
while 1:
    if (debugID == 3):
        print("Testing out GPIO")
        while 1:
            GPIO.output(25, True)
            time.sleep(1)
            GPIO.output(25, False)
            time.sleep(1)
            if GPIO.input(23) == 0:
                print("Switch pressed")

    #Get the current time
    timeNow = datetime.now().strftime('%H:%M')
    print("Current system time is: ", timeNow)

    #If watering time then test constraints for watering
    if timeNow == wateringTime:
        print("Watering period starts now, checking constraints...")
        checkWateringConstraints()

    #If manual button then water regardless - needs to be outside of the delay loop

    #Delay in seconds before next test - just confirms operation to user screen
    if (debugID > 0):
        toggleValve = hsleep(5)
    else:
        toggleValve = hsleep(60)

    if toggleValve:
        if valveStatus:
            valveStatus = False
            print("    Manual Override - OFF")
            GPIO.output(25, False)
        else:
            valveStatus = True
            print("    Manual Override - ON")
            GPIO.output(25, True)
        time.sleep(0.25) #to act as debounce

    #end of main loop/while


# Should we get to the end I guess we need something like this;
GPIO.cleanup()

