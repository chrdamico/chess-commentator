# Chess commentator

Simple LLM based tool that comments games of the [Top Chess Engine Championship (TCEC)](https://en.wikipedia.org/wiki/Top_Chess_Engine_Championship).
Game data is gathered from the public WebSocket, then parsed and fed into an LLM (currently implementation uses the latest GPT-4 API). 
Commentary is then vocalized by [PIPER-TTS](https://github.com/rhasspy/piper), an open source Text to Speech solution with a conveninent python interface.

## What is this
I like to watch chess tournaments. Seeing the highest level players play is interesting, exciting and educational. The
best part about chess tournaments is that they are often commentated by very strong Grandmaster that allow you to understand 
better the action and learn a lot.

I sometimes like to watch chess computers play each other. Unfortunately, since computers don't get tired, they tend to 
play very long tournaments that go on 24/7 with no commentary. But, well, who better than computers can comment computers?!
This project is just a tiny little tool that I sometimes turn on while watching computer chess at the TCEC to have some
nice simple commentary. Of course it's nowhere near as good as real humans commentating, but it's still nice.

## Installation

### Python
Create a virtual environment with python `>=3.11` with your preferred tool. 
For pyenv and virtualenv this would mean installing the specific python version with
```bash
pyenv install 3.11
```
and setting it to be used in the local folder
```bash
pyenv local 3.11.7
```

Then creating a virtual environment
```bash
python -m venv .venv
```
and activating it
```bash
source .venv/bin/activate
```

Finally installing all the required packages:
```bash
pip install .
```

### Required environment

Modifying the behavior of the project is done via environment variables. These can be easily set by adding a `.env` file in `src/conf`.
Supported variables are found here with a short comment saying what they do: [settings.py](src%2Fconf%2Fsettings.py).
The only environment variable that is really necessary is the openAI API key: `OPENAI_API_KEY="your_api_key"`.
An example configuration of all the available variables is:
```
log_level="DEBUG"
DUMP_RAW_MESSAGES=false
OPENAI_API_KEY="your_api_key"
VOICE_MODEL_FILE_LOCATION="voices/en_US-lessac-medium.onnx"
DATA_DUMP_FILE_PATH="data/another_data_dump.txt"
LOCAL_SOURCE_FILE_PATH="data/example_data_dump.txt"
SILENT_MODE=false
```

### Running in Docker

There is a [Dockerfile](Dockerfile) available in this project that makes running it much easier. In order to allow Docker to access the 
audio output devices on the host machine there are a few different options. A very nice informative summary of the 
tradeoffs is available here: [ALSA or Pulseaudio](https://github.com/mviereck/x11docker/wiki/Container-sound:-ALSA-or-Pulseaudio).

For this project the easiest method is to just use ALSA. You can check if this is working on your machine by running
```
docker run --rm --device /dev/snd ALSAIMAGE speaker-test
```

In order to run via docker it is still necessary to provide an openAI API key. This can be written in the [Dockerfile](Dockerfile) 
or provided as an argument during the docker run command. Choosing the latter option, we can build the container as
```
docker build . -t chess-commentator
```
and run it using
```
docker run --device /dev/snd -e OPENAI_API_KEY=<your_api_key> chess-commentator
```

### Piper TTS

I have chosen a simple generic voice from the open souce MIT licensed ones at [PIPER-TTS](https://github.com/rhasspy/piper)
and added it here to the project for convenience. It is very easy to change it! You can try voices [here](https://rhasspy.github.io/piper-samples/).
Once you find one that you like you can download it (both the `.onnx` and the `.onnx.json` files), store it somewhere and point
to it with the environment variable `VOICE_MODEL_FILE_LOCATION`. A list of downloadable voices is available
[here](https://github.com/rhasspy/piper/blob/master/VOICES.md)