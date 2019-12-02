from plug_lib import Plug, MongoDB
print('Enter the device name: ')
appliance = input()
print('Do you want to do real time detection (y or n)? ')
y_or_n = input()
detect = False
if (y_or_n.lower() == 'y'):
    detect = True
on_or_off_str = 'on' if detect == True else 'off'     

print('Appliance name is {}. Real Time detection is {}.\n Continue? (y or n)'.format(appliance,on_or_off_str))
y_or_n = input()
if (y_or_n.lower() == 'y'):
    db = MongoDB("mongodb://localhost:27017/", "FitHome", appliance)
    plug = Plug(appliance, db, detect_on=detect)
    plug.start()
else:
    print('Will not be collecting readings.\nBye!')
