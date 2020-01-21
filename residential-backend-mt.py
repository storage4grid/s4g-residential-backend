#!/usr/bin/env python
# Copyright 2018 Ligios Michele <michele.ligios@linksfoundation.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''
---------------------------------------------------------------------------------------------------------------
Simple REST server for Python (3). Built to be multithreaded.
---------------------------------------------------------------------------------------------------------------
@Version 6.4.1
                                           Storage4Grid EU Project
                                      Implementation of Residential Backend
                                          on residential Aggregators
Features:
* Provide both static files and json based results
* Map URI patterns using regular expressions
* Map HTTP Requests (GET, PUT)
* Basic responses in compliance with HTTP protocol
* ----------------------------------------------------------------------------------------------------------- *
                                              API Description:
* Because of visibility permissions, these such APIs will be accessible only from LAN
* These such APIs will be accessible also from the VPN for demonstrative purposes
* ----------------------------------------------------------------------------------------------------------- *
                                              API Examples:
* Remember to add the prefix: http://address:port/
* ----------------------------------------------------------------------------------------------------------- *
* Energy evaluated from Power measurements:
*   LOCALENERGY/{fromDate}/{toDate}/{SMXmeasurement}         <<< Interact with Local DWH
*   ENERGY/{fromDate}/{toDate}/{SMXmeasurement}              <<< Interact with Global DWH
*   ENERGY/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015
*   LOCALENERGY/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015
*   GROUPBY=ADAPTIVE (Hardcoded)
*   {BolzanoSMX}     =  {       EV        /       PV        /        ESS       /      Load      }
*   {SMXmeasurement} =  {S4G-GW-EDYNA-0014/S4G-GW-EDYNA-0015/S4G-GW-EDYNA-0016/S4G-GW-EDYNA-0017}
* We need to Manage the Fronius-Entries in InfluxDB, by allowing:
*   ENERGY/{fromDate}/{toDate}/{FroniusMeasurement}/{FieldOfInterest}
*   ENERGY/2018-12-24/2018-12-25/InstallationHouse20/photovoltaic
*   {FieldOfInterest}    = {photovoltaic/load/battery/grid}
*   {FroniusMeasurement} = {InstallationHouse20/InstallationHouse24/InstallationHouse25/InstallationHouse26/InstallationHouse27}
*   {FroniusMeasurement} = {InstallationHouseBolzano}
*  Correct Result is a number!
* ----------------------------------------------------------------------------------------------------------- *
* ### Filtered Energy Estimations (exploiting signed values and operations such as: GROUPBY):
*  ENERGY/{fromDate}/{toDate}/{measurement}/{Field}/{FILTER}/{OPERATION}/{VALUE}
*  ENERGY/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015/P/POSITIVE/GROUPBY/30
*  ENERGY/2019-03-25/2019-03-27/InstallationHouse20/battery/POSITIVE/GROUPBY/30
*  Correct Result is a number!
* ----------------------------------------------------------------------------------------------------------- *
* ### Filtered Data (plus operations such as: GROUPBY):
*  INFLUXDB/{fromDate}/{toDate}/{measurement}/{Field}/{FILTER}/{OPERATION}/{VALUE}
*  INFLUXDB/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015/P/POSITIVE/GROUPBY/30
*  INFLUXDB/2019-03-25/2019-03-27/InstallationHouse20/battery/POSITIVE/GROUPBY/30
*  Result is an array!
* ----------------------------------------------------------------------------------------------------------- *
* - Consumption Battery = (-P_Akku) if(P_Akku<0):
*  Extract Battery Consumption exploiting the following API (then multiply each value to -1):
*  INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/battery/NEGATIVE/GROUPBY/30
*  Correct Result is an array!
*
* - Over Production = (-P_Grid) if(P_Grid<0)
*  Extract Over Production exploiting the following API (then multiply each value to -1):
*  INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/grid/NEGATIVE/GROUPBY/30
*  Correct Result is an array!
*
* - Power From Battery = (P_Akku) if(P_akku>0)
*  Extract Power From Battery exploiting the following API:
*  INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/battery/POSITIVE/GROUPBY/30
*  Correct Result is an array!
* ----------------------------------------------------------------------------------------------------------- *
* DEDICATED FRONT-END API TO BUILD PROPERLY HISTORICAL CHARTS:
* ----------------------------------------------------------------------------------------------------------- *
* - Direct consumption:
*  consumption_direct = (-P_Load) if(P_Grid < 0)
*  Evaluate Direct house consumption exploiting the following API (then multiply each value to -1):
*  INFLUXDB/2018-12-24/2018-12-25/InstallationHouseBolzano/direct_consumption/GROUPBY/30
*  Correct Result is a Json!
* ----------------------------------------------------------------------------------------------------------- *
* - House overall consumption:
*  Consumption_house  = (-P_Load)
*  Evaluate house consumption exploiting the following API (then multiply each value to -1):
*  INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/load/GROUPBY/30
*  Correct Result is a Json!
* ----------------------------------------------------------------------------------------------------------- *
* The following two arrays will be built starting from the above extracted values:
* - Power sent to the Grid:
* power2grid = Over_production + Consumption_battery
* - Overall production:
* Production = SMX_PV - Over_production
* ----------------------------------------------------------------------------------------------------------- *
*                                       ** NEW FORMULAS TO PROPERLY PLOT CHARTS **
* ----------------------------------------------------------------------------------------------------------- *
* Extract Power about selected measurement & field on the provided time-frame (MONTH)
*  INFLUXDB/MONTH/{Date}/{measurement}/{Field}/{FILTER}
*  INFLUXDB/MONTH/2019-03/InstallationHouseBolzano/load/ALL
*  Correct Result is a Json! (Average for each day)
*  [get_historical_month_data]
*
* ----------------------------------------------------------------------------------------------------------- *
* Extract Power about selected measurement & field on the provided time-frame (YEAR)
*  INFLUXDB/YEAR/{Date}/{measurement}/{Field}/{FILTER}
*  INFLUXDB/YEAR/2019/InstallationHouseBolzano/load/ALL
*  Correct Result is a Json! (Average for each Month)
*  [get_historical_year_data]
*
* ----------------------------------------------------------------------------------------------------------- *
*                                         ** Other Formulas **
* ----------------------------------------------------------------------------------------------------------- *
* - power_from_grid        = consumption_house
* - consumption_house      = (-P_Load) 
*   Extract run-time via: MQTT topic( RESIDENTIAL/GUI ) measurement_name( InstallationHouseBolzano )  Field( P_Load )
*   [get_historical_specific_data]
*   Extract Hystorical via: (INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/load/GROUPBY/30)
*   Then multiply all the received values to -1
*   Consequently, has been built a dedicated API for it:
*   [get_consumption_house]
*   Extract Hystorical via: (INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/consumption_house/GROUPBY/30)
*   Note: range of values: positive & negative!
* ----------------------------------------------------------------------------------------------------------- *
* - over_production        = if (P_Grid<0) then (-P_Grid) else 0
*   Extract run-time via: MQTT topic( RESIDENTIAL/GUI ) measurement_name( InstallationHouseBolzano )  Field( P_Grid )
*   [get_filtered_data]
*   Extract Hystorical via: INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/grid/NEGATIVE/GROUPBY/30
*   Then multiply all the received values to -1
*   Consequently, has been built a dedicated API for it:
*   [get_over_production]
*   Extract Hystorical via: (INFLUXDB/2019-01-25/2019-03-27/InstallationHouseBolzano/over_production/GROUPBY/30)
*   Note: range of values: only positive!
* ----------------------------------------------------------------------------------------------------------- *
* - power2battery          = consumption_battery
* - consumption_battery    = if (P_Akku<0) then (-P_Akku) else 0
*   Extract run-time via: MQTT topic( RESIDENTIAL/GUI ) measurement_name( InstallationHouseBolzano )  Field( P_Akku )
*   [get_filtered_data]
*   Extract Hystorical via: INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/battery/NEGATIVE/GROUPBY/30
*   Then multiply all the received values to -1
*   Consequently, has been built a dedicated API for it:
*   [get_power2battery]
*   Extract Hystorical via: (INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/power2battery/GROUPBY/30)
*   Note: range of values: only positive!
* ----------------------------------------------------------------------------------------------------------- *
* - power_from_battery     = production_battery
* - production_battery     = if (P_Akku>0) then (+P_Akku) else 0
*   Extract run-time via: MQTT topic( RESIDENTIAL/GUI ) measurement_name( InstallationHouseBolzano )  Field( P_Akku )
*   [get_filtered_data]
*   Extract Hystorical via: INFLUXDB/2019-01-25/2019-03-27/InstallationHouseBolzano/battery/POSITIVE/GROUPBY/30
*   Note: range of values: only positive!
* ----------------------------------------------------------------------------------------------------------- *
* - consumption_for_energy = if (P_Grid<0) then (consumption_house) else 0    [Where consumption_house = -P_Load]
*   [get_consumption_direct]
*   Extract Hystorical via: INFLUXDB/2018-12-24/2018-12-25/InstallationHouseBolzano/direct_consumption/GROUPBY/30
*   Old [Then multiply all the received values to -1]
*   Old API!! Remains for backward compatibility!!!
*
* - consumption_for_energy = if (P_Grid<0) then (consumption_house) else 0    [Where consumption_house = -P_Load]
*   [get_consumption_direct_v2]
*   Extract Hystorical via: INFLUXDB/2018-12-24/2018-12-25/InstallationHouseBolzano/direct_consumption_v2/GROUPBY/30
*   Old [Then multiply all the received values to -1]
*   Changed!! Now it returns the requested values!!!
* ----------------------------------------------------------------------------------------------------------- *
* - prod_PV                = Processed_P da (SMX)
*   Extract Hystorical via:  (INFLUXDB/2019-03-25/2019-03-27/S4G-GW-EDYNA-0015/P_PV/GROUPBY/30)
*   [get_historical_specific_data]
*   Extract run-time via: MQTT topic( RESIDENTIAL/GUI ) measurement_name( S4G-GW-EDYNA-0015 )  Field( Processed_P )
* ----------------------------------------------------------------------------------------------------------- *
* - production             = prod_PV - over_production
*   [evaluate_production]
*   Extract Hystorical via: INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/evaluate_production/GROUPBY/30
* ----------------------------------------------------------------------------------------------------------- *
* - total_production       = production_battery + prod_PV
*   [evaluate_total_production]
*   Extract Hystorical via: INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/evaluate_total_production/GROUPBY/30
* ----------------------------------------------------------------------------------------------------------- *
* - consumption_direct     = abs(prod_PV - consumption_battery - over_production)
*   [evaluate_direct_consumption]
*   Extract Hystorical via: INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/evaluate_direct_consumption/GROUPBY/30
* ----------------------------------------------------------------------------------------------------------- *
* - power2grid             = over_production + consumption_battery
*   [evaluate_power2grid]
*   Extract Hystorical via: INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/evaluate_power2grid/GROUPBY/30
* ----------------------------------------------------------------------------------------------------------- *
*
* ----------------------------------------------------------------------------------------------------------- *
* Generic Raw Data:  
*   LOCALINFLUXDB/{fromDate}/{toDate}/{measurement}       <<< Interact with Local DWH
*   INFLUXDB/{fromDate}/{toDate}/{measurement}            <<< Interact with Global DWH
*   DEFAULT(FIXED) = GROUP BY 30 minutes
*   INFLUXDB/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015
*   LOCALINFLUXDB/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015
*  Correct Result is a Json!
* ----------------------------------------------------------------------------------------------------------- *
* Generic Data (plus operations such as: GROUPBY):
*   LOCALINFLUXDB/{fromDate}/{toDate}/{measurement}/{OPERATION}/{VALUE}
*   INFLUXDB/{fromDate}/{toDate}/{measurement}/{OPERATION}/{VALUE}
*   INFLUXDB/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015/GROUPBY/30
*   LOCALINFLUXDB/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015/GROUPBY/30
*  Correct Result is a Json!
* ----------------------------------------------------------------------------------------------------------- *
* ### Retrieve Number of battery cycles:  
* Get cycles (REST GET): 
*   Battery/cycles
*  Correct Result is a number!
* ----------------------------------------------------------------------------------------------------------- *
* ### Interact with PROFESS:
* ----------------------------------------------------------------------------------------------------------- *
* Get Operational Mode (REST GET):
*   OPMODE
* Set Operational Mode (REST PUT):
*   OPMODE
*   + Integer as payload:{0,1,2,4}
* {0:"maximizeSelfConsumption",1:"maximizeSelfProduction",2:"minimizeCosts",4:"None"}
* The above API will trigger the interaction with the PROFESS tool.
* First, both will verify the current status by requesting it to PROFESS.
* Then, it will be checked if is there already a running operation mode, if true, it will stop it first.
* Then, the OPMODE SET will update the status by forwarding the received parameters of interest to PROFESS.
*
* ----------------------------------------------------------------------------------------------------------- *
* ### Interact with EVconnector:
* ----------------------------------------------------------------------------------------------------------- *
* ### Set The EV target of interest (relying on eCar system) [Build for demonstrative purposes]:  
* EV/SET/<CU_ID>
* Default CU_id used (from configfile):
* EV_selected = ""
* EV_idList   = []
* --------------------------------------------------------- #
* ### Retrieve data related to the CU of interest (from remote eCar system):  
* EV/data 
* Output is a json including the following fields:
* {
*    "Charging": "False",
*    "SoC": 0,
*    "remainingTime": 0
* }
* --------------------------------------------------------- #
* ### Retrieve last status of EV:
* EV/status (Deprecated)
* --------------------------------------------------------- #
* ### Retrieve current EV SoC:
* EV/SOC    (Deprecated)
* ----------------------------------------------------------------------------------------------------------- *
@Author Ligios Michele
@update: 2019-12-12
@Version final
'''
# ------------------------------------------------------------------------------------ #
# Generic Libraries:
import sys, os, re, shutil, json

import urllib.request, urllib.parse, urllib.error
from urllib.request import urlopen

import http.server
from http.server import HTTPServer as BaseHTTPServer
# Single-thread REST Server:
# from http.server import SimpleHTTPRequestHandler, HTTPServer

import requests
import socketserver
from socketserver import ThreadingMixIn
from requests.auth import HTTPBasicAuth
# ------------------------------------------------------------------------------------ #
import datetime
import time
from datetime import datetime, timedelta
# ------------------------------------------------------------------------------------ #
import pysolar
import numpy as np
import pytz as tz
import pandas as pd
# ------------------------------------------------------------------------------------ #
import xmltodict
# ------------------------------------------------------------------------------------ #
from scipy import integrate
# ------------------------------------------------------------------------------------ #
import paho.mqtt.client as mqtt
import threading

if (sys.version_info > (3, 0)):
	import queue
else:
	import Queue 

import configparser
from calendar import monthrange

# ------------------------------------------------------------------------------------ #
# Avoid issues with relative paths
here    = os.path.dirname(os.path.realpath(__file__))
records = {}
# ------------------------------------------------------------------------------------ #
# Full Numpy array (Avoid compression of data)
np.set_printoptions(threshold=np.inf)

# ------------------------------------------------------------------------------------ #
# 		Global temporary flags to enable print logging:
# ------------------------------------------------------------------------------------ #
# 1. Enable Control Flow prints about main logic
# ------------------------------------------------------------------------------------ #
enablePrints         = True
enableFullStructuresPrints = False     # AVOID #  # Enable Structures content prints!
# ------------------------------------------------------------------------------------ #
# 2. Enable Content results prints about Run-time evaluation
# ------------------------------------------------------------------------------------ #
enableResultsContent = False
# ------------------------------------------------------------------------------------ #
# 3. Enable Control Flow prints about HTTP Server
# ------------------------------------------------------------------------------------ #
enableHTTPPrints     = False
# ------------------------------------------------------------------------------------ #
# 4. Enable Time-Monitoring features to verify delays introduced by the HTTP server
# ------------------------------------------------------------------------------------ #
enableTimingEval     = False
# ------------------------------------------------------------------------------------ #
# SENSOR_NAME MAPPING (only numerical values are allowed inside influx_format)
# TYPE = VALUE
# SMM(PCC)   = 0
# PV         = 1
# EV         = 2
# ESS        = 3
# ASM        = 4
# ER         = 5
# AGGREGATOR = 6
# FRONIUS    = 7
# ------------------------------------------------------------------------------------ #
# Init procedure:
# Read which Fronius are you interest in 
# Discover the right id about the stream of interest
# Subscribe to the local broker for the SMX stream ( Power of Battery or SoC )
# Subscribe to the remote broker for the fronius stream ( Power of PV or P-PV )
# When receive a new MQTT message:
# Evaluate if the main rule is applied
# Update local counters
# ------------------------------------------------------------------------------------ #
mqtt_local_topic   = "RESIDENTIAL/GUI"
mqtt_fronius_topic = "FRONIUS/RESIDENTIAL/GUI"
# ---------------------- #
enableCycleEvaluation = True
# ------------------------------------------------------------------------------------ #
# Threshold used to determine battery cycles:
N_THRESHOLD = 80
P_THRESHOLD = 50
# ------------------------------------------------------------------------------------ #
# ---------------------- #
# Aggregator Broker info:
# ---------------------- #
# Set of addresses
# Used only for development!
debugTestingRemote    = False

if(debugTestingRemote == True):
	mqtt_local_broker = "10.8.0.81"
	mqtt_local_port   = 1883
else:
	mqtt_local_broker = "localhost"
	mqtt_local_port   = 1883
# ------------------------------------------------------------------------------------ #
# ---------------------- #
# Influx Database auth:
# ---------------------- #
configFile = "auth.conf"
username = ""
password = ""
# ---------------------- #
# Known PROFESS configuration states: [stopped,starting,running] (starting will still be considered as stopped)
RUNNING_STATUS_PROFESS = "running"
DEFAULT_OPMODE         = 4
# ------------------------------------------------------------------------------------ #
# DEFAULT VALUE ABOUT OPMODE: 4
# ALLOWED VALUES: [0,1,2,3,4]
#
# knownOpmode = {0:"Self Consumption",1:"Cooperation Mode",2:"Maximize Money",3:"Maximize Battery Health",4:"None"}
# maximizeSelfProduction
# minimizeCosts
# maximizeSelfConsumption
# ------------------------------------------------------------------------------------ #
# The following option will return an error:
# MaximizeBatteryHealth because it is not known by PROFESS!
# ------------------------------------------------------------------------------------ #	
knownOpmode = {0:"maximizeSelfConsumption",1:"maximizeSelfProduction",2:"minimizeCosts",3:"MaximizeBatteryHealth",4:"None"}
opmode      = DEFAULT_OPMODE

evconnector_url = "https://10.8.0.50:8082"

# Starting value about overall number of Batery Cycles
# Default Starting value for cycles (should be zero) 
STARTING_CYCLES = 0
cycles = STARTING_CYCLES

if (sys.version_info > (3, 0)):
	internal_queue   = queue.Queue()  # Py3.4 Py3.5 Py3.6
else:
	internal_queue 	 = Queue.Queue()  # Py2.7

# ------------------------------------------------------------------------------------ #
# Following API will regroup automatically the selected time-window values:
# Less then 1 month            <->  30 minutes
# Between 1 month and 6 months <->  1 hour
# More then 6 months           <->  3 hours
# ------------------------------------------------------------------------------------ #
# Threshold to manage group by operations to enable InfluxDB query about big time-window via browser:
# ThresholdDate,GroupBy
# Unit: Days,Minutes
THRESHOLD_INF_LOW   = [1,5]
THRESHOLD_MIN       = [2,15]
THRESHOLD_LOW       = [30,30]
THRESHOLD_MID       = [90,60]
THRESHOLD_HIGH      = [120,120]
THRESHOLD_MAX       = [180,180]
THRESHOLD_INF_HIGH  = [1440,360]
# ---------------------------------------------------------------------------------------------------------------- #
influxLocalServer = "http://localhost:8086/query?db="
influxServer      = "http://10.8.0.50:8086/query?db="
basequery         = "&q=select mean(*) from "
# energyquery       = "&q=select mean(P) from "
energyquery       = "&q=select mean(Processed_P) from "
froniusquery1     = "&q=select mean(\""
froniusquery2     = "\") from "
# ------------------------------------------------------------------------------------ #
# Map representing the available operations to support improved query towards the DB
knownOperations = {"GROUPBY":"GROUP BY"}
### Generic Data (plus operations such as: GROUPBY) InfluxDB/{fromDate}/{toDate}/{measurement}/{Field}/{OPERATION}/{VALUE}
#   INFLUXDB/2018-12-24/2018-12-25/InstallationHouseBolzano/load/GROUPBY/30
def get_historical_specific_data(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] Get historical Specific data (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	field = words.split("/")[5]

	if(str(field)   == "photovoltaic"):
		field = "P-PV"
	elif(str(field) == "grid"):
		field = "P-Grid"
	elif(str(field) == "load"):
		field = "P-Load"
	elif(str(field) == "battery"):
		field = "P-Akku"
	elif(str(field) == "SoC"):
		field = "SOC"

	if(enablePrints == True):
		print("[Residential][LOG][SPECIFIC] Field selected: " + str(field))

	operation = words.split("/")[6]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[7]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	if(("S4G-GW") in measurementID):
		database = "S4G-DWH-USM"
	elif(("InstallationHouse") in measurementID):
		database = "S4G-DWH-TEST"
	else:
		return str("[Residential][LOG] Error: Uknwown Device and Database selected")

	service_path = address + database + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	# --------------------------------------------------------------------- #
	# DEBUGGING PURPOSES
	# today    = datetime.utcnow()
	# tomorrow = datetime.utcnow() + timedelta(1)
	# --------------------------------------------------------------------- #
	# 2018 11 13 23 00
	# startDate = today.strftime('%Y%m%d')
	# startDate += "0000"
	# endDate   = tomorrow.strftime('%Y%m%d')
	# endDate   += "0000"
	# --------------------------------------------------------------------- #
	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	

	return response.json()


### Direct Consumption (plus operations such as: GROUPBY) InfluxDB/{fromDate}/{toDate}/{measurement}/direct_consumption/{OPERATION}/{VALUE}
#   INFLUXDB/2018-12-24/2018-12-25/InstallationHouseBolzano/direct_consumption/GROUPBY/30
#   consumption_direct = (-P_Load) if(P_Grid < 0)  
# curl -u admin:storage4grid -G http://10.8.0.50:8086/query?db=S4G-DWH-TEST --data-urlencode "q=select MEAN(\"P-Load\") from \"InstallationHouseBolzano\" where time > '2018-12-29 11:30:00' AND time < '2018-12-30 00:00:00' AND \"P-Grid\"<0 GROUP BY time(10m)"
# TO BE CHANGED!!!!!
def get_consumption_direct(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] Get Direct Consumption (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	operation = words.split("/")[6]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[7]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	if(("InstallationHouse") in measurementID):
		database = "S4G-DWH-TEST"
	else:
		return str("[Residential][LOG] Error: Uknwown Device and Database selected")

	service_path = address + database + froniusquery1 + "P-Load" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"P-Grid\" < 0 " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	

	return response.json()


### Direct Consumption (plus operations such as: GROUPBY) InfluxDB/{fromDate}/{toDate}/{measurement}/direct_consumption/{OPERATION}/{VALUE}
#   INFLUXDB/2018-12-24/2018-12-25/InstallationHouseBolzano/direct_consumption/GROUPBY/30
#   consumption_direct = (-P_Load) if(P_Grid < 0)  
# curl -u admin:storage4grid -G http://10.8.0.50:8086/query?db=S4G-DWH-TEST --data-urlencode "q=select MEAN(\"P-Load\") from \"InstallationHouseBolzano\" where time > '2018-12-29 11:30:00' AND time < '2018-12-30 00:00:00' AND \"P-Grid\"<0 GROUP BY time(10m)"
# TO BE CHANGED!!!!!
def get_consumption_direct_v2(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] Get Direct Consumption (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	operation = words.split("/")[6]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[7]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	if(("InstallationHouse") in measurementID):
		database = "S4G-DWH-TEST"
	else:
		return str("[Residential][LOG] Error: Uknwown Device and Database selected")

	service_path = address + database + froniusquery1 + "P-Load" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"P-Grid\" < 0 " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	
	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	# -------------------------------------------- #
	# if response is not empty
	if not response or len(response.json()['results'][0]) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] Empty message")
		return ("[Residential][LOG] Empty message")
	# -------------------------------------------- #
	listOfinterest = response.json()['results'][0]['series'][0]['values']	
	# multiply each value to -1 (mantain just the json list)	
	result = [(x[0],x[1]*(-1)) for x in listOfinterest if x[1]]

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	

	return result


### Generic Data (plus operations such as: GROUPBY) InfluxDB/{fromDate}/{toDate}/{measurement}/{OPERATION}/{VALUE}
#   INFLUXDB/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015/GROUPBY/30
def get_historical_data(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] Get historical data (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	operation = words.split("/")[5]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[6]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	if(("S4G-GW") in measurementID):
		database = "S4G-DWH-USM"
	elif(("InstallationHouse") in measurementID):
		database = "S4G-DWH-TEST"
	else:
		return str("[Residential][LOG] Error: Uknwown Device and Database selected")

	service_path = address + database + basequery + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	

	return response.json()

# ------------------------------------------------------------------------------------ #
#### Filtered Energy Estimations (exploiting signed values and operations such as: GROUPBY):
#  ENERGY/{fromDate}/{toDate}/{measurement}/{Field}/{FILTER}/{OPERATION}/{VALUE}
#  ENERGY/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015/P/POSITIVE/GROUPBY/30
#  ENERGY/2019-03-25/2019-03-27/InstallationHouse20/battery/POSITIVE/GROUPBY/30
def get_filtered_area(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] Get historical filtered data to evaluate Energy (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "ENERGY"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate     = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate     = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	field      = words.split("/")[5]
	currfilter = words.split("/")[6]
	
	operation = words.split("/")[7]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG][ENERGY][FILTERED] Unknown Operation")

	interval  = words.split("/")[8]

	if(enablePrints == True):
		print("[Residential][LOG][ENERGY][FILTERED] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG][ENERGY][FILTERED] Wrong Date: " + str(fromDate))

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG][ENERGY][FILTERED] Wrong Date: " + str(toDate))


	diff = toDate - fromDate

	fromDate = str(fromDate).split('+')[0]
	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG][ENERGY][FILTERED] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	fronius  = False
	if(("S4G-GW") in measurementID):
		database = "S4G-DWH-USM"
	elif(("InstallationHouse") in measurementID):
		fronius  = True
		database = "S4G-DWH-TEST"
		try:
			field    = words.split("/")[5]
		except Exception as e:
			print("Exception: %s" %e)
			return ("[Residential][LOG][ENERGY][FILTERED] Error: You must select the Fronius Field! Look at documentation!")

		if(str(field)   == "photovoltaic"):
			field = "P-PV"
		elif(str(field) == "grid"):
			field = "P-Grid"
		elif(str(field) == "load"):
			field = "P-Load"
		elif(str(field) == "battery"):
			field = "P-Akku"
		elif(str(field) == "SoC"):
			field = "SOC"
		else:
			return ("[Residential][LOG][ENERGY][FILTERED] Error: Uknwown Field selected: " + str(field))
	else:
		return "[Residential][LOG][ENERGY][FILTERED] Error: Uknwown Device and Database selected"	


	# ------------------------------------------------------------------ #
	# DEPRECATED BECAUSE OF PARAMETRIZED VALUE!
	# ------------------------------------------------------------------ #
	# Adaptive Query to enable InfluxDB data extraction within browsers
	# [AVOIDING CONNECTION TIMEOUTS]!
	# ------------------------------------------------------------------ #
	# threshold_lowest  = timedelta(days = int(THRESHOLD_INF_LOW[0]))
	# threshold_min     = timedelta(days = int(THRESHOLD_MIN[0]))
	# threshold_low     = timedelta(days = int(THRESHOLD_LOW[0]))
	# threshold_mid     = timedelta(days = int(THRESHOLD_MID[0]))
	# threshold_high    = timedelta(days = int(THRESHOLD_HIGH[0]))
	# threshold_highest = timedelta(days = int(THRESHOLD_INF_HIGH[0]))
	# 
	# if(diff <= threshold_lowest):
	# 	groupBy = THRESHOLD_INF_LOW[1]
	# elif (diff > threshold_lowest and diff <= threshold_min):
	# 	groupBy = THRESHOLD_MIN[1]
	# elif (diff > threshold_min and diff <= threshold_low):
	# 	groupBy = THRESHOLD_LOW[1]
	# elif (diff > threshold_low and diff <= threshold_mid):
	# 	groupBy = THRESHOLD_MID[1]
	# elif (diff > threshold_mid and diff <= threshold_high):
	# 	groupBy = THRESHOLD_HIGH[1]
	# elif (diff > threshold_high and diff <= threshold_highest):
	# 	groupBy = THRESHOLD_MAX[1]
	# elif (diff > threshold_highest):
	# 	groupBy = THRESHOLD_INF_HIGH[1]
	# 

	if(enablePrints == True):
		print("[Residential][LOG][ENERGY][FILTERED] THRESHOLDS SETTINGS: ")
		print("[Residential][LOG][ENERGY][FILTERED] Time-Window Requested: "+ str(diff))


	if(fronius == True):
		# Focusing on this case, you have to chose which is the power of interest
		service_path = address + database + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' GROUP BY time(" + str(interval) + "m)" 

	else:
		# Focusing on this case, you will always extract the Power exposed by the USM (that's why exploit energyquery content)
		service_path = address + database + energyquery + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG][ENERGY][FILTERED] INFLUX API " + service_path)
		return str("[Residential][ENERGY][FILTERED] Influx Service Not reachable/available")


	if(enableFullStructuresPrints == True):
		print("[Residential][LOG][ENERGY][FILTERED] Field evaluation FULLCONTENT: " + str(response.json()))
	try:
		empty = False
		try:
			# Verify if content exists:
			a = response.json()['results'][0]['series']
		except Exception as e:
			empty = True
			result = None

		if(empty == False):
			if(enableFullStructuresPrints == True):
				print("[Residential][LOG][ENERGY][FILTERED] Field Result:" + str(response.json()['results'][0]['series'][0]['values']))
			result = response.json()['results'][0]['series'][0]['values']
		else:
			raise Exception('Empty response')
	except Exception as e:
		if(enablePrints == True):
			print("[Residential][LOG][ENERGY][FILTERED] Field Parsing Returned Error: %s" %e)
		return ("[Residential][LOG][ENERGY][FILTERED] Field Parsing Returned Error: %s" %e)

	if(enablePrints == True):
		print("[Residential][LOG] --- ENERGY FILTERED EVALUATION ---")
		print("[Residential][LOG] NUMBER OF SAMPLES: " + str(len(result)))
		print("[Residential][LOG] TIMEDELTA: " + str(diff))
		print("[Residential][LOG] SECONDS: " + str(diff.total_seconds()))
		print("[Residential][LOG] INCREMENT(seconds): " + str(diff.total_seconds() / len(result)))

	functionToIntegrate = []

	# We need to define the X array
	# Starting from the TimeWindow and the Amount of samples
	# Identify increment value to define explicitly every X position related to the sample Y
	xAxes  = []
	xStart = 0
	xEnd   = diff.total_seconds()
	xInc   = diff.total_seconds() / len(result)

	# if response is not empty
	if not result or len(result) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG][ENERGY][FILTERED] Field returns Empty message")
		return ("[Residential][LOG][ENERGY][FILTERED] Field returns Empty message")

	# -------------------------------------- #
	# Manage "None" values:
	# Override with 0
	# -------------------------------------- #
	if(enablePrints == True):
		debugflag  = False
		debugStart = 0
		debugEnd   = 0
		debugTmp   = 0


	for key,value in result:
		debugTmp = key
		xAxes.append(xStart)

		if(value == None):
			tmp = 0
			if(enablePrints == True and debugflag == False):
				debugflag  = True
				debugStart = key

		elif(currfilter == "POSITIVE"):
		# Only Positive values
			if(value > 0):
				tmp = value
			else: 
				tmp = 0
		elif(currfilter == "NEGATIVE"):
		# Only Negative values
			if(value < 0):
				tmp = value
			else: 
				tmp = 0
		else:
		# All
			tmp = value

		functionToIntegrate.append(tmp)

		if(enablePrints == True and debugflag == True):
			debugflag = False
			debugEnd  = key
			print("[Residential][LOG][ENERGY][FILTERED] Found sequence of missing data: ")
			print("[Residential][LOG][ENERGY][FILTERED] From Time: " + str(debugStart))
			print("[Residential][LOG][ENERGY][FILTERED] To Time: " + str(debugEnd))

		xStart += xInc

	# If we did not recover from the None Sequence (last value still None):
	if(enablePrints == True and debugflag == True):
		debugflag = False
		debugEnd  = debugTmp
		print("[Residential][LOG][ENERGY][FILTERED] Found sequence of missing data: ")
		print("[Residential][LOG][ENERGY][FILTERED] From Time: " + str(debugStart))
		print("[Residential][LOG][ENERGY][FILTERED] To Time: " + str(debugEnd))

	# Y axes = Power values
	# X axes = TimeFrame values related to sampling (together with grouped means):
	try:
		energy = integrate.simps(functionToIntegrate,xAxes)

	except Exception as e:
		if(enablePrints == True):
			print("[Residential][LOG][ENERGY][FILTERED] Integrate Returned Error: %s" %e)
		return ("[Residential][LOG][ENERGY][FILTERED] Integrate Returned Error: %s" %e)

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG][ENERGY][FILTERED] API last: " + str(end - start))	


	if(enablePrints == True):
		print("[ENERGY][FILTERED] X axes(time): " + str(xAxes))
		print("[ENERGY][FILTERED] Y axes(power): " + str(functionToIntegrate))


	# ------------------------------ #	
	# Energy is now: Watt*seconds
	# We want Energy in: Watt*hours
	# ------------------------------ #
	return energy/3600


# ------------------------------------------------------------------------------------ #
### Filtered Month Data 
#  INFLUXDB/MONTH/{Date}/{measurement}/{Field}/{FILTER}
#  INFLUXDB/MONTH/2019-03/InstallationHouseBolzano/load/ALL
def get_historical_month_data(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] Get get_historical_month_data (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	# words.split("/")[2] -> MONTH

	fromDate_tmp = words.split("/")[3]
	fromDate     = fromDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	field      = words.split("/")[5]
	currfilter = words.split("/")[6]
	
	if(enablePrints == True):
		print("[Residential][LOG] get month historical data (" + measurementID + ") from: (" + fromDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), 1, 0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	if(enablePrints == True):
		print("[Residential][LOG] Date converted: " + str(fromDate))

	# Identify which month is and the amount of days to set toDate:
	weekday,day = monthrange(int(year), int(month))

	if(enablePrints == True):
		print("[Residential][LOG] Month overall days:" + str(day))

	# Verify if correct date
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	if(enablePrints == True):
		print("[Residential][LOG] toDate set:" + str(toDate))

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	fronius  = False
	if(("S4G-GW") in measurementID):
		database = "S4G-DWH-USM"
	elif(("InstallationHouse") in measurementID):
		fronius  = True
		database = "S4G-DWH-TEST"
		try:
			field    = words.split("/")[5]
		except Exception as e:
			print("Exception: %s" %e)
			return ("[Residential][LOG] Error: You must select the Fronius Field! Look at documentation!")

		if(str(field)   == "photovoltaic"):
			field = "P-PV"
		elif(str(field) == "grid"):
			field = "P-Grid"
		elif(str(field) == "load"):
			field = "P-Load"
		elif(str(field) == "battery"):
			field = "P-Akku"
		elif(str(field) == "SoC"):
			field = "SOC"
		elif(str(field) == "direct_consumption"):
			pass
		else:
			return ("[Residential][LOG] Error: Uknwown Field selected: " + str(field))
	else:
		return "[Residential][LOG] Error: Uknwown Device and Database selected"	


	# DEDICATED FAST-FIX FOR DIRECT_CONSUMPTION
	if(str(field) == "direct_consumption"):
		service_path = address + database + froniusquery1 + "P-Load" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"P-Grid\" < 0 GROUP BY time(1d)"

	elif(currfilter == "ALL"):
		if(fronius == True):
			# Focusing on this case, you have to chose which is the power of interest
			service_path = address + database + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' GROUP BY time(1d)" 

		else:
			# Focusing on this case, you will always extract the Power exposed by the USM (that's why exploit energyquery content)
			service_path = address + database + energyquery + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' GROUP BY time(1d)"
	elif(currfilter == "POSITIVE"):
		if(fronius == True):
			# Focusing on this case, you have to chose which is the power of interest
			service_path = address + database + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"" + field + "\" > 0 GROUP BY time(1d)" 

		else:
			# Focusing on this case, you will always extract the Power exposed by the USM (that's why exploit energyquery content)
			service_path = address + database + energyquery + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' GROUP BY time(1d)"
	elif(currfilter == "NEGATIVE"):
		if(fronius == True):
			# Focusing on this case, you have to chose which is the power of interest
			service_path = address + database + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"" + field + "\" < 0 GROUP BY time(1d)" 

		else:
			# Focusing on this case, you will always extract the Power exposed by the USM (that's why exploit energyquery content)
			service_path = address + database + energyquery + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"Processed_P\" < 0 GROUP BY time(1d)"

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	return response.json()


# ---------------------------------------------------- #
### Filtered Year Data 
#  INFLUXDB/YEAR/{Date}/{measurement}/{Field}/{FILTER}
#  INFLUXDB/YEAR/2019/InstallationHouseBolzano/load/ALL
def get_historical_year_data(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	yearResponse = {"results": [{"statement_id": 0, "series": [{"name": "", "columns": ["time", "mean"], "values":[]}]}]}

	if(enablePrints == True):
		print("[Residential][LOG] Get get_historical_year_data (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate   = words.split("/")[3]
	year       = fromDate

	measurementID = words.split("/")[4]

	field      = words.split("/")[5]
	currfilter = words.split("/")[6]
	
	if(enablePrints == True):
		print("[Residential][LOG] get month historical data (" + measurementID + ") from: (" + fromDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	try:
		fromDate = datetime(int(year), 1, 1 ,0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	try:
		toDate = datetime(int(year), 12, 31, 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date")

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	fronius  = False
	if(("S4G-GW") in measurementID):
		database = "S4G-DWH-USM"
	elif(("InstallationHouse") in measurementID):
		fronius  = True
		database = "S4G-DWH-TEST"
		try:
			field    = words.split("/")[5]
		except Exception as e:
			print("Exception: %s" %e)
			return ("[Residential][LOG] Error: You must select the Fronius Field! Look at documentation!")

		if(str(field)   == "photovoltaic"):
			field = "P-PV"
		elif(str(field) == "grid"):
			field = "P-Grid"
		elif(str(field) == "load"):
			field = "P-Load"
		elif(str(field) == "battery"):
			field = "P-Akku"
		elif(str(field) == "SoC"):
			field = "SOC"
		elif(str(field) == "direct_consumption"):
			pass
		else:
			return ("[Residential][LOG] Error: Uknwown Field selected: " + str(field))
	else:
		return "[Residential][LOG] Error: Uknwown Device and Database selected"	

	# DEDICATED FAST-FIX FOR DIRECT_CONSUMPTION
	if(str(field) == "direct_consumption"):
		service_path = address + database + froniusquery1 + "P-Load" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"P-Grid\" < 0 GROUP BY time(1d)"

	elif(currfilter == "ALL"):
		if(fronius == True):
			# Focusing on this case, you have to chose which is the power of interest
			service_path = address + database + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' GROUP BY time(1d)" 

		else:
			# Focusing on this case, you will always extract the Power exposed by the USM (that's why exploit energyquery content)
			service_path = address + database + energyquery + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' GROUP BY time(1d)"
	elif(currfilter == "POSITIVE"):
		if(fronius == True):
			# Focusing on this case, you have to chose which is the power of interest
			service_path = address + database + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"" + field + "\" > 0 GROUP BY time(1d)" 

		else:
			# Focusing on this case, you will always extract the Power exposed by the USM (that's why exploit energyquery content)
			service_path = address + database + energyquery + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' GROUP BY time(1d)"
	elif(currfilter == "NEGATIVE"):
		if(fronius == True):
			# Focusing on this case, you have to chose which is the power of interest
			service_path = address + database + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"" + field + "\" < 0 GROUP BY time(1d)" 

		else:
			# Focusing on this case, you will always extract the Power exposed by the USM (that's why exploit energyquery content)
			service_path = address + database + energyquery + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"Processed_P\" < 0 GROUP BY time(1d)"


	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	# sreturn response.json()
	# ------------------------------------------------------------------------------------ #
	# Concerning that, it is not present a direct Query allowing to regroup automatically over months
	# it is mandatory to build a new Json response with the aggregated values calculated over it.
	# Iterate on each month of the year and estimate the average.
	# ------------------------------------------------------------------------------------ #
	#print("RESPONSE[0]: ")
	#print(response.json()['results'][0]['series'][0]['values'][0])
	#print("RESPONSE[1]: ")
	#print(response.json()['results'][0]['series'][0]['values'][1])
	#print("RESPONSE[2]: ")
	#print(response.json()['results'][0]['series'][0]['values'][2])

	#print("RESPONSE[183]: ")
	#print(response.json()['results'][0]['series'][0]['values'][183])
	#print("RESPONSE[184]: ")
	#print(response.json()['results'][0]['series'][0]['values'][184])

	# yearResponse = response.json()
	# print("LEN: " + str(len(yearResponse['results'][0]['series'][0]['values'])))
	# print("RANGE: " + str(range(len(yearResponse['results'][0]['series'][0]['values']))))
	# for x in range(len(response.json()['results'][0]['series'][0]['values'])):
	#	print("X: " + str(x))
	#	del yearResponse['results'][0]['series'][0]['values'][int(x)]
	#
	print("YEAR-----: ")
	#print(yearResponse)

	try:
		dayoffset = -1
		for monthCounter in range(1,13):
			monthlyAvg = 0
			# Identify which month is and the amount of days to set toDate:
			weekday,days = monthrange(int(year), int(monthCounter))
			print("Month number: " +str(monthCounter) + " counters: " + str(dayoffset))		
			# Exploit only the days with real values (not null)
			# realDays = int(days)+1
			realDays = int(days)

			for dayCounter in range(1,days+1):
				print("> Counter: "+ str(dayoffset+dayCounter))		
				t,power = response.json()['results'][0]['series'][0]['values'][int(dayCounter+dayoffset)]
				if(power):
					monthlyAvg += power
				else:
					realDays -= 1

			print("Power(month): " + str(monthlyAvg))

			if(realDays > 0):
				monthlyAvg /= realDays
			else:
				monthlyAvg = None

			print("Estimate Month average over ("+str(realDays)+") days of data: " +str(monthlyAvg))

			resultDate = datetime(int(year), monthCounter , 1, 0, 0, 0, tzinfo=tz.utc)
			resultDate = str(resultDate).split('+')[0]
			resultDate = str(resultDate).split(' ')[0]
			print("resultDate: " + str(resultDate))

			yearResponse['results'][0]['series'][0]['values'].append(tuple((resultDate,monthlyAvg)))

			dayoffset += int(days)

			print("Next(month)---------------:")
	except Exception as e:
		if(enablePrints == True):
			print("[Residential][LOG] FILTERED Field Parsing Returned Error: %s" %e)
		return ("[Residential][LOG] FILTERED Field Parsing Returned Error: %s" %e)


	print("YEAR2------------------------------: ")
	#print(yearResponse)
	# Fill in the label on the message to be returned back:
	
	yearResponse['results'][0]['series'][0]['name'] = measurementID #.append(tuple((resultDate,monthlyAvg)))

	return yearResponse

	if(enableFullStructuresPrints == True):
		print("[Residential][LOG]  FILTERED Field evaluation FULLCONTENT: " + str(response.json()))
	try:
		empty = False
		try:
			# Verify if content exists:
			a = response.json()['results'][0]['series']
		except Exception as e:
			empty = True
			result = None

		if(empty == False):
			if(enableFullStructuresPrints == True):
				print("[Residential][LOG] FILTERED Field Result:" + str(response.json()['results'][0]['series'][0]['values']))
			result = response.json()['results'][0]['series'][0]['values']
	except Exception as e:
		if(enablePrints == True):
			print("[Residential][LOG] FILTERED Field Parsing Returned Error: %s" %e)
		return ("[Residential][LOG] FILTERED Field Parsing Returned Error: %s" %e)

	xAxes  = []

	# if response is not empty
	if not result or len(result) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] FILTERED Field returns Empty message")
		return ("[Residential][LOG] FILTERED Field returns Empty message")

	for key,value in result:
		debugTmp = key
		if(value == None):
			tmp = 0

		elif(currfilter == "POSITIVE"):
		# Only Positive values
			if(value > 0):
				tmp = value
			else: 
				tmp = 0
		elif(currfilter == "NEGATIVE"):
		# Only Negative values
			if(value < 0):
				tmp = value
			else: 
				tmp = 0
		else:
		# All
			tmp = value

		xAxes.append(tmp)

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	

	return json.dumps(xAxes)


	return response.json()

# ------------------------------------------------------------------------------------ #
### Filtered Data (plus operations such as: GROUPBY) InfluxDB/{fromDate}/{toDate}/{measurement}/{Field}/{FILTER}/{OPERATION}/{VALUE}
#   INFLUXDB/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015/P/POSITIVE/GROUPBY/30
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouse20/battery/POSITIVE/GROUPBY/30
def get_filtered_data(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] Get historical data (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate     = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate     = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	field      = words.split("/")[5]
	currfilter = words.split("/")[6]
	
	operation = words.split("/")[7]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[8]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	fronius  = False
	if(("S4G-GW") in measurementID):
		database = "S4G-DWH-USM"
	elif(("InstallationHouse") in measurementID):
		fronius  = True
		database = "S4G-DWH-TEST"
		try:
			field    = words.split("/")[5]
		except Exception as e:
			print("Exception: %s" %e)
			return ("[Residential][LOG] Error: You must select the Fronius Field! Look at documentation!")

		if(str(field)   == "photovoltaic"):
			field = "P-PV"
		elif(str(field) == "grid"):
			field = "P-Grid"
		elif(str(field) == "load"):
			field = "P-Load"
		elif(str(field) == "battery"):
			field = "P-Akku"
		elif(str(field) == "SoC"):
			field = "SOC"
		else:
			return ("[Residential][LOG] Error: Uknwown Field selected: " + str(field))
	else:
		return "[Residential][LOG] Error: Uknwown Device and Database selected"	


	if(fronius == True):
		# Focusing on this case, you have to chose which is the power of interest
		service_path = address + database + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' GROUP BY time(" + str(interval) + "m)" 

	else:
		# Focusing on this case, you will always extract the Power exposed by the USM (that's why exploit energyquery content)
		service_path = address + database + energyquery + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")


	if(enableFullStructuresPrints == True):
		print("[Residential][LOG]  FILTERED Field evaluation FULLCONTENT: " + str(response.json()))
	try:
		empty = False
		try:
			# Verify if content exists:
			a = response.json()['results'][0]['series']
		except Exception as e:
			empty = True
			result = None

		if(empty == False):
			if(enableFullStructuresPrints == True):
				print("[Residential][LOG] FILTERED Field Result:" + str(response.json()['results'][0]['series'][0]['values']))
			result = response.json()['results'][0]['series'][0]['values']
	except Exception as e:
		if(enablePrints == True):
			print("[Residential][LOG] FILTERED Field Parsing Returned Error: %s" %e)
		return ("[Residential][LOG] FILTERED Field Parsing Returned Error: %s" %e)

	xAxes  = []

	# if response is not empty
	if not result or len(result) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] FILTERED Field returns Empty message")
		return ("[Residential][LOG] FILTERED Field returns Empty message")

	for key,value in result:
		debugTmp = key
		if(value == None):
			tmp = 0

		elif(currfilter == "POSITIVE"):
		# Only Positive values
			if(value > 0):
				tmp = value
			else: 
				tmp = 0
		elif(currfilter == "NEGATIVE"):
		# Only Negative values
			if(value < 0):
				tmp = value
			else: 
				tmp = 0
		else:
		# All
			tmp = value

		xAxes.append(tmp)

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	

	return json.dumps(xAxes)

# ---------------------------------------------------------------------------------------------------------------- #
### Energy Data: 
#    1      /    2     /   3    /       4
#   ENERGY/{fromDate}/{toDate}/{measurement}
#   ENERGY/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015
#   LOCALENERGY/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015
# ----------------------------------------------------------------------- #
# Following API will regroup automatically the selected time-window values:
# ----------------------------------------------------------------------- #
# if today (until this moment)
def get_energy(handler):
	global influxServer
	global influxLocalServer
	global energyquery

	words = handler.path
	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "ENERGY"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	if(enablePrints == True):
		print("[Residential][LOG] Get historical raw data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return("[Residential][LOG] Wrong Date: " + str(fromDate))


	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return("[Residential][LOG] Wrong Date: " + str(toDate))


	diff = toDate - fromDate

	fromDateStr = str(fromDate).split('+')[0]
	toDateStr   = str(toDate).split('+')[0]
	endDateStr  = str(toDateStr)

	if(enablePrints == True):
		print("[Residential][LOG] FROM: " + fromDateStr)
		print("[Residential][LOG] TO: " + toDateStr)


	# ------------------------------------------ #
	# Verify if starting date is before ending date
	if(fromDateStr > endDateStr):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(endDate) + "]")

	# ------------------------------------------ #
	currentDateTime = datetime.utcnow()
	currentDate     = str(currentDateTime).split(' ')[0]
	endDate         = str(toDateStr).split(' ')[0]

	# ------------------------------------------ #
	if(currentDate < endDate):
		if(enablePrints == True):
			print("[Residential][LOG] We have to limit the query because ending date is in the future!")

		year, month, day = str(currentDate).split('-')
		tmp = str(currentDateTime).split(' ')[1]
		tmp = str(tmp).split('.')[0]	
		hour, minute, second = tmp.split(':')
		try:
			endDate = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), tzinfo=tz.utc)
		except ValueError:
			return ("[Residential][LOG] Wrong Date: " + toDateStr)

		# Update diff!
		diff = endDate - fromDate
		endDateStr = str(endDate).split('+')[0]
	elif(currentDate == endDate):
		# We need to update endDate with current Time!
		print("[Residential][LOG] Trying to evaluate current Day: ")
		print("[Residential][LOG] FromDate("+str(type(fromDate))+"): " + str(fromDate))
		print("[Residential][LOG] CurrentDateTime("+str(type(currentDateTime))+"): " + str(currentDateTime))

		# Required Timezone awarness adaptation:
		tmpDateTime = currentDateTime.replace(tzinfo=tz.UTC)
		diff = tmpDateTime - fromDate
		endDateStr=str(tmpDateTime).split('+')[0]


	# We need to Manage the Fronius-Entries in InfluxDB, by allowing:
	#   ENERGY/{fromDate}/{toDate}/{FroniusMeasurement}/{FieldOfInterest}
	#   ENERGY/2018-12-24/2018-12-25/InstallationHouse20/P-PV
	fronius  = False

	if(("S4G-GW") in measurementID):
		database = "S4G-DWH-USM"
	elif(("InstallationHouse") in measurementID):
		fronius  = True
		database = "S4G-DWH-TEST"
		try:
			field    = words.split("/")[5]
		except Exception as e:
			print("Exception: %s" %e)
			return ("[Residential][LOG] Error: You must select the Fronius Field! Look at documentation!")

		if(str(field)   == "photovoltaic"):
			field = "P-PV"
		elif(str(field) == "grid"):
			field = "P-Grid"
		elif(str(field) == "load"):
			field = "P-Load"
		elif(str(field) == "battery"):
			field = "P-Akku"
		elif(str(field) == "SoC"):
			field = "SOC"
		else:
			return ("[Residential][LOG] Error: Uknwown Field selected: " + str(field))
	else:
		return "[Residential][LOG] Error: Uknwown Device and Database selected"	

	# ------------------------------------------------------------------ #
	# Adaptive Query to enable InfluxDB data extraction within browsers
	# [AVOIDING CONNECTION TIMEOUTS]!
	# ------------------------------------------------------------------ #
	threshold_lowest  = timedelta(days = int(THRESHOLD_INF_LOW[0]))
	threshold_min     = timedelta(days = int(THRESHOLD_MIN[0]))
	threshold_low     = timedelta(days = int(THRESHOLD_LOW[0]))
	threshold_mid     = timedelta(days = int(THRESHOLD_MID[0]))
	threshold_high    = timedelta(days = int(THRESHOLD_HIGH[0]))
	threshold_highest = timedelta(days = int(THRESHOLD_INF_HIGH[0]))

	if(diff <= threshold_lowest):
		groupBy = THRESHOLD_INF_LOW[1]
	elif (diff > threshold_lowest and diff <= threshold_min):
		groupBy = THRESHOLD_MIN[1]
	elif (diff > threshold_min and diff <= threshold_low):
		groupBy = THRESHOLD_LOW[1]
	elif (diff > threshold_low and diff <= threshold_mid):
		groupBy = THRESHOLD_MID[1]
	elif (diff > threshold_mid and diff <= threshold_high):
		groupBy = THRESHOLD_HIGH[1]
	elif (diff > threshold_high and diff <= threshold_highest):
		groupBy = THRESHOLD_MAX[1]
	elif (diff > threshold_highest):
		groupBy = THRESHOLD_INF_HIGH[1]


	if(enablePrints == True):
		print("[Residential][LOG] THRESHOLDS SETTINGS: ")
		print("[Residential][LOG] Time-Window Requested: "+ str(diff))
		print("[Residential][LOG] Thresholds ["+ str(threshold_lowest) +"]["+str(threshold_min) +"]["+str(threshold_low) +"]["+str(threshold_mid) +"]["+str(threshold_high) +"]["+str(threshold_highest)+"]")
		print("[Residential][LOG] GroupBy: " + str(groupBy) + " minutes")

	# --------------------------------------------------------------------- #
	if(fronius == True):
		service_path = address + database + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDateStr) + "\' and time < " + "\'" + str(endDateStr) + "\' GROUP BY time(" + str(groupBy) + "m)" 

	else:
		service_path = address + database + energyquery + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDateStr) + "\' and time < " + "\'" + str(endDateStr) + "\' GROUP BY time(" + str(groupBy) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] ENERGY API(uri): " + service_path)

	try:
		response = requests.get(str(service_path), auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] ENERGY API (Error) " + service_path)
		return "[Residential] ENERGY Service Not reachable/available"


	# response.json() WILL HOLD just Power Values (with the inherithed step defined by the GROUPBY operation)
	# HERE we have to perfomr integral of given power within the time-window given and the selected step!
	if(enableFullStructuresPrints == True):
		print("[Residential][LOG] ENERGY evaluation FULLCONTENT: " + str(response.json()))
	try:
		empty = False
		try:
			# Verify if content exists:
			a = response.json()['results'][0]['series']
		except Exception as e:
			empty = True
			result = None

		if(empty == False):
			if(enableFullStructuresPrints == True):
				print("[Residential][LOG] ENERGY Result:" + str(response.json()['results'][0]['series'][0]['values']))
			result = response.json()['results'][0]['series'][0]['values']
	except Exception as e:
		if(enablePrints == True):
			print("[Residential][LOG] ENERGY Parsing Returned Error: %s" %e)
		return ("[Residential][LOG] ENERGY Parsing Returned Error: %s" %e)

	# if response is not empty
	if not result or len(result) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] ENERGY Returned Empty message")
		return ("[Residential][LOG] ENERGY Returned Empty message")


	if(enablePrints == True):
		print("[Residential][LOG] --- ENERGY EVALUATION ---")
		print("[Residential][LOG] NUMBER OF SAMPLES: " + str(len(result)))
		print("[Residential][LOG] TIMEDELTA: " + str(diff))
		print("[Residential][LOG] SECONDS: " + str(diff.total_seconds()))
		print("[Residential][LOG] INCREMENT(seconds): " + str(diff.total_seconds() / len(result)))

	functionToIntegrate = []

	# We need to define the X array
	# Starting from the TimeWindow and the Amount of samples
	# Identify increment value to define explicitly every X position related to the sample Y
	xAxes  = []
	xStart = 0
	xEnd   = diff.total_seconds()
	xInc   = diff.total_seconds() / len(result)

	# -------------------------------------- #
	# To Manage "None" values, 
	# we will override with zeros!
	# For debugging purposes it will be shown:
	# The Start/End of Null values sequences
	# -------------------------------------- #
	if(enablePrints == True):
		debugflag  = False
		debugStart = 0
		debugEnd   = 0
		debugTmp   = 0
	

	for key,value in result:
		debugTmp = key
		xAxes.append(xStart)
		if(value == None):
			functionToIntegrate.append(0)
			if(enablePrints == True and debugflag == False):
				debugflag  = True
				debugStart = key
		else:
			functionToIntegrate.append(value)
			if(enablePrints == True and debugflag == True):
				debugflag = False
				debugEnd  = key
				print("[Residential][LOG] Found sequence of missing data: ")
				print("[Residential][LOG] From Time: " + str(debugStart))
				print("[Residential][LOG] To Time: " + str(debugEnd))
		xStart += xInc

	# If we did not recover from the None Sequence (last value still None):
	if(enablePrints == True and debugflag == True):
		debugflag = False
		debugEnd  = debugTmp
		print("[Residential][LOG] Found sequence of missing data: ")
		print("[Residential][LOG] From Time: " + str(debugStart))
		print("[Residential][LOG] To Time: " + str(debugEnd))

	# Y axes = Power values
	# X axes = TimeFrame values related to sampling (together with grouped means):
	try:
		energy = integrate.simps(functionToIntegrate,xAxes)

	except Exception as e:
		if(enablePrints == True):
			print("[Residential][LOG] ENERGY Integrate Returned Error: %s" %e)
		return ("[Residential][LOG] ENERGY Integrate Returned Error: %s" %e)

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] ENERGY API last: " + str(end - start))	


	if(enablePrints == True):
		print("X axes(time): " + str(xAxes))
		print("Y axes(power): " + str(functionToIntegrate))

	# ------------------------------ #	
	# Energy is now: Watt*seconds
	# We want Energy in: Watt*hours
	# ------------------------------ #
	return energy/3600
# ---------------------------------------------------------------------------------------------------------------- #
### Generic Raw Data: 
#    1      /    2     /   3    /       4
#   InfluxDB/{fromDate}/{toDate}/{measurement}
#   DEFAULT=GROUPBY/30
#   INFLUXDB/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015
# ----------------------------------------------------------------------- #
# Following API will regroup automatically the selected time-window values:
# Less then 1 month            <->  30 minutes
# Between 1 month and 6 months <->  1 hour
# More then 6 months           <->  3 hours
# ----------------------------------------------------------------------- #
def get_historical_rawdata(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	# Default values:
	groupBy = 30
	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	if(enablePrints == True):
		print("[Residential][LOG] get historical raw data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))


	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	diff = toDate - fromDate

	fromDate = str(fromDate).split('+')[0]
	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering:  FROM = [" + str(fromDate) + "]   TO = [" + str(toDate) + "]")

	if(("S4G-GW") in measurementID):
		database = "S4G-DWH-USM"
	elif(("InstallationHouse") in measurementID):
		database = "S4G-DWH-TEST"
	else:
		return str("[Residential][LOG] Error: Unknwown Measurement")

	# ------------------------------------------------------------------ #
	# Adaptive Query to enable InfluxDB data extraction within browsers
	# [AVOIDING CONNECTION TIMEOUTS]!
	# ------------------------------------------------------------------ #
	threshold_min  = timedelta(days = int(THRESHOLD_MIN[0]))
	threshold_low  = timedelta(days = int(THRESHOLD_LOW[0]))
	threshold_mid  = timedelta(days = int(THRESHOLD_MID[0]))
	threshold_high = timedelta(days = int(THRESHOLD_HIGH[0]))
	threshold_max  = timedelta(days = int(THRESHOLD_MAX[0]))

	if (diff <= threshold_min):
		groupBy = THRESHOLD_MIN[1]
	elif (diff > threshold_min and diff <= threshold_low):
		groupBy = THRESHOLD_LOW[1]
	elif (diff > threshold_low and diff <= threshold_mid):
		groupBy = THRESHOLD_MID[1]
	elif (diff > threshold_mid and diff <= threshold_high):
		groupBy = THRESHOLD_HIGH[1]
	elif (diff > threshold_high and diff <= threshold_max):
		groupBy = THRESHOLD_MAX[1]
	elif (diff > threshold_max):
		groupBy = THRESHOLD_INF

	# --------------------------------------------------------------------- #
	service_path = address + database + basequery + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' GROUP BY time(" + str(groupBy) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	

	return response.json()


# --------------------------------------------------------------------- #
#                                  NEW APIs:
# --------------------------------------------------------------------- #
### Consumption_house (plus operations such as: GROUPBY) 
### power_from_grid [aka: consumption_house]
#   consumption_house      = (-P_Load) 
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/consumption_house/{OPERATION}/{VALUE}
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/consumption_house/GROUPBY/30
def get_consumption_house(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] Get consumption_house (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	operation = words.split("/")[6]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[7]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	if(("InstallationHouse") in measurementID):
		database = "S4G-DWH-TEST"
	else:
		return str("[Residential][LOG] Error: Uknwown Device and Database selected")

	service_path = address + database + froniusquery1 + "P-Load" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	

	# if response is not empty
	if not response or len(response.json()['results'][0]) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] Empty message")
		return ("[Residential][LOG] Empty message")

	listOfinterest = response.json()['results'][0]['series'][0]['values']	
	# multiply each value to -1 (mantain just the json list)
	# Filter out the None values!
	# Note: if you want to keep them: 
	# result = [(x[0],float(x[1]*(-1))) if x[1] else (x[0],x[1]) for x in listOfinterest]
	result = [(x[0],x[1]*(-1)) for x in listOfinterest if x[1]]
	
	return result


### Over Production (plus operations such as: GROUPBY) 
#   over_production        = if (P_Grid<0) then (-P_Grid) else 0
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/over_production/{OPERATION}/{VALUE}
#   INFLUXDB/2019-01-25/2019-03-27/InstallationHouseBolzano/over_production/GROUPBY/30
def get_over_production(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] Get over_production (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	operation = words.split("/")[6]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[7]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	if(("InstallationHouse") in measurementID):
		database = "S4G-DWH-TEST"
	else:
		return str("[Residential][LOG] Error: Uknwown Device and Database selected")

	service_path = address + database + froniusquery1 + "P-Grid" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"P-Grid\" < 0 " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	# if response is not empty
	if not response or len(response.json()['results'][0]) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] Empty message")
		return ("[Residential][LOG] Empty message")

	# multiply each value to -1
	listOfinterest = response.json()['results'][0]['series'][0]['values']		
	result = [(x[0],x[1]*(-1)) for x in listOfinterest if x[1]]

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	


	return result


### evaluate_production (OK):
#   production                 = prod_PV - over_production
#   Where: over_production     = if (P_Grid<0) then (-P_Grid) else 0
#   Where: prod_PV             = Processed_P da (SMX)
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/evaluate_production/{OPERATION}/{VALUE}
#   INFLUXDB/2019-01-25/2019-03-27/InstallationHouseBolzano/evaluate_production/GROUPBY/30
def evaluate_production(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] evaluate_production (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	operation = words.split("/")[6]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[7]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	if(("InstallationHouse") in measurementID):
		database = "S4G-DWH-TEST"
	else:
		return str("[Residential][LOG] Error: Uknwown Device and Database selected")

	if(measurementID == "InstallationHouseBolzano"):
		measurementID2 = "S4G-GW-EDYNA-0015"
		database2 = "S4G-DWH-USM"
		field     = "Processed_P" 
	else:
		print("[Residential][LOG] Error: only Bolzano pilot have SMX measuring PV consumption!")		
		print("[Residential][LOG] Error: Try to exploit PV values from Fronius instead!")		
		measurementID2 = measurementID
		database2 = "S4G-DWH-TEST"
		field = "P-PV"

	# ----------------------------------------------------------------------------------------- #		
	#   Where: over_production     = if (P_Grid<0) then (-P_Grid) else 0
	service_over_production_path = address + database + froniusquery1 + "P-Grid" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"P-Grid\" < 0 " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_over_production_path)

	try:
		response1 = requests.get(service_over_production_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_over_production_path)
		return str("[Residential] Influx Service Not reachable/available")


	# if response is not empty
	if not response1 or len(response1.json()['results'][0]) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] Empty message1")
		return ("[Residential][LOG] Empty message1")

	# over_production = if (P_Grid<0) then (-P_Grid) else 0
	# Consequently, multiply response1 to -1
	listOfinterest = response1.json()['results'][0]['series'][0]['values']
	resultOverProd = [(x[0],float(x[1]*(-1))) if x[1] else (x[0],x[1]) for x in listOfinterest]
	# ----------------------------------------------------------------------------------------- #
	
	# ----------------------------------------------------------------------------------------- #
	service_prod_PV_path = address + database2 + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID2) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_prod_PV_path)

	try:
		response2 = requests.get(service_prod_PV_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_prod_PV_path)
		return str("[Residential] Influx Service Not reachable/available")

	# if response is not empty
	if not response2 or len(response2.json()['results'][0]) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] Empty message2")
		return ("[Residential][LOG] Empty message2")

	secondlistOfinterest = response2.json()['results'][0]['series'][0]['values']

	# Even Production is multipled to -1 if the source is SMX (negative values for production)
	# Otherwise (if PV source is Fronius) then exloit the raw value (positive values for production)
	if(field == "Processed_P"):
		if(enablePrints == True):
			print("Identified PV SMX source ")
		# resultPV = [(x[0],float(x[1]*(-1))) for x in secondlistOfinterest if x[1]]
		resultPV = [(x[0],float(x[1]*(-1))) if x[1] else (x[0],x[1]) for x in secondlistOfinterest]
	else:
		if(enablePrints == True):
			print("Identified PV Fronius source ")
		# resultPV = [(x[0],float(x[1])) for x in secondlistOfinterest if x[1]]
		resultPV = [(x[0],float(x[1])) if x[1] else (x[0],x[1]) for x in secondlistOfinterest]

	if(len(resultPV) >= len(resultOverProd)):
		currentLen = len(resultOverProd)
	else:
		currentLen = len(resultPV)

	# Build up the tuple composed by: (timestamp,value)
	# where value is the current production (estimated as): 
	# production = prod_PV - over_production
	# Only if the value exists (Not Null/None values)
	# Note that: it is mandatory to keep the relation with the time for both of them
	# Otherwise, the resulting lists will be different! (Consequently the evaluation will fail)
	finalresult = [(resultPV[y][0],float(resultPV[y][1] - resultOverProd[y][1])) for y in range(currentLen) if resultPV[y][1] and resultOverProd[y][1]]

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	


	return finalresult



### power2battery [aka: consumption_battery]:
#   power2battery          = consumption_battery
#   consumption_battery    = if (P_Akku<0) then (-P_Akku) else 0
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/power2battery/{OPERATION}/{VALUE}
#   INFLUXDB/2019-01-25/2019-03-27/InstallationHouseBolzano/power2battery/GROUPBY/30
def get_power2battery(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] Get power2battery (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	operation = words.split("/")[6]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[7]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	if(("InstallationHouse") in measurementID):
		database = "S4G-DWH-TEST"
	else:
		return str("[Residential][LOG] Error: Uknwown Device and Database selected")

	#   consumption_battery    = if (P_Akku<0) then (-P_Akku) else 0
	service_path = address + database + froniusquery1 + "P-Akku" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"P-Akku\" < 0 " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	# if response is not empty
	if not response or len(response.json()['results'][0]) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] Empty message")
		return ("[Residential][LOG] Empty message")
	
	listOfinterest = response.json()['results'][0]['series'][0]['values']		
	result = [(x[0],x[1]*(-1)) for x in listOfinterest if x[1]]


	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))

	return result




### evaluate_total_production:
#   total_production           = production_battery + prod_PV
#   Where: production_battery  = if (P_Akku>0) then (+P_Akku) else 0
#   Where: prod_PV             = Processed_P da (SMX) or P_PV da (Fronius)
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/evaluate_total_production/{OPERATION}/{VALUE}
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/evaluate_total_production/GROUPBY/30
def evaluate_total_production(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] evaluate_total_production (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	operation = words.split("/")[6]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[7]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	if(measurementID == "InstallationHouseBolzano"):
		measurementID2 = "S4G-GW-EDYNA-0015"
		database2 = "S4G-DWH-USM"
		field     = "Processed_P" 
	else:
		print("[Residential][LOG] Error: only Bolzano pilot have SMX measuring PV consumption!")		
		print("[Residential][LOG] Error: Try to exploit PV values from Fronius instead!")		
		measurementID2 = measurementID
		database2 = "S4G-DWH-TEST"
		field = "P-PV"

	#   Where: production_battery  = if (P_Akku>0) then (+P_Akku) else 0
	service_path = address + database2 + froniusquery1 + "P-Akku" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"P-Akku\" > 0 " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")


	# if response is not empty
	if not response or len(response.json()['results'][0]) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] Empty message1")
		return ("[Residential][LOG] Empty message1")

	# ***
	production_batterylist = response.json()['results'][0]['series'][0]['values']
	prod_batterylist = [(x[0],float(x[1]*(-1))) if x[1] else (x[0],x[1]) for x in production_batterylist]

	#   Where: prod_PV             = Processed_P da (SMX) or P_PV da (Fronius)
	service_path = address + database2 + froniusquery1 + field + froniusquery2 + "\"" + str(measurementID2) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response2 = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")


	# if response is not empty
	if not response2 or len(response2.json()['results'][0]) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] Empty message2")
		return ("[Residential][LOG] Empty message2")

	secondlistOfinterest = response2.json()['results'][0]['series'][0]['values']
	# Even Production is multipled to -1 if the source is SMX (negative values for production)
	# Otherwise (if PV source is Fronius) then exloit the raw value (positive values for production)
	if(field == "Processed_P"):
		print("Identified PV SMX source ")
		# resultPV = [(x[0],float(x[1]*(-1))) for x in secondlistOfinterest if x[1]]
		resultPV = [(x[0],float(x[1]*(-1))) if x[1] else (x[0],x[1]) for x in secondlistOfinterest]
	else:
		print("Identified PV Fronius source ")
		# resultPV = [(x[0],float(x[1])) for x in secondlistOfinterest if x[1]]
		resultPV = [(x[0],float(x[1])) if x[1] else (x[0],x[1]) for x in secondlistOfinterest]

	# Build up the tuple composed by: (timestamp,value)
	# where value is the total_production (estimated as): 
	# production = production_battery + prod_PV
	# Only if the value exists (Not Null/None values)
	finalresult = [(resultPV[y][0],float(prod_batterylist[y][1] - resultPV[y][1])) for y in range(len(resultPV)) if resultPV[y][1] and prod_batterylist[y][1]]

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	


	return finalresult


### evaluate_direct_consumption (DEPRECATED):
#   consumption_direct     = abs(prod_PV - consumption_battery - over_production)
#   Where: consumption_battery = if (P_Akku<0) then (-P_Akku) else 0
#   Where: prod_PV             = Processed_P da (SMX) or P_PV da (Fronius)
#   Where: over_production     = if (P_Grid<0) then (-P_Grid) else 0 
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/evaluate_direct_consumption/{OPERATION}/{VALUE}
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/evaluate_direct_consumption/GROUPBY/30
def evaluate_direct_consumption(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] evaluate_direct_consumption (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	operation = words.split("/")[6]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[7]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	if(("InstallationHouse") in measurementID):
		database = "S4G-DWH-TEST"
	else:
		return str("[Residential][LOG] Error: Uknwown Device and Database selected")

	service_path = address + database + froniusquery1 + "P-Load" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"P-Grid\" < 0 " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response = requests.get(service_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	

	return "Not Yet fully implemented (DEPRECATED)"


### evaluate_power2grid:
#   power2grid             = over_production + consumption_battery
#   Where: over_production        = if (P_Grid<0) then (-P_Grid) else 0
#   Where: consumption_battery    = if (P_Akku<0) then (-P_Akku) else 0
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/evaluate_power2grid/{OPERATION}/{VALUE}
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/evaluate_power2grid/GROUPBY/30
def evaluate_power2grid(handler):
	global influxServer
	global influxLocalServer
	global basequery
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] evaluate_power2grid (starts)")

	# --------------------------------------------------------------------- #
	if(enableTimingEval == True):
		start = datetime.utcnow()

	destination = words.split("/")[1]

	if(destination == "INFLUXDB"):
		address = influxServer
	else:
		address = influxLocalServer

	fromDate_tmp = words.split("/")[2]
	fromDate = fromDate_tmp.replace("-",".")

	toDate_tmp = words.split("/")[3]
	toDate = toDate_tmp.replace("-",".")

	measurementID = words.split("/")[4]

	operation = words.split("/")[6]

	if(operation in knownOperations):
		opQuery = knownOperations[operation]
	else:
		return str("[Residential][LOG] Unknown Operation")

	interval  = words.split("/")[7]

	if(enablePrints == True):
		print("[Residential][LOG] get historical data (" + measurementID + ") from: (" + fromDate + ") to: (" + toDate + ")")

	# --------------------------------------------------------------------- #
	# Build real datetime objects to avoid compatibility issue
	# Verify if correct date
	year, month, day = fromDate.split('.')
	try:
		fromDate = datetime(int(year), int(month), int(day),0, 0, 0, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(fromDate))

	fromDate = str(fromDate).split('+')[0]

	# Verify if correct date
	year, month, day = toDate.split('.')
	try:
		# toDate = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=tz.utc)
		toDate = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=tz.utc)
	except ValueError:
		return str("[Residential][LOG] Wrong Date: " + str(toDate))

	toDate = str(toDate).split('+')[0]

	# Verify if starting date is before ending date
	if(fromDate > toDate):
		return str("[Residential][LOG] Bad Date Ordering, FROM:[" + str(fromDate) + "] TO:[" + str(toDate) + "]")

	# DataBase selection:
	if(("InstallationHouse") in measurementID):
		database = "S4G-DWH-TEST"
	else:
		return str("[Residential][LOG] Error: Uknwown Device and Database selected")

	# Where over_production        = if (P_Grid<0) then (-P_Grid) else 0
	service_over_production_path = address + database + froniusquery1 + "P-Grid" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"P-Grid\" < 0 " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_over_production_path)

	try:
		response1 = requests.get(service_over_production_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	# multiply response1 to -1
	# if response is not empty
	if not response1 or len(response1.json()['results'][0]) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] Empty message1")
		return ("[Residential][LOG] Empty message1")

	# over_production = if (P_Grid<0) then (-P_Grid) else 0
	# Consequently, multiply response1 to -1
	listOfinterest = response1.json()['results'][0]['series'][0]['values']
	# resultOverProd = [(x[0],x[1]*(-1)) for x in listOfinterest if x[1]]
	resultOverProd = [(x[0],float(x[1]*(-1))) if x[1] else (x[0],x[1]) for x in listOfinterest]

	# Where consumption_battery    = if (P_Akku<0) then (-P_Akku) else 0
	service_consumption_battery_path = address + database + froniusquery1 + "P-Akku" + froniusquery2 + "\"" + str(measurementID) + "\" where time > " + "\'" + str(fromDate) + "\' and time < " + "\'" + str(toDate) + "\' and \"P-Akku\" < 0 " + str(opQuery) + " time(" + str(interval) + "m)" 

	if(enablePrints == True):
		print("[Residential][LOG] INFLUX API " + service_path)

	try:
		response2 = requests.get(service_consumption_battery_path, auth=HTTPBasicAuth(username,password))
	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] INFLUX API " + service_path)
		return str("[Residential] Influx Service Not reachable/available")

	# multiply response2 to -1
	# if response is not empty
	if not response2 or len(response2.json()['results'][0]) <= 1:
		if(enablePrints == True):
			print("[Residential][LOG] Empty message1")
		return ("[Residential][LOG] Empty message1")

	# consumption_battery    = if (P_Akku<0) then (-P_Akku) else 0
	# Consequently, multiply response1 to -1
	listOfinterest = response2.json()['results'][0]['series'][0]['values']
	# resultConsBatt = [(x[0],x[1]*(-1)) for x in listOfinterest if x[1]]
	resultConsBatt = [(x[0],float(x[1]*(-1))) if x[1] else (x[0],x[1]) for x in listOfinterest]

	# Build up the tuple composed by: (timestamp,value)
	# where value is the total_production (estimated as): 
	# power2grid = over_production + consumption_battery
	# Only if the value exists (Not Null/None values)
	finalresult = [(resultOverProd[y][0],float(resultOverProd[y][1] + resultConsBatt[y][1])) for y in range(len(resultOverProd)) if resultOverProd[y][1] and resultConsBatt[y][1]]

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] INFLUX API last: " + str(end - start))	

	return finalresult



############################################################################
# Start command for the optimization framework
############################################################################
#{
#  "control_frequency": 30,
#  "horizon_in_steps": 24,
#  "dT_in_seconds": 3600,
#  "model_name": "model_name",
#  "repetition": 0,
#  "solver": "solver"
#}
# ------------------------------------------------------------------------------------ #
HEADERS            = {'content-type': 'application/json'}
PROFESS_ADDRESS    = "http://10.8.0.84:8080/v1"

URL_PROFESS_STATUS = PROFESS_ADDRESS + "/optimization/status"
URL_PROFESS_START  = PROFESS_ADDRESS + "/optimization/start/"
URL_PROFESS_STOP   = PROFESS_ADDRESS + "/optimization/stop/"  
# ------------------------------------------------------------------------------------ #
reverseknownOpmode = {"maximizeSelfConsumption":0,"maximizeSelfProduction":1,"minimizeCosts":2,"MaximizeBatteryHealth":3,"None":4}  
# ------------------------------------------------------------------------------------ #
professStartMsg = {"control_frequency": 30,\
		   "horizon_in_steps": 24,\
		   "dT_in_seconds": 3600,\
		   "model_name": "name",\
		   "optimization_type":"value",\
		   "repetition": 0,\
		   "single_ev": False,\
		   "solver": "solver"}

# ------------------------------------------------------------------------------------ #
def get_opmode(handler):
	global opmode

	if(enablePrints == True):
		print("[Residential][LOG][GET]: " + str(opmode))
		print("[Residential][LOG] Current operational Mode: " + str(knownOpmode[int(opmode)]))

	# # # # # # # # # # # # # # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # #
	# Start interactions with PROFESS to align the current local OpMode value
	# # # # # # # # # # # # # # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # #
	# 1. Get Registration ID & Status
	# 2. Update Local value
	# 3. Return Updated value
	# # # # # # # # # # # # # # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # #

	try:
		response = requests.get(url = URL_PROFESS_STATUS)
	except Exception as e:
		if(enablePrints == True):
			print("[Residential][LOG] Get PROFESS Status " + URL_PROFESS_STATUS + " Error: %s" %e)
		return ("[Residential][LOG] Get PROFESS Status " + URL_PROFESS_STATUS + " Error: %s" %e)

	if (sys.version_info > (3, 0) and sys.version_info < (3, 6)):
		json_string = response.json() 
	else:
		json_string = json.loads(response.content)

	if(enablePrints == True):
		print("[Residential][LOG] Get PROFESS Status")

	# # # # # # # # # # # # # # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # #
	# Start Parsing:
	try:
		tmpResult = json_string['status']

		if(enablePrints == True):
			print("[Residential][LOG] Status parsing: " + str(tmpResult))

		found = False
		for key in tmpResult:
			if(enablePrints == True):			
				print("[Residential][LOG] Status parsing [KEY]: " + str(key))

			temporary = tmpResult[str(key)]
			startTime = temporary['start_time']
			status    = temporary['status']
			if(str(status) == str(RUNNING_STATUS_PROFESS)):
				result    = temporary['config']
				if(enablePrints == True):			
					print("[Residential][LOG] FOUND [KEY]: " + str(result['model_name']))
					print("[Residential][LOG] Is Active: " + str(status))
				found = True			

		if (found == False):
			if(enablePrints == True):			
				print("[Residential][LOG] Get PROFESS Status Parsing returned no active options")

			# Update Local Value
			opmode = DEFAULT_OPMODE

			return int(opmode)

	except Exception as e:
		print("[Residential][LOG] Get PROFESS Status Failed: %s (PROFESS Not Active)" %e)
		return ("[Residential][LOG] Get PROFESS Status Failed: %s (PROFESS Not Active)" %e)

	# if response is not empty and one PROFESS configuration is active
	if not result or len(result) == 0:
		if(enablePrints == True):
			print("[Residential][LOG][PROFESS] Returned Empty message")
	else:
		if(enablePrints == True):
			print("[Residential][LOG][PROFESS] Returned message, start parsing")
		try:
			professStartMsg['control_frequency'] = result['control_frequency']
			professStartMsg['horizon_in_steps']  = result['horizon_in_steps']
			professStartMsg['dT_in_seconds']     = result['dT_in_seconds']
			professStartMsg['model_name']        = result['model_name']
			professStartMsg['optimization_type'] = result['optimization_type']
			professStartMsg['repetition']        = result['repetition']
			professStartMsg['single_ev']         = result['single_ev']
			professStartMsg['solver']            = result['solver']
		except Exception as e:
			if(enablePrints == True):
				print("[Residential][LOG] PROFESS Returned partial message! Error: %s" %e)
			return ("[Residential][LOG] PROFESS Returned partial message! Error: %s" %e)

		# Translate the received message in the known Operation modes:
		try:
			if(professStartMsg['model_name'] in reverseknownOpmode):
				opmode = reverseknownOpmode[professStartMsg['model_name']]
		except Exception as e:
			print("[Residential][LOG] PROFESS Returned Uknwown OpMode! Error: %s" %e)
			return ("[Residential][LOG] PROFESS Returned Uknwown OpMode! Error: %s" %e)
	# # # # # # # # # # # # # # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # #
	return int(opmode)

# ------------------------------------------------------------------------------------ #
# REMEMBER THAT THE FOLLOWING API LASTS 4 TO 20 SECONDS 
# (depending on the behavioral branch: stop+start or just start)
# REMEMBER that between the stop and the next running opmode, 
# the server will respond with No Active modes.
# [Because starting state and not yet running]
# ------------------------------------------------------------------------------------ #
def set_opmode(handler):
	global opmode
	global knownOpmode

	if(enablePrints == True):
		print("[Residential][LOG][SET] Will override: " + str(opmode))

	try:
		key = handler.get_payload()
		if (key != None):
			if(str(key).isdigit() == True):
				if (key in knownOpmode):
					if(enablePrints == True):
						print("[Residential][LOG][SET]: " + str(key) + " == " + str(knownOpmode[key]))

					# Update local value
					opmode = int(key)
					
					# Remember to verify if PROFESS was running and to disable the previous settings
					# Otherwise PROFESS will continue its work while GESSCon will try to manage it.
					if (opmode == 3):
						# # # # # # # # # # # # # # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # #
						# Proper Value (Start interactions with GESSCon):
						# # # # # # # # # # # # # # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # #
						print("[Residential] Requested setting not enabled yet: " + str(knownOpmode[int(opmode)]))
						return ("[Residential] Requested setting not enabled yet: " + str(knownOpmode[int(opmode)]))


					# # # # # # # # # # # # # # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # #
					# Proper Value (Start interactions with PROFESS):
					# # # # # # # # # # # # # # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # #
					# 1. Get Registration ID & Status
					# 2. Fill & Send Start command with retrieved data
					# # # # # # # # # # # # # # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # #
					try:
						response = requests.get(url = URL_PROFESS_STATUS)
					except Exception as e:
						if(enablePrints == True):
							print("[Residential][LOG] Get/Set PROFESS Status " + URL_PROFESS_STATUS + " Error: %s" %e)
						return ("[Residential][LOG] Get/Set PROFESS Status " + URL_PROFESS_STATUS + " Error: %s" %e)

					if (sys.version_info > (3, 0) and sys.version_info < (3, 6)):
						json_string = response.json() 
					else:
						json_string = json.loads(response.content)

					if(enablePrints == True):
						print("[Residential][LOG] Get/Set PROFESS Status")

					try:
						tmpResult = json_string['status']

						if(enablePrints == True):
							print("[Residential][LOG] Status parsing: " + str(tmpResult))

						found         = False
						foundSettings = False

						for field in tmpResult:
							if(enablePrints == True):			
								print("[Residential][LOG] Status parsing [KEY]: " + str(field))

							temporary = tmpResult[str(field)]
							result    = temporary['config']
							startTime = temporary['start_time']
							status    = temporary['status']

							if(str(status) == str(RUNNING_STATUS_PROFESS)):
							# Verify if one is already active
								if(enablePrints == True):			
									print("[Residential][LOG] FOUND [KEY]: " + str(result['model_name']))
									print("[Residential][LOG] Is Active: " + str(status))
								found        = True
								idOfInterest = field

							if(str(result['model_name']) == str(knownOpmode[int(opmode)])):
							# Collect info about the mode of interest
								if(enablePrints == True):			
									print("[Residential][LOG] FOUND [KEY]: " + str(result['model_name']))
									print("[Residential][LOG] Collecting its config: " + str(status))
								foundSettings    = True
								resultOfInterest = temporary['config']
								idtoStart = field			

						if (found == False):
							# PROFESS Not Active 
							if(enablePrints == True):			
								print("[Residential][LOG] Get PROFESS Status Parsing returned no active options")
							# It means that we can start a new option (without stopping the previous one)
							opmode = DEFAULT_OPMODE
						else:						
							# PROFESS Already Active:
							# Exploit current status details (idOfInterest)
							# Exploit status details to activate (idtoStart + params)
							# Send the stop command -> idOfInterest
							# Then Send the start command (idtoStart + params)
							try:
								# Trigger a new PROFESS start
								response = requests.put(url = str(URL_PROFESS_STOP) + str(idOfInterest), headers = HEADERS)
							except Exception as e:
								print("[Residential][LOG] PROFESS Did not accept STOP! [" + str(idOfInterest) + "] Error: %s" %e)
								return ("[Residential][LOG] PROFESS Did not accept STOP! Error: %s" %e)

					except Exception as e:
						print("[Residential][LOG] Retrieval of current PROFESS Status Failed: %s (PROFESS Not Active)" %e)
						return ("[Residential][LOG] Retrieval of current PROFESS Status Failed: %s (PROFESS Not Active)" %e)

					if(foundSettings == False and str(knownOpmode[int(opmode)]) != "None"):
						print("[Residential][LOG] Set PROFESS Status Failed: opmode not found: " + str(knownOpmode[int(opmode)]))
						return ("[Residential][LOG] Set PROFESS Status Failed: opmode not found: " + str(knownOpmode[int(opmode)]))
					elif(foundSettings == False and str(knownOpmode[int(opmode)]) == "None"):
						if(enablePrints == True):
							print("[Residential][LOG] Set PROFESS Status to: " + str(knownOpmode[int(opmode)]))
						return int(opmode)

					# if response is not empty
					if not result or len(result) == 0:
						if(enablePrints == True):
							print("[Residential][LOG][PROFESS] Returned Empty message")
					else:
						if(enablePrints == True):
							print("[Residential][LOG][PROFESS] Returned message, start parsing")

						# We could have received a message containing an old Operation mode that
						# we want to change 
						# Exploit the model_name
						try:
							professStartMsg['control_frequency'] = resultOfInterest['control_frequency']
							professStartMsg['horizon_in_steps']  = resultOfInterest['horizon_in_steps']
							professStartMsg['dT_in_seconds']     = resultOfInterest['dT_in_seconds']
							professStartMsg['model_name']        = resultOfInterest['model_name']
							professStartMsg['optimization_type'] = resultOfInterest['optimization_type']
							professStartMsg['repetition']        = resultOfInterest['repetition']
							professStartMsg['single_ev']         = resultOfInterest['single_ev']
							professStartMsg['solver']            = resultOfInterest['solver']
						except Exception as e:
							if(enablePrints == True):
								print("[Residential][LOG] PROFESS Returned partial message! Error: %s" %e)
							return ("[Residential][LOG] PROFESS Returned partial message! Error: %s" %e)

						if(enablePrints == True):
							print("[Residential][LOG] PREVIOUS PROFESS(OPMODE): " + str(professStartMsg['model_name']))

						# Translate the received message in the known Operation modes:
						# professStartMsg['model_name'] (OLD OPERATION MODE)
						# Update model value
						professStartMsg['model_name'] = str(knownOpmode[key])

						if(enablePrints == True):
							print("[Residential][LOG] PROFESS(OPMODE) TO SET: " + str(professStartMsg['model_name']))

						try:
							# Trigger a new PROFESS start
							response = requests.put(url = str(URL_PROFESS_START) + str(idtoStart), data = json.dumps(professStartMsg), headers = HEADERS)
						except Exception as e:
							print("[Residential][LOG] PROFESS Did not accept START! Error: %s" %e)
							return ("[Residential][LOG] PROFESS Did not accept START! Error: %s" %e)

					# # # # # # # # # # # # # # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # #
				else:
					if(enablePrints == True):
						print("[Residential][LOG][SET] Operation Mode: " + str(key) + " FAILED! [Not Allowed Value]")
					return "[Residential][LOG][SET] Operation Mode: " + str(key) + " FAILED! [Not Allowed Value]"


				if(enablePrints == True):
					print("[Residential][LOG][SET] Operation Mode: " + str(knownOpmode[key]))

				# Proper Value Returns
				return int(key)
			else:
				if(enablePrints == True):
					print("[Residential][LOG][SET] Operation Mode Given is not a permitted value! [" + str(key) + "]")
				return ("[Residential][LOG][SET] Operation Mode Given is not a permitted value! [" + str(key) + "]")
		else:
			if(enablePrints == True):
				print("[Residential][LOG][SET] Operation Mode Not Given! Empty body or Not Allowed Values")
			return "[Residential][LOG][SET] Operation Mode Not Given! Empty body or Not Allowed Values"

	except Exception as e:
		print("[Residential][LOG] Value generating exception: " + str(key))
		print("[Residential][LOG][SET]: %s" %e)
		return str("[Residential][LOG]Exception! Wrong message! Set %s" %e)
	
# ------------------------------------------------------------------------------------ #
# ESS RELATED:
# ------------------------------------------------------------------------------------ #
### Retrieve Number of battery cycles:  Battery/cycles
### Constantly Updated (overall Number of battery cycles) by [EvaluateCyclesThread]
### Persistently stored on a TXT file (for easy management and demo purposes)
# ------------------------------------------------------------------------------------ #
def get_cycles(handler):
	global cycles

	if(enablePrints == True):
		print("[Residential][LOG][GET] Overall Cycles")
		print("[Residential][LOG] Current cycles: " + str(cycles))

	return int(cycles)


# ------------------------------------------------------------------------------------ #
# If the current flag is not enabled we cannot get any information about ESS!
if(enableCycleEvaluation == True):
	def get_status(handler):
		global state
		if(enablePrints == True):
			print("[Residential][LOG][GET] Battery")
			print("[Residential][LOG] Current Status: " + str(ess_status))
			print("[Residential][LOG] Estimated Status: " + str(state))

		statusResponse = {"FroniusStatus":str(ess_status),"EstimatedStatus":str(state)}

		return statusResponse
else:
	def get_status(handler):
		return str("Endpoint Disabled! Verify Backend flags!")
# ------------------------------------------------------------------------------------ #


# ------------------------------------------------------------------------------------ #
# EV RELATED: 
# Following APIs will generate new requests towards the EVconnector system.
# By doing that, we will retrieve the Charging Unit Data of Interest.
# ------------------------------------------------------------------------------------ #
# By relying on the following API, during the DEMO setup, it will be required to select
# the proper EV stream by setting up the CU-ID
# ------------------------------------------------------------------------------------ #
EV_selected = ""
EV_idList   = []
EV_session  = "0"
# ------------------------------------------------------------------------------------ #
# Set the EV Target of interets! (To be exploited later on)
def set_EVofInterest(handler):
	global EV_selected
	words = handler.path

	if(enablePrints == True):
		print("[Residential][LOG] set_EVofInterest (starts)")

	if(enableTimingEval == True):
		start = datetime.utcnow()

	destinationEV = words.split("/")[3]

	if(destinationEV in EV_idList):
		EV_selected = destinationEV
	else:
		print("Selected destination is not managed by the current Backend: " + str(destinationEV))
		return str("Selected destination is not managed by the current Backend!")

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] set_EVofInterest API last: " + str(end - start))

	return str("EV Properly Set: " + str(destinationEV))
# ------------------------------------------------------------------------------------ #
# Get the EV selected Status from Fronius! 
def get_EVstatus(handler):
	global EV_session
	print("Did you update the EVconnector to the last version ?!?")

	if(enablePrints == True):
		print("[Residential][LOG][GET] EV status")

	if(enableTimingEval == True):
		start = datetime.utcnow()

	# FixedValue = words.split("/")[1] == "/EV/"
	# destinationEV = words.split("/")[2] == "/status/"

	service_path = evconnector_url + "/S4G/status/last"

	responseData = {"rechargeState":"","meterState":"","code":""}

	# Exploit the EVconnector Endopoints to retrieve the current status 
	# about the selected EV
	# (EV_selected)
	try:
		response = requests.get(str(service_path),verify=False)

		if(response.status_code != 200):
			responseData['code'] = "EV server Error: " + str(response.status_code) 
			return responseData

	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] EV status API (Error) " + service_path)
		responseData['code'] = "EV server unreachable"
		return responseData

	# TODO: for demonstrative purposes it is required to parse the last values of the available sessions
	# Parse here response and extract the proper status value:
	# and store the current session ID if present
	responseData['rechargeState'] = response['Status'][0]['rechargeState']
	responseData['meterState']    = response['Status'][0]['meterState']
	responseData['code']          = "OK"

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] get_EVstatus API last: " + str(end - start))

	return responseData


# ------------------------------------------------------------------------------------ #
# Get the EV selected SoC and remaining time from Fronius! 
def get_EVdata(handler):
	if(enablePrints == True):
		print("[Residential][LOG][GET] EV Data")

	EVsession = 0
	EVtime    = 0

	if(enableTimingEval == True):
		start = datetime.utcnow()
	# ------------------------------------------------------------------------ #
	# FixedValue = words.split("/")[1] == "/EV/"
	# destinationEV = words.split("/")[2] == "/SOC/"
	# ------------------------------------------------------------------------ #
	# Approaches to select the proper SoC:
	# Option1: request the activeSoCs and verify if the current EV-CU-ID
	# is present in one of the idChain of the present sessions
	# Option2: request the activeSessions and verify if the current EV-CU-ID
	# is present in one of the sessionID of the showed sessions
	# Then, extract the sessionID and request more details about it
	# ------------------------------------------------------------------------ #
	# service_path = evconnector_url + "/S4G/activesocs/show"
	service_path = evconnector_url + "/S4G/active/sessions"

	# responseData = {"Charging":"False","Connected":"False","SoC":0,"remainingTime":0}
	responseData = {"Charging":"False","SoC":0,"remainingTime":0}
	# ------------------------------------------------------------------------ #
	# Exploit the EVconnector Endopoints to retrieve the current SoC 
	# about the selected EV
	# Exploit the EVconnector Endopoints to retrieve the remaining time exposed 
	# about the selected EV
	# (EV_selected)
	# ------------------------------------------------------------------------ #
	try:
		response = requests.get(str(service_path),verify=False)

		if(response.status_code != 200):
			return "[Residential] EV server Not reachable"

		result = response.json()['activeSession']
		
		if(len(result)<1):
			return responseData
		
		for socValues in result:
			if(socValues['cuCode'] == EV_selected):
				# --------------------------------------------------- #
				# The current CU is providing energy now! (active)
				# Extract the sessionID & remaining Time:
				# --------------------------------------------------- #
				EVsession = socValues['sessionID']
				EVtime    = socValues['millsToRecEnd']
				# --------------------------------------------------- #
				# EVtime is a UTC-timestamp,
				# we are going to compare it to the current timestamp
				# returning the amount of missing seconds to fullfill
				# the recharging session requirement (100%)
				# --------------------------------------------------- #
				now = datetime.utcnow().timestamp()         # Seconds
				amountSeconds = int(int(int(EVtime)/1000) - int(now))
				# --------------------------------------------------- #
				# responseData['Connected']     = "True"
				responseData['Charging']      = "True"
				responseData['remainingTime'] = int(amountSeconds)
				break
		
		if(EVsession == 0):
			return responseData

		# https://10.8.0.50:8082/S4G/socs/<sessionID>
		service_path = evconnector_url + "/S4G/socs/" + str(EVsession)

		response = requests.get(str(service_path),verify=False)

		if(response.status_code != 200):
			return "[Residential] EV server Not reachable"

		result = response.json()['SoC'][0]

		# This should never happen:
		# This means misalignment of data structures!
		if(len(result)<1):
			return responseData
		
		responseData['SoC'] = round(result['soc'],3)

	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] EV data API (Error) " + service_path)
		return "[Residential] EV data Not reachable/available"

	# Parse here response and extract the proper SoC value:
	# exploiting the current session ID (if present)
	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] get_EVdata API last: " + str(end - start))


	return responseData
# ------------------------------------------------------------------------------------ #
# DEPRECATED
# Get the EV selected SoC from Fronius! 
def get_EVsoc(handler):
	if(enablePrints == True):
		print("[Residential][LOG][GET] EV SoC")

	if(enableTimingEval == True):
		start = datetime.utcnow()
	# ------------------------------------------------------------------------ #
	# FixedValue = words.split("/")[1] == "/EV/"
	# destinationEV = words.split("/")[2] == "/SOC/"
	# ------------------------------------------------------------------------ #
	# Approaches to select the proper SoC:
	# Option1: request the activeSoCs and verify if the current EV-CU-ID
	# is present in one of the idChain of the present sessions
	# Option2: request the activeSessions and verify if the current EV-CU-ID
	# is present in one of the sessionID of the showed sessions
	# Then, extract the sessionID and request more details about it
	# ------------------------------------------------------------------------ #

	service_path = evconnector_url + "/S4G/socs/"

	# Exploit the EVconnector Endopoints to retrieve the current SoC 
	# about the selected EV
	# (EV_selected)
	try:
		response = requests.get(str(service_path),verify=False)

		if(response.status_code != 200):
			return "[Residential] EV server Not reachable"

	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] EV SoC API (Error) " + service_path)
		return "[Residential] EV SoC Not reachable/available"

	# Parse here response and extract the proper SoC value:
	# exploiting the current session ID (if present)

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] get_EVsoc API last: " + str(end - start))


	return str("STILL TO BE FINALIZED")
# ------------------------------------------------------------------------------------ #
# DEPRECATED
# Get the EV remaining recharging time from Fronius! 
def get_EVremaining(handler):
	if(enablePrints == True):
		print("[Residential][LOG][GET] EV remaining time")

	if(enableTimingEval == True):
		start = datetime.utcnow()

	# FixedValue = words.split("/")[1] == "/EV/"
	# destinationEV = words.split("/")[2] == "/remaining/"
        # https://10.8.0.50:8082/S4G/session/653082
	service_path = evconnector_url + "/S4G/"

	# Exploit the EVconnector Endopoints to retrieve the remaining time exposed 
	# about the selected EV
	# (EV_selected)
	try:
		response = requests.get(str(service_path),verify=False)

		if(response.status_code != 200):
			return "[Residential] EV server Not reachable"

	except Exception as e:
		print("Exception: %s" %e)
		if(enablePrints == True):
			print("[Residential][LOG] EV remaining time API (Error) " + service_path)
		return "[Residential] EV remaining time Not reachable/available"

	if(enableTimingEval == True):
		end = datetime.utcnow()
		print("[Residential][LOG] get_EVremaining API last: " + str(end - start))


	return str("STILL TO BE FINALIZED")
# ------------------------------------------------------------------------------------ #




# ------------------------------------------------------------------------------------ #
# 				HTTP REST SERVER
# ------------------------------------------------------------------------------------ #
# MULTI-THREAD IMPLEMENTATION:
class ThreadingHTTPServer(socketserver.ThreadingMixIn, BaseHTTPServer):
    pass

class RESTRequestHandler(http.server.BaseHTTPRequestHandler):
	def __init__(self, *args, **kwargs):
		self.routes = {
# --------------------------------------------------------- #
### Generic hisorical Energy Data (One Fields)
#   ENERGY/{fromDate}/{toDate}/{measurement}
#   ENERGY/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015
#   LOCALENERGY/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015
#   DEFAULT=GROUPBY/30
#   or
#   ENERGY/{fromDate}/{toDate}/{FroniusMeasurement}/{FieldOfInterest}
#   ENERGY/2018-12-24/2018-12-25/InstallationHouse20/photovoltaic
# --------------------------------------------------------- #
		r'^/(ENERGY|LOCALENERGY)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+(/(photovoltaic|grid|load|battery|SoC))?$': {'GET': get_energy, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Generic Hystoricla Raw Data (All Fields):  
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/
#   DEFAULT=GROUPBY/30
#   INFLUXDB/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015
# --------------------------------------------------------- #
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+$': {'GET': get_historical_rawdata, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Generic hisorical Raw Data (One Fields) (plus operations such as: GROUPBY) 
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/{field}/{OPERATION}/{VALUE}
#   INFLUXDB/2018-12-24/2018-12-25/InstallationHouseBolzano/load/GROUPBY/30
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/(P|Processed_P|photovoltaic|grid|load|battery|SoC)/GROUPBY/[0-9]+$': {'GET': get_historical_specific_data, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Dedicated API to evaluate direct consumption [consumption_for_energy]: if(P_Grid < 0) then (-P_Load)  
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/{field}/{OPERATION}/{VALUE}
#   INFLUXDB/2018-12-24/2018-12-25/InstallationHouseBolzano/direct_consumption/GROUPBY/30
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/direct_consumption/GROUPBY/[0-9]+$': {'GET': get_consumption_direct, 'media_type': 'application/json'},
### Dedicated API to evaluate direct consumption [consumption_for_energy]: if(P_Grid < 0) then (-P_Load)  
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/{field}/{OPERATION}/{VALUE}
#   INFLUXDB/2018-12-24/2018-12-25/InstallationHouseBolzano/direct_consumption/GROUPBY/30
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/direct_consumption_v2/GROUPBY/[0-9]+$': {'GET': get_consumption_direct_v2, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Generic hisorical Raw Data (All Fields) (plus operations such as: GROUPBY) 
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/{OPERATION}/{VALUE}
#   INFLUXDB/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015/GROUPBY/30
# --------------------------------------------------------- #
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/GROUPBY/[0-9]+$': {'GET': get_historical_data, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Retrieve Number of battery cycles (from remote Fronius stream):  Battery/cycles
# --------------------------------------------------------- #
		r'^/Battery/cycles$': {'GET': get_cycles, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Retrieve battery Status (from remote Fronius stream):  Battery/status
# --------------------------------------------------------- #
		r'^/Battery/status$': {'GET': get_status, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Generic Filtered Energy Data
#  ENERGY/{fromDate}/{toDate}/{measurement}/{Field}/{FILTER}/{OPERATION}/{VALUE}
#  ENERGY/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015/P/POSITIVE/GROUPBY/30
#  ENERGY/2019-03-25/2019-03-27/InstallationHouse20/battery/POSITIVE/GROUPBY/30
# --------------------------------------------------------- #
		r'^/(ENERGY|LOCALENERGY)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/(P|Processed_P|photovoltaic|grid|load|battery|SoC)/(POSITIVE|NEGATIVE|ALL)/GROUPBY/[0-9]+$': {'GET': get_filtered_area, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Generic Data (FILTERED)(plus operations such as: GROUPBY) 
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/{FieldOfInterest}/{FILTER}/{OPERATION}/{VALUE}
#   INFLUXDB/2018-12-24/2018-12-25/S4G-GW-EDYNA-0015/P/POSITIVE/GROUPBY/30
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/battery/POSITIVE/GROUPBY/30
# --------------------------------------------------------- #
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/(P|Processed_P|photovoltaic|grid|load|battery|SoC)/(POSITIVE|NEGATIVE|ALL)/GROUPBY/[0-9]+$': {'GET': get_filtered_data, 'media_type': 'application/json'},
# --------------------------------------------------------- #
# API for an improved plot visualization
# --------------------------------------------------------- #
# get_historical_month_data
#  INFLUXDB/MONTH/{Date}/{measurement}/{Field}/{FILTER}
#  INFLUXDB/MONTH/2019-03/InstallationHouseBolzano/load/ALL
		r'^/(INFLUXDB|LOCALINFLUXDB)/MONTH/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])/[A-Za-z0-9\-]+/(P|Processed_P|photovoltaic|grid|load|battery|SoC|direct_consumption)/(POSITIVE|NEGATIVE|ALL)$': {'GET': get_historical_month_data, 'media_type': 'application/json'},
# --------------------------------------------------------- #
# get_historical_year_data
#  INFLUXDB/YEAR/{Date}/{measurement}/{Field}/{FILTER}
#  INFLUXDB/YEAR/2019/InstallationHouseBolzano/load/ALL
		r'^/(INFLUXDB|LOCALINFLUXDB)/YEAR/20[0-9][0-9]/[A-Za-z0-9\-]+/(P|Processed_P|photovoltaic|grid|load|battery|SoC|direct_consumption)/(POSITIVE|NEGATIVE|ALL)$': {'GET': get_historical_year_data, 'media_type': 'application/json'},
# --------------------------------------------------------- #
# Other APIs:
# --------------------------------------------------------- #
### power_from_grid [aka: consumption_house]
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/consumption_house/{OPERATION}/{VALUE}
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/consumption_house/GROUPBY/30
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/consumption_house/(GROUPBY/[0-9]+)$': {'GET': get_consumption_house, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### over_production:
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/over_production/{OPERATION}/{VALUE}
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/over_production/GROUPBY/30
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/over_production/(GROUPBY/[0-9]+)$': {'GET': get_over_production, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### power2battery [aka: consumption_battery]:
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/power2battery/{OPERATION}/{VALUE}
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/power2battery/GROUPBY/30
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/power2battery/(GROUPBY/[0-9]+)$': {'GET': get_power2battery, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### evaluate_production:
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/evaluate_production/{OPERATION}/{VALUE}
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/evaluate_production/GROUPBY/30
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/evaluate_production/(GROUPBY/[0-9]+)$': {'GET': evaluate_production, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### evaluate_total_production:
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/evaluate_total_production/{OPERATION}/{VALUE}
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/evaluate_total_production/GROUPBY/30
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/evaluate_total_production/(GROUPBY/[0-9]+)$': {'GET': evaluate_total_production, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### evaluate_direct_consumption:
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/evaluate_direct_consumption/{OPERATION}/{VALUE}
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/evaluate_direct_consumption/GROUPBY/30
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/evaluate_direct_consumption/(GROUPBY/[0-9]+)$': {'GET': evaluate_direct_consumption, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### evaluate_power2grid:
#   INFLUXDB/{fromDate}/{toDate}/{measurement}/evaluate_power2grid/{OPERATION}/{VALUE}
#   INFLUXDB/2019-03-25/2019-03-27/InstallationHouseBolzano/evaluate_power2grid/GROUPBY/30
		r'^/(INFLUXDB|LOCALINFLUXDB)/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/20[0-9][0-9](\.|-)(0[1-9]|1[0-2])(\.|-)(0[1-9]|1[0-9]|2[0-9]|3[0-1])/[A-Za-z0-9\-]+/evaluate_power2grid/(GROUPBY/[0-9]+)$': {'GET': evaluate_power2grid, 'media_type': 'application/json'},
# --------------------------------------------------------- #
# --------------------------------------------------------- #
# EV Related Endpoints:
# --------------------------------------------------------- #
### Set The EV target of interest (relying on eCar system):  
# Temporary! For demonstrative purposes only!
# EV/SET/<ID>
# --------------------------------------------------------- #
		r'^/EV/SET/[A-Z0-9\_]+$': {'GET': set_EVofInterest, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Retrieve last status of EV (from remote eCar system):  
# EV/status
# Requires EV update first!
# --------------------------------------------------------- #
#		r'^/EV/status$': {'GET': get_EVstatus, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Retrieve current EV SoC (from remote eCar system):  
# EV/SOC
# --------------------------------------------------------- #
		r'^/EV/data$': {'GET': get_EVdata, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Retrieve current EV SoC (from remote eCar system):  
# EV/SOC
# --------------------------------------------------------- #
#		r'^/EV/SOC$': {'GET': get_EVsoc, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Retrieve time lasts to Full EV SoC (from remote eCar system):  
# EV/remaining
# --------------------------------------------------------- #
		#r'^/EV/remaining$': {'GET': get_EVremaining, 'media_type': 'application/json'},
# --------------------------------------------------------- #
### Get or Set Operational Mode:
# --------------------------------------------------------- #
		r'^/OPMODE$': {'GET': get_opmode, 'POST': set_opmode, 'media_type': 'application/json', 'Access-Control-Allow-Origin': '*'}}
# --------------------------------------------------------- #
		return http.server.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

	def do_HEAD(self):
		self.handle_method('HEAD')
    
	def do_GET(self):
		self.handle_method('GET')

	def do_POST(self):
		self.handle_method('POST')

	def do_PUT(self):
		self.handle_method('PUT')

	def do_DELETE(self):
		self.handle_method('DELETE')
    
	def get_payload(self):
		payload_len = int(self.headers['Content-Length'])

		if(enablePrints == True):
			print("[Residential][HTTP][LOG] Payload: Len = " + str(payload_len))

		if(payload_len >= 1):	
			payload = self.rfile.read(payload_len).decode('UTF-8')
			if(str(payload).isdigit() == False):
				if(enablePrints == True):
					print("[Residential][HTTP][LOG] Payload not a digit: " + str(payload))

				return payload
			else:
				payload = json.loads(payload)
				if(enablePrints == True):
					print("[Residential][HTTP][LOG] Extracted Payload: Content={ " + str(payload)+" }")

				return payload
		else:
			if(enablePrints == True):
				print("[Residential][HTTP][LOG] Empty Payload: Len = [" + str(payload_len) + "]")

			return None

        # HTTP Response Method:
	def handle_method(self, method):		
		if(enableHTTPPrints == True):
			print("[Residential][HTTP][LOG] handle_method START")

		route = self.get_route()
		if route is None:
			if(enableHTTPPrints == True):
				print("[Residential][HTTP][LOG] route None")
			self.send_response(404)
			self.end_headers()
			# The following case should be very fast
			# That's why should not be required a dedicated try catch
			# to manage clients that disconnects before receiving responses
			self.wfile.write('Route not found\n'.encode('UTF-8'))
		else:
			if(enableHTTPPrints == True):
				print("[Residential][HTTP][LOG] route: " + str(route))
			if method == 'HEAD':
				self.send_response(200)
				if 'media_type' in route:
					self.send_header('Content-type', route['media_type'])
				# 2019-04-15
				# if 'Access-Control-Allow-Origin' in route:
				# RESTORED @ 2019-07-17
				self.send_header('Access-Control-Allow-Origin', route['Access-Control-Allow-Origin'])

				self.end_headers()
			else:
				if 'file' in route:
					if(enableHTTPPrints == True):
						print("[Residential][HTTP][LOG] File Request!")

					if method == 'GET':
						if(enableHTTPPrints == True):
							print("[Residential][HTTP][LOG] GET Request Recognized!")
						try:
							f = open(os.path.join(here, route['file']), 'rb')
							if(enableHTTPPrints == True):
								print("[Residential][HTTP][LOG] File opened!")
							try:
								self.send_response(200)
								if(enableHTTPPrints == True):
									print("[Residential][HTTP][LOG] Response sent!")
								# 2019-04-15								
								# RESTORED @ 2019-07-17
								self.send_header('Access-Control-Allow-Origin', '*')

								if 'media_type' in route:
									self.send_header('Content-type', route['media_type'])
								self.end_headers()
								if(enableHTTPPrints == True):
									print("[Residential][HTTP][LOG] Headers closed!")
								shutil.copyfileobj(f, self.wfile)
								if(enableHTTPPrints == True):
									print("[Residential][HTTP][LOG] File object copy ended!")
							finally:
								# The following case should be very fast
								# That's why should not be required a dedicated try catch
								# to manage clients that disconnects before receiving responses
								f.close()
						except Exception as e:
							if(enableHTTPPrints == True):
								print("[Residential][HTTP][LOG] Raised Exception! (Missing file?) %s " %e)
							self.send_response(404)
							self.end_headers()
							self.wfile.write('File not found\n'.encode('UTF-8'))
					else:
						if(enableHTTPPrints == True):
							print("[Residential][HTTP][LOG] NoN-GET Request Recognized!")
						self.send_response(405)
						self.end_headers()
						# The following case should be very fast
						# That's why should not be required a dedicated try catch
						# to manage clients that disconnects before receiving responses
						self.wfile.write('Only GET is supported\n'.encode('UTF-8'))
				else:
					if(enableHTTPPrints == True):
						# print("[LOG] Method Request! " + str(route))
						print("[Residential][HTTP][LOG] Method Request: " + str(method))
					try:
						if method in route:
							if(enableHTTPPrints == True):
								print("[Residential][HTTP][LOG] Method Request in routes!")
							content = route[method](self)
							if content is not None:
								if(enableHTTPPrints == True):
									print("[Residential][HTTP][LOG] Method content not Null!")

								self.send_response(200)
								if 'media_type' in route:
									self.send_header('Content-type', route['media_type'])

								# 2019-04-15
								# if 'Access-Control-Allow-Origin' in route:
								# RESTORED @ 2019-07-17
								self.send_header('Access-Control-Allow-Origin', '*')

								self.end_headers()
								if method != 'DELETE':
		                        				self.wfile.write(json.dumps(content).encode('UTF-8'))
							else:
					                    self.send_response(404)
					                    self.end_headers()
		                			    self.wfile.write('Not found\n'.encode('UTF-8'))
						else:
							if(enableHTTPPrints == True):
								print("[Residential][HTTP][LOG] Method Request NOT in routes!")

							self.send_response(405)
							self.end_headers()
							self.wfile.write(str(method).encode('UTF-8') + " method is not supported\n".encode('UTF-8'))
					except Exception as e:
						print("[Residential][HTTP][LOG] Raised Exception! (Client disconnected badly): %s" %e)
                    
# ------------------------------------------------------------------------------------ #    
# Find out which APIs to dispatch
	def get_route(self):
		for path, route in list(self.routes.items()):
			if re.match(path, self.path):
				return route
		return None

# Start REST server 
# ------------------------------------------------------------------------------------ #
def rest_server(server_class=ThreadingHTTPServer, handler_class=RESTRequestHandler):
	'Starts the REST server'
	# Here we COULD respond only to the private-IPv4.
	# Note that, this device is reachable only from the LAN and from the VPN.
	# Consequently, this approach is not required here.
	cyclesThreadActive = False

	ip   = '0.0.0.0'
	port = 18081

	# Multi-threaded
	http_server = server_class((ip, port),handler_class)

	# Single-threaded
	# http_server = http.server.HTTPServer((ip, port), RESTRequestHandler)

	print(('[Residential-Backend] Starting MT HTTP server at %s:%d' % (ip, port)))

	# ------------------------------------------ #
	if(enableCycleEvaluation == True):
		cyclesThreadActive = True	
		cyclesthread = EvaluateCyclesThread()
		cyclesthread.start() 
	# ------------------------------------------ #
	try:
        	http_server.serve_forever()
	except KeyboardInterrupt:
		pass
	print('[Residential-Backend] Stopping HTTP server')
	http_server.server_close()
	# ------------------------------------------ #
	if(cyclesThreadActive == True):
		print("[Residential-Backend][END] Ending Parallel Thread")
		cyclesthread.kill_received = True
		cyclesthread.join(5.0)
	# ------------------------------------------ #


######################################################################################################################################
persistent_file = "cyclesEvaluated.conf"
state = ""
# Following flag will be used to understand if Charging/Discharging 
# (Because the Fronius ESS-status field could contains also EMPTY while it start charging)
class EvaluateCyclesThread(threading.Thread):
	# ---------------------------------------------------------------------------------------------------------- #
	def __init__(self):
		global cycles
		global state
		super(EvaluateCyclesThread, self).__init__()
		# ---------------------------------------------------------- #
		# The value must be persistent! 
		# Otherwise a system restart will erase the current value 
		# and will restart from zero.
		# ---------------------------------------------------------- #
		state   = "idle"           # Allowed values:{charging,discharging,idle}
		# ---------------------------------------------------------- #
		# Restore value from file/DB
		# If does not exists it means that it is the first run!
		try:
			pers = configparser.ConfigParser()
			pers.read(str(here)+"/"+str(persistent_file))
			pers.sections()	
			cycles = int(pers['DEFAULT']['CYCLES'])
		except Exception as e:
			print("[PERSISTENT FILE NOT FOUND] First Run!? %s" %e)
			persistent = configparser.ConfigParser()
			persistent['DEFAULT'] = {'CYCLES': str(cycles)}
			with open(str(here)+"/"+persistent_file, 'w') as myfile:
				persistent.write(myfile)
			print("[PERSISTENT FILE] Just Created!")

		if(enablePrints == True):
			print("[EvaluateCyclesThread] INIT on: " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))
			print("[EvaluateCyclesThread] Restored Value: " + str(cycles))
		# ---------------------------------------------------------- #
		
		self.kill_received = False
		# ---------------------------------------------------------- #

	def run(self):
		global enablePrints
		global cycles
		global state
		global N_THRESHOLD
		global P_THRESHOLD
		# ---------------------------------------------------------- #
		# The idle status of the battery it is not exactly zero!
		# To avoid misunderstandings wihtin the procedure will be exploited
		# a Positive and Negative threshold of 50 Watt
		# ---------------------------------------------------------- #
		highThreshold = P_THRESHOLD 
		lowThreshold  = N_THRESHOLD   
		statecounter = 0
		incFlag      = 0
		newCycleFlag = 0
		# ---------------------------------------------------------- #
		if(enablePrints == True):
			print("[EvaluateCyclesThread] RUN: (" +str(cycles)+ ")")
		# ---------------------------------------------------------- #
		# Wait for extracted Battery Power values from MQTT stream
		# Evaluate if the received value is inline with the previous one
		# Otherwise increment the number of cycles!
		# ---------------------------------------------------------- #
		while(True):
			if(self.kill_received == True):
				print("[EvaluateCyclesThread] Kill Received")
				time.sleep(1)
				return

			if internal_queue.empty() == True:
				# No Messages found (we can afford to sleep a bit longer)
				time.sleep(0.5)
			else:
				# ---------------------------------------------------------------------------------- #
				# Extract from the queue the message from the OGC Wrapper Battery SMX Stream:
				avg = internal_queue.get()
				# ---------------------------------------------------------------------------------- #
				internal_queue.task_done()
				# ---------------------------------------------------------------------------------- #
				if(enablePrints == True):
					print("[EvaluateCyclesThread] Message Received: (" + str(avg) + ")")

				# ---------------------------------------------------------------------------------- #
				# SIMPLEST APPROACH (rely on ESS-status)[Could also be: IDLE/EMPTY/FULL]:
				# ---------------------------------------------------------------------------------- #
				# if("CHARGING" and NEW_CYCLE==0):
				#  NEW_CYCLE   = 1
				#  PERFORM_INC = 1
				# elif("DISCHARGING" and NEW_CYCLE==1):
				#  NEW_CYCLE = 0
				#
				# if(NEW_CYCLE == 1 and PERFORM_INC == 1):
				#  CYCLE++
				#  PERFORM_INC = 0
				# ---------------------------------------------------------------------------------- #

				
				# ---------------------------------------------------------------------------------- #
				# COMPLEX APPROACH (rely on real ESS SOC value):
				# ---------------------------------------------------------------------------------- #
				if(lastAvg < currAvg):
					# To be sure, preventing fluctuations to force multiple cycles per charging
					# Control also the thresholds!
					if(avg > lowThreshold):
						# Means Charging
						state = "charging"
						if(newCycleFlag == 0):
							if(avg > highThreshold and incFlag == 0):
								incFlag      = 1
								newCycleFlag = 1
						else:
							incFlag = 0
					else:
						# Probably Charging but almost empty ESS
						state = "charging" 

				elif(lastAvg > currAvg):
					# To be sure, preventing fluctuations to force multiple cycles per charging
					# Control also the thresholds!
					if(avg < highThreshold):
						# Means DisCharging
						state = "discharging"
						# We reset the flag only when we are sure that we are discharging 
						# to avoid multiple battery cycles increments on the same cycle!
						newCycleFlag = 0
					else:
						# Probably DisCharging but almost FULL ESS
						state = "discharging" 
				else:
					# Not enough data to understand the current state
					continue


				# ---------------------------------------------------------------------------------- #
				# We need 2 flags because we need to prevent multiple increments over one single cycle
				if(incFlag == 1 and newCycleFlag == 1):			
					# One cycle more!
					cycles += 1
					# Write on File
					if(enablePrints == True):
						print("[EvaluateCyclesThread] Cycle Completed:["+str(cycles)+"]")

					persistent = configparser.ConfigParser()
					persistent['DEFAULT'] = {'CYCLES': str(cycles)}
					with open(str(here)+"/"+persistent_file, 'w') as myfile:
						persistent.write(myfile)


######################################################################################################################################
# ----------------------------------------------------------------------------------------------------------------------------- #
mqtt_local_sub    = mqtt.Client()
# Fixed values		
# BattField    = "Processed_P"
BattField    = "SOC"
internal_counter  = 0
ess_soc = 0
lastAvg = 0
currAvg = 0
ess_status = "STARTING"
# The following value must be properly dimensioned to avoid useless processing:
counter_threshold = 3
# ---------------------------------------------------------------------------------------------------------- #
# Example of message:
#
# RESIDENTIAL/GUI S4G-GW-EDYNA-0016
# Processed_I2=2.39,Processed_I1=2.45,U3=234.4,P2=575,Q1=0,P1=579,Processed_P2=-575.0,Am=2843011.3000000003,K3=-1.0,
# Processed_I3=2.38,U2=241.10000000000002,Processed_Q2=0.0,U1=237.70000000000002,Processed_P3=-557.0,
# Ap=2265735.4,P3=557,f=50.0,Q=0,Processed_P1=-579.0,Processed_Q3=0.0,I3=2.38,I1=2.45,K2=-1.0,P=1712,Q3=0,
# Rp=11756.6,K1=-1.0,Rm=7933.8,Processed_Q1=0.0,Processed_P=-1711.0,I2=2.39,Q2=0,Processed_Q=0.0,Type=3 1555660512000000000
#
# ---------------------------------------------------------------------------------------------------------- #
def on_local_message(mqtt_local_sub, obj, msg):
	global enablePrints
	global internal_queue
	global BattField
	global ess_soc
	global ess_status
	global internal_counter
	global lastAvg
	global currAvg
	

	payload = str(msg.payload)

	if(len(msg.payload) > 0):
		try:
			decodedMsg = msg.payload.decode('utf-8') 
			# ---------------------------------------------------------------------------------- #
			# Extract from the given Message the internal BattField and then the value of interest:
			# The field of interest is: SOC
			# ---------------------------------------------------------------------------------- #
			sensorID, extractedMsg, extractedTS = str(decodedMsg).split(" ")
			# ---------------------------------------------------------------------------------- #
			# Verify if the sensor is the one of interest
			# This value must be adapted in test sites
			# But, this code runs on the residential Aggregator / LINKSLab aggregator
			# Over there, we will intercept only one Fronius Flow!
			# Consequently, it is simpler to avoid the following control!
			# if(str(sensorID) == str(hostName)):
			# ---------------------------------------------------------------------------------- #
			if(enablePrints == True):
				print("[MQTT-LOCAL] Accepted Message from: " +str(sensorID))
			# ---------------------------------------------------------------------------------- #
			# Increment counter, we will do downsampling here to build meaningful averages.
			# It is useless to forward every packet 
			# (most of the time it will be recognized as IDLE state)
			# ---------------------------------------------------------------------------------- #
			if(internal_counter >= counter_threshold):
				if(enablePrints == True):
					print("[MQTT-LOCAL] Write inside queue")

				average = ess_soc/internal_counter
				# Reset counter
				internal_counter = 0
				# Reset SoC accumulator
				ess_soc = 0

				if(lastAvg == 0):
					lastAvg = average
					currAvg = average
				elif(lastAvg == currAvg):
					currAvg = average
				else:
					lastAvg = currAvg
					currAvg = average

				if(enablePrints == True):
					print("[MQTT-LOCAL] Average: "+ str(average))

				internal_queue.put(average)
			else:
				try:
					data = dict(s.split('=') for s in extractedMsg.split(','))
					ess_soc += float(data[str(BattField)])
					ess_status = data['ESS-status']
					ess_status = ess_status.replace('"','')
					internal_counter += 1
				except Exception as e:
					print("Exception: %s" %e)
					raise Exception("SOC PARSING Error!")
		except Exception as e:
			print("[MQTT-LOCAL][DATA] What: %s " %e)


def on_local_connect(mqtt_local_sub, userdata, flags, rc):
	mqtt_local_sub.subscribe(mqtt_fronius_topic)


def on_local_disconnect(client, userdata, rc):
	global enablePrints
	global mqtt_local_port
	global mqtt_local_broker
	global mqtt_local_sub

	time.sleep(10)
	if(enablePrints == True):
		print("[MQTT-LOCAL][DATA] Re-connecting to: " +str(mqtt_local_broker) + ":" + str(mqtt_local_port))

	try:
		mqtt_local_sub.connect(mqtt_local_broker, int(mqtt_local_port), 60)
	except Exception as e:
		print("[MQTT-LOCAL][DATA] Failure %s " %e)


def startLocalSubscriber():
	global enablePrints
	global mqtt_local_broker
	global mqtt_local_port
	global mqtt_local_sub
	try:
		if(enablePrints == True):       
			print("[MQTT-LOCAL][DATA] Building the LOCAL SUBSCRIBER (mqtt-client)")

		mqtt_local_sub.on_message    = on_local_message
		mqtt_local_sub.on_connect    = on_local_connect
		mqtt_local_sub.on_disconnect = on_local_disconnect
		if(enablePrints == True):
			print("[MQTT-LOCAL][DATA] Connecting to: " +str(mqtt_local_broker) + ":" + str(mqtt_local_port))

		mqtt_local_sub.connect(mqtt_local_broker, int(mqtt_local_port), 60)
		mqtt_local_sub.loop_start() 	

	except Exception as e:
		print("[MQTT-LOCAL][DATA] Stopped %s " %e)
		raise Exception('Failed to connect to the Local Broker')



# ----------------------------------------------------------------------------------------------------------------------------- #
def main(argv):
	global username
	global password
	global EV_selected
	global EV_idList

	print((sys.version_info))
	
	print("Storage4Grid EU Project: Implementation of Residential Backend on residential Aggregators")
	
	try:

		print("[Residential-Backend] Read AUTH configuration")
		print(str(here)+"/"+str(configFile))

		config = configparser.ConfigParser()
		config.read(str(here)+"/"+str(configFile))
		config.sections()

		username  = config['USER']['VALUE']
		password  = config['PASSWORD']['VALUE']

		EV_selected = config['EV_SELECTED']['VALUE']
		EV_tmp      = config['EV_LIST']['VALUE']
		EV_idList   = EV_tmp.split(",")
		print("[Residential-Backend] Starting MQTT subscriber")
		startLocalSubscriber()

		print("[Residential-Backend] Starting REST Server")
		rest_server()
	except Exception as e:
		print("[Residential-Backend][Failure] Stopped %s " %e)


if __name__ == '__main__':
	main(sys.argv[1:])

