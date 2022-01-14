from pretty_midi import Note

def power_chord_substitution(inst,kswtable):
	iN1=0
	toDelete=[]
	newNotes=[]
	for note1 in inst.notes:
		iN2 = 0
		for note2 in inst.notes:
			if note2.start == note1.start and note1.end==note2.end and note2.pitch-note1.pitch==7:
				#power chord
				proceed=True
				for note in newNotes:
					str_pitch=str(note.pitch)
					if (note.pitch == note1.pitch or note2.pitch and note.pitch==note1.start):
						#and (not (str_pitch in kswtable['pickmode'].keys() or str_pitch in kswtable['fretmode'].keys())):
						proceed=False
				if proceed:
					newNotes.append(Note(127,3,note1.start,note1.end))
					toDelete.append(iN2)
			iN2 += 1
		iN1+=1
	toDelete=sorted(toDelete,reverse=True)
	for index in toDelete:
		#print(index)
		del inst.notes[index]
	for note in newNotes:
		inst.notes.append(note)
	inst.notes=sorted(inst.notes,key=lambda x: x.start)
	return inst
"""
mid=pm.PrettyMIDI('idk2.mid')
for inst in mid.instruments:
	if inst.name=='Rhythm Guitar':
		PowerChordSubstitution(inst)
		"""
