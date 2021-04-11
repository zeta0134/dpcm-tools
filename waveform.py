# note: all generator functions accept a delta-time, and have a period of 1.0
# all functions are centered around 0.5, and attempt to produce an amplitude
# of around 0.5. The result may be biased, so that the waveform starts and
# ends close to 0.5.

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

def sawtooth(dt):
    return (dt + 0.5) % 1.0

def sine(dt):
    return (math.sin(dt * 2.0 * math.pi) + 1.0) / 2.0

def sample(generator, sample_index, frequency, playback_rate):
    dt = sample_index * frequency / playback_rate;
    return generator(dt)



