###############################################################
#
# The Plug class gets the smart plug that is on the wifi with
# the appliance name (passed in during init) and then sends
# it to the path to be stored (e.g.: within a mongodb or Firebase RT db)
# taking readings every interval seconds.
###############################################################
from pyHS100 import Discover, SmartPlug, SmartDeviceException
import requests
import time
import threading
import pymongo
from datetime import datetime
import json
from config import read_config

#
# The DB class is used as an abstract class so that different
# back ends can be used to store the data.


class DB:
    def __init__(self):
        pass

    def send(self):

        pass

#
# Store the readings into mongodb.  I'm using mongodb that's on the
# same rasp pi that is running this script.
#


class MongoDB(DB):
    # e.g. path: "mongodb://localhost:27017/"
    # e.g. db: "FitHome"
    # e.g. collection: "microwave"
    # MongoDB is pretty accepting, so double check the inputs!
    def __init__(self, path_str, db_str, collection_str):
        super().__init__()
        try:
            client = pymongo.MongoClient(path_str)
        except pymongo.errors.ConfigurationError as err:
            print('The path does not work.  It should be something like "mongodb://localhost:27017/".  The error is: {}'.format(err))
            return
        db = client[db_str]
        self.collection = db[collection_str]

    def send(self, data):
        json_data = json.loads(data)
        result = self.collection.insert_one(json_data)
        print(result.inserted_id)


class FirebaseDB(DB):
    # The path is set to the Firebase path...
    #   ts_str = str(int(time.time()))
    #     return 'https://' + self.project_id+'.firebaseio.com/' + \
    #         self.monitor_name+'/device_readings/'+plug_name+'/'+ts_str+'/.json'
    # Probably with9ut the ts_str - I'm updating the code, so right now focused on Mongodb.
    #

    pass


class Plug:
    # - appliance is the name of the appliance.  It should be something well known
    # like 'microwave'...it needs to match the alias name of the smart plug.
    # - db - previously set up via an instance of the DB class.
    # - interval:  The time between sampling.
    # - detect_on tells the code to detect during run time if the device is on or off

    def __init__(self, appliance, db, interval=1, detect_on=True):
        self.appliance = appliance.lower()
        # The collecting variable is used to know the state...the start
        # method sets collecting to True.  The stop, to False.
        self.collecting = False
        self.interval = interval
        self.db = db

        self.plug = None
        # These three variables are used for real time detection of a device
        # If detect_cycle is False, the device doesn't cycle. E.g.s of devices
        # that cycle include washing machines, refrigerators.  E.g.s of devices
        # that don't cycle include toasters, microwaves...
        # If the detect cycle is False, then real time detection occurs
        # if detect_low < P < detect_high -> device is on.
        self.detect_on = detect_on
        self.detect_cycle = False
        self.detect_low = 0
        self.detect_high = 0
        self.url = ''
        # Find the plug with the alias named 'appliance'
        try:
            # Get the dictionary of smart devices.
            # The key is the IP address of the device.
            a_dict = Discover.discover()
        except SmartDeviceException as err:
            print("Exception talking to the TP-LINK: ", err)
            return
        else:
            for key, value in a_dict.items():
                # Sometimes the name ends up with characters
                # We don't want in it...
                # Take out quotes and spaces from the name.
                name = a_dict[key].alias.strip('" ').lower()
                if (name == self.appliance):
                    self.plug = value
                    break
        if (detect_on):
            try:
                with open("device_thresholds.json", "r") as file:
                    thresholds = json.load(file)
                    self.url = read_config('url')
                    for k in thresholds:
                        if (k == self.appliance):
                            self.detect_low = thresholds[k]['low']
                            self.detect_high = thresholds[k]['high']
                            break
                if (self.detect_high == 0):
                    raise ValueError(
                        'Values for threshold detection are not available.')

            except FileNotFoundError as err:
                print(err)
                return

    ########################################################
    # start() collecting readings
    #
    # RETURN:
    #  False if __init__ could not find a plug with an alias name that
    #  is the same as the appliance name.
    ########################################################

    def start(self):
        if (self.plug is None):
            return False
        self.collect = True
        self._start_timer()
        return True

    def stop(self):
        self.collect = False
    ########################################################
    # Internal methods
    ########################################################

    def _start_timer(self):
        if (self.collect):
            # I saw this in a StackOverflow answer..which now I can't find...
            # start a timer for the interval amount then call the method
            # to collect and send a reading.  The timer goes off and
            # calls itself again.  Then I use the collect flag to stop
            # turning on the timer.
            threading.Timer(self.interval, self._start_timer).start()
            self._handle_reading()

    def _handle_reading(self):
        p, i = self.get_reading()
        if (p != None and i != None):
            self.send_reading(p, i)

    def get_reading(self):
        try:
            # Contact plug and get energy measurements.

            measurements = self.plug.get_emeter_realtime()
            p = measurements['power']
            i = measurements['current']
        except SmartDeviceException as err:
            print("Exception talking to the TP-LINK: ", err)
            return None, None
        else:
            return p, i

    def send_reading(self, power, current):
        now = datetime.now()
        timestamp = datetime.timestamp(now)
        # This is hoaky right now...focussed on micowave, since this is the device
        # I have observed.
        # The goal is to determine in real time is the device is on or off.
        # Then I can sync this with the aggregate readings as a column of 0 and 1's
        # e.g.: column name = 'microwave'.  rows are either 0 or 1.
        device_on = 0
        if (self.detect_on):
            print('power: {} low: {} high: {}'.format(
                power, self.detect_low, self.detect_high))
            if (self.detect_low < power < self.detect_high):
                device_on = 1
            else:
                device_on = 0
            print('device is: {}'.format(device_on))
            data = '{' + \
                ' "timestamp":{},"P":{},"I":{},"on":{}'.format(
                    timestamp, power, current, device_on) + '}'
            # if device_on, send Flask app microwave_on
            # if device_on = 0 send flask app microwave_off
            # hardcode for now to get this working then fix as more devices are added.
            payload = '{"device_on":' + str(device_on)+'}'
            headers = {'Content-Type': "application/json"}
            try:
                response = requests.request(
                    "POST", self.url, data=payload, headers=headers)
            except IndexError as e:
                print('error: {}'.format(e))
                return False
            print('response: {}'.format(response.text))
        else:
            data = '{' + \
                ' "timestamp":{},"P":{},"I":{}'.format(
                    timestamp, power, current) + '}'
        self.db.send(data)
        # try:
        #     response = requests.put(self.path, data=data)
        #     if (response.status_code == 400):
        #         print(response.text)
        #         return False

        # except IndexError as e:
        #     print('error: {}'.format(e))
        #     return False
        # else:
        #     return True

    # def _make_path(self, plug_name):
    #     # Get current timestamp
    #     ts_str = str(int(time.time()))
    #     return 'https://' + self.project_id+'.firebaseio.com/' + \
    #         self.monitor_name+'/device_readings/'+plug_name+'/'+ts_str+'/.json'
