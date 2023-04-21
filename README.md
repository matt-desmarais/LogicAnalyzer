# LogicAnalyzer 
[![Hackaday Article](https://img.shields.io/badge/Hackaday-Article-blue)](https://hackaday.com/2023/04/06/chatgpt-powers-a-different-kind-of-logic-analyzer/)
## Pi Audio Device
pi + rainbowhat + touchscreen + usb sound card (mic or aux in) + open ai = audio logic analyzer
## LogicAnalyzer TwitterBot
## LogicAnalyzer DiscordBot
# still under development
# NEW web version
## web versions upload data to nodejs app running on vps
button operated interview mode and auto mode with aux in that will detect 2 second pause to end recording and analyze. Audio samples should be with less than roughly 3 minutes, 4 if its a slow speeker.

[Main Page](https://bullshit.mattthemaker.org/)

[Web Analysis (all files)](https://bullshit.mattthemaker.org/files)

# Screen version
It will listen for speech, when speech stops (or paused) it will analyze what was said with whisper+gpt3.5turbo, it will display # of LF on the display, leds represent how much of what was said was fallacious and it will print its explanations on the touch screen OR hdmi as tty1.

## If no fallacies are found
![No Fallacies Found](https://github.com/matt-desmarais/LogicAnalyzer/raw/main/PXL_20230331_202900977.jpg)

## If fallacy found
![Fallacy Detected](https://github.com/matt-desmarais/LogicAnalyzer/raw/main/PXL_20230331_213810695%20(1).jpg)


# BS METER INSTALL INSTRUCTIONS

sudo apt update

raspi-config enable i2c

sudo nano /usr/share/alsa/alsa.conf

Look for these lines:

defaults.ctl.card 0

defaults.pcm.card 0

Replace with:

defaults.ctl.card 1

defaults.pcm.card 1


sudo apt install git python3-pip python3-pyaudio python3-smbus

git clone https://github.com/matt-desmarais/LogicAnalyzer.git

pip3 install pyaudio rainbowhat openai SpeechRecognition pydub
