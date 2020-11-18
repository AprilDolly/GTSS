GTSS (Guitar SuperSystem) is a tool that allows you to create somewhat realistic-sounding guitar tracks from midi files.

To use:
1) Extract guitar_samples.7z001,002,003.
2) Install the dependencies listed in requirements.txt
3) Run gtss_main.py to launch GTSS.
4) After that, hit OK, load up your midi, select the instruments you want to render from your midi, and start rendering!

Midi creation:
GTSS currently supports 3 articulations: open plucking, palm mute plucking, and tapping.
In order to use these, you must place keyswitch notes in your midi alongside the melodies that you create.
The default keyswitches are:
Note 0: open
Note 1: mute
Note 3: tap
These can be changed in the configuration menu.
If you are confused about how this works, examine example.mid in your midi sequencer, and try to render a guitar track from it.

If you have any problems, send an email to aprildolly@mail.com or message u/aprildoll on Reddit.
