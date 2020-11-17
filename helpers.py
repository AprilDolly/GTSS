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