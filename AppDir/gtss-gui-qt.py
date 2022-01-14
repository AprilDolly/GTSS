#!/usr/bin/python3
from lib_gtss import*
from PyQt5.QtCore import*
from PyQt5.QtGui import*
from PyQt5.QtWidgets import*
import multiprocessing
import os
import sys

class GTSSGui(QApplication):
	class Window(QWidget):
		def __init__(self,width,height):
			super().__init__()
			self.width=width
			self.height=height
			self.setWindowTitle('GTSS')
			self.directory=os.path.dirname(os.path.abspath(__file__))
			icon_path=os.path.join(self.directory,'gtss.png')
			print(width,height)
			#self.setGeometry(width,height,width,height)
			self.setWindowIcon(QIcon(icon_path))
			self.show()
			self.main_menu()
		def default_config(self):
			default_cfg={}
			default_cfg['ksw_table']={'pickmode':{0:'open',1:'mute',2:'tap'},'fretmode':{3:'pc'}}
			default_cfg['reset_period']=10
			default_cfg['attack_cut']=7.0
			default_cfg['centroid_tolerance']=10.0
			default_cfg['pitch_shift']=0
			return default_cfg
		def load_config(self,directory=None):
			default_cfg=self.default_config()
			try:
				f=open('config','r')
				self.config=json.load(f)
				f.close()
			except:
				self.config=default_cfg
				f=open('config','w')
				json.dump(self.config,f)
				f.close()
		def main_menu(self):
			self.load_config()
			self.setGeometry(300,400,300,350)
			self.move(self.width/2-200,self.height/2-200)
			self.bg_image=QPixmap(os.path.join(self.directory,'assets/home_screen.png'))
			self.bg=QLabel(self)
			self.bg.setPixmap(self.bg_image)
			self.bg.show()
			self.file_button=QPushButton(self)
			self.file_button.setText('Open MIDI File')
			self.file_button.move(50,310)
			self.file_button.clicked.connect(self.filedialog)
			self.file_button.show()
			self.config_button=QPushButton(self)
			self.config_button.setText('Configure')
			self.config_button.move(150,310)
			self.config_button.clicked.connect(self.config_menu)
			self.config_button.show()
		def config_menu(self):
			self.cfg_locked=False
			pm_keylist=list(self.config['ksw_table']['pickmode'].keys())
			print(pm_keylist[0],pm_keylist[1],pm_keylist[2])
			self.close_main_menu()
			self.setGeometry(self.width/2-320,self.height/2-240,640,480)
			self.ksw_selection_label=QLabel(self)
			kswtext='Articulation Keyswitch Notes (0-127)\nThese are to be changed depending on the sample library you use.'
			kswtext+='\nIgnore these if you use fakeguitar.sfz'
			self.ksw_selection_label.setText(kswtext)
			self.ksw_selection_label.move(10,10)
			self.ksw_selection_label.show()
			self.open_label=QLabel(self)
			self.open_label.setText('Open Pluck')
			self.open_label.move(10,70)
			self.open_label.show()
			self.mute_label=QLabel(self)
			self.mute_label.setText('Muted Pluck')
			self.mute_label.move(10,100)
			self.mute_label.show()
			self.tap_label=QLabel(self)
			self.tap_label.setText('Tap')
			self.tap_label.move(10,130)
			self.tap_label.show()
			notelist=[]
			for i in range(128):
				notelist.append(str(i))
			self.open_selection=QComboBox(self)
			self.open_selection.addItems(notelist)
			self.open_selection.move(90,70)
			self.open_selection.setCurrentIndex(int(pm_keylist[0]))
			self.open_selection.show()
			self.mute_selection=QComboBox(self)
			self.mute_selection.addItems(notelist)
			self.mute_selection.move(90,100)
			self.mute_selection.setCurrentIndex(int(pm_keylist[1]))
			self.mute_selection.show()
			self.tap_selection=QComboBox(self)
			self.tap_selection.addItems(notelist)
			self.tap_selection.move(90,130)
			self.tap_selection.setCurrentIndex(int(pm_keylist[2]))
			self.tap_selection.show()
			self.period_label=QLabel(self)
			self.period_label.setText('Reset period (higher number==greater sample diversity)')
			self.period_label.move(10,170)
			self.period_label.show()
			self.period_field=QLineEdit(self)
			self.period_field.setText(str(self.config['reset_period']))
			self.period_field.textChanged.connect(self.update_config)
			self.period_field.move(10,190)
			self.period_field.show()
			self.atk_label=QLabel(self)
			self.atk_label.move(10,220)
			self.atk_label.setText('Attack cut in milliseconds (increase if picking is to loud, decrease if too soft)')
			self.atk_label.show()
			self.atk_field=QLineEdit(self)
			self.atk_field.move(10,240)
			self.atk_field.setText(str(self.config['attack_cut']))
			self.atk_field.textChanged.connect(self.update_config)
			self.atk_field.show()
			self.centroid_label=QLabel(self)
			self.centroid_label.setText('Spectral centroid tolerance (Hz, lower number==more accurate sample harmonics)')
			self.centroid_label.move(10,270)
			self.centroid_label.show()
			self.centroid_field=QLineEdit(self)
			self.centroid_field.setText(str(self.config['centroid_tolerance']))
			self.centroid_field.textChanged.connect(self.update_config)
			self.centroid_field.move(10,290)
			self.centroid_field.show()
			self.pitch_label=QLabel(self)
			self.pitch_label.setText('pre-keyswitch pitch shift (semitones, change if your DAW exports midi at a higher/lower pitch than normal)')
			self.pitch_label.move(10,320)
			self.pitch_label.show()
			self.pitch_field=QLineEdit(self)
			self.pitch_field.setText(str(self.config['pitch_shift']))
			self.pitch_field.textChanged.connect(self.update_config)
			self.pitch_field.move(10,340)
			self.pitch_field.show()
			self.ok=QPushButton(self)
			self.ok.setText('Ok')
			self.ok.clicked.connect(self.save_config_and_exit)
			self.ok.move(10,400)
			self.ok.show()
			self.apply=QPushButton(self)
			self.apply.setText('Apply')
			self.apply.move(110,400)
			self.apply.clicked.connect(self.apply_config)
			self.apply.show()
			self.reset_config=QPushButton(self)
			self.reset_config.setText('Reset to Defaults')
			self.reset_config.clicked.connect(self.reset_to_defaults)
			self.reset_config.move(210,400)
			self.reset_config.show()
			self.cancel=QPushButton(self)
			self.cancel.setText('Cancel')
			self.cancel.clicked.connect(self.exit_config_menu)
			self.cancel.move(340,400)
			self.cancel.show()
		def save_config_and_exit(self):
			self.apply_config()
			self.exit_config_menu()
		def exit_config_menu(self):
			self.ksw_selection_label.hide()
			self.open_label.hide()
			self.mute_label.hide()
			self.tap_label.hide()
			self.open_selection.hide()
			self.mute_selection.hide()
			self.tap_selection.hide()
			self.period_label.hide()
			self.period_field.hide()
			self.atk_label.hide()
			self.atk_field.hide()
			self.centroid_label.hide()
			self.centroid_field.hide()
			self.pitch_label.hide()
			self.pitch_field.hide()
			self.ok.hide()
			self.apply.hide()
			self.reset_config.hide()
			self.cancel.hide()
			
			self.ksw_selection_label.deleteLater()
			self.open_label.deleteLater()
			self.mute_label.deleteLater()
			self.tap_label.deleteLater()
			self.open_selection.deleteLater()
			self.mute_selection.deleteLater()
			self.tap_selection.deleteLater()
			self.period_label.deleteLater()
			self.period_field.deleteLater()
			self.atk_label.deleteLater()
			self.atk_field.deleteLater()
			self.centroid_label.deleteLater()
			self.centroid_field.deleteLater()
			self.pitch_label.deleteLater()
			self.pitch_field.deleteLater()
			self.ok.deleteLater()
			self.apply.deleteLater()
			self.reset_config.deleteLater()
			self.cancel.deleteLater()
			
			self.main_menu()
		def apply_config(self):
			f=open('config','w')
			json.dump(self.config,f)
			f.close()
			self.update_config_widgets()
		def reset_to_defaults(self):
			self.cfg_locked=True
			self.config=self.default_config()
			self.update_config_widgets()
			self.apply_config()
			self.cfg_locked=False
		def update_config_widgets(self):
			self.open_selection.setCurrentIndex(int(list(self.config['ksw_table']['pickmode'].keys())[0]))
			self.mute_selection.setCurrentIndex(int(list(self.config['ksw_table']['pickmode'].keys())[1]))
			self.tap_selection.setCurrentIndex(int(list(self.config['ksw_table']['pickmode'].keys())[2]))
			self.period_field.setText(str(self.config['reset_period']))
			self.atk_field.setText(str(self.config['attack_cut']))
			self.centroid_field.setText(str(self.config['centroid_tolerance']))
			self.pitch_field.setText(str(self.config['pitch_shift']))
		def update_config(self):
			if not self.cfg_locked:
				ksw_open=int(self.open_selection.currentText())
				ksw_mute=int(self.mute_selection.currentText())
				ksw_tap=int(self.tap_selection.currentText())
				self.config['ksw_table']={'pickmode':{ksw_open:'open',ksw_mute:'mute',ksw_tap:'tap'},'fretmode':{3:'pc'}}
				try:
					self.config['reset_period']=abs(int(self.period_field.text()))
					self.period_field.setText(str(self.config['reset_period']))
				except ValueError:
					pass
				try:
					self.config['attack_cut']=float(self.atk_field.text())
				except ValueError:
					pass
				try:
					self.config['centroid_tolerance']=abs(float(self.centroid_field.text()))
				except ValueError:
					pass
				try:
					self.config['pitch_shift']=int(self.pitch_field.text())
					self.pitch_field.setText(str(self.config['pitch_shift']))
				except ValueError:
					pass
		def close_main_menu(self):
			self.file_button.hide()
			self.file_button.deleteLater()
			self.bg.hide()
			self.bg.deleteLater()
			self.config_button.hide()
			self.config_button.deleteLater()
		def filedialog(self):
			filename,_=QFileDialog.getOpenFileName(self)
			if len(filename)>0:
				self.midi_file=filename
				self.midi=PrettyMIDI(filename)
				self.inst_names=[]
				for inst in self.midi.instruments:
					self.inst_names.append(inst.name)
				self.close_main_menu()
				self.configure_instruments()
		def configure_instruments(self):
			self.setGeometry(300,400,640,480)
			self.move(self.width/2-320,self.height/2-480/2)
			self.track_num_prompt=QLabel(self)
			self.track_num_prompt.setText('Choose the number of tracks to render (max 10):')
			self.track_num_prompt.move(50,20)
			self.track_num_prompt.show()
			self.track_num_field=QLineEdit(self)
			self.track_num_field.setMaxLength(2)
			self.track_num_field.setGeometry(350,20,30,20)
			#self.track_num_field.move(350,20)
			self.track_num_field.setText('0')
			self.num_tracks=0
			self.track_num_field.textChanged.connect(self.track_num_updated)
			self.track_num_field.show()
			self.render_button=QPushButton(self)
			self.render_button.clicked.connect(self.render_tracks)
			self.render_button.setText('Render Tracks')
			self.render_button.move(400,20)
			self.track_selections=[]
			self.track_labels=[]
			for i in range(10):
				tselection=QComboBox(self)
				tselection.addItems(self.inst_names)
				tselection.move(150,70+40*i)
				self.track_selections.append(tselection)
				tlabel=QLabel(self)
				tlabel.setText('Track {}:'.format(i+1))
				tlabel.move(80,70+40*i)
				self.track_labels.append(tlabel)
		def track_num_updated(self):
			try:
				self.num_tracks=int(self.track_num_field.text())
			except ValueError:
				self.num_tracks=0
			if self.num_tracks>10:
				self.num_tracks=10
				self.track_num_field.setText('10')
			for i in range(10):
				if i<self.num_tracks:
					self.track_selections[i].show()
					self.track_labels[i].show()
				else:
					self.track_selections[i].hide()
					self.track_labels[i].hide()
			if self.num_tracks>0:
				self.render_button.show()
			else:
				self.render_button.hide()
		def render_tracks(self):
			self.track_num_prompt.hide()
			self.track_num_prompt.deleteLater()
			self.track_num_field.hide()
			self.track_num_prompt.deleteLater()
			self.render_button.hide()
			self.render_button.deleteLater()
			for i in range(10):
				self.track_selections[i].hide()
				self.track_labels[i].hide()
				self.track_labels[i].deleteLater()
			self.target_instruments=[]
			for i in range(self.num_tracks):
				target=self.track_selections[i].currentText()
				self.target_instruments.append(target)
			for i in range(10):
				self.track_selections[i].deleteLater()
			print(self.target_instruments)
			self.rendering_text=QLabel(self)
			self.rendering_text.setText('Rendering {} tracks. This will take a long time.'.format(self.num_tracks))
			self.rendering_text.move(100,100)
			self.rendering_text.show()
			self.tracks_rendered=0
			self.percent_selected=0
			self.percent_notes_rendered=0
			self.track_progress=QLabel(self)
			self.track_progress.move(100,150)
			self.update_render_info_text()
			self.thread=QThread(parent=self)
			self.worker=self.GTSSWorker(self.target_instruments,self.midi_file,self.config['ksw_table'],self.config['reset_period'],self.config['attack_cut'],self.config['centroid_tolerance'],self.config['pitch_shift'])
			self.worker.moveToThread(self.thread)
			self.thread.started.connect(self.worker.run)
			#self.worker.finished.connect(self.thread.exit)
			self.worker.finished.connect(self.thread.exit)
			self.worker.finished.connect(self.worker.deleteLater)
			self.worker.finished.connect(self.render_complete)
			self.worker.append_track.connect(self.update_track_progress)
			self.worker.selection_percent.connect(self.update_selection_percent)
			self.worker.sample_render_percent.connect(self.update_sample_render_percent)
			self.thread.start()
		def update_track_progress(self):
			self.tracks_rendered+=1
			self.update_render_info_text()
		def update_selection_percent(self,percent):
			self.percent_selected=percent
			self.update_render_info_text()
		def update_sample_render_percent(self,percent):
			self.percent_notes_rendered=percent
			self.update_render_info_text()
		def update_render_info_text(self):
			self.track_progress.setText('Notes selected: {}%\nNotes Rendered: {}%\nRendered {}/{} tracks'.format(self.percent_selected,self.percent_notes_rendered,self.tracks_rendered,self.num_tracks))
			self.track_progress.show()
		def render_complete(self):
			self.track_progress.hide()
			self.track_progress.deleteLater()
			self.rendering_text.setText('All tracks have been rendered!')
			self.main_menu_button=QPushButton(self)
			self.main_menu_button.setText('Main Menu')
			self.main_menu_button.clicked.connect(self.to_main_menu)
			self.main_menu_button.move(100,150)
			self.main_menu_button.show()
		def to_main_menu(self):
			self.thread.exit(0)
			self.thread.deleteLater()
			self.main_menu_button.hide()
			self.main_menu_button.deleteLater()
			self.rendering_text.hide()
			self.rendering_text.deleteLater()
			self.main_menu()
		class GTSSWorker(QObject):
			finished=pyqtSignal()
			selection_percent=pyqtSignal(int)
			sample_render_percent=pyqtSignal(int)
			append_track=pyqtSignal()
			def __init__(self,tracks,midi_file_name,ksw,reset_period,attack_cut,centroid_tolerance,pitch_shift):
				super().__init__()
				self.ksw=ksw
				self.reset_period=reset_period
				self.attack_cut=attack_cut
				self.centroid_tolerance=centroid_tolerance
				self.pitch_shift=pitch_shift
				self.tracks=tracks
				self.midi=midi_file_name
			def run_gtss(self):
				gtss=GTSS(ksw_table=self.ksw,reset_period=self.reset_period,attack_cut=self.attack_cut,centroid_tolerance=self.centroid_tolerance,midi_pitch_offset=self.pitch_shift,track_updater=self.emit_track_signal,selection_updater=self.emit_selection_signal,render_updater=self.emit_render_signal)
				#basename=os.path.basename(self.midi)
				for i,inst_name in enumerate(self.tracks):
					inst=gtss.preprocess_midi_sequence(self.midi,inst_name)
					seq=gtss.select_samples(inst)
					gtss.render_sequence_to_file(seq,'{} t{}: {}.wav'.format(self.midi,i+1,inst_name))
			def emit_selection_signal(self,note_index,num_notes):
				self.selection_percent.emit(int(100.*float(note_index)/float(num_notes)))
			def emit_render_signal(self,note_index,num_notes):
				self.sample_render_percent.emit(int(100.*float(note_index)/float(num_notes)))
			def emit_track_signal(self):
				self.append_track.emit()
			def run(self):
				self.run_gtss()
				self.finished.emit()
		
			
	def __init__(self):
		super().__init__(sys.argv)
		size=self.primaryScreen().size()
		self.window=self.Window(size.width(),size.height())
		self.exec_()
	
GTSSGui()
