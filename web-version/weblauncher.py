import rainbowhat as rh
import signal
import time
import subprocess

rh.lights.rgb(0, 0, 0)
# Clear the LEDs
rh.lights.rgb(0, 0, 0)
# Clear the display
rh.display.clear()
rh.display.show()
rh.rainbow.set_all(0, 0, 0)
rh.rainbow.show()

global stop
stop = False

def display_message(message):
    rh.display.print_str(message)
    rh.display.show()
    time.sleep(.15)

@rh.touch.A.press()
def touch_a(channel):
    global stop
    print("Button A touched!")
    if(not stop):
        stop = True
        rh.display.clear()
        rh.display.show()
        rh.display.print_str(" MIC") 
        rh.display.show() 
        rh.lights.rgb(1, 0, 0)
        rh.rainbow.set_all(0, 0, 0)
        rh.rainbow.show()
        subprocess.Popen('python3 /home/pi/LogicAnalyzer/web-version/interview.py', shell=True)

@rh.touch.B.press()
def touch_b(channel):
    global stop
    print("Button B touched!")
    if(not stop):
        stop = True
        rh.display.clear()
        rh.display.show()
        rh.display.print_str(" AUX")
        rh.display.show()
        rh.lights.rgb(0, 1, 0)
        rh.rainbow.set_all(0, 0, 0)
        rh.rainbow.show()
        subprocess.Popen('python3 /home/pi/LogicAnalyzer/web-version/auxinweb.py', shell=True)

@rh.touch.C.press()
def touch_c(channel):
    global stop
    print("Button C touched!")
    stop = True
    rh.lights.rgb(0, 0, 1)
    time.sleep(2)
    rh.lights.rgb(0, 0, 0)
    rh.display.clear()
    rh.display.show()
    rh.rainbow.set_all(0, 0, 0)
    rh.rainbow.show()
    # Find the process ID of the microphone.py program
    output = subprocess.check_output(['ps', 'aux'])
    pid = None
    for line in output.splitlines():
        if b'interview.py' in line or b'auxin.py' in line:
            pid = int(line.split(None, 2)[1])
            break
    if(pid != None):
        subprocess.call(['kill', str(pid)])
    print(f'python process (PID {pid}) has been killed.')
    #subprocess.Popen('sudo systemctl restart logic.service')
    subprocess.Popen('sudo killall python3 python', shell=True)

# Pause the main thread so it doesn't exit
#signal.pause()
counter = 0
while not stop:
#    print("running")
    rh.rainbow.set_all(0, 255, 0)
    rh.rainbow.show()
    if(counter % 10 == 0):
        display_message("    ")
    if(counter % 10 == 1):
        display_message("   R")
    if(counter % 10 == 2):
        display_message("  RE")
    if(counter % 10 == 3):
        display_message(" REA")
    if(counter % 10 == 4):
        display_message("READ")
    if(counter % 10 == 5):
        display_message("EADY")
    if(counter % 10 == 6):
        display_message("ADY ")
    if(counter % 10 == 7):
        display_message("DY  ")
    if(counter % 10 == 8):
        display_message("Y   ")
    if(counter % 10 == 9):
        display_message("    ")
    counter += 1

signal.pause()
