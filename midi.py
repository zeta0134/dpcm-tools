import re

frequency = [
    16.35, # C0
    17.32,
    18.35,
    19.45,
    20.6,
    21.83,
    23.12,
    24.5,
    25.96,
    27.5,
    29.1,
    30.9,
    32.7,
    34.6,
    36.7,
    38.9,
    41.2,
    43.7,
    46.2,
    49,
    51.9,
    55,
    58.3,
    61.7,
    65.4,
    69.3,
    73.4,
    77.8,
    82.4,
    87.3,
    92.5,
    98,
    103.8,
    110,
    116.5,
    123.5,
    130.8,
    138.6,
    146.8,
    155.6,
    164.8,
    174.6,
    185,
    196,
    207.7,
    220,
    233.1,
    246.9,
    261.6,
    277.2,
    293.7,
    311.1,
    329.6,
    349.2,
    370,
    392,
    415.3,
    440,
    466.2,
    493.9,
    523.3,
    554.4,
    587.3,
    622.3,
    659.3,
    698.5,
    740,
    784,
    830.6,
    880,
    932.3,
    987.8,
    1046.5,
    1108.7,
    1174.7,
    1244.5,
    1318.5,
    1396.9,
    1480,
    1568,
    1661.2,
    1760,
    1864.7,
    1975.5,
    2093,
    2217.5,
    2349.3,
    2489,
    2637,
    2793.8,
    2960,
    3136,
    3322.4,
    3520,
    3729.3,
    3951.1,
]

def _note_index(letter_name, octave_number, modifier):
    letter_indices = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}
    modifiers = {'#': 1, 's': 1, 'b': -1}
    note_index = letter_indices[letter_name.lower()]
    octave_index = octave_number * 12
    modifier_offset = modifiers.get(modifier.lower(), 0)
    return octave_index + note_index + modifier_offset

def note_index(note_name):
    match = re.match(r'([A-Ga-g])([BbSs#]?)(\d+)', note_name)
    if not match:
        raise Exception("Invalid note name")
    letter_name, modifier, octave_str = match.groups()
    octave_number = int(octave_str)
    return _note_index(letter_name, octave_number, modifier)

def note_name(midi_index):
    letter_indices = ['C', 'Cs', 'D', 'Ds', 'E', 'F', 'Fs', 'G', 'Gs', 'A', 'As', 'B']
    letter = letter_indices[midi_index % 12]
    octave = str(int(midi_index / 12))
    return letter + octave

def parse_note_list(note_list_str):
    entries = note_list_str.split(",")
    note_list = []
    for entry in entries:
        notes = entry.split("-")
        if len(notes) == 1:
            note_list.append(note_index(entry))
        else:
            for i in range(note_index(notes[0]), note_index(notes[1]) + 1):
                note_list.append(i)
    return note_list