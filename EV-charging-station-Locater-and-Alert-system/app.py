from flask import Flask, jsonify, render_template, request
import time
import serial.tools.list_ports
import serial
import json
import math
import requests
token = "pk.eyJ1IjoidmVub20taGlsbHMiLCJhIjoiY2t2MmJudG9pM3dwYTJuczdtYzFqNGFkZiJ9.D0rUWLRbQlUdhEB3Gt3B9Q"

ev_stations = [
{'s_name': 'Uznaka Charging Station', 'coordinates': [85.13662725450322,25.60046285586244] , 'level': [1], 'distance':0},
{'s_name': 'Goenka Electric Motor Vehicles Pvt.Ltd.', 'coordinates': [85.18566080755618, 25.59122664048361], 'level': [2], 'distance':0},
{'s_name': 'Hop Motors ( Green India Motors )', 'coordinates': [85.23682594261271, 25.592381229757887], 'level': [3], 'distance':0},
{'s_name': 'Electric Vehicle Charging Station', 'coordinates': [85.13015819065498, 25.621430955596193], 'level': [1], 'distance':0},
{'s_name': 'con motors Charging Station', 'coordinates': [ 84.4194720963607, 24.876724526039904], 'level': [3], 'distance':0}
]



ports = serial.tools.list_ports.comports()
portvar = "COM3"
serialInst = serial.Serial()
serialInst.baudrate = 9600
serialInst.port = portvar


app = Flask(__name__)

@app.route('/stuff', methods = ['GET'])
def stuff():
    return jsonify(result=battery_per())


@app.route('/' , methods=['POST', 'GET'])
def index():
    return render_template('battery.html')


@app.route('/map')
def map():
    longitude  = request.args.get('longitude',None)
    latitude = request.args.get('latitude', None)
    our_location = [longitude, latitude]
    near_station = nearest_station(ev_stations,our_location, 4)
    for i in near_station:
        dist_dur = request_call(i['coordinates'], our_location)
        i['distance'] = dist_dur['distance']
        i['duration'] = dist_dur['duration']
    return render_template('hover.html', longitude=longitude, latitude=latitude, json_data = json_dict(near_station))

def battery_per():
    percent = ""
    serialInst.open()
    while True:
        if serialInst.in_waiting:
            packet = serialInst.readline()
            percent = packet.decode('utf').rstrip('\n')
            break
    serialInst.close()
    return int(percent)

def cal_distance(ev_coordinate, our_location):
	R = 6373.0
	lat1 = math.radians(float(our_location[1]))
	lon1 = math.radians(float(our_location[0]))
	lat2 = math.radians(float(ev_coordinate[1]))
	lon2 = math.radians(float(ev_coordinate[0]))
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
	distance = R * c
	return distance

def nearest_station(ev_stations, our_location, num):
	near_stations =[]
	for i in ev_stations:
		i['distance'] = cal_distance(i['coordinates'],our_location)
	near_stations = sorted(ev_stations, key= lambda ev_stations: ev_stations['distance'])
	near_stations = near_stations[0:num]
	return near_stations

def request_call(ev_coordinate, our_location):
	request_string = "https://api.mapbox.com/directions/v5/mapbox/driving/" + str(our_location[0])+',' + str(our_location[1])+ ';'  + str(ev_coordinate[0]) + ','  + str(ev_coordinate[1]) +';' + "85.18483611369648, 25.589447332662957" + "?geometries=geojson&access_token=" + token 
	response = requests.get(request_string)
	res = response.json()['routes'][0]
	res = {'distance': res['distance'], 'duration': res['duration']}
	return res

def json_dict(near_stations):
	json_map_Stations = []
	for i in near_stations:
		temp = {'type': 'Feature'} 
		des = '<strong>' + i['s_name'] + '</strong><p>Duration: ' + str(int(i['duration']/60)) + " min<br>Distance: "+ str(int(i['distance']))+" m<br>Charger Level: "+ str(i['level'][0])+ "</p>"
		temp['properties'] = {'description': des}
		temp['geometry'] = {'type': 'Point', 'coordinates': i['coordinates']}
		json_map_Stations.append(temp)
	return json_map_Stations

if __name__=='__main__':
    app.run()
