import socket
import subprocess
import os
import re
from datetime import datetime

import logging
from threading import Thread, active_count

import speech_recognition as sr

# 配置日志记录，设置日志级别为DEBUG，格式为'[级别] 消息'
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

def sanitize_filename(filename):
    # 使用正則表達式將文件名中的非法字符替換為空
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
    # 接收客戶端傳送的檔名
    filename = client_socket.recv(1024).decode('utf-8')
    # 對檔名進行清理，確保它只包含合法字符
    filename = sanitize_filename(filename)       
            
    # 生成帶有時間戳的檔名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename_with_timestamp = f"AUDIO_{timestamp}_{filename}.3gp"

    with open(filename_with_timestamp, "wb") as f:
        while True:
            # 持續接收客戶端傳輸的數據並寫入檔案
            data = client_socket.recv(1024)
            if not data:
                break
            f.write(data)
    logging.info(f"音訊檔案已儲存為 {filename_with_timestamp}")
    
    # 將音頻檔案轉換為文字
    result = audio_file_to_text(filename_with_timestamp)
    logging.info(f"轉換後的文字內容：{result}")
    
    # 傳送回應消息給客戶端
    response = "音訊已接收、儲存並轉換為文字"
    client_socket.send(response.encode())
    client_socket.close()

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
