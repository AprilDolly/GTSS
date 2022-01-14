# GTSS

GTSS (Guitar SuperSystem) is a tool that allows you to create somewhat realistic-sounding guitar tracks from midi files.

# Installation:
1) [Download the latest release here.](https://github.com/AprilDolly/GTSS/releases/tag/V2.0)
2) Extract it, keep gtss-x86_64.AppImage in the same directory as the guitar_samples directory if you decide to move it somewhere else.

# Instructions
1) Run gtss-x86_64.AppImage
2) Load your rendered midi file
3) Select the number of guitar tracks to render, and the midi instruments to read notes from for each track.
4) Render and wait for it to complete. Each track will be rendered as a .wav file in the same directory as your midi file.

# Midi creation:
GTSS currently supports 3 articulations: open plucking, palm mute plucking, and tapping.
In order to use these, you must place keyswitch notes in your midi alongside the melodies that you create.
The default keyswitches are:
Note 0: open
Note 1: mute
Note 3: tap
These can be changed in the configuration menu.
If you are confused about how this works, examine example.mid in your midi sequencer, and try to render a guitar track from it.

# Configuration:
- 
