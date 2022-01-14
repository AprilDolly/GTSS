#!/usr/bin/python3
from pretty_midi import PrettyMIDI,Instrument
import numpy as np
import os
import pickle
import json
from gtss_helpers import*
from audio_features import*
from librosa import note_to_hz
from scipy import signal
import warnings
import logging
from midi_preprocess import*
from pydub import AudioSegment
from pydub import effects
from shift_pitch import *
from sklearn.preprocessing import normalize
import soundfile


class GTSS:
	class GuitarSample:
		class RenderParams:
			def __init__(self):
				self.pitch_change = 0
				self.new_length = 0
				self.attack_change = 0
				self.stretch=0
				self.start=0
				self.end=0
				self.velocity=0
		def initialize_render_params(self):
			self.render_params=self.RenderParams()
		def __init__(self,sample_path):
			self.path=sample_path
			#self.render_params=self.RenderParams()
		def generate_metadata(self):
			#generate all the metadata used for sample selection
			with warnings.catch_warnings():
				warnings.simplefilter('ignore')
				sample_path=self.path
				sample_params=os.path.splitext(os.path.basename(sample_path))[0].split('_')
				data,rate=soundfile.read(sample_path)
				self.length=float(len(data))/float(rate)
				self.pitch=note_to_pitch(sample_params[0])
				modes=sample_params[1].split(',')
				self.pick_mode=modes[0]
				self.fret_mode_args=None
				self.fret_mode=None
				if len(modes)>1:
					self.fret_mode=modes[1]
					if len(modes)>2:
						self.fret_mode_args=modes[2]
				self.is_fallback=False
				if sample_params[2]=='fallback':
					self.is_fallback=True
				self.attack=get_pick_attack_len(sample_path)
				self.tf0=note_to_hz(sample_params[0].replace('s','#'))
				self.centroid=get_avg_spectral_centroid(sample_path)
				self.centroid_offset=self.centroid-self.tf0
				self.f0=fundamental_frequency(sample_path,self.tf0)
				self.adf0=np.abs(self.tf0-self.f0)
				self.tuning_correction=12*np.log2(self.tf0-self.f0)
				if self.tuning_correction>0.6 or np.isnan(self.tuning_correction):
					#don't want pitch of palm-muted notes to be all over the place lol
					self.tuning_correction=0
		def dump_metadata(self):
			#dump metadata to a more storable format
			return self.__dict__
		def load_metadata(self,metadata):
			self.__dict__.update(metadata)
	def dummy(self,*args):
		pass
	def __init__(self,samples_directory='guitar_samples',metadata_file_name='metadataV2',attack_cut=7.0,midi_pitch_offset=0,centroid_tolerance=10.0,ksw_table={'pickmode':{0:'open',1:'mute',2:'tap'},'fretmode':{3:'pc'}},reset_period=10,appimage=False,selection_updater=None,render_updater=None,track_updater=None):
		#look for samples metadata file first, if none then create
		self.samples_directory=samples_directory
		self.metadata_file_name=metadata_file_name
		self.ksw_table=ksw_table
		self.midi_pitch_offset=midi_pitch_offset
		self.centroid_tolerance=centroid_tolerance
		self.attack_cut=attack_cut/1000.0#in milliseconds
		self.appimage=appimage
		self.pitch_warning_given=False
		self.used_pairs=[]
		self.selection_updater=selection_updater
		self.render_updater=render_updater
		self.track_updater=track_updater
		self.reset_period=reset_period
		if self.selection_updater==None:
			self.selection_updater=self.dummy
		if self.render_updater==None:
			self.render_updater=self.dummy
		if self.track_updater==None:
			self.track_updater=self.dummy
		if not os.path.exists(os.path.join(samples_directory,metadata_file_name)):
			#read sample data and generate metadata file
			print('No metadata file exists. Generating...')
			self.generate_sample_metadata()
			print('Metadata generation finished.')
		else:
			#load samples metadata from file
			print('Loading sample metadata')
			self.load_sample_metadata()
			pass
		self.attack_slope,self.attack_intercept=attack_model(self.samples)
	def generate_sample_metadata(self):
		sample_subdirectories=os.listdir(self.samples_directory)
		samples_metadata=[]
		self.samples=[]
		atk_len_data=[]
		for dir in sample_subdirectories:
			dir=os.path.join(self.samples_directory,dir)
			if os.path.isdir(dir):
				sample_paths=os.listdir(dir)
				for sample_path in sample_paths:
					sample_path=os.path.join(dir,sample_path)
					if os.path.splitext(sample_path)[1]=='.wav':
						#sample file found! load sample and generate metadata
						new_sample=self.GuitarSample(sample_path)
						print('Generating metadata for {}'.format(sample_path))
						new_sample.generate_metadata()
						self.samples.append(new_sample)
						sample_dict=new_sample.dump_metadata()
						samples_metadata.append(sample_dict)
						atk_len_data.append([new_sample.length,new_sample.attack])
		f=open(os.path.join(self.samples_directory,self.metadata_file_name),'w')
		f.write(json.dumps(samples_metadata))
		f.close()
		
	def load_sample_metadata(self):
		f=open(os.path.join(self.samples_directory,self.metadata_file_name),'r')
		metadata_json=f.read()
		f.close()
		self.samples=[]
		sample_dicts=json.loads(metadata_json)
		for d in sample_dicts:
			loaded_sample=self.GuitarSample(d['path'])
			loaded_sample.load_metadata(d)
			self.samples.append(loaded_sample)
		print('{} samples loaded.'.format(len(self.samples)))
		
	
	def preprocess_midi_sequence(self,midi_file,target_inst_name,ksw_shift=0.01):
		mid=PrettyMIDI(midi_file)
		inst_found=False
		for inst in mid.instruments:
			if inst.name==target_inst_name:
				inst_found=True
				target_inst=inst
		
		if inst_found==False:
			target_inst=mid.instruments[0]
		for i,note in enumerate(target_inst.notes):
			target_inst.notes[i].pitch+=self.midi_pitch_offset
		target_inst.notes=sorted(target_inst.notes,key=lambda v: v.start)
		def shift_ksw():
			for i in range(len(target_inst.notes)):
				note=target_inst.notes[i]
				str_pitch=str(note.pitch)
				if (str_pitch in self.ksw_table['pickmode'].keys() or str_pitch in self.ksw_table['fretmode'].keys()) and note.start-ksw_shift>0:
					target_inst.notes[i].start-=ksw_shift
					target_inst.notes[i].end-=ksw_shift
		shift_ksw()
		target_inst=power_chord_substitution(target_inst,self.ksw_table)
		shift_ksw()
		target_inst.notes=sorted(target_inst.notes,key=lambda v: v.start)
		return target_inst
	
	def select_samples(self,inst,initial_mode='open'):
		self.render_updater(0,10)
		self.current_pick_mode='open'
		self.current_fret_mode=None
		self.last_note=inst.notes[0]
		self.last_sample=None
		self.exclude=[]
		self.last_pitch=0
		chosen_samples=[]
		for note in inst.notes:
			str_pitch=str(note.pitch)
			if str_pitch in self.ksw_table['pickmode'].keys() and self.current_pick_mode==None:
				self.current_pick_mode=self.ksw_table['pickmode'][str_pitch]
			elif str_pitch in self.ksw_table['fretmode'].keys() and self.current_fret_mode==None:
				self.current_fret_mode=self.ksw_table['fretmode'][str_pitch]
			elif self.current_pick_mode!=None and self.current_fret_mode!=None:
				break
		for i,note in enumerate(inst.notes):
			str_pitch=str(note.pitch)
			if str_pitch in self.ksw_table['pickmode'].keys():
				self.current_pick_mode=self.ksw_table['pickmode'][str_pitch]
			elif str_pitch in self.ksw_table['fretmode'].keys():
				self.current_fret_mode=self.ksw_table['fretmode'][str_pitch]
			else:
				print(note.pitch,self.current_fret_mode,self.current_pick_mode)
				self.last_note_difference=0.0
				if self.last_note!=None:
					self.last_note_difference=note.start-self.last_note.end
				#shit this is going to be hard
				chosen_sample=choose_sample(self,note)
				if chosen_sample==None:
					print('could not find sample for',note)
				else:
					print(chosen_sample.path,chosen_sample.pitch)
					print(chosen_sample.render_params.pitch_change)
				self.current_fret_mode=None
				self.used_pairs.append((chosen_sample.path,chosen_sample.render_params.start))
				chosen_samples.append(chosen_sample)
				self.last_sample=chosen_sample
				self.selection_updater(i,len(inst.notes))
		self.selection_updater(len(inst.notes),len(inst.notes))
		return chosen_samples
	
	def render_sample_sequence(self,sequence,normalize_to_velocity=True,normalized_coef=15.,export_coef=1.):
		rendered=None
		for i,sample in enumerate(sequence):
			#print('adding {}/{} samples'.format(i+1,len(sequence)))
			
			segment=AudioSegment.from_file(sample.path)
			target_frame_count=int(sample.render_params.new_length*segment.frame_rate)
			attack_adjustment=int(sample.render_params.attack_change*segment.frame_rate)
			frames=np.array(segment.get_array_of_samples()[attack_adjustment:target_frame_count+attack_adjustment],dtype=float)
			
			frames=normalize(frames.reshape(1,-1)).ravel()
			start_pos=int(sample.render_params.start*segment.frame_rate)
			if sample.is_fallback:
				sample.render_params.pitch_change+=sample.tuning_correction
			if sample.render_params.pitch_change!=0:
				try:
					frames=ShiftPitch(frames,sample.render_params.pitch_change,function=rbps)
				except RuntimeError:
					if not self.pitch_warning_given:
						self.pitch_warning_given=True
						print('rubberband-cli not found. Falling back on librosa for pitch manipulation.')
					frames=ShiftPitch(frames,sample.render_params.pitch_change,function=lrps)
			if normalize_to_velocity:
				frames=frames/np.linalg.norm(frames)*(sample.render_params.velocity/127)*normalized_coef
			frames=np.concatenate((np.zeros(start_pos,dtype=float),frames))
			try:
				len(rendered)
			except:
				rendered=np.zeros(len(frames),dtype=float)
			rendered=add_arrays([rendered,frames])
			self.render_updater(i,len(sequence))
		filter=signal.butter(10,300.,btype='hp',fs=44100,output='sos')
		rendered=signal.sosfilt(filter,rendered)
		return rendered*export_coef
	def backup_output(self,filename,audio):
		if os.path.exists(filename):
			os.remove(filename)
		f=open('{}.bak'.format(filename),'wb')
		pickle.dump(audio,f)
		f.close()
	def load_backup(self,filename):
		f=open('{}.bak'.format(filename),'rb')
		audio=pickle.load(f)
		f.close()
		return audio
	def render_sequence_to_file(self,sequence,filename,sr=44100,sw=2):
		print('Rendering {} ...'.format(filename))
		audio=self.render_sample_sequence(sequence)
		#self.backup_output(filename,audio)
		soundfile.write(filename,audio,sr)#,sampwidth=sw)
		print('Render of {} finished.'.format(filename))
		self.track_updater()
		
if __name__=='__main__':
	print(os.getcwd())
	gtss=GTSS(midi_pitch_offset=-12,appimage=True)
	inst=gtss.preprocess_midi_sequence('example.mid','lgtS')
	seq=gtss.select_samples(inst)
	gtss.render_sequence_to_file(seq,'example.wav')
