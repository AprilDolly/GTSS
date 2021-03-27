#Time to jump in the dumpster!

import PySimpleGUI as sg
import os
import pretty_midi as pm
import multiprocessing
import pickle

def initialize_config():
    default_cfg={}
    default_cfg['ksw_table']={'pickmode':{0:'open',1:'mute',2:'tap'},'fretmode':{3:'pc'}}
    default_cfg['reset_period']=50
    default_cfg['attack_cut']=3.0
    default_cfg['centroid_tolerance']=10.0
    default_cfg['pitch_shift']=0
    try:
        f=open('config','rb')
        cfg=pickle.load(f)
        f.close()
    except (FileNotFoundError,EOFError):
        cfg=default_cfg
        f=open('config','wb')
        f.truncate()
        pickle.dump(cfg,f)
        f.close()
    return cfg

def config_menu(window_icon='assets/gtss.png'):
    default_cfg={}
    default_cfg['ksw_table']={'pickmode':{0:'open',1:'mute',2:'tap'},'fretmode':{3:'pc'}}
    default_cfg['reset_period']=50
    default_cfg['attack_cut']=3.0
    default_cfg['centroid_tolerance']=10.0
    default_cfg['pitch_shift']=0
    cfg=initialize_config()
    ksw_powerchord=list(cfg['ksw_table']['fretmode'].keys())[0]
    ksw_open=list(cfg['ksw_table']['pickmode'].keys())[0]
    ksw_mute=list(cfg['ksw_table']['pickmode'].keys())[1]
    ksw_tap=list(cfg['ksw_table']['pickmode'].keys())[2]
    reset_period=cfg['reset_period']
    attack_cut=cfg['attack_cut']
    centroid_tolerance=cfg['centroid_tolerance']
    pitch_shift=cfg['pitch_shift']
    midi_range=list(range(128))
    def get_layout():
        layout=[
            [sg.Text('Keyswitch notes (0-127)\nThese are to be changed depending on the plugin/soundfont you used.\nIgnore these if you use fakeguitar, the SFZ also made by AprilDolly.')],
            [sg.Text('Open pluck:'),sg.Combo(midi_range,default_value=ksw_open,key='open')],
            [sg.Text('Muted pluck:'),sg.Combo(midi_range,default_value=ksw_mute,key='mute')],
            [sg.Text('Tap:'),sg.Combo(midi_range,default_value=ksw_tap,key='tap')],
            [sg.Text('power chord'),sg.Combo(midi_range,default_value=ksw_powerchord,key='pc'),sg.Text('Used internally for power chord detection.\nOnly change if you want to use note {} as another keyswitch.'.format(ksw_powerchord))],
            [sg.Text('\n')],
            [sg.Text('Reset period (higher number==more diverse selection of samples)'),sg.Combo(list(range(5,501)),default_value=reset_period,key='reset_period')],
            [sg.Text('Attack cut (ms)'),sg.Input(attack_cut,key='atk')],
            [sg.Text('Spectral centroid tolerance\n(lower number==more accurate sample harmonics)'),sg.Input(centroid_tolerance,key='spectral')],
            [sg.Text('Pitch shift\n(change if your guitar tracks come out higher or lower than normal)'),sg.Input(pitch_shift,key='pitch_shift'),sg.Text('semitones')],
            [sg.Ok(),sg.Button('Apply'),sg.Button('Reset to Defaults'),sg.Cancel()]
            ]
        return layout
    config_window=sg.Window('Settings',get_layout(),icon=window_icon)
    while True:
        event,values=config_window.read()
        print(values)
        if event==None or event=='Cancel':
            config_window.close()
            return
        elif event=='Reset to Defaults':
            cfg=default_cfg
            f=open('config','wb')
            f.truncate()
            pickle.dump(cfg,f)
            f.close()
            config_window.close()
            config_window=sg.Window('Settings',get_layout(),icon=window_icon)
        else:
            #TODO: check to make sure ksws are not the same note
            cfg['ksw_table']={'pickmode':{int(values['open']):'open',int(values['mute']):'mute',int(values['tap']):'tap'},'fretmode':{3:'pc'}}
            cfg['reset_period']=int(values['reset_period'])
            cfg['attack_cut']=float(values['atk'])
            cfg['centroid_tolerance']=float(values['spectral'])
            cfg['pitch_shift']=int(values['pitch_shift'])
            f=open('config','wb')
            f.truncate()
            print(cfg)
            pickle.dump(cfg,f)
            f.close()
            if event=='Ok':
                config_window.close()
                return
                
            


def main_gui(render_function,window_icon='assets/gtss.png'):
    sg.LOOK_AND_FEEL_TABLE['Cutsie']={
        'BACKGROUND': '#FFDAE8', 
        'TEXT': '#d52a6a', 
        'INPUT': '#ffffff', 
        'TEXT_INPUT': '#d52a6a', 
        'SCROLL': '#FF478C', 
        'BUTTON': ('#FFFFFF', '#FF478C'), 
        'PROGRESS': ('#D1826B', '#CC8019'), 
        'BORDER': 1, 'SLIDER_DEPTH': 0,  
        'PROGRESS_DEPTH': 0,
    }
    sg.theme('Cutsie')
    initialize_config()
    while True:
        try:
            f=open('last_directory.txt','r')
            directory=f.read()
            f.close()
        except:
            directory=None
        entry_layout=[
            [sg.Image('assets/home_screen.png')],
            [sg.FileBrowse('Choose MIDI file',initial_folder=directory),sg.Button('Configure',tooltip='Configure stuff')],
            []
            ]
        entry_window=sg.Window('Guitar Super System',entry_layout,icon=window_icon)
        midi_choice=None
        while True:
            
            event,values=entry_window.read(timeout=.01)
            #print(event,values)
            if len(str(values['Choose MIDI file']))>0 and values['Choose MIDI file'] != midi_choice:
                midi_choice=values['Choose MIDI file']
                name,ext=os.path.splitext(midi_choice)
                if ext.lower() in ['.mid','.midi']:
                    #good to go
                    break
                else:
                    sg.Popup('{} is not a  midi file.\nMidi files have either .mid or .midi extensions.\nPlease try again.'.format(os.path.basename(midi_choice)),icon=window_icon)
            elif event=='Configure':
                config_menu()
            elif event==None:
                return
        entry_window.close()
        last_dir=os.path.dirname(midi_choice)
        
        f=open('last_directory.txt','w')
        f.truncate()
        f.write(last_dir)
        f.close()
        
        
        midi_data=pm.PrettyMIDI(midi_choice)
        inst_names=[]
        for inst in midi_data.instruments:
            inst_names.append(inst.name)
        inst_select_layout=[
            [sg.Text('Select instruments to render guitar tracks from, and number of tracks.\nAn instrument may be used more than once to render layered tracks.')],
            [sg.Text('Number of tracks to render (max. 10)'),sg.Input('0',enable_events=True,)],]
        
        for i in range(10):
            inst_select_layout.append([sg.Text('Track {}:'.format(i+1),visible=False,key='track{}text'.format(i+1)),sg.Combo(inst_names,visible=False,key='track{}inst'.format(i+1))])
        inst_select_layout.append([sg.Button('Proceed')])
        inst_select_window=sg.Window('Select instruments to use',inst_select_layout,icon=window_icon)
        num_tracks=0
        final_track_list=[]
        while True:
            event,values=inst_select_window.read()
            print(event,values)
            if event == 0 and str(values[0]) != str(num_tracks):
                try:
                    num_tracks=int(values[0])
                except ValueError:
                    num_tracks=0
                if num_tracks>10:
                    num_tracks=10
                for i in range(10):
                    txt_key='track{}text'.format(i+1)
                    box_key='track{}inst'.format(i+1)
                    if i<num_tracks:
                        vis=True
                    else:
                        vis=False
                    inst_select_window[txt_key].Update(visible=vis)
                    inst_select_window[box_key].Update(visible=vis)
                #inst_select_layout.append([sg.Button('Proceed')])
                #inst_select_window.Rows=inst_select_layout
                
                #inst_select_window.close()
                #inst_select_window=sg.Window('',inst_select_layout,icon=window_icon)
            elif event=='Proceed':
                if num_tracks>0:
                    final_track_list=[]
                    for i in range(1,num_tracks+1):
                        box_key='track{}inst'.format(i)
                        final_track_list.append(values[box_key])
                    #print(final_track_list)
                    #print('final_track_list: '.format(final_track_list))
                    if '' in final_track_list:
                        sg.Popup('One or more of your tracks does not have a designated instrument.',icon=window_icon)
                    else:
                        break
                else:
                    sg.Popup('Number of tracks to render must be more than 0.',icon=window_icon)
                
            elif event==None:
                return
        inst_select_window.close()
        #print('final_track_list: {}'.format(final_track_list))
        config=initialize_config()
        ksw_table=config['ksw_table']
        reset_period=config['reset_period']
        attack_cut=config['attack_cut']/1000.0
        centroid_tolerance=config['centroid_tolerance']
        pitch_shift=config['pitch_shift']
        
        render_layout=[
            [sg.Text('Rendering guitar tracks...this may take some time.')],
            [sg.Button('Cancel')]
            ]
        render_win=sg.Window('Rendering tracks',render_layout,icon=window_icon)
        started=False
        th=None
        while True:
            event,values=render_win.read(timeout=0.1)
            if started==False:
                #print('final_track_list: {}'.format(final_track_list))
                th=multiprocessing.Process(target=render_function,args=(midi_choice,final_track_list,ksw_table,reset_period,attack_cut,centroid_tolerance,pitch_shift))
                th.start()
                started=True
            elif th.is_alive()==False:
                render_win.close()
                sg.Popup('Guitar tracks successfully rendered!\nThey will appear in the same directory as your midi file.',icon=window_icon)
                break
            elif event=='Cancel' or event==None:
                th.terminate()
                render_win.close()
                if event==None:
                    return
                break
