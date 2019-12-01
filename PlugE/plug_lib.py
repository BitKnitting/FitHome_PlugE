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

#
# The Reading class is a superclass for


class DB:
    def __init__(self):
        pass

    def send(self):

        pass


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
    # Pass in the monitor name.  The monitor name is assigned to the FitHome
    # member's monitor when it is installed in their home.
    def __init__(self, appliance):
        self.appliance = appliance.lower()
        # The collecting variable is used to know the state...the start
        # method sets collecting to True.  The stop, to False.
        self.collecting = False
        self.interval = None

        self.plug = None
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
                    print('appliance {} match'.format(name))
                    self.plug = value
                    break

    ########################################################
    # start() collecting readings and putting the readings in
    # The Firebase RT.
    # Input:
    # - monitor_name: The name assigned to the monitor when the
    #   homeowner signed up for the FitHome experience.
    # - project_id: The Firebase project ID where the readings are
    #   written to.
    # - interval:  The time between sampling.
    #
    # RETURN:
    #  False if __init__ could not find a plug with an alias name that
    #  is the same as the appliance name.
    ########################################################

    def start(self, db, interval=2):
        if (self.plug is None):
            return False
        self.collect = True
        self.interval = interval
        self.db = db
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
        p, i = self._get_reading()
        if (p != None and i != None):
            self._send_reading(p, i)

    def _get_reading(self):
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

    def _send_reading(self, power, current):
        now = datetime.now()
        timestamp = datetime.timestamp(now)
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
