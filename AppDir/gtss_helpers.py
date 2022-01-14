from sklearn.linear_model import LinearRegression
import numpy as np
import copy


def add_arrays(arrays,data_type=float):
		out=np.array([0],dtype=data_type)
		for ar in arrays:
			#print(ar)
			ldif=len(ar)-len(out)
			if ldif>0:
				out = np.concatenate((out,np.zeros(ldif,dtype=data_type)))
			elif ldif < 0:
				ar=np.concatenate((ar,np.zeros(-1*ldif,dtype=data_type)))
			out += ar
		return out
def note_to_pitch(noteStr):
	noteStr = noteStr.lower()
	noteTable = {'c':0,'cs':1,'d':2,'ds':3,'e':4,'f':5,'fs':6,'g':7,'gs':8,'a':9,'as':10,'b':11}
	try:
		noteID = noteTable[noteStr[0:2]]
		noteNum = int(noteStr[2])
		return 12*noteNum+12+noteID
	except:
		noteID = noteTable[noteStr[0]]
		noteNum = int(noteStr[1])
		return 12*noteNum+12+noteID
def attack_model(samples):
	noteLengths=[]
	atkLengths=[]
	for sample in samples:
		noteLengths.append(sample.length)
		atkLengths.append(sample.attack)
	noteLengths = np.array(noteLengths)
	atkLengths = np.array(atkLengths)
	clf = LinearRegression()
	clf.fit(noteLengths.reshape(-1,1), atkLengths)
	return clf.coef_,clf.intercept_

def choose_sample(gtss,note,print_debug=False):
	def debug(msg):
		if print_debug:
			print(msg)
	mute_cutoff=81
	reset_period=gtss.reset_period
	cfd_threshold=200
	use_fallback=False
	samples=sorted(gtss.samples,key=lambda x: x.length)
	#samples=sorted(gtss.samples,key=lambda x: x.adf0*x.length**3*float(np.abs(note.pitch-x.pitch))**20)
	max_pitch_threshold=10
	pitch_threshold=0
	adf0_threshold=8.0
	max_adf0_threshold=70.
	max_cfd_threshold=0
	def iterate_through_samples():
		current_pick_mode=copy.deepcopy(gtss.current_pick_mode)
		if len(gtss.exclude)>=reset_period:
			gtss.exclude=[]
		for s in samples:
			try:
				assert use_fallback==True or s.is_fallback==False
				if gtss.last_sample!=None:
					assert s.path!=gtss.last_sample.path or use_fallback==True
				pitchdif=note.pitch-s.pitch
				#assert (s.is_fallback and use_fallback==True) or (s.is_fallback==False and use_fallback==False)
				assert s.length>=note.end-note.start
				assert s.path not in gtss.exclude
				assert (s.path,note.start) not in gtss.used_pairs
				if gtss.current_fret_mode=='pc':
					if current_pick_mode=='open':
						current_pick_mode='opc'
					elif current_pick_mode=='mute':
						current_pick_mode='mpc'
					gtss.current_fret_mode=None
				if s.f0>200. and use_fallback==False:
					assert s.adf0<adf0_threshold
					if s.fret_mode==None and gtss.last_sample!=None:
						if gtss.last_sample.pitch==note.pitch:
							assert abs(s.centroid-gtss.last_sample.centroid) < cfd_threshold*float(abs(gtss.last_note.pitch-note.pitch)+1)
						elif gtss.last_sample.pitch>note.pitch:
							assert gtss.last_sample.centroid>s.centroid-gtss.centroid_tolerance
						else:
							assert gtss.last_sample.centroid<s.centroid+gtss.centroid_tolerance
				atkAdjustment = copy.deepcopy(gtss.attack_cut)
				theoreticalAtk = float(gtss.attack_slope)*(note.end-note.start)+gtss.attack_intercept
				assert abs(s.pitch-note.pitch)<pitch_threshold
				if theoreticalAtk < s.attack:
					atkAdjustment += s.attack - theoreticalAtk
				if use_fallback==True:
					assert s.is_fallback
					if current_pick_mode=='tap':
						current_pick_mode='open'
						atkAdjustment*=50
				assert s.pick_mode==current_pick_mode
				assert s.fret_mode==gtss.current_fret_mode or use_fallback==True
				if note.pitch > mute_cutoff and current_pick_mode=='mute':
					current_pick_mode = 'open'
				#todo: implement slides
				assert note.end-note.start+atkAdjustment<s.length
				rs=gtss.GuitarSample(s.path)
				rs.load_metadata(s.dump_metadata())
				rs.initialize_render_params()
				rs.render_params.pitch_change=pitchdif
				rs.render_params.new_length = note.end-note.start
				rs.render_params.attack_change = atkAdjustment
				rs.render_params.stretch=0
				rs.render_params.start=note.start
				rs.render_params.end=note.end
				rs.render_params.velocity=note.velocity
				gtss.exclude.append(rs.path)
				gtss.current_fret_mode=None
				return rs
			except AssertionError:
				pass
	for i in range(6):
		pitch_threshold=0
		adf0_threshold=0
		while pitch_threshold<max_pitch_threshold:
			sample=iterate_through_samples()
			pitch_threshold+=1
			if adf0_threshold<max_adf0_threshold:
				adf0_threshold+=10
			if sample!=None:
				return sample
		if i==1:
			print('reset exclude')
			gtss.exclude=[]
		if i==2:
			max_pitch_threshold*=2
			max_adf0_threshold=1000
			print('double pt')
		elif i==3:
			gtss.exclude=[]
			max_pitch_threshold=50
			samples=sorted(gtss.samples,key=lambda x: abs(x.pitch-note.pitch))
			max_adf0_threshold=10000
			print('reset exclude, pt=50')
		elif i==4:
			gtss.exclude=[]
			gtss.last_sample=None
			print('using fallback')
			use_fallback=True
			max_pitch_threshold=100
		elif i==5:
			print_debug=True
	
