# GTSS

GTSS (Guitar SuperSystem) is a tool that allows you to create somewhat realistic-sounding guitar tracks from midi files.

# Instructions (Linux):
1) Download and extract the repository or use git clone https://github.com/AprilDolly/GTSS.git
2) Run 'gtss' to launch GTSS.
3) Load up your midi, select the instruments you want to render from your midi, and start rendering!

# Instructions (Windows):
1) i have no idea how to get this to run on windows other than by manually installing all the python dependencies and rubberband-cli. someone help me pls

# Midi creation:
GTSS currently supports 3 articulations: open plucking, palm mute plucking, and tapping.
In order to use these, you must place keyswitch notes in your midi alongside the melodies that you create.
The default keyswitches are:
Note 0: open
Note 1: mute
Note 3: tap
These can be changed in the configuration menu.
If you are confused about how this works, examine example.mid in your midi sequencer, and try to render a guitar track from it.
