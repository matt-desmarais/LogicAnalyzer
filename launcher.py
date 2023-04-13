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
        subprocess.Popen('python3 /home/pi/LogicAnalyzer/microphone.py', shell=True)

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
        subprocess.Popen('python3 /home/pi/LogicAnalyzer/auxin.py', shell=True)

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
        if b'microphone.py' in line or b'newauxin.py' in line:
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
    if(counter % 24 == 0):
        display_message("    ")
    if(counter % 24 == 1):
        display_message("   B")
    if(counter % 24 == 2):
        display_message("  BU")
    if(counter % 24 == 3):
        display_message(" BUL")
    if(counter % 24 == 4):
        display_message("BULL")
    if(counter % 24 == 5):
        display_message("ULLS")
    if(counter % 24 == 6):
        display_message("LLSH")
    if(counter % 24 == 7):
        display_message("LSHI")
    if(counter % 24 == 8):
        display_message("SHIT")
    if(counter % 24 == 9):
        display_message("HIT ")
    if(counter % 24 == 10):
        display_message("IT M")
    if(counter % 24 == 11):
        display_message("T ME")
    if(counter % 24 == 12):
        display_message(" MET")
    if(counter % 24 == 13):
        display_message("METE")
    if(counter % 24 == 14):
        display_message("ETER")
    if(counter % 24 == 15):
        display_message("TER ")
    if(counter % 24 == 16):
        display_message("ER R")
    if(counter % 24 == 17):
        display_message("R RE")
    if(counter % 24 == 18):
        display_message(" REA")
    if(counter % 24 == 19):
        display_message("READ")
    if(counter % 24 == 20):
        display_message("EADY")
    if(counter % 24 == 21):
        display_message("ADY ")
    if(counter % 24 == 22):
        display_message("DY  ")
    if(counter % 24 == 23):
        display_message("Y   ")
    counter += 1

signal.pause()
