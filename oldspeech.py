#用SpeechRecognition程式庫做語音辨識
import speech_recognition as sr
import re
import time
import os
import pyaudio
import wave
import pyttsx3
speak = pyttsx3.init()

def Play_Voice(AUDIO_FILE_NAME):
    CHUNK=1024
    #開啟聲音檔案
    File = wave.open(AUDIO_FILE_NAME, "rb")
    #導入PyAudio
    p = pyaudio.PyAudio()
    #開啟串流 open stream
    stream = p.open(format = p.get_format_from_width(File.getsampwidth()),channels = File.getnchannels(),rate = File.getframerate(),output = True)
    #讀取音源檔
    data = File.readframes (CHUNK)
    #撥放音源檔
    while data:
        stream.write(data)
        data = File.readframes (CHUNK)
    #停止音源檔
    stream.stop_stream()
    stream.close()
    #關閉PyAudio
    p.terminate()
    
def AudioFile_To_Text(AUDIO_FILE_NAME):
    r = sr.Recognizer()
    with sr.AudioFile(AUDIO_FILE_NAME) as source:
        r.adjust_for_ambient_noise(source,duration=0)
        audio = r.record(source)#美文語音檔案
    #Text=r.recognize_ google (audio, language='zh-TW') #中文語音檔案
    #Text=r.recognize_google (audio, language='en-US')
    Text=r.recognize_google (audio, language='zh-TW')
    return Text

#中文口語翻譯中文文字
def Voice_To_Text():
    r =sr.Recognizer()
    with sr.Microphone() as source:
        print("請開始說話：")
#函敟調墪麥克風的噪音:
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    try:
        Text=r.recognize_google(audio,key="c1527066ae4233174dbc7b48f08bb92c301de243", language='zh-TW', show_all=True)
    except sr.UnknownValueError:
        Text="無法翻譯"
    except sr.RequestError as e:
        Text ="can't翻譯 {0}".format(e)
    except sr.HTTPError as e:
        print("Couldn't connect to the websites perhaps , Hyper text transfer protocol error",e)
    return Text

#main
#設定文字檔儲存路徑
outfile='D:\Topic\VoiceToText\Voice.txt'
f1=open(outfile,'w', encoding='CP950')

print('播放語音檔:')
AUDIO_FILE_NAME = ("D:\Topic\VoiceToText\yating.wav")
Play_Voice(AUDIO_FILE_NAME)

print('轉换語音檔成文字：')
Text=AudioFile_To_Text(AUDIO_FILE_NAME)
print(Text)
f1.write(Text)   #將轉換文字存檔
print('口語翻譯成文字：')
Text=Voice_To_Text()
print (Text)
f1.write(Text+ '\n')   #將轉换文字存檔
print('\n\n檔案'+outfile+'己存檔。')
f1.close()  