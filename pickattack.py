import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    
    #from pyAudioAnalysis import audioBasicIO
    #from pyAudioAnalysis import ShortTermFeatures
    #import numpy as np

    import soundfile as sf
    import numpy as np
    """
    import librosa
    from librosa import *



    #Retrieves pick attack by assessing differences in energy accross the wavefrom
    def GetPickAttackLen(wave,window=0.01):
        try:
            overlap = window/2
            [Fs, x] = audioBasicIO.read_audio_file(wave)
            F, f_names = ShortTermFeatures.feature_extraction(x, Fs, window*Fs, overlap*Fs)
            energies = F[1]
            lastEnergy = None
            maxEnergyDif = 0
            iMaxEnergyDif = 0
            i = 0
            for energy in np.nditer(energies):
                try:
                    if energy - lastEnergy > maxEnergyDif:
                        maxEnergyDif = energy - lastEnergy
                        iMaxEnergyDif = i
                        lastEnergy = energy
                except:
                    lastEnergy = energy
                i += 1
            atkLen = (iMaxEnergyDif)*overlap
            return atkLen
        except:
            #probably something wrong with the sample being too short to process. Assume negligible pick attack.
            return 0.0
    """
    def GetPickAttackLen(wave):
        w,sr=sf.read(wave)
        peakIndex=0
        biggest=0
        for idx,val in enumerate(np.nditer(w)):
            if np.abs(val)>biggest:
                biggest=np.abs(val)
                peakIndex=idx
        return float(peakIndex)/float(sr)
