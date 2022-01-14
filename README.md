# GTSS

GTSS (Guitar SuperSystem) is a tool that allows you to create somewhat realistic-sounding guitar tracks from midi files. It is mainly optimized for metal guitar playing, so it may not sound as natural through a clean amp.

### Installation
1) [Download the latest release here.](https://github.com/AprilDolly/GTSS/releases/tag/V2.0)
2) Extract it, keep gtss-x86_64.AppImage in the same directory as the guitar_samples directory if you decide to move it somewhere else.

### Usage
1) Run gtss-x86_64.AppImage
2) Click 'Open Midi File' to load a midi file, or 'Configure' to bring up the configuration menu.
3) Select the number of guitar tracks to render, and the midi instruments to read notes from for each track.
4) Render and wait for it to complete. Each track will be rendered as a .wav file in the same directory as your midi file.

### Midi creation
GTSS currently supports 3 articulations: open plucking, palm mute plucking, and tapping.
In order to use these, you must place keyswitch notes in your midi alongside the melodies that you create.<br>
The default keyswitches are:
- Note 0: open
- Note 1: mute
- Note 3: tap
These can be changed in the configuration menu.
If you are confused about how this works, examine example.mid in your midi sequencer, and try to render a guitar track from it.

### Configuration Parameters
- Articulation Keyswitch notes: Changes the midi note used to set the current articulation as described above.
- Reset period: Changes the frequency at which the record of selected samples is discarded during the sample selection process. Increasing this will lead to a greater diversity of samples used in your tracks, but may result in longer waiting time for the process to complete.
- Attack cut: The amount of time to cut off the start of all samples in addition to the regression-based attack cutting already done, in milliseconds. Increase if the picking sounds too harsh, decrease if the picking sounds too soft.
- Spectral centroid tolerance: The amount that the spectral centroid of a given sample is allowed to differ from the previously selected sample, in Hz. Increase if you want a more diverse selection of samples, decrease if it sounds like the guitarist is jumping all over the fretboard.
- pre-keyswitch pitch shift: Amount of semitones to shift all midi notes by immediately after import. Change this if your keyswitches don't work and all the notes are a higher or lower pitch than they should be. This will happen with some DAWs that export MIDI at a higher pitch than normal. For example, [LMMS](https://github.com/lmms/lmms) exports midi at an octave higher than it should be, so the pre-keyswitch pitch shift should be set to -12 when loading a midi exported from LMMS.
