
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('midifile',help='The midi file to generate guitar tracks from')
parser.add_argument('instruments',help='Names of MIDI instruments within the midi file to use for guitar track generation')
parser.add_argument('--ksw-open-pluck',nargs='?',const=0,default=0,type=int,help='Midi note that switches articulation to unmuted plucking')
parser.add_argument('--ksw-muted-pluck',nargs='?',const=1,default=1,type=int,help='Midi note that switches articulation to muted plucking')
parser.add_argument('--ksw-tap',nargs='?',const=2,default=2,type=int,help='Midi note that switches articulation to finger tapping')
parser.add_argument('--attack-cut',nargs='?',const=7.0,default=7.0,type=float,help='Amount of attack to cut notes by, in milliseconds. Increase if picking sounds too hard, decrease if too soft.')
parser.add_argument('--centroid-tolerance',nargs='?',const=10.0,default=0,type=float,help='Permitted difference between a sample\'s spectral centroid and the previous sample\'s spectral centroid. Increasing will result in greater diversity of samples selected, but will result in decreased realism.')
parser.add_argument('--midi-pitch-offset',nargs='?',const=0,default=0,type=int,help='Used if midi file is rendered at a higher or lower pitch than it should be. Only change if keyswitches are undetected.')
parser.add_argument('--output-filenames',nargs='?',const='',default='',type=str,help='Specify names of output .wav files, separated by commas. Must be same length as instruments argument.')
parser.add_argument('--metadata-file-name',nargs='?',const='metadataV2',default='metadataV2',type=str,help='Filename to store sample metadata in.')
#parser.parse_args()
args={}
for arg,value in parser.parse_args()._get_kwargs():
    if value!=None:
        print(arg,value)
        args[arg]=value
    
from lib_gtss import*
gtss=GTSS(midi_pitch_offset=int(args['midi_pitch_offset']))