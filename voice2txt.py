import socket
import re
import os
import subprocess
import firebase_admin
from firebase_admin import credentials, storage
import logging
from threading import Thread, active_count

import speech_recognition as sr

# 配置日志记录，设置日志级别为DEBUG，格式为'[级别] 消息'
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

def sanitize_input(input_str):
    # 使用正規表示式過濾掉不可見字符和特殊字符，只保留英數字、底線、句點和連字符
    return re.sub(r'[^\w.-]', '', input_str)

def audio_file_to_text(wav_audio_file_path):
    # 使用SpeechRecognition程式庫將音頻文件轉換為文字
    r = sr.Recognizer()
    with sr.AudioFile(wav_audio_file_path) as source:
        r.adjust_for_ambient_noise(source, duration=0)
        audio = r.record(source)
    try:
        result = r.recognize_google(audio, language='zh-TW')
        return result
    except sr.UnknownValueError:
        result = "無法翻譯"
        return result
    except sr.RequestError as e:
        result = "翻譯錯誤：{0}".format(e)
        return result
 # 添加一个标志，以确保只初始化一次
firebase_initialized = False

def initialize_firebase():
    global firebase_initialized
    if not firebase_initialized:
        # 初始化 Firebase Admin SDK
        cred = credentials.Certificate("D:\Topic\VoiceToText\serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {"storageBucket": "stroke-2015a.appspot.com"})
        firebase_initialized = True   

def handle_client_connection(client_socket):
    try:
        # 接收客户端发送的文件名
        info_string = client_socket.recv(1024).decode('utf-8')

        # 做文件名的错误处理和验证
        if not info_string.strip():
            logging.warning("接收到空白文件名")
            return

        # 分离信息字符串为 username、dateTime 和 filename
        username, dateTime, filename = info_string.split('/')
        username = sanitize_input(username)
        dateTime = sanitize_input(dateTime)
        filename = sanitize_input(filename)
        
        if not username or not dateTime or not filename:
            logging.warning("无效的信息字符串")
            return
        
       # 存放音频文件的路径
        audio_dir = os.path.join("D:/Topic/VoiceToText", username, dateTime)
        os.makedirs(audio_dir, exist_ok=True)  # 创建目录，如果目录不存在

        audio_file_path = os.path.join(audio_dir, filename)
    
        with open(audio_file_path, "wb") as f:
            while True:
                # 持续接收客户端传输的数据并写入文件
                data = client_socket.recv(1024)
                if not data:
                    break
                f.write(data)
        logging.info(f"音频文件已储存为 {filename}")
        
        # 將mp3轉成wav
        if audio_file_path.endswith('.mp3'):
            wav_audio_file_path = audio_file_path.replace('.mp3', '.wav')
            subprocess.run(['ffmpeg', '-i', audio_file_path, wav_audio_file_path])
            logging.info(f"音频文件已转换为 {wav_audio_file_path}")
            audio_file_path = wav_audio_file_path
            
        # 检查并创建 wav 文件
        if not os.path.isfile(wav_audio_file_path):
            subprocess.run(['ffmpeg', '-i', audio_file_path, wav_audio_file_path])
            logging.info(f"音频文件已转换为 {wav_audio_file_path}")
        
        # 将音频文件转换为文字
        result = audio_file_to_text(wav_audio_file_path)
        logging.info(f"转换后的文字内容：{result}")
        
         # 将转换结果发送回客户端
        client_socket.send(result.encode())
        
        # 将转换结果存储到文本文件中
        store_result(result, wav_audio_file_path, username, dateTime, filename)
        
    except Exception as e:
        logging.error(f"处理客户端连接时发生错误：{e}")
    finally:
        #關閉socket
        client_socket.close()

def store_result(result, wav_audio_file_path, username, dateTime, filename):
    # 初始化 Firebase Admin SDK（确保只初始化一次）
    initialize_firebase()
    
    bucket = storage.bucket() 
    # 上传文本文件到 Firebase Storage
    folder_path = f"text/{username}/{dateTime}/"

    # 上传文本文件到文件夹中
    file_name = f"{filename}.txt"
    text_blob = bucket.blob(f"{folder_path}{file_name}")
    text_blob.upload_from_string(result, content_type="text/plain")
    
    # 获取上传后的文件的公共 URL（可选）
    text_blob.make_public()
    public_url = text_blob.public_url

    print(f"文本文件已上传至 Firebase Storage，公共 URL 为: {public_url}")

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
