# Python Script for Noise Level Calculation

## Log (May 7, 2018):
- A knob for adjusting octave band is added (the 'octave_band' in config; if octave_band = 1, then it is 1/1 octave, if octave_band = 2, then it is 1/2 octave, and so on). However, Waggle protocol does not allow flexable data length, so that the length of output data will be one array for 10 float, and one another float data which are calculated dB for each bin and total dB for the octave from 20Hz - 20kHz (a function called 'match_length()' handles the length of the data).
- Recording raw audio is added (the 'recording' in config; True - Yes recording or False - No recording). However, image pipeline cannot handle the wav form data to add metadata, and the size of the file is too big to send it through. Need to be figured out.

## Base code for spl plugin:
The python script samples 5 seconds of audio from a microphone attachend on edge-processor and calculate noise level in dBm.
The script needs **pyaudio** to read audio data, and **numpy** to do further processes as shown below. The format of recorded sound is pyaudio.paInt16, the number of channel is 1, sampling rate is 44100, each chunk length is 1024, and it records 5 seconds.

The code can get two arguments: do you want to record the raw sound from the mic (--record), and what octave band do you want (--octave; 1 octave, 1/2 octave, or 1/3 octave band). If you do not put any of the arguments, the default is 1/9 octave band, and not recording the raw. **However** waggle protocol for this spl just does not allow flexible length, so that the result is fixed to 11 values (one 10th array and a total dBm; May 2018). Also, this data uses image pipeline, the recorded wav cannot be send to beehive server. Additionally, the recorded file size is so much big, so thses issues need to be solved before send the wav to beehive.

```
if __name__ == '__main__':
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Sound Pressure Level calculation.')
    parser.add_argument('--octave', required=False,
                        default=9,
                        metavar="selected octave cycle",
                        help='Integer numer of octave cycle: \
                        [1: octave cycle, 2: 1/2 octave cycle, 3: 1/3 octave cycle, and so on..')
    parser.add_argument('--record', required=False,
                        metavar="True or False to send raw audio",
                        help='Send raw audio by packing it in image shape')
    args = parser.parse_args()

    xf, yf, N = record(args.record)
    main(args.octave, xf, yf, N)
```

When I tested the mic personally in my laptop, ```input_device_index``` was 9. But it must be specifically defined with regard
to the device index in edge-processor (the script is tested in ubuntu and mac os). The recorded sound is stored in an array.

```
import pyaudio
import numpy as np

import datetime

import wave
import time

# constants for audio recording
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5

audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,rate=RATE, input=True, frames_per_buffer=CHUNK, input_device_index=9)
#stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

def record(r):
    if r == None:
        r = False

    frames = []

    # Recording audio from the input device
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(np.frombuffer(data, dtype=np.int16))
    
    if bool(r) == True:
        file_name = "audio_{:%Y%m%dT%H%M%S}.wav".format(datetime.datetime.now())
        waveFile = wave.open(file_name, 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()

    print("format: ", audio.get_sample_size(FORMAT))
    print("chunk: ", CHUNK)

    # Change data format from audio to np.array
    numpydata = np.hstack(frames)
    times = np.arange(len(numpydata))/float(RATE)

    N = numpydata.shape[0] # the total number of samples: 10 sec * 44100 sampling rate
    T = 1.0 / RATE # a unit time for each sample: 44100 samples per a second

    yf = np.fft.fftn(numpydata) # the n-dimensional FFT
    xf = np.linspace(0.0, 1.0/(2.0*T), N//2) # 1.0/(2.0*T) = RATE / 2

    return xf, yf, N

```
According to the input argument --octave, upper octave cycle, which are an array of upper octave frequency is determined. 

```
def cal_upper_oct(octv):
    n = 5 * octv + (octv - 1) + 10
    m = 4 * octv + 10

    center = []
    for i in reversed(range(n)):
        c = 1000/2**((i+1)/octv)
        if c > 20:
            center.append(round(c, 4))
    center.append(1000)
    for i in range(m):
        c = 1000*2**((i+1)/octv)
        if c < 22000:
            center.append(round(c, 4))

    upper_octave_cycle = []
    for i in range(len(center)):
        u = center[i]*2**(1/(octv*2))
        if len(upper_octave_cycle) < (octv * 10):
            upper_octave_cycle.append(round(u, 4))
    lower_octave_cycle = []
    for i in range(len(center)):
        l = center[i]/2**(1/(octv*2))
        if len(lower_octave_cycle) < (octv * 10):
            lower_octave_cycle.append(round(l, 4))

    return lower_octave_cycle, center, upper_octave_cycle
```

After the upper octave cycle is calculated and the recorded data is fft processed, real numbers of fft result are sorted out with regards to the frequency range. Each bins of data are averaged, calculated into dBm, and saved into avg_db. With the avg_db, total dBm of sound pressure level is calculated. 
```
def main(octv, xf, yf, N):
    if octv == None:
        octv = 1
    else:
        octv = int(octv)

    low, center, upper_octave_cycle = cal_upper_oct(octv)

    octave = {}
    avg = []
    for i in range(len(upper_octave_cycle)):
        octave[i] = []

    val = yf[0:N//2]
    
    for hz, magnitude in zip(xf, val):
        if hz < 20:
            continue
        index = np.searchsorted(upper_octave_cycle, hz, side="left")
        if index >= len(upper_octave_cycle):
            continue
        octave[index].append(magnitude)

    for di in range(len(octave)):
        if len(octave[di]) == 0:
            avg.append(1)
            continue
        avg.append(sum(octave[di])/len(octave[di]))

    avg = np.asarray(avg)
    avgdb = 10*np.log10(np.abs(avg))

    a = []
    b = 0
    for ia in range(len(avg)):
        a.append(10**(avgdb[ia]/10))
        b = b + a[ia]

    sdb = 10*np.log10(b)

    print(low, '\n')
    print(center, '\n')
    print(upper_octave_cycle, '\n')
    print(avgdb, sdb)
    # print(len(avgdb), sdb)

    # sdb --> addtion of SPL, avgdb --> average of each octave



```

The average dBm for each bin are used to calculate sound pressure level (SPL) of recorded sound with regards of 
Adding acoustic levels of sound sources: http://www.sengpielaudio.com/calculator-spl.htm, and http://www.sengpielaudio.com/calculator-spl30.htm.

And upper frequency for octave cycle is refered: https://courses.physics.illinois.edu/phys406/sp2017/Lab_Handouts/Octave_Bands.pdf


### Result values:
avgdb (1x10 array) and sdb (single value) are the results of the calculation. Those values need to be return back to DBs 
using image pipeline (May 2018).

