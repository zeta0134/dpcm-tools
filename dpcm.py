import midi
import math

# note: sensible indexes here range from 0-255
def patch_bytes(length_index):
	return 16 * length_index + 1

def patch_samples(length_index):
	return patch_bytes(length_index) * 8

def phase_offset(length_index, target_frequency, playback_rate):
	patch_delta = patch_samples(length_index) / playback_rate
	frequency_delta = 1 / target_frequency
	return (patch_delta % frequency_delta) * target_frequency

def tuning_error(length_index, target_frequency, playback_rate):
    return 0.5 - abs(phase_offset(length_index, target_frequency, playback_rate) - 0.5)

def repetitions(length_index, target_frequency, playback_rate):
    samples = patch_samples(length_index)
    return round(samples / (playback_rate / target_frequency), 0)

def effective_frequency(length_index, repetitions, playback_rate):
    samples = patch_samples(length_index)
    return playback_rate / (samples / max(repetitions,1))

def dpcm_level(pcm_sample):
  clamped_dpcm_level = int(max(0, min(127, pcm_sample / 2.0)))
  return clamped_dpcm_level

def pack_dpcm_bits_into_bytes(bit_array):
  while len(bit_array) % 8 != 0:
    # oscillate the appended sample, so we don't move too far from the last position in the real data
    bit_array.append(len(bit_array) % 2)
  byte_array = []
  while len(bit_array) > 0:
    byte_value = 0
    for i in range(0,8):
      byte_value += bit_array.pop(0) << i
    byte_array.append(byte_value)
  return bytes(byte_array)

def to_dpcm(pcm_samples):
  current_dpcm_level = dpcm_level(pcm_samples[0])
  dpcm_levels = map(dpcm_level, pcm_samples)
  dpcm_bits = []
  for target_level in dpcm_levels:
    if target_level > current_dpcm_level:
      dpcm_bits.append(1)
      current_dpcm_level += 2
    else:
      dpcm_bits.append(0)
      current_dpcm_level -= 2
  return pack_dpcm_bits_into_bytes(dpcm_bits)

playback_rate = [None] * 16
playback_rate[0x0] = 4181.71
playback_rate[0x1] = 4709.93
playback_rate[0x2] = 5264.04
playback_rate[0x3] = 5593.04
playback_rate[0x4] = 6257.95
playback_rate[0x5] = 7046.35
playback_rate[0x6] = 7919.35
playback_rate[0x7] = 8363.42
playback_rate[0x8] = 9419.86
playback_rate[0x9] = 11186.1
playback_rate[0xA] = 12604.0
playback_rate[0xB] = 13982.6
playback_rate[0xC] = 16884.6
playback_rate[0xD] = 21306.8
playback_rate[0xE] = 24858.0
playback_rate[0xF] = 33143.9

equivalency = [None] * 16
equivalency[0xE] = midi.note_index("C4") - midi.note_index("G3")
equivalency[0xD] = midi.note_index("G3") - midi.note_index("E3")
equivalency[0xC] = midi.note_index("E3") - midi.note_index("C3")
equivalency[0xB] = midi.note_index("C3") - midi.note_index("A2")
equivalency[0xA] = midi.note_index("A2") - midi.note_index("G2")
equivalency[0x9] = midi.note_index("G2") - midi.note_index("F2")
equivalency[0x8] = midi.note_index("F2") - midi.note_index("D2")
equivalency[0x7] = midi.note_index("D2") - midi.note_index("C2")
equivalency[0x6] = midi.note_index("C2") - midi.note_index("B1")
equivalency[0x5] = midi.note_index("B1") - midi.note_index("A1")
equivalency[0x4] = midi.note_index("A1") - midi.note_index("G1")
equivalency[0x3] = midi.note_index("G1") - midi.note_index("F1")
equivalency[0x2] = midi.note_index("F1") - midi.note_index("E1")
equivalency[0x1] = midi.note_index("E1") - midi.note_index("D1")
equivalency[0x0] = midi.note_index("D1") - midi.note_index("C1")
