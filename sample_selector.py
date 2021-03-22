import pickle
from sys import float_info
MAX_FLOAT=float_info.max

def SampleSelector(note,pick_mode,fret_mode,lastPitch,wft,last_sample,samples_data,am,full_dataset,notes_parsed,do_not_use,chord_agnostic=False,pitch_threshold=8,mute_cutoff=72,allow_slides=True,min_start_position=0,attack_cut=0.0,max_cfd_threshold=0,reset_frequency=20,bl=[],max_adf0=5000,centroid_tolerance=10):
    cfd_threshold=200
    
    reset=False
    def NoteLen(note):
        return note.end - note.start
    
    if samples_data[0]==full_dataset[0]:
        fulldata=True
    else:
        fulldata=False
    adf0_threshold=4.0
    #fulldata=True
    #print(wft)
    wft=sorted(wft,key=lambda x: x.length)
    #print(wft)
    noteLen=NoteLen(note)
    fullscope=False
    pt=0
    bestLenDif = MAX_FLOAT
    bestWave = None
    data_position=0
    use_fallback=False
    
    tap=False
    noAtk = False
    
    pseudotap=False
    #notes on high strings are hardly ever muted
    if note.pitch > mute_cutoff and pick_mode=='mute':
        pick_mode = 'open'
    while True:
        if (pseudotap==False and use_fallback==True) or pseudotap==True:
            noAtk=True
            pick_mode='open'
            pseudotap=True
        for i,wave in enumerate(wft):
            #wave=wft[i]
            ok = False
            try:
                ok = (last_sample.path!=wave.path) or use_fallback==True

            except:
                ok=True
            brightness_ok=True
            if wave.f0 >=200:
                try:
                    if ok==True:
                        if wave.adf0<=adf0_threshold:
                            ok=True
                        
                        else:
                            ok=False
                            
                    if max_cfd_threshold > 0 and use_fallback==False:
                        if last_sample.pitch==note.pitch:
                            brightness_ok = abs(wave.avg_centroid-last_sample.avg_centroid) < cfd_threshold*float(abs(lastPitch-note.pitch)+1)
                        elif wave.fret_mode != None:
                            brightness_ok=True
                        elif last_sample.pitch>note.pitch:
                            brightness_ok=last_sample.avg_centroid>wave.avg_centroid-centroid_tolerance
                        else:
                            brightness_ok=last_sample.avg_centroid<wave.avg_centroid+centroid_tolerance
                    else:
                        brightness_ok=True
                except:
                    pass
            
            #print(brightness_ok)
                #list of tuples (sample.path,sample.start)
            if (use_fallback==True and wave.fallback==True and (not (wave.path,note.start) in bl))or((not (wave.path,note.start) in bl)and (not wave.path in do_not_use ) and brightness_ok and ok == True and ((wave.fallback == False and use_fallback==False) or fullscope==None or noAtk ==True) and (wave.fallback == True or noAtk == False)):
                
                #for finger sliding on notes
                fretModeAccepted = False
                if wave.fret_mode == None: 
                    if fret_mode == None:
                        fretModeAccepted = True
                    else:
                        fretModeAccepted = False
                elif fret_mode == wave.fret_mode:
                    fretModeAccepted=True
                elif allow_slides:
                    if (lastPitch > wave.pitch and fret_mode=='slidedown') or (lastPitch < wave.pitch and fret_mode=='slideup'):
                        notePitchChange = note.pitch-lastPitch
                        if wave.fret_mode_args==None:
                            fretModeAccepted=True
                        elif int(wave.fret_mode_args) == notePitchChange:
                            fretModeAccepted=True
                        else:
                            fretModeAccepted=False
                    else:
                        fretModeAccepted=False
                
                if chord_agnostic == True:
                    try:
                        if wave.pick_mode == 'opc':
                            wave.pick_mode = 'open'
                        elif wave.pick_mode == 'mpc':
                            wave.pick_mode = 'mute'
                    except:
                        pass
                        #print(wave)
                pitchdif = note.pitch-wave.pitch
                if fret_mode=='pc':
                    if pick_mode=='open':
                        pick_mode='opc'
                    elif pick_mode=='mute':
                        pick_mode='mpc'
                    fretModeAccepted=True
                    #print(abs(pitchdif) <=pt, wave.pick_mode == pick_mode, fretModeAccepted==True)
                
                
                #print(wave.pick_mode,pick_mode,wave.pitch,note.pitch,wave.path)
                lenDif = abs(noteLen - wave.length)
                if lenDif < bestLenDif and wave.pick_mode == pick_mode and (not (wave.path,note.start) in bl):
                    bestLenDif = lenDif
                    wave.pitchchange = pitchdif
                    wave.newlength = wave.length
                    wave.attackchange = 0
                    bestWave = wave
                
                if abs(pitchdif) <=pt and wave.pick_mode == pick_mode and fretModeAccepted==True:
                    atkAdjustment = attack_cut
                    theoreticalAtk = float(am[0])*noteLen+am[1]
                    if theoreticalAtk < wave.attack:
                        atkAdjustment += (wave.attack - theoreticalAtk)
                    
                    #see above temp fix
                    if noAtk:
                        atkAdjustment=wave.attack*3+attack_cut
                    #print(wave.length-(noteLen+atkAdjustment),wave.path)
                    lenDif = abs((noteLen + atkAdjustment) - wave.length)
                    
                    
                    if  noteLen + atkAdjustment < wave.length:
                        data_position += 1
                        if min_start_position <= data_position:
                            oldwave=wave
                            wave.pitchchange = pitchdif
                            wave.newlength = NoteLen(note)
                            wave.attackchange = atkAdjustment
                            wave.pitchchange = note.pitch - wave.pitch
                            wave.stretch=None
                            wave.start=note.start
                            wave.end=note.end

                            #print(wave.adf0,wave.path)
                            elem = wft[i]
                            do_not_use.append(elem.path)
                            #if pick_mode == 'mute':
                            #print(note.pitch,wave.pitchchange,wave.path)
                            #print(note.pitch)
                            notes_parsed+=1
                            if notes_parsed > reset_frequency:
                                #print('\n\n\nRESET SAMPLES THING\n\n\n')
                                do_not_use=[]
                                notes_parsed=0
                            return wave,wft,note,notes_parsed,do_not_use
        centroid_tolerance += 60
        if cfd_threshold <max_cfd_threshold:
            cfd_threshold += 100
        if adf0_threshold < max_adf0:
            adf0_threshold+=10
        if pt<=pitch_threshold:
            adf0_threshold=1
            pt+=1
            #bestLenDif = 50000000.
        elif fullscope==False:
            adf0_threshold=10000
            #print(pt,note.pitch,pick_mode,noteLen)
            do_not_use=[]
            pt=0
            fullscope=True
            #bestLenDif = 50000000.
        
        elif use_fallback==False:
            adf0_threshold=10000
            pt=0
            use_fallback=True
        elif fulldata==False:
            #use full dataset
            wft = full_dataset
            #atkModel = unpickle[1]wft=full_dataset
            fulldata=True
            pt=0
        elif pt <= pitch_threshold*2:
            pt += 1
        elif pt < 500:
            pt=500
        elif reset==False:
            do_not_use=[]
            notes_parsed=0
            reset=True
        else:
            #TODO: create some sort of fallback mechanism in case the thing truly cannot find a note
            #print('i had to settle for a shorter note :c')
            if note.start+bestWave.length<note.end:
                note.end = note.start+bestWave.length
            
            #bestWave.stretch=bestWave.length/noteLen
            #print(bestWave.path)
            bestWave.start=note.start
            return bestWave,wft,note,0,[]
        
        
        """
        elif fullscope==True:
            #when you cannot find a note within the given pitch threshold
            fullscope=None
        """
