# HOPPY - a smart watering system using MetOffice API
# for E14 Monthly Theme Competition
# by rodders
# 30th March 2018
# v1.6

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

        timeNow = datetime.datetime.now()
        sTimeNow=timeNow.strftime('%H:%M:%S')
        setValve(0)
        print("Watering valve OFF at:",sTimeNow)

        lastWateredTime = datetime.now()
        return


def setValve(valveState):


    if (valveState==0):
        GPIO.output(25,True)
    else:
        GPIO.output(25, False)
    return

def getMetOfficeData(testValue):
    testValue = 1               #default is that the plants need watering now, unless the algorithm determines that should be held off
    if (not skipAPI):
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
    if (skipAPI):
        waterCycle = 0.01
    else:
        waterCycle = 24


    if (sTimeElapsed > waterCycle):
        wateredLast24hrs = True
        print("Was watered in last 24 hours")

    if ((probWet > 40) and (wateredLast24hrs)):
        print("    Could rain soon. Hold off")
        testValue = 0
    elif ((probWet > 90) and (wateredLast24hrs != 1)):
        print("    We held off for the last 24 hrs but here is a high probability of rain; so still hold off watering.")
        testValue = 0
    else:
        print("Not high probability of rain and hasn't been watered...so signal for water")

    print("testValue is:", testValue)
    return testValue

#The main loop
print("Welcome to HOPPY - your smart plant irrigation system")
print("by Rodders for Element14, March 2018, v1.6")
print("\n")

#get the time from the arguments provided or use a default value set to 8pm when sun has probably gone down
# see https://stackoverflow.com/questions/7427101/simple-argparse-example-wanted-1-argument-3-results#7427376
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", dest="filename",help="write report to FILE", metavar="FILE")
parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", default=True,help="don't print status messages to stdout")
parser.add_argument("-t", "--time", type=valid_time, default="20:00", help="time for watering to start")
parser.add_argument("-d", "--duration", type=int, default="60", help="duration to water in seconds")
parser.add_argument("-l", "--location", type=str, default="3772", help="location ID from MetOffice API list")

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

#Setup I/O
GPIO.setmode(GPIO.BCM)
GPIO.setup(25,GPIO.OUT)

# Setup data/variables
output_file = open('test.json', 'w')
RepNo = 0
data = {}
testValue = 0
#wateredLast24hrs = 0
lastWateredTime = datetime.now()
timeNow =0
timeElapsed = 0
skipAPI = True
wateredLast24hrs = False            #start with not knowing if watered before - so will force watering to start up

setValve(0)         #otherwise it might default to on for a long time !


#You can sign up free for your own key from MetOffice.
# Just add it as plain text to a file as named below.
API_key_file = open("MyMetOfficeAPIKey.txt",'r')
myKey=API_key_file.read()
API_key_file.close()


while(1):
    #Get the current time
    timeNow = datetime.now().strftime('%H:%M')
    print("Current system time is: ",timeNow)

    #If watering time then test constraints for watering
    if (timeNow == wateringTime):
        print("Watering period is now, checking constraints...")
        checkWateringConstraints()

    #If manual button then water regardless

    #Delay in seconds before next test - just confirms operation to user screen
    time.sleep(5)

    #end of main loop/while

GPIO.cleanup()
