from pyHS100 import Discover, SmartPlug, SmartDeviceException
import requests
import time
import threading


class Plugs:
    # Pass in the monitor name.  The monitor name is assigned to the FitHome
    # member's monitor when it is installed in their home.
    def __init__(self):
        self.monitor_name = ''
        self.project_id = ''
        self.plugs = []
        self.collecting = False
        self.interval = None
        # Finds plugs that can send energy readings.
        try:
            a_dict = Discover.discover()
        except SmartDeviceException as err:
            print("Exception talking to the TP-LINK: ", err)
            return
        else:
            for key in a_dict:
                # If the plug can send energy readings....
                if (a_dict[key].has_emeter):
                    self.plugs.append(a_dict)

    def _collect_reading(self):

        for plug in self.plugs:
            # plug is a dictionary where the key is the (string) ip addr of the
            # Smart device
            for key in plug:
                smart_plug = plug[key]
                p, i = self._get_reading(smart_plug)
                if (p != None and i != None):
                    print('power: {} current: {}'.format(p, i))
                    self._send_reading(p, i, smart_plug.alias)

    def _start_timer(self):
        if (self.collect):
            # I saw this in a StackOverflow answer..which now I can't find...
            # start a timer for the interval amount then call the method
            # to collect and send a reading.  The timer goes off and
            # calls itself again.  Then I use the collect flag to stop
            # turning on the timer.
            threading.Timer(self.interval, self._start_timer).start()
            self._collect_reading()

    def start(self, monitor_name, project_id, interval=2):
        self.collect = True
        self.monitor_name = monitor_name
        self.interval = interval
        self.project_id = project_id
        self._start_timer()

    def stop(self):
        self.collect = False

    def _get_reading(self, plug):
        try:
            # Contact plug and get energy measurements.

            measurements = plug.get_emeter_realtime()
            p = measurements['power']
            i = measurements['current']
        except SmartDeviceException as err:
            print("Exception talking to the TP-LINK: ", err)
            return None, None
        else:
            return p, i

    def _send_reading(self, power, current, plug_name):
        data = '{'+'"P":{},"I":{}'.format(power, current) + '}'
        path = self._make_path(plug_name)
        try:
            response = requests.put(path, data=data)
            if (response.status_code == 400):
                print(response.text)
                return False

        except IndexError as e:
            print('error: {}'.format(e))
            return False
        else:
            return True

    def _make_path(self, plug_name):
        # Get current timestamp
        ts_str = str(int(time.time()))
        return 'https://' + self.project_id+'.firebaseio.com/' + \
            self.monitor_name+'/device_readings/'+plug_name+'/'+ts_str+'/.json'
