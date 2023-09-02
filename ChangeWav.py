import os
import subprocess
import speech_recognition as sr

# 轉換3GP為WAV格式
def convert_3gp_to_wav(input_file, output_file):
    subprocess.run(["ffmpeg", "-i", input_file, "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", output_file])

# 語音辨識
def recognize_speech(output_file):
    r = sr.Recognizer()
    with sr.AudioFile(output_file) as source:
        r.adjust_for_ambient_noise(source,duration=0)
        audio = r.record(source)
    
    recognition_results = r.recognize_google (audio, language='zh-TW')
    return recognition_results

# 主程式
input_3gp_file = "D:\\Topic\\VoiceToText\\recorded_audio.3gp"  # 替換為你的3GP檔案路徑
output_wav_file = "D:\\Topic\\VoiceToText\\test.wav"  # 替換為你想要的輸出WAV檔案路徑

if os.path.exists(input_3gp_file):
    convert_3gp_to_wav(input_3gp_file, output_wav_file)
    print("轉換完成")
    
    recognition_results = recognize_speech(output_wav_file)
    best_transcript = recognition_results.get("alternative", [])[0].get("transcript")
    print("最有可能的文字轉錄：", best_transcript)
else:
    print("指定的3GP檔案不存在")
