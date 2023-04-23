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
from secrets import OPENAI_API_KEY
from secrets import SERVER
from secrets import SERVER_KEY
import math
from pydub import AudioSegment

os.system("sudo ttyecho -n /dev/tty1 clear")

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

global FORMAT, CHANNELS, RATE, CHUNK, audio, stream
FORMAT = pyaudio.paInt16
CHANNELS = 1
#RATE = 44100
RATE = 48000
CHUNK = 4096
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK) #, input_device_index=3)

def update_lights():
    """Update the light colors based on their current state."""
    red = 1 if red_light_on else 0
    green = 1 if green_light_on else 0
    blue = 1 if blue_light_on else 0
    rh.lights.rgb(red, green, blue)

def light_up_leds_thread(percentage, num):
    global stop_rainbow_flag
    stop_rainbow_flag = True
    display_message(str(num)+" LF")
    # Calculate the number of LEDs to light up based on the percentage
    num_leds = round(percentage / 100 * 7)
    # Turn on the corresponding number of LEDs in red
    for i in range(num_leds):
        rh.rainbow.set_pixel(i, 255, 0, 0)
    for i in range(num_leds, 7):
        rh.rainbow.set_pixel(i, 0, 0, 0)
    rh.rainbow.show()
    if(percentage == 0):
        rh.rainbow.set_all(0, 255, 0)
        rh.rainbow.show()
    if(percentage == -1):
        rh.rainbow.set_all(0, 0, 255)
        rh.rainbow.show()
    # Sleep for 5 seconds
    time.sleep(5)
    # Turn off the LEDs
#    rh.rainbow.set_all(0, 0, 0)
#    rh.rainbow.show()
    stop_rainbow_flag = False
#    rh.display.clear()
#    rh.display.show()

def light_up_leds(percentage,number):
    threading.Thread(target=light_up_leds_thread, args=(percentage,number,)).start()

# Function to convert MIDI note to frequency
def note_to_freq(note):
    return 2**((note-69)/12) * 440

# Set up a flag to signal the thread to stop
global stop_jeopardy_flag
stop_jeopardy_flag = False
global stop_rainbow_flag
stop_rainbow_flag = False
global toggle_flag
toggle_flag = True

# Function to play the buzzer notes on the Rainbow HAT
def play_melody():
    global stop_jeopardy_flag, stop_rainbow_flag
    stop_rainbow_flag = True
    rh.display.clear()
    rh.display.show()
    while(not stop_jeopardy_flag):
        for note, duration in buzzer_notes:
            if note is not None and not stop_jeopardy_flag:
                frequency = note_to_freq(note)
                rh.buzzer.midi_note(note, duration)
            time.sleep(duration)
    # Turn off the buzzer and LEDs
        rh.buzzer.stop()
        time.sleep(.2)

def rainbow():
    global stop_rainbow_flag
    counter = 0
    while True:
        while not stop_rainbow_flag:
            for x in range(7):
                delta = time.time() * 75
                hue = delta + (x * 2)
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
        percentage = float(percentage_match.group(1))
        return percentage
    else:
        return None

def listen():
    global stop_rainbow_flag, toggle_flag, RATE
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    full_audio_data = b""  # Initialize an empty bytes object
    #t2 = threading.Thread(target=rainbow)
    while True:
        if toggle_flag:
            with microphone as source:
                recognizer.energy_threshold = 300
                #recognizer.pause_threshold = 2
                recognizer.pause_threshold = 2
                print("Listening for speech...")
                audio = recognizer.listen(source)
#                audio = recognizer.listen(source, timeout=3)
                full_audio_data += audio.get_wav_data()
                print("Dumping Speech")
#                duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
#                print("Duration: "+str(duration))
#                if duration < 25.0:
                full_audio = sr.AudioData(full_audio_data, RATE, audio.sample_width)
                print("sr: "+str(audio.sample_rate))
                print("sw: "+str(audio.sample_width))
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
            save_audio_thread = threading.Thread(target=save_audio, args=(full_audio, file_name))
            save_audio_thread.start()
            #t1 = threading.Thread(target=play_melody)
            #t1.start()
            full_audio_data = b"" 

def save_audio(audio_data, file_name):
    #os.system("sudo ttyecho -n /dev/tty1 clear")
    # Start the melody and rainbow as separate threads
    global stop_jeopardy_flag, stop_rainbow_flag, RATE
    stop_jeopardy_flag = False
    stop_rainbow_flag = True
    t1 = threading.Thread(target=play_melody)
    t1.start()
    rh.rainbow.set_all(0, 0, 0)
    rh.rainbow.show()
    rh.display.clear()
    rh.display.show()
    display_message("WAIT")
#    with open(file_name, "wb") as f:
#        f.write(audio_data.get_wav_data())
    with wave.open(file_name, 'wb') as wav_file:
        # Set the WAV file parameters
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wav_file.setframerate(RATE)
        #wav_file.setsampwidth(2)  # 16-bit
#        wav_file.setframerate(16000)  # Sample rate
        # Write the audio data to the WAV file
        wav_file.writeframes(audio_data.get_wav_data())

    audio = file_name
    audio_file = open(file_name, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    text = transcript.text
    print(text)

    response=openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
#      model="gpt-4",
      temperature=0,
      messages=[
            {"role": "system", "content": "You analyze statements for logical fallacies and explain the reasoning for each occuring fallacy in the message"},
            {"role": "user", "content": "Create a html page, start page with link centered in h1 tags <a href=\""+SERVER+"/files/\">All Analyses</a> evaluate next message in chonological order for all logical fallacies; Output a list of each occuring fallacy with the fallacy number/name in color blue as a h1 tag then the explaination as h2 tag in color blue. cite the offending quote with h3 tag in quote in color red; insert blank line, show \"total number of fallacies: (number)\" as in interger followed by a whole number percentage of how many sentences were fallacious both in h3 tags in color purple" },
            {"role": "assistant", "content": text},
        ]
    )


    stop_jeopardy_flag = True
    resp = response['choices'][0]['message']['content']
    print(resp)
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"text_{timestamp}.txt"
    with open(file_name, "w") as file:
        # Write the variables to the file
        file.write(f"{resp}\n")
        file.write(f"Transcript: {transcript.text}")
    result = split_at_text(resp)
    percentage = None
    number = None
    if(resp.startswith("I'm sorry,")): 
        percentage = -1
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
        file_name2 = f"analysis_{timestamp}.txt"
        with open(file_name2, "w") as file:
            # Write the variables to the file
            file.write(explaination)
        time.sleep(.25)
        os.system(f"""curl -X POST -H "Authorization: Bearer {SERVER_KEY}"  -F "file=@/home/pi/LogicAnalyzer/{file_name}" {SERVER}/upload""")
        beep_fallacies(number)
#    if percentage is not None and number is not None:
#        print("Got Percentage and Number")
#        print(f"Percentage: {percentage}")
#        print(f"Number: {number}")
#        light_up_leds(percentage, number)
    else:
        os.system(f"""curl -X POST -H "Authorization: Bearer {SERVER_KEY}"  -F "file=@/home/pi/LogicAnalyzer/{file_name}" {SERVER}/upload""")
#        os.system(f'''sudo ttyecho -n /dev/tty1 "clear && sleep 1 && echo There are no logical fallacies in this message."''')
        print("No percentage or number found in the text.")
        if(percentage != -1):
            percentage = 0
        number = 0
        light_up_leds(percentage, number)
    os.system(f"""curl -X POST -H "Authorization: Bearer {SERVER_KEY}"  -F "file=@/home/pi/LogicAnalyzer/{audio}" {SERVER}/upload""")
    stop_jeopardy_flag = True
    t1.join()

def main():
    #FORMAT = pyaudio.paInt16
    #CHANNELS = 1
    #RATE = 44100
    #CHUNK = 64
    #audio = pyaudio.PyAudio()
    #stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK) #, input_device_index=3)
    t2 = threading.Thread(target=rainbow)
    t2.start()
    listen_thread = threading.Thread(target=listen)
    listen_thread.start()

if __name__ == "__main__":
# Register the cleanup function to be called on exit
    main()
