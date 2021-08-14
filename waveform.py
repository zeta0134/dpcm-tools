# note: all generator functions accept a delta-time, and have a period of 1.0
# all functions are centered around 0.5, and attempt to produce an amplitude
# of around 0.5. The result may be biased, so that the waveform starts and
# ends close to 0.5.

import math
import wave

def square(dt):
    dt = dt % 1.0
    if dt < 0.25 or dt > 0.75:
        return 0.5
    return 1.0

def triangle(dt):
    dt = dt % 1.0
    if dt < 0.25:
        return 0.5 + (2.0 * dt)
    if dt > 0.75:
        return (dt - 0.75) * 2.0
    return 1.0 - ((dt - 0.25) * 2.0)

# note: meant to be used in situations where the DPCM level shifter can't
# keep up, to generate an artificially pure triangle
def artificial_ramp(dt):
    dt = dt % 1.0
    if dt <= 0.5:
        return 2.0
    return -2.0

def sawtooth(dt):
    return (dt + 0.5) % 1.0

def sine(dt):
    return (math.sin(dt * 2.0 * math.pi) + 1.0) / 2.0

def bias(dt):
    return dt / 64.0 # baseline bias targets +1 DPCM level

def wave_file(filename):
    reader = wave.open(filename, "rb")
    sample_count = reader.getnframes()
    data = reader.readframes(sample_count)
    print("Read ", sample_count, " frames from ", filename)
    reader.close()
    def generator(dt):
        sample_index = int((dt * sample_count) % sample_count)
        return data[sample_index] / 255
    return generator

def sample(generator, sample_index, frequency, playback_rate):
    dt = sample_index * frequency / playback_rate;
    return generator(dt)



