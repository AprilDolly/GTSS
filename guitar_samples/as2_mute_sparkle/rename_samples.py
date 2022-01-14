
#!/usr/bin/python3.6
import os

wavfilename = os.path.basename(os.getcwd())
iName = 1
files = os.listdir()
xtraZeros = len(str(len(files)))
for file in files:
    ext = os.path.splitext(file)[1]
    if ext == '.wav':
        xtra = ''
        for i in range(xtraZeros-len(str(iName))):
            xtra += '0'
        os.rename(file,'{}_{}{}{}'.format(wavfilename,xtra,iName,ext))
        iName += 1
    