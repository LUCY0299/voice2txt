import socket
import re
import pyaudio
import wave
import subprocess

import logging
from threading import Thread, active_count

import speech_recognition as sr

# 配置日志记录，设置日志级别为DEBUG，格式为'[级别] 消息'
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

def sanitize_filename(filename):
    # 使用正規表示式過濾掉不可見字符和特殊字符，只保留英數字、底線、句點和連字符
    return re.sub(r'[^\w.-]', '', filename)

def audio_file_to_text(audio_file_name):
    # 使用SpeechRecognition程式庫將音頻文件轉換為文字
    r = sr.Recognizer()
    with sr.AudioFile(audio_file_name) as source:
        r.adjust_for_ambient_noise(source, duration=0)
        audio = r.record(source)
    try:
        result = r.recognize_google(audio, language='zh-TW')
    except sr.UnknownValueError:
        result = "無法翻譯"
    except sr.RequestError as e:
        result = "翻譯錯誤：{0}".format(e)
    return result

def handle_client_connection(client_socket):
    try:# 接收客戶端傳送的檔名
        filename = client_socket.recv(1024).decode('utf-8')
         # 做文件名的错误处理和验证
        if not filename.strip():
            logging.warning("接收到空白文件名")
            return
        
        filename = sanitize_filename(filename)  
        if not filename:
            logging.warning("無效的文件名")
            return
        # 對檔名進行清理，確保它只包含合法字符
        filename = sanitize_filename(filename)       
                
        # # 生成帶有時間戳的檔名
        # timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        # filename_with_timestamp = f"AUDIO_{timestamp}_{filename}.3gp"

        # 存放音訊檔案的路徑
        audio_file_path = "D:/Topic/VoiceToText/" + filename
    
        with open(audio_file_path, "wb") as f:
            while True:
                # 持續接收客戶端傳輸的數據並寫入檔案
                data = client_socket.recv(1024)
                if not data:
                    break
                f.write(data)
        logging.info(f"音訊檔案已儲存為 {filename}")
        
         # 将 3GP 音频文件转换为 WAV 格式
        wav_audio_file_path = audio_file_path.replace('.3gp', '.wav')
        subprocess.run(['ffmpeg', '-i', audio_file_path, wav_audio_file_path])
        
        # 將音頻檔案轉換為文字
        result = audio_file_to_text(audio_file_path)
        logging.info(f"轉換後的文字內容：{result}")
        
        # 播放音频文件
        play_audio(audio_file_path)
        
        # 将转换结果存储到文本文件中
        store_result(result)
        
    except Exception as e:
        logging.error(f"处理客户端连接时发生错误：{e}")
    finally:
        # 关闭客户端连接
        client_socket.close()
    
    # 傳送回應消息給客戶端
    response = "音訊已接收、儲存並轉換為文字"
    client_socket.send(response.encode())
    client_socket.close()
    
# 添加播放音频的函数
def play_audio(audio_file_path):
    CHUNK = 1024
    File = wave.open(audio_file_path, "rb")
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(File.getsampwidth()), 
                    channels=File.getnchannels(), 
                    rate=File.getframerate(), 
                    output=True)
    data = File.readframes(CHUNK)
    while data:
        stream.write(data)
        data = File.readframes(CHUNK)
    stream.stop_stream()
    stream.close()
    p.terminate()

# 添加存储转换结果的函数
def store_result(result):
    outfile = 'D:/Topic/VoiceToText/Voiceresult.txt'
    with open(outfile, 'a', encoding='CP950') as f:
        f.write(result + '\n')
    print('\n\n檔案'+outfile+'己存檔。')

def start_socket_server():
    # 建立socket伺服器，綁定地址並監聽連線
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 3000))
    server.listen(5)
    logging.info("正在監聽 0.0.0.0:3000")

    while True:
        # 接受客戶端連線請求
        client_sock, address = server.accept()
        logging.info(f"已接受來自 {address[0]}:{address[1]} 的連線")
        logging.info(f"當前活動線程數量：{active_count()}")
        # 建立線程來處理客戶端連線
        client_handler = Thread(
            target=handle_client_connection,
            args=(client_sock,)
        )
        client_handler.start()

# 啟動socket伺服器的主線程
Thread(target=start_socket_server).start()
