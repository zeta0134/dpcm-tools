import midi
import math
import collections

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

def safe_amplitude(target_frequency, playback_rate):
    period_in_samples = playback_rate / target_frequency
    # DPCM level adjuster is +2 or -2 with a range from 0-127, meaning it can go from
    # min to max over the course of ~around~ 64 samples. To go bottom to top and down again
    # is ~around~ 128 samples total. Fudge this just slightly, to provide some headeroom.
    maximum_theoretical_amplitude = period_in_samples / 128
    safer_theoretical_amplitude = maximum_theoretical_amplitude * 0.9
    return min(1.0, safer_theoretical_amplitude)

def dpcm_level(pcm_sample):
  #clamped_dpcm_level = int(max(0, min(127, pcm_sample / 2.0)))
  #return clamped_dpcm_level
  return pcm_sample / 2.0

def pack_dpcm_bits_into_bytes(bit_array):
  # pad the bit array out to one complete byte
  while len(bit_array) % 8 != 0:
    # oscillate the appended sample, so we don't move too far from the last position in the real data
    bit_array.append(len(bit_array) % 2)
  # here go from list -> deque, which has MUCH faster pop performance
  bit_array = collections.deque(bit_array)
  byte_array = []
  while len(bit_array) > 0:
    byte_value = 0
    for i in range(0,8):
      byte_value += bit_array.popleft() << i
    byte_array.append(byte_value)
  return bytes(byte_array)

def unpack_bytes_into_bits(byte_array):
  bit_array = []
  while len(byte_array) > 0:
    byte_value = byte_array.pop(0)
    for i in range(0,8):
      bit_array.append((byte_value & (1 << i)) >> i)
  return bit_array

def to_dpcm(pcm_samples, starting_level=None):
  current_dpcm_level = dpcm_level(pcm_samples[0])
  if starting_level != None:
    current_dpcm_level = starting_level
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

def bias(dpcm_bytes):
  bit_array = unpack_bytes_into_bits(list(dpcm_bytes))
  current_dpcm_level = 0 # signed, also we don't care about range for this
  while len(bit_array) > 0:
    sample = bit_array.pop(0)
    if sample == 1:
      current_dpcm_level += 2
    else:
      current_dpcm_level -= 2
  return current_dpcm_level


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

ntsc_equivalency = [None] * 16
ntsc_equivalency[0xE] = midi.note_index("C4") - midi.note_index("G3")
ntsc_equivalency[0xD] = midi.note_index("G3") - midi.note_index("E3")
ntsc_equivalency[0xC] = midi.note_index("E3") - midi.note_index("C3")
ntsc_equivalency[0xB] = midi.note_index("C3") - midi.note_index("A2")
ntsc_equivalency[0xA] = midi.note_index("A2") - midi.note_index("G2")
ntsc_equivalency[0x9] = midi.note_index("G2") - midi.note_index("F2")
ntsc_equivalency[0x8] = midi.note_index("F2") - midi.note_index("D2")
ntsc_equivalency[0x7] = midi.note_index("D2") - midi.note_index("C2")
ntsc_equivalency[0x6] = midi.note_index("C2") - midi.note_index("B1")
ntsc_equivalency[0x5] = midi.note_index("B1") - midi.note_index("A1")
ntsc_equivalency[0x4] = midi.note_index("A1") - midi.note_index("G1")
ntsc_equivalency[0x3] = midi.note_index("G1") - midi.note_index("F1")
ntsc_equivalency[0x2] = midi.note_index("F1") - midi.note_index("E1")
ntsc_equivalency[0x1] = midi.note_index("E1") - midi.note_index("D1")
ntsc_equivalency[0x0] = midi.note_index("D1") - midi.note_index("C1")

pal_safe_equivalency = [None] * 16
pal_safe_equivalency[0xD] = midi.note_index("C4") - midi.note_index("E3")
pal_safe_equivalency[0xC] = midi.note_index("E3") - midi.note_index("C3")
pal_safe_equivalency[0xB] = midi.note_index("C3") - midi.note_index("A2")
pal_safe_equivalency[0xA] = midi.note_index("A2") - midi.note_index("G2")
pal_safe_equivalency[0x9] = midi.note_index("G2") - midi.note_index("F2")
pal_safe_equivalency[0x8] = midi.note_index("F2") - midi.note_index("D2")
pal_safe_equivalency[0x7] = midi.note_index("D2") - midi.note_index("C2")
pal_safe_equivalency[0x6] = midi.note_index("C2") - midi.note_index("B1")
pal_safe_equivalency[0x5] = midi.note_index("B1") - midi.note_index("A1")
pal_safe_equivalency[0x3] = midi.note_index("A1") - midi.note_index("F1")
pal_safe_equivalency[0x2] = midi.note_index("F1") - midi.note_index("E1")
pal_safe_equivalency[0x1] = midi.note_index("E1") - midi.note_index("D1")
pal_safe_equivalency[0x0] = midi.note_index("D1") - midi.note_index("C1")

# in cents, compared to rate + $1
repitching_error = [None] * 16
repitching_error[0xE] = 2.0
repitching_error[0xD] = 33.1
repitching_error[0xC] = -2.7
repitching_error[0xB] = -26.5
repitching_error[0xA] = 20.3
repitching_error[0x9] = -6.6
repitching_error[0x8] = 2.5
repitching_error[0x7] = -5.9
repitching_error[0x6] = 5.5
repitching_error[0x5] = -2.2
repitching_error[0x4] = -5.4
repitching_error[0x3] = 5.5
repitching_error[0x2] = -5.0
repitching_error[0x1] = 7.4
repitching_error[0x0] = -5.9

def cumulative_repitching_error(reference_rate, target_rate):
  if reference_rate == target_rate:
    return 0
  return sum(repitching_error[target_rate : reference_rate])