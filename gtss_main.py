#!bin/python3.6

#Please don't scroll down...............




import numpy.core._dtype_ctypes
from pretty_midi import PrettyMIDI,Instrument
import wavio
import numpy as np
import os
import pickle
import fuckit
from audio_features import*
import sample_selector
from sample_selector import SampleSelector
from sklearn.preprocessing import normalize
from sklearn.linear_model import LinearRegression
from shift_pitch import *
from random import randrange
import soundfile
import time

from pydub import AudioSegment
from pydub import effects

from midi_preprocess import *
from gtss_psg import*

from matplotlib import pyplot as plt





#ok, you asked for this god forsaken mess. here it is:

if __name__=='__main__':
    """
    pick modes: open, mute, tap, opc (open power chord), mpc (mute power chord)
    fret modes: None (nothing special), slideup (slides up), slidedown
    """

    KSWTable = {'pickmode':{0:'open',1:'mute',2:'tap'},'fretmode':{3:'pc'}}
    RESET_PERIOD=50
    CENTROID_TOLERANCE=10.0
    ATTACK_CUT=3.0/1000.0

    #print(os.getcwd())
    sampleset_directory='guitar_samples'


    STARTS={}
    iSTART=0
    #GuitarSample object represents a single sample. Constructed as samples are read in the IndexAllSamples method.
    #New temporary attributes may be given to the sample objects in other functions.
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
    class GuitarSample(object):
        pass

    #def SetAmplitude(sound,)
    def match_target_amplitude(sound, target_dBFS):
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)
    #Concatenates a guitar sample to the rest of the output
    def AddWav(dat,wavToAppend,normalize_to_velocity=True,normalized_coef=0.005):

        wavefile=AudioSegment.from_file(dat.path)
        sampleLen = int(dat.newlength*wavefile.frame_rate)
        atkAdjustment = int(dat.attackchange*wavefile.frame_rate)
        #newdata=wavefile.data[0:sampleLen]
        #wavefile=wavefile.apply_gain(-50)#effects.normalize(wavefile)
        #wavefile=match_target_amplitude(wavefile,-70.)
        newdata=np.array(wavefile.get_array_of_samples()[atkAdjustment:sampleLen+atkAdjustment],dtype=float)
        newdata=normalize(newdata.reshape(1,-1),norm='max').ravel()
        #print(newdata)

        
        start_pos=int(dat.start*float(wavefile.frame_rate))
        
        #print(wavefile.frame_rate)
        if dat.fallback:
            dat.pitchchange += dat.tuning_correction
        if dat.pitchchange != 0.0:
            newdata = ShiftPitch(newdata,dat.pitchchange)
        if normalize_to_velocity:
            newdata=newdata/np.linalg.norm(newdata)*(dat.velocity/127)*normalized_coef
        else:
            pass
        #print(newdata)
        newdata=np.concatenate((np.zeros(start_pos,dtype=float),newdata))
        try:
            len(wavToAppend)
        except:
            wavToAppend=np.zeros(len(newdata),dtype=float)
        #print('wavToAppend:{}\nnewdata:{}'.format(wavToAppend,newdata))
        output=add_arrays([wavToAppend,newdata])
        #print(output)
        return output

    #Returns the length of a note
    def NoteLen(note):
        return note.end - note.start

    #Returns the length of a wave file in seconds
    def WavLength(wavfile):
        n_samples = len(wavfile.data)
        length = float(n_samples)/float(wavfile.rate)
        return length


    def NoteToPitch(noteStr):
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
    def PitchToFrequency(pitch):
        return 16.35*(2.0**(float(pitch)/12.0))

    #Generates an index file containing the parameters for every sample in the dataset, in order to speed up sample search operations.
    def IndexAllSamples(directory):
        dir = os.listdir(directory)
        samplesIndex = list([])
        atkLenData = [[],[]]
        for d in dir:
            #print(d)
            if os.path.isdir(directory+'/'+d):
                path = directory+'/'+d+'/'
                hasWav = False
                bn = os.path.basename(d)
                files = os.listdir(directory+'/'+bn)
                files.sort()
                for fn in files:
                    z,ext = os.path.splitext(fn)
                    if ext == '.wav':
                        fn = directory+'/'+d+'/'+fn
                        bn = os.path.basename(fn)
                        newsample = GuitarSample()
                        wavlist = z.split('_')
                        wav = wavio.read(fn)

                        newsample.path = fn
                        
                        newsample.length = WavLength(wav)
                        newsample.pitch = NoteToPitch(wavlist[0])
                        
                        modes=wavlist[1].split(',')
                        newsample.pick_mode = modes[0]
                        if len(modes)>1:
                            newsample.fret_mode=modes[1]
                            if len(modes)>2:
                                newsample.fret_mode_args=modes[2]
                            else:
                                newsample.fret_mode_args=None
                        else:
                            newsample.fret_mode=None
                        
                        
                        
                        if wavlist[2] == 'fallback':
                            newsample.fallback = True
                        else:
                            newsample.fallback = False
                        #newsample['seqnum'] = int(wavlist[2])
                        
                        newsample.attack = GetPickAttackLen(fn)
                        newsample.avg_centroid=GetAvgSpectralCentroid(fn)
                        newsample.cfd=newsample.avg_centroid-PitchToFrequency(newsample.pitch)
                        
                        newsample.tf0=NoteFrequency(wavlist[0].replace('s','#'))
                        newsample.f0=FundamentalFrequency(fn,newsample.tf0)
                        newsample.adf0=np.abs(newsample.tf0-newsample.f0)
                        newsample.tuning_correction=12*np.log2(newsample.tf0/newsample.f0)
                        if np.abs(newsample.tuning_correction) > 0.6:
                            newsample.tuning_correction=0.0
                        #print(fn,newsample.cfd)
                        #print(newsample.tuning_correction,newsample.path)
                        samplesIndex.append(newsample)
                        #print(newsample)
                        atkLenData[0].append(newsample.length)
                        atkLenData[1].append(newsample.attack)
            else:
                print('something wrong')
        
        return samplesIndex,atkLenData

    ########################################################################################################################################################
    ########################################################################################################################################################

    SAMPLES_INDEX = None
    atkModel = None

    #list of tuples (sample.path,sample.start)
    blacklist=[]
    try:
        print('Loading index file...')
        f = open(os.getcwd()+'/'+sampleset_directory+'/index-2.data','rb')
        unpickle = pickle.load(f)
        f.close()
        SAMPLES_INDEX = unpickle[0]
        atkModel = unpickle[1]
        print('verifying index...')
        toPop = []
        for i in range(len(SAMPLES_INDEX)):
            dict = SAMPLES_INDEX[i]
            if not os.path.exists(dict.path):
                toPop.append(i)
        for index in toPop:
            SAMPLES_INDEX.pop(index)
        print('Loaded.')
    except FileNotFoundError:
        print('None found.\nIndexing samples...')
        SAMPLES_INDEX,atkLenData = IndexAllSamples(sampleset_directory)
        
        #Calculates the relationship between sample lengths and pick attack lengths.
        #Used for shortening the pick attack on very short notes.
        print('Samples indexed.\nCalculating attack model...')
        noteLengths = np.array(atkLenData[0])
        atkLengths = np.array(atkLenData[1])
        clf = LinearRegression()
        clf.fit(noteLengths.reshape(-1,1), atkLengths)
        atkModel = [clf.coef_,clf.intercept_]
        

        #Writes the index and attack model to file.
        f = open(sampleset_directory+'/index-2.data','wb')
        pickle.dump(list([SAMPLES_INDEX,atkModel]),f)
        f.close()

    """
    #plot fundamental frequency vs spectral centroid
    ffs=[]
    scs=[]
    for sample in SAMPLES_INDEX:
        ffs.append(sample.f0)
        scs.append(sample.avg_centroid)
    plt.plot(ffs,scs)
    plt.show()
    """

    newSI = SAMPLES_INDEX
    for si in SAMPLES_INDEX:
        if si == None:
            newSI = newSI.remove(None)
    SAMPLES_INDEX = newSI

    #If multiple, parallel samples are to be rendered, this will make exclusive subsets of the sample data
    def GenerateSubsets(num_subsets,samples_index=SAMPLES_INDEX):
        samples_index = sorted(samples_index,key=lambda x: x.pitch)
        subsets=[]
        for i in range(num_subsets):
            subsets.append([])
        iSub=0
        for s in samples_index:
            subsets[iSub].append(s)
            iSub+=1
            if iSub >= num_subsets:
                iSub=0
        return subsets


    #Splits each voice into a separate instrument. Required for functioning polyphony.
    def GenerateVoices(midfile,inst_name,pa,ksw_table=KSWTable,ksw_shift=0.01):
        for inst in midfile.instruments:
            if inst.name==inst_name:
                target_inst=inst
                found=True
                break
        else:
            target_inst=midfile.instruments[0]
            found=False
            
        if len(midfile.instruments) == 1 or found==True:
            #all_voices will contain all the midi voices, as well as the keyswitch.
            all_voices = PrettyMIDI()
            last_note = None
            for i in range(len(target_inst.notes)):
                target_inst.notes[i].pitch+=pa
            target_inst=PowerChordSubstitution(target_inst,KSWTable)
            currentSeq = target_inst.notes
            thisVoice = Instrument(0)
            leftoverNotes = Instrument(1)
            voice_generation_finished = False
            vi = 0
            while voice_generation_finished == False:
                #print('unfinished')
                for note in currentSeq:
                    
                    #note.pitch += pa
                    if note.pitch in ksw_table['pickmode'] or note.pitch in ksw_table['fretmode']:
                        if note.start - ksw_shift >= 0:
                            note.start -= ksw_shift
                            note.end -= ksw_shift
                        thisVoice.notes.append(note)
                    else:
                        #add to first voice
                        thisVoice.notes.append(note)
                        last_note = note
                    #print(note.start,note.pitch)
                #print(len(thisVoice.notes))
                if len(thisVoice.notes) > 0:
                    thisVoice.notes = sorted(thisVoice.notes,key=lambda v: v.start)
                    return thisVoice

                else:
                    
                    
                    voice_generation_finished = True
                    return thisVoice
                vi += 1
                last_note = None
            #all_voices.write('last_voices.mid')


    #Finds a sample appropriate for a given midi note, etc.



    #
    def WavFromVoice(voice,dupecount,initialMode = 'open',ksw=KSWTable,wavfiledata=SAMPLES_INDEX,sr=44100):
        do_not_include=[]
        currentPickMode=None
        currentFretMode=None
        waves = []
        lastSample = None
        lastNote = None
        lastPitch = 0
        wfdtemp=wavfiledata
        samples = []
        iNote = 0
        notesparsed=0
        #find initial pick mode and fret mode
        for note in voice.notes:
            if note.pitch in ksw['pickmode'] and currentPickMode==None:
                currentPickMode = ksw['pickmode'][note.pitch]
            elif note.pitch in ksw['fretmode'] and currentFretMode==None:
                if note.start == 0:
                    currentFretMode=ksw['fretmode'][note.pitch]
            elif currentFretMode != None and currentPickMode != None:
                break
        
        #select samples and concatenate wave
        for note in voice.notes:
            
            #print(note.pitch)
            #print('hi')
            if note.pitch in ksw['pickmode']:
                #change mode
                currentPickMode = ksw['pickmode'][note.pitch]
            elif note.pitch in ksw['fretmode']:
                currentFretMode=ksw['fretmode'][note.pitch]
            else:
                
                dif = 0
                with fuckit:
                    if waves == []:
                        for i in range(dupecount):
                            waves.append(  np.array([0]*int(1+note.start*float(sr)))  )
                            print('waves',waves)
                            
                
                if lastNote != None:
                    dif = note.start - lastNote.end
                    #print(dif)
                    #print(dif)
                    #print(lastNote)
                newSamples = []
                for i in range(dupecount):
                    newSample,wfdtemp,lastNote,notesparsed,do_not_include = SampleSelector(note,currentPickMode,currentFretMode,lastPitch,wfdtemp,lastSample,(wavfiledata,0),atkModel,(wavfiledata,0),notesparsed,do_not_include,attack_cut=ATTACK_CUT,reset_frequency=RESET_PERIOD,min_start_position=0,bl=blacklist,centroid_tolerance=CENTROID_TOLERANCE)
                    newSample.velocity=note.velocity
                    lastSample = newSample
                    newSamples.append(newSample)
                    #list of tuples (sample.path,sample.start)
                    blacklist.append(   (newSample.path,note.start)   )
                currentFretMode=None
                lastSample = newSample
                lastNote = note
                lastPitch = note.pitch
                for i in range(dupecount):
                    #print('waves[i] before: ',waves[i])
                    waves[i] = AddWav(newSamples[i],waves[i])
                    #print('waves[i] after: ',waves[i])
                iNote += 1
                
        #print(voice.notes)
        return waves
            
                
                
    #Generates voices from midi,superimposes them, and saves the output
    def RenderGuitarFromMidi(midifile,wavename,clip_num,inst=None,pitch_adjust=0,dupecount=1,dataset=SAMPLES_INDEX,ksw=KSWTable):
        midifile += '.mid'
        if inst!=None:
            wavename += '_{}'.format(inst)
        wavename+='.wav'
        mid = PrettyMIDI(midifile)
        voice = GenerateVoices(mid,inst,pa=pitch_adjust,ksw_table=ksw)
        waves = []

        wav_dupes = WavFromVoice(voice,dupecount,wavfiledata=dataset)
        print('wav_dupes: {}'.format(wav_dupes))
        waves.append(wav_dupes)
        
        for i,w in enumerate(wav_dupes):
            if clip_num > 0:
                name,ext = os.path.splitext(wavename)
                wavename=name+'-{}{}'.format(clip_num+1,ext)
            wavio.write(wavename,w,44100,sampwidth=2)
            print('wrote {}'.format(wavename))
            


    #RenderGuitarFromMidi(input('Enter the name of the source midi file: '),input('Enter desired wave file name: '))
    def RenderMultipleTracks(midi_file_name,instnames,ksw_table,reset_period,attack_cut,centroid_tolerance,pitch_shift):
        RESET_PERIOD=reset_period
        CENTROID_TOLERANCE=centroid_tolerance
        ATTACK_CUT=attack_cut
        name,ext=os.path.splitext(midi_file_name)
        mid = PrettyMIDI(midi_file_name)
        print('instnames: {}'.format(instnames))
        for i,instname in enumerate(instnames):
            #print('-----------------------------------------------------------------------------------------------------------INVOKING')
            RenderGuitarFromMidi(name,name,i,inst=instname,pitch_adjust=pitch_shift,dupecount=1,ksw=ksw_table)
            print('inst: {}'.format(instname))
        print('EXIT')
main_gui(RenderMultipleTracks)
debug_samples=False
add=np.array([0],dtype=float)
if debug_samples:
    for s in SAMPLES_INDEX:
        wavefile = AudioSegment.from_file(s.path)
        newdata=np.array(wavefile.get_array_of_samples())
        add =add_arrays([add,newdata])
#print(add.shape)
