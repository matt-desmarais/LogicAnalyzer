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
from pydub import AudioSegment
from stopwatch import Stopwatch

os.system("sudo ttyecho -n /dev/tty1 clear")

openai.api_key = OPENAI_API_KEY

rh.rainbow.set_all(0, 0, 0)
rh.rainbow.show()
rh.display.clear()
rh.display.show()

def cleanup():
    # Turn off the LEDs and clear the display
    rh.rainbow.set_all(0, 0, 0)
    rh.rainbow.show()
    #rh.lights.rgb(0, 0, 0)
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
    if(num == 0 or num == None):
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
        percentage = float(math.ceil(float(percentage_match.group(1))))
        return percentage
    else:
        return None

def listen():
    global stop_rainbow_flag, toggle_flag
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    full_audio_data = b""  # Initialize an empty bytes object
    while True:
        if toggle_flag:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source)
                print("Listening for speech...")
                audio = recognizer.listen(source)
                # Append the new audio segment to the full_audio
                full_audio_data += audio.get_wav_data()
                full_audio = sr.AudioData(full_audio_data, audio.sample_rate, audio.sample_width)
                duration = len(full_audio.get_wav_data()) / 100000.0  # Duration in seconds
                print("Duration: "+str(duration))
                if duration < 20.0:
                    print("Recording too short, continuing...")
                    continue
                stop_rainbow_flag = True
                rh.buzzer.midi_note(85, .25)
                time.sleep(.25)
                rh.buzzer.midi_note(95, .25)
            print("Speech detected, recording...")
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"audio_{timestamp}.wav"
            stop_rainbow_flag = True
            print(f"Audio saved to: {file_name}")
            save_audio_thread = threading.Thread(target=save_audio, args=(full_audio, file_name))
            save_audio_thread.start()
            full_audio_data = b""

def save_audio(audio_data, file_name):
    # Start the melody and rainbow as separate threads
    global stop_jeopardy_flag, stop_rainbow_flag
    stop_rainbow_flag = True
    time.sleep(1)
    rh.display.clear()
    rh.display.show()
    display_message("WAIT")
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
            {"role": "system", "content": "You analyze statements for logical fallacies and explain them, you take apart statements to find logical fallacies. Do not list any fallacies that do not occur"},
            {"role": "user", "content": "evaluate next message in chonological order for all logical fallacies;  Output a list of each occuring fallacies preceded with \x1b[1;34m for the fallacy name then the explaination preceded with \u001b[0m; insert \u001b[31m then cite the to offending quote; end every quote with \u001b[0m. followed by \"total number of fallacies:\" as in interger followed by a whole number \"percentage of how many sentences were fallacious\"" },
            {"role": "assistant", "content": text},
        ]
    )

    resp = response['choices'][0]['message']['content']
    print(resp)
    percentage = None
    number = None
    if(resp.startswith("I'm sorry,") or resp.startswith("Sorry") or resp.startswith("There is no statement to analyze for logical fallacies")):
        percentage = -1
    if(resp.startswith("There are no logical fallacies in this message")):
        percentage = 0
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"text_{timestamp}.txt"
    with open(file_name, "w") as file:
        # Write the variables to the file
        file.write(f"Text:\n{transcript.text}\n")
        file.write(f"Analysis:\n {resp}\n")
    result = split_at_text(resp)
    if(result != None and percentage != -1):
        explaination = result[0] if len(result) > 0 else None
        summary = result[1] if len(result) > 1 else None
        explaination = "\n".join([line for line in explaination.split("\n") if line.strip() != ""])
        explaination += "\n"
        percentage = extract_percentage(summary)
        number = extract_number(summary)
        light_up_leds(percentage, number)
        print(f"Analysis:\n{explaination}")
        print(f"Summary:\n{summary}")
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
    stopwatch = Stopwatch(1)
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
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
