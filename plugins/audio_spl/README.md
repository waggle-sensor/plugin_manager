# Python Script for Noise Level Calculation

The python script samples 5 seconds of audio from a microphone attachend on edge-processor and calculate noise level in dBm.
The script needs pyaudio to read audio data, and numpy to do further processes as shown below. The format of recorded sound is
pyaudio.paInt16, the number of channel is 1, sampling rate is 44100, each chunk length is 1024, and it records 5 seconds.

When I tested the mic personally in my laptop, ```input_device_index``` was 9. But it must be specifically defined with regard
to the device index in edge-processor (the script is tested in ubuntu and mac os).

```
import pyaudio
import numpy as np

# constants for audio recording
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5

audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,rate=RATE, input=True, frames_per_buffer=CHUNK, input_device_index=9)

frames = []
audioop_frames = b''

# Recording audio from the input device
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(np.frombuffer(data, dtype=np.int16))
    audioop_frames += data
```

The recorded data is stored in array, and changes format of the audio for fft and sound level calculation.
After fft process, the fft real numbers of results are sorted into octave with medium of 
```medium = [31, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]``` Hz, and calculate average of each bin,
which are stored in ```avgdb```.

```
# Change data format from audio to np.array
numpydata = np.hstack(frames)
times = np.arange(len(numpydata))/float(RATE)

N = numpydata.shape[0] # the total number of samples: 10 sec * 44100 sampling rate
T = 1.0 / RATE # a unit time for each sample: 44100 samples per a second

yf = np.fft.fftn(numpydata) # the n-dimensional FFT
xf = np.linspace(0.0, 1.0/(2.0*T), N//2) # 1.0/(2.0*T) = RATE / 2

octave = {}
avg = []
medium = [31, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000] # Medium? of octave, hearable frequency

for i in range(10):
    octave[i] = [medium[i]]

val = yf[0:N//2]

for idx in range(len(xf)):
    if xf[idx] > 20 and xf[idx] < 44:
        octave[0].append(val[idx])
    elif xf[idx] > 43 and xf[idx] < 88:
        octave[1].append(val[idx])
    elif xf[idx] > 87 and xf[idx] < 176:
        octave[2].append(val[idx])
    elif xf[idx] > 175 and xf[idx] < 353:
        octave[3].append(val[idx])
    elif xf[idx] > 352 and xf[idx] < 707:
        octave[4].append(val[idx])
    elif xf[idx] > 706 and xf[idx] < 1414:
        octave[5].append(val[idx])
    elif xf[idx] > 1413 and xf[idx] < 2825:
        octave[6].append(val[idx])
    elif xf[idx] > 2824 and xf[idx] < 5650:
        octave[7].append(val[idx])
    elif xf[idx] > 5649 and xf[idx] < 11300:
        octave[8].append(val[idx])
    elif xf[idx] > 11299:
        octave[9].append(val[idx])

for di in range(len(octave)):
    avg.append(sum(octave[di])/len(octave[di]))

avg = np.asarray(avg)
avgdb = 10*np.log10(np.abs(avg))
```

The average dBm for each bin are used to calculate sound pressure level (SPL) of recorded sound with regards of 
Adding acoustic levels of sound sources: http://www.sengpielaudio.com/calculator-spl.htm.

```
a = []
b = 0,
for ia in range(len(avg)):
    a.append(((10**(avgdb[ia]/10))**(1/2)) * 0.00002)
    b = b + (a[ia]/0.00002)**2

sdb = 10*np.log10(b)

# sdb --> addition of SPL, avgdb --> average of each octave
```

### Tesult values:
avgdb (1x10 array) and sdb (single value) are the results of the calculation. Those values need to be return back to DBs 
using image/audio pipeline.
