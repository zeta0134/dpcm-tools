# DPCM Tools
Zeta's tools for DPCM sample generation, targeting Ricoh 2A03. Most tools can generate both raw `.dmc` and also `.fti` instruments, for use with FamiTracker and its various forks.

## Looper

Generates looping melodic DPCM samples. Given a target note, it works out a sample length and a number of _repeats_ of a source waveform to fill out that length and get the note as close to in-tune as possible. In addition to basic shapes, a custom waveform can be provided; use 8-bit PCM in Mono for the `.wav` file.

This tool prioritizes _clean loops_, trading perfect tuning as necessary. Generated samples will vary in length, and a few notes (especially in the extreme bass) cannot be reliably tuned. The target size and acceptable tuning error can be tweaked. Don't be afraid to experiment!

```
usage: looper.py [-h] [-s DIRECTORY] [-i INSTRUMENT] [--prefix PREFIX] [-g GENERATOR] [-w WAVEFILE] [-v VOLUME]
                 [-e ERROR_THRESHOLD] [-b BIAS] [-l MAX_LENGTH] [--safe-volume | --no-safe-volume] [-d DELTA]
                 [--repitch | --no-repitch] [--fullname FULLNAME]
                 notes

Automatically generate looping DPCM samples

positional arguments:
  notes                 Notes to generate. Ex: gs2,f3-a3

optional arguments:
  -h, --help            show this help message and exit
  -s DIRECTORY, --directory DIRECTORY
                        Directory to store generated samples as .dmc
  -i INSTRUMENT, --instrument INSTRUMENT
                        FamiTracker instrument filename to generate
  --prefix PREFIX       Samples will be named [prefix]-[note] (default: filename)

Sample Generation:
  -g GENERATOR, --generator GENERATOR
                        One of: sine, square, triangle, sawtooth, wave, artificial_ramp
  -w WAVEFILE, --wavefile WAVEFILE
                        For the wave generator. Should contain one loop, like N163.
  -v VOLUME, --volume VOLUME
                        Linear volume multiplier for generated waveforms
  -e ERROR_THRESHOLD, --error-threshold ERROR_THRESHOLD
                        Prefer smaller samples within this tuning percentage (default: 0%)
  -b BIAS, --bias BIAS  Bias generated samples in this direction. (default: 0)
  -l MAX_LENGTH, --max-length MAX_LENGTH
                        Longest sample size to consider. Generally improves tuning, costs more space. (default:
                        255)
  --safe-volume, --no-safe-volume
                        Scale volume for high notes, to avoid triangle shape creep. (default: True)

FamiTracker Instruments:
  -d DELTA, --delta DELTA
                        Set the delta counter when playback begins
  --repitch, --no-repitch
                        Fill out an instrument's lower range with repitched samples (default: True)
  --fullname FULLNAME   The full name of this instrument, show in FamiTracker's UI

    Examples:
      Sawtooth, Sunsoft style:
        looper.py -g sawtooth -i sunsaw.fti as2-d3

      Half-volume triangle, positive bias:
        looper.py -g triangle -v 0.5 -b 1 -i tri-50.fti c4-c5

      Custom waveform:
        looper.py -g wave -w organ.wav -i organ.fti c4-c5
```


