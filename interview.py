import math
import re
import time
import wave
import pyaudio
import rainbowhat as rh
import RPi.GPIO as GPIO
import datetime
import openai
from secrets import OPENAI_API_KEY
import os
from secrets import SERVER
from secrets import SERVER_KEY

openai.api_key = OPENAI_API_KEY

def light_up_leds(percentage, num):
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
    time.sleep(3)
    rh.rainbow.set_all(0, 0, 0)
    rh.rainbow.show()
    rh.display.clear()
    rh.display.show()
    rh.lights.rgb(0, 0, 0)
def display_message(message):
    rh.display.print_str(message)
    rh.display.show()

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

global record
record = False
global filename
now = datetime.datetime.now()
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
filename = f"interview_{timestamp}.wav"

# Set up GPIO input for button A
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set up audio parameters
CHANNELS = 1
RATE = 44100
WIDTH = 2
#RECORD_SECONDS = 5
rh.lights.rgb(0, 0, 0)

@rh.touch.B.press()
def press_b(channel):
    global filename
    rh.lights.rgb(0, 1, 0)
    display_message("TEST")
#    with open(filename, "wb") as f:
#        f.write(audio_data.get_wav_data())
    audio_file = open(filename, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    text = transcript.text
    print(text)

#    response=openai.ChatCompletion.create(
#      model="gpt-3.5-turbo",
#      temperature=0,
#      messages=[
#            {"role": "system", "content": "You analyze statements for logical fallacies and explain them, you take apart statements to find logical fallacies. Do not list any fallacies that do not occur"},
#            {"role": "user", "content": "Create a pretty html page, start page with link centered in h1 tags <a href=\"https://bullshit.mattthemaker.org/files/\">All Analyses</a> evaluate next message in chonological order for all logical fallacies; Output a list of each occuring fallacies with the fallacy name in color blue as a h1 tag then the explaination as h2 tag in color black. cite the to offending quote with h3 tag in color red; show \"total number of fallacies:\" as in interger followed by a whole number percentage of how many sentences were fallacious both in h3 tags in color purple" },
#            {"role": "assistant", "content": text},
#        ]
#    )


    response=openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      temperature=0,
      messages=[
            {"role": "system", "content": "You analyze statements for logical fallacies and explain the reasoning"},
            {"role": "user", "content": "Create a html page, start page with link centered in h1 tags <a href=\""+SERVER+"/files/\">All Analyses</a> evaluate next message in chonological order for all logical fallacies; Output a list of each occuring fallacy with the fallacy number/name in color blue as a h1 tag then the explaination as h2 tag in color blue. cite the offending quote with h3 tag in quote in color red; insert blank line, show \"total number of fallacies:\" as in interger followed by a whole number percentage of how many sentences were fallacious both in h3 tags in color purple" },
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
    file_name = f"interview_{timestamp}.txt"
    with open(file_name, "w") as file:
        # Write the variables to the file
        #file.write(f"Transcript:\n{transcript.text}\n")
        file.write(f"{resp}\n")
        file.write(f"Transcript:\n{transcript.text}\n")
    result = split_at_text(resp)
    if(result != None and percentage != -1):
        explaination = result[0] if len(result) > 0 else None
        summary = result[1] if len(result) > 1 else None
#        explaination = "\n".join([line for line in explaination.split("\n") if line.strip() != ""])
#        explaination += "\n"
        percentage = extract_percentage(summary)
        number = extract_number(summary)
        os.system(f"""curl -X POST -H "Authorization: Bearer {SERVER_KEY}"  -F "file=@/home/pi/LogicAnalyzer/{file_name}" {SERVER}/upload""")
        light_up_leds(percentage, number)
        print(f"Exp:\n{explaination}")
#        print(f"Summary:\n{summary}")
        #file_name = f"interview_analysis_{timestamp}.txt"
        #with open(file_name, "w") as file:
            # Write the variables to the file
        #    file.write(explaination)

        os.system(f'''sudo ttyecho -n /dev/tty1 "clear && cat /home/pi/LogicAnalyzer/{file_name}"''')
    else:
        os.system(f'''sudo ttyecho -n /dev/tty1 "clear && sleep 1 && echo There are no logical fallacies in this message."''')
        print("No percentage or number found in the text.")
        if(percentage != -1):
            percentage = 0
        number = 0
        os.system(f"""curl -X POST -H "Authorization: Bearer {SERVER_KEY}"  -F "file=@/home/pi/LogicAnalyzer/{file_name}" {SERVER}/upload""")
        light_up_leds(percentage, number)
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"interview_{timestamp}.wav"


@rh.touch.A.press()
def press_a(channel):
    global record
    record = not record
    if record:
        print("recording")
        display_message("TALK")
        rh.lights.rgb(1, 0, 0)
        start_recording()
    else:
        print("not recording")

@rh.touch.release()
def release(channel):
    global record
    print(GPIO.input(21))
    print("Button release!")
    if not record:
        display_message("STOP")
        print("recording release!")
        rh.lights.rgb(0, 0, 0)
        record = False
# Set up PyAudio audio capture
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=1024)

def start_recording():
    global filename
#    stream = p.open(format=pyaudio.paInt16,
#                    channels=CHANNELS,
#                    rate=RATE,
#                    input=True,
#                    frames_per_buffer=1024)
    print("test")
    # Set up the WAV file
    #filename = "recording.wav"
    # Open the WAV file for reading
    #filename = "recording.wav"
    try:
        with wave.open(filename, 'rb') as wf:
            # Get the audio data
            data = wf.readframes(wf.getnframes())
            wf = wave.open(filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(RATE)
            wf.writeframes(data)
    except FileNotFoundError:
        print("File not found:", filename)
#        data = None
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(RATE)
#    wf = wave.open(filename, 'wb')
#    wf.setnchannels(CHANNELS)
#    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
#    wf.setframerate(RATE)
#    wf.writeframes(data)
    # Start recording
    stream.start_stream()
#    while rh.touch.A.pressed:
    print("pressed")
    time.sleep(1)
    while record and GPIO.input(21) == GPIO.HIGH:
        print(GPIO.input(21))
        try:
            rh.lights.rgb(1, 0, 0)
            data = stream.read(1024, exception_on_overflow=False)
        except IOError as ex:
            if ex[1] != pyaudio.paInputOverflowed:
                raise ex
            data = ''
        wf.writeframes(data)

        # Check if recording time is over
#        if time.time() - start_time > RECORD_SECONDS:
#            break

    # Stop recording and close the WAV file
    stream.stop_stream()
#    stream.close()
#    p.terminate()
    wf.close()


# Wait for button to be pressed
while True:
    #if rh.touch.A.pressed:
    #    start_recording()
    #    break
    time.sleep(0.1)
