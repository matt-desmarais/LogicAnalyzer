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
    # Sleep for 5 seconds
    time.sleep(5)

    # Turn off the LEDs
    rh.rainbow.set_all(0, 0, 0)
    rh.rainbow.show()
    stop_rainbow_flag = False
    rh.display.clear()
    rh.display.show()

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
        if not stop_rainbow_flag:
            for x in range(7):
                delta = time.time() * 40
                hue = delta + (x * 10)
                hue %= 360    # Clamp to 0-359.9r
                hue /= 360.0  # Scale to 0.0 to 1.0
                r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
                rh.rainbow.set_pixel(6 - x, r, g, b, brightness=0.1)
            rh.rainbow.show()
            if(counter % 6 == 0):
                display_message("XXXX")
            if(counter % 6 == 1):
                display_message("XOXO")
            if(counter % 6 == 2):
                display_message("    ")
            if(counter % 6 == 3):
                display_message("OOOO")
            if(counter % 6 == 4):
                display_message("XOXO")
            if(counter % 6 == 5):
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
    percentage_match = re.search(r"(\d{1,3})%", input_str, re.IGNORECASE)
    if percentage_match:
        percentage = int(percentage_match.group(1))
        return percentage
    else:
        return None

def listen():
    global stop_rainbow_flag, toggle_flag
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    #t2 = threading.Thread(target=rainbow)
    while True:
        if toggle_flag:
            with microphone as source:
                recognizer.pause_threshold = 1.25
                print("Listening for speech...")
                audio = recognizer.listen(source)
                print("After")
                duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
                print("Duration: "+str(duration))
                if duration < 10.0:
                    print("Recording too short, discarding...")
                    listen()
            stop_rainbow_flag = True
            print("Speech detected, recording...")
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"audio_{timestamp}.wav"
            save_audio_thread = threading.Thread(target=save_audio, args=(audio, file_name))
            save_audio_thread.start()

def save_audio(audio_data, file_name):
    os.system("sudo ttyecho -n /dev/tty1 clear")
    # Start the melody and rainbow as separate threads
    global stop_jeopardy_flag, stop_rainbow_flag
    stop_jeopardy_flag = False
    stop_rainbow_flag = True
    t1 = threading.Thread(target=play_melody)
    t1.start()
    rh.rainbow.set_all(0, 0, 0)
    rh.rainbow.show()
    rh.display.clear()
    rh.display.show()
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
            {"role": "system", "content": "You analyze statements for logical fallacies"},
            {"role": "user", "content": "evaluate next message for logical fallacies;  Output a list of each occuring fallacies preceded with \u001b[31m for the fallacy name then for the 1 line explaination of each preceded with \u001b[0m, after that output  the \"total number of fallacies:\" and a integer percentage of how much text was fallacious" },
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
        file.write(f"Text: {transcript.text}\n")
        file.write(f"Analysis: {resp}\n")
    result = split_at_text(resp)
    percentage = None
    number = None
    if(result != None):
        explaination = result[0] if len(result) > 0 else None
        summary = result[1] if len(result) > 1 else None
        explaination = "\n".join([line for line in explaination.split("\n") if line.strip() != ""])
        explaination += "\n"
        percentage = extract_percentage(summary)
        number = extract_number(summary)
        print(f"Analysis: {explaination}")
        print(f"Summary: {summary}")
        file_name = f"analysis_{timestamp}.txt"
        with open(file_name, "w") as file:
            # Write the variables to the file
            file.write(explaination)
        time.sleep(.25)
        os.system(f'''sudo ttyecho -n /dev/tty1 "clear && cat /home/pi/LogicAnalyzer/{file_name}"''')
    if percentage is not None and number is not None:
        print("Got Percentage and Number")
        print(f"Percentage: {percentage}")
        print(f"Number: {number}")
        light_up_leds(percentage, number)
    else:
        os.system(f'''sudo ttyecho -n /dev/tty1 "clear && sleep 1 && echo There are no logical fallacies in this message."''')
        print("No percentage or number found in the text.")
        percentage = 0
        number = 0
        light_up_leds(percentage, number)
    stop_jeopardy_flag = True
    t1.join()

def main():
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 64
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK) #, input_device_index=3)
    t2 = threading.Thread(target=rainbow)
    t2.start()
    listen_thread = threading.Thread(target=listen)
    listen_thread.start()
    # Stop and close the audio stream
    stream.stop_stream()
    #stream.close()
    audio.terminate()
    rh.rainbow.set_all(0, 0, 0)
    rh.rainbow.show()
    rh.lights.rgb(0, 0, 0)

if __name__ == "__main__":
# Register the cleanup function to be called on exit
    main()
