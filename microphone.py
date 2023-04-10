import pyaudio
import wave
import os
import datetime
import speech_recognition as sr
import openai
import re
import threading
import time
import rainbowhat as rh
import colorsys
import sys
import atexit
import signal
from secrets import OPENAI_API_KEY
import math

os.system("sudo ttyecho -n /dev/tty1 clear")

# Flag to indicate if the program is exiting
exiting = False

# Function to be run on program exit
def cleanup():
    global exiting
    # Set the exiting flag to True to stop all threads
    exiting = True
    # Wait for all threads to finish
    main_thread = threading.current_thread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        t.join()
    time.sleep(1)
    # Clear the LEDs and display
    rh.rainbow.set_all(0, 0, 0)
    rh.rainbow.show()
    rh.display.clear()
    rh.display.show()

# Register the signal handler function
def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

openai.api_key = OPENAI_API_KEY

rh.rainbow.set_all(0, 0, 0)
rh.rainbow.show()
rh.lights.rgb(0, 0, 0)
rh.display.clear()
rh.display.show()

def cleanup():
    # Turn off the LEDs and clear the display
    rh.rainbow.set_all(0, 0, 0)
    rh.rainbow.show()
    rh.lights.rgb(0, 0, 0)
    rh.display.clear()
    rh.display.show()


buzzer_notes = [(78, 0.748), (83, 0.48), (78, 0.48), (71, 0.48), (78, 0.48), (83, 0.48), (78, 0.48), (None, .2),
                (78, 0.48), (83, 0.48), (78, 0.48), (83, 0.48), (87, 0.75),  (85, 0.24),
                (82, 0.24), (76, 0.24), (74, 0.24),  (78, 0.48), (83, 0.48), (78, 0.48),
                (71, 0.24), (71, 0.24), (78, 0.48), (83, 0.48), (78, 0.48), (83, 0.48), (None, 0.24),
                (83, 0.24), (82, 0.24), (82, 0.24), (80, 0.24), (78, 0.24), (78, 0.48), (76, 0.48), (74, 1.0)]

def display_message(message):
    rh.display.print_str(message)
    rh.display.show()
    time.sleep(.125)

def beep_fallacies(num):
    if(num == 0):
        return
    for n in range(num):
        rh.buzzer.midi_note(35, .5)
        time.sleep(1)

# State variables to track the light states
red_light_on = False
green_light_on = False
blue_light_on = False

def update_lights():
    """Update the light colors based on their current state."""
    red = 1 if red_light_on else 0
    green = 1 if green_light_on else 0
    blue = 1 if blue_light_on else 0
    rh.lights.rgb(red, green, blue)


def light_up_leds_thread(percentage, num):
    rh.rainbow.set_all(0, 0, 0)
    rh.rainbow.show()
    global stop_rainbow_flag
    stop_rainbow_flag = True
    display_message(str(num)+" LF")
    # Calculate the number of LEDs to light up based on the percentage
    num_leds = round(percentage / 100 * 7)
    # Turn on the corresponding number of LEDs in red
    for i in range(num_leds):
        rh.rainbow.set_pixel(i, 255, 0, 0)
    rh.rainbow.show()
    if(percentage == 0):
        rh.rainbow.set_all(0, 255, 0)
        rh.rainbow.show()
    if(percentage == -1):
        rh.rainbow.set_all(0, 0, 255)
        rh.rainbow.show()
    # Sleep for 5 seconds
    time.sleep(5)
    stop_rainbow_flag = False

def light_up_leds(percentage,number):
    threading.Thread(target=light_up_leds_thread, args=(percentage,number,)).start()

# Function to convert MIDI note to frequency
def note_to_freq(note):
    return 2**((note-69)/12) * 440

# Set up the buzzer
buzzer = rh.buzzer

# Set up a flag to signal the thread to stop
global stop_rainbow_flag
stop_rainbow_flag = False
global toggle_flag
toggle_flag = True

def rainbow():
    global stop_rainbow_flag
    while True:
        counter = 0
        while not stop_rainbow_flag:
            for x in range(7):
                delta = time.time() * 20
                hue = delta + (x * 10)
                hue %= 360    # Clamp to 0-359.9r
                hue /= 360.0  # Scale to 0.0 to 1.0
                r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
                rh.rainbow.set_pixel(6 - x, r, g, b, brightness=0.1)
                rh.rainbow.show()

                if(counter % 13 == 0):
                    display_message("   L")
                if(counter % 13 == 1):
                    display_message("  LI")
                if(counter % 13 == 2):
                    display_message(" LIS")
                if(counter % 13 == 3):
                    display_message("LIST")
                if(counter % 13 == 4):
                    display_message("ISTE")
                if(counter % 13 == 5):
                    display_message("STEN")
                if(counter % 13 == 6):
                    display_message("TENI")
                if(counter % 13 == 7):
                    display_message("ENIN")
                if(counter % 13 == 8):
                    display_message("NING")
                if(counter % 13 == 9):
                    display_message("ING ")
                if(counter % 13 == 10):
                    display_message("NG  ")
                if(counter % 13 == 11):
                    display_message("G   ")
                if(counter % 13 == 12):
                    display_message("    ")
                counter += 1
            rh.rainbow.show()
#        if(counter > 0):
#            rh.display.clear()
#            rh.display.show()
#            display_message("WAIT")
        # Turn off the LEDs
        #rh.rainbow.set_all(0, 0, 0)
        #rh.rainbow.show()

def split_at_text(s):
    # Split the string at the last occurrence of the phrase
    s = s.lower()
    index = s.rfind("total number of fallacies")
    if index == -1:
        return None
    else:
        parts = [s[:index], s[index:]]
        return parts

def extract_number(input_str):
    number_match = re.search(r"Total number of fallacies: (\d{1,2})", input_str, re.IGNORECASE)
    if number_match:
        number = int(number_match.group(1))
        return number
    else:
        return None

def extract_percentage(input_str):
#    percentage_match = re.search(r"(\d{1,3})%", input_str, re.IGNORECASE)
    percentage_match = re.search(r"(\d{1,3}(?:\.\d{1,2})?)%", input_str, re.IGNORECASE)
    if percentage_match:
        percentage = int(math.ceil(float(percentage_match.group(1))))
        return percentage
    else:
        return None

def listen():
    global stop_rainbow_flag, toggle_flag
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    while True:
        if toggle_flag:
#            t2 = threading.Thread(target=rainbow)
#            stop_rainbow_flag = False
#            if not t2.is_alive():
#                t2.start()
#            else:
#                t2.join()
#                t2.start()
            with microphone as source:
                print(recognizer.adjust_for_ambient_noise(source))
                #recognizer.energy_threshold = 50
                recognizer.pause_threshold = 3
                #stop_rainbow_flag = False
                print("Listening for speech...")
                rh.buzzer.midi_note(75, .25)
                audio = recognizer.listen(source)
                if not toggle_flag:
                    stop_rainbow_flag = True
                    #t2.join()
                    # Stop listening if flag is toggled off
                    break
                stop_rainbow_flag = True
                rh.buzzer.midi_note(85, .25)
                time.sleep(.25)
                rh.buzzer.midi_note(95, .25)
                # Check the duration of the audio recording
                duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
                print("Duration: "+str(duration))
                if duration < 10.0:
                    rh.buzzer.midi_note(65, .25)
                    time.sleep(.25)
                    rh.buzzer.midi_note(65, .25)
                    print("Recording too short, discarding...")
                    stop_rainbow_flag = False
                    continue
            #stop_rainbow_flag = True
#            rh.display.clear()
#            rh.display.show()
#            display_message("WAIT")
            print("Speech detected, recording...")
#            rh.display.clear()
#            rh.display.show()
#            display_message("WAIT")
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"audio_{timestamp}.wav"
            stop_rainbow_flag = True
            #save_audio(audio, file_name)
            print(f"Audio saved to: {file_name}")
            save_audio_thread = threading.Thread(target=save_audio, args=(audio, file_name))
            save_audio_thread.start()

def save_audio(audio_data, file_name):
#    os.system("sudo ttyecho -n /dev/tty1 clear")
    # Start the melody and rainbow as separate threads
    global stop_jeopardy_flag, stop_rainbow_flag
    stop_jeopardy_flag = False
    stop_rainbow_flag = True
    rh.display.clear()
    rh.display.show()
    display_message("WAIT")
    #t1 = threading.Thread(target=play_melody)
    #t1.start()
    with open(file_name, "wb") as f:
        f.write(audio_data.get_wav_data())
    audio_file = open(file_name, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    text = transcript.text
    print(text)

    response=openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      temperature=0,
      messages=[
            {"role": "system", "content": "You analyze statements for logical fallacies and explain them, you take apart statements to find logical fallacies"},
            {"role": "user", "content": "evaluate next message in chonological order for all logical fallacies;  Output a list of each occuring fallacies preceded with \x1b[1;34m for the fallacy name then the explaination preceded with \u001b[0m; precede \u001b[31m to offending quote of speaker for each fallacy; end every quote with \u001b[0m. followed by \"total number of fallacies:\" as in interger followed by a whole number \"percentage of how many sentences were fallacious\"" },
            {"role": "assistant", "content": text},
        ]
    )

    #stop_jeopardy_flag = True
    resp = response['choices'][0]['message']['content']
    print(resp)
    percentage = None
    number = None
    if(resp.startswith("I'm sorry,")): 
        percentage = -1
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"text_{timestamp}.txt"
    with open(file_name, "w") as file:
        # Write the variables to the file
        file.write(f"TWext: {transcript.text}\n")
        file.write(f"Analysis: {resp}\n")
    result = split_at_text(resp)
    if(result != None and percentage != -1):
        explaination = result[0] if len(result) > 0 else None
        summary = result[1] if len(result) > 1 else None
        explaination = "\n".join([line for line in explaination.split("\n") if line.strip() != ""])
        explaination += "\n"
        percentage = extract_percentage(summary)
        number = extract_number(summary)
        light_up_leds(percentage, number)
        print(f"Analysis: {explaination}")
        print(f"Summary: {summary}")
        file_name = f"analysis_{timestamp}.txt"
        with open(file_name, "w") as file:
            # Write the variables to the file
            file.write(explaination)
        os.system(f'''sudo ttyecho -n /dev/tty1 "clear && cat /home/pi/LogicAnalyzer/{file_name}"''')
        beep_fallacies(number)

    else:
        os.system(f'''sudo ttyecho -n /dev/tty1 "clear && sleep 1 && echo There are no logical fallacies in this message."''')
        print("No percentage or number found in the text.")
        if(percentage != -1):
            percentage = 0
        number = 0
        light_up_leds(percentage, number)

def main():
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 8000
    CHUNK = 1024
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    rainbow_thread = threading.Thread(target=rainbow)
    rainbow_thread.start()

    listen_thread = threading.Thread(target=listen)
    listen_thread.start()

if __name__ == "__main__":
# Register the cleanup function to be called on exit
    main()
