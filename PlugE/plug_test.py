from pyHS100 import SmartPlug, Discover
#
# print(dev) E.g. output -
# <SmartPlug model HS110(US) at 192.168.86.227 (microwave), is_on: True - dev specific: {'LED state': False, 'On since': datetime.datetime(2019, 11, 16, 0, 47, 49, 530091)}>
# <SmartPlug model HS110(US) at 192.168.86.226 (M_Computer), is_on: True - dev specific: {'LED state': True, 'On since': datetime.datetime(2019, 10, 29, 18, 15, 50, 558937)}>
# <SmartPlug model HS110(US) at 192.168.86.27 (washing_machine), is_on: True - dev specific: {'LED state': True, 'On since': datetime.datetime(2019, 12, 2, 13, 2, 50, 578911)}>
# <SmartPlug model HS110(US) at 192.168.86.220 (Entertainment), is_on: True - dev specific: {'LED state': True, 'On since': datetime.datetime(2019, 10, 29, 18, 15, 49, 598561)}>
#
# for dev in Discover.discover().values():
#    print(dev)
#
# Test plug_lib.py
from plug_lib import Plug, MongoDB

db = MongoDB("mongodb://localhost:27017/", "FitHome", "microwave")
plug = Plug("microwave", db, detect_on=False)
plug.start()
