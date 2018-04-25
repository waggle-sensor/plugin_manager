#! /usr/bin/python3

import time
import json
import argparse

import pyaudio
import numpy as np

from waggle.pipeline import Plugin
from waggle.protocol.v5.encoder import encode_frame


def get_default_configuration():
    default_config = {
        # TODO: There should be better way to find Waggle microphone
        'audio_name': 'USB PnP Sound Device:',
        'audio_channels': 1,
        'audio_rate': 44100,
        'audio_chunk': 1024,
        'sampling_period': 5,  # in Second
        'interval': 60,  # 1 minute
    }
    return default_config


class SoundPressureLevel(Plugin):
    plugin_name = 'spl'
    plugin_version = '0'

    def __init__(self, hrf=False, node_id='NO_ID'):
        super().__init__()
        self.config = self._get_config_table()
        self.hrf = hrf
        self.audio_name = self.config['audio_name']
        self.audio_format = pyaudio.paInt16
        self.audio_channels = self.config['audio_channels']
        self.audio_rate = self.config['audio_rate']
        self.audio_chunk = self.config['audio_chunk']
        self.audio_sampling_seconds = self.config['sampling_period']
        self.total_count = int(self.audio_rate / self.audio_chunk * self.audio_sampling_seconds)

    def _get_config_table(self):
        config_file = '/wagglerw/waggle/audio_spl.conf'
        config_data = None
        try:
            with open(config_file) as config:
                config_data = json.loads(config.read())
        except Exception:
            config_data = get_default_configuration()
            with open(config_file, 'w') as config:
                config.write(json.dumps(config_data, sort_keys=True, indent=4))
        return config_data

    def _read_callback(self, in_data, frame_count, time_info, status):
        self.frames.append(np.frombuffer(in_data, dtype=np.int16))
        self.frame_count += 1
        if self.frame_count >= self.total_count:
            return (in_data, pyaudio.paComplete)
        else:
            return (in_data, pyaudio.paContinue)

    def _open_and_read(self):
        audio = pyaudio.PyAudio()
        device_count = audio.get_device_count()
        device_index = -1

        for i in range(device_count):
            device_info = audio.get_device_info_by_index(i)
            if self.audio_name in device_info['name']:
                device_index = device_info['index']
                break

        if device_index < 0:
            audio.terminate()
            return False, 'Failed to find Waggle microphone'

        stream = audio.open(
            format=self.audio_format,
            channels=self.audio_channels,
            rate=self.audio_rate,
            input=True,
            frames_per_buffer=self.audio_chunk,
            input_device_index=device_index,
            stream_callback=self._read_callback)

        self.frames = []
        self.frame_count = 0
        error_code = 1
        try:
            stream.start_stream()
            # Give it 30 more seconds as timeout
            for i in range(self.audio_sampling_seconds + 30):
                if self.frame_count >= self.total_count:
                    error_code = 0
                    break
                time.sleep(1)
        except Exception as ex:
            return False, str(ex)
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
        len(self.frames)
        if error_code == 0:
            return True, self.frames
        else:
            return False, 'Timeout on data collection'

    def close(self):
        pass

    def _do_process(self):
        f, raw_data = self._open_and_read()
        if f is False:
            raise Exception(raw_data)
        print('Received frame')
        numpydata = np.hstack(raw_data)

        number_of_samples = numpydata.shape[0]
        time_per_sample = 1.0 / self.audio_rate

        yf = np.fft.fftn(numpydata)  # the n-dimensional FFT
        xf = np.linspace(0.0, 1.0 / (2.0 * time_per_sample), number_of_samples // 2)  # 1.0/(2.0*T) = RATE / 2

        octave = {}
        avg = []
        for i in range(10):
            octave[i] = []

        val = yf[0:number_of_samples // 2]
        octaves_upper_hz = [44, 88, 176, 353, 707, 1414, 2825, 5650, 11300, 22000]
        for hz, magnitude in zip(xf, val):
            if hz < 20:
                continue
            index = np.searchsorted(octaves_upper_hz, hz, side="left")
            if index >= 10:
                continue
            octave[index].append(magnitude)

        for di in range(len(octave)):
            avg.append(sum(octave[di]) / len(octave[di]))

        avg = np.asarray(avg)
        avg_db = 10 * np.log10(np.abs(avg))

        total = 0.
        for ia in range(len(avg)):
            total = total + 10 ** (avg_db[ia] / 10)

        sdb = 10 * np.log10(total)

        if self.hrf:
            sensor_name = 'audio_spl_octave'
            for i, db in enumerate(avg_db):
                print('%s%d %f' % (sensor_name, i + 1, db))
            print('%s_total %f' % (sensor_name, sdb))
        else:
            avg_db = np.append(avg_db, sdb)
            packet = {
                0x93: avg_db.tolist()
            }
            binary_packet = encode_frame(packet)
            self.send(sensor='', data=binary_packet)

    def run(self):
        while True:
            self._do_process()
            time.sleep(self.config['interval'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--hrf', action='store_true', help='Print in human readable form')
    args = parser.parse_args()

    plugin = SoundPressureLevel.defaultConfig()
    plugin.hrf = args.hrf
    try:
        plugin.run()
    except (KeyboardInterrupt, Exception) as ex:
        print(str(ex))
    finally:
        plugin.close()
