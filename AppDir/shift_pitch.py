import numpy as np
import pyrubberband as rb
from librosa.effects import pitch_shift

def lrps(audio,pitch_change,sr):
	audio= audio.astype('float64')
	return pitch_shift(audio,sr,n_steps=pitch_change,res_type='fft')

def rbps(audio,pitch_change,sr,coef=19800):
	return coef*rb.pitch_shift(audio,sr,pitch_change,rbargs={'-c':0})

def ShiftPitch(audio,pitch_change,function=rbps,sr=44100):
	return function(audio,pitch_change,sr)

def TimeStretch(audio,stretch,sr=44100):
	print(stretch,sr)
	return rb.time_stretch(audio,sr,stretch)
