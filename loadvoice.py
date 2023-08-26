import socket
import subprocess
import os
import re
from datetime import datetime

import logging
from threading import Thread, active_count  #多線程

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

def sanitize_filename(filename):
    # 使用正規表示式過濾掉不可見字符和特殊字符，只保留英數字、底線、句點和連字符
    return re.sub(r'[^\w.-]', '', filename)

def handle_client_connection(client_socket):
    # 修改接收檔案名稱的部分，直接接收二進制數據
    filename_bytes = client_socket.recv(1024)

    # 不需要解碼，直接處理二進制數據即可
    filename = sanitize_filename(filename_bytes.decode('utf-8'))

     # 確保檔名是有效的
    filename = sanitize_filename(filename)
    
    # 將3gp檔案名稱加上日期時間前綴
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename_with_timestamp = f"AUDIO_{timestamp}_{filename}"

    with open(filename_with_timestamp, "wb") as f:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            f.write(data)
    logging.info(f"Audio file saved as {filename_with_timestamp}")
    
     # 获取输入文件的路径
    input_filepath = os.path.abspath(filename_with_timestamp)

    # 构建输出的MP3文件的路径
    output_directory = os.path.dirname(input_filepath)
    mp3_filename = os.path.join(output_directory, "com.mp3")

  # 转换为MP3格式
    ffmpeg_cmd = ["ffmpeg", "-i", filename_with_timestamp, "-acodec", "aac", mp3_filename]
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        logging.info(f"Audio file converted to {mp3_filename}")
        response = "Audio file received, saved, and converted to MP3"
        logging.info(f"MP3 file saved as {mp3_filename}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to convert audio file: {e}")
        response = "Failed to convert audio file"
    except Exception as e:
        logging.error(f"An error occurred during audio conversion: {e}")
        response = "An error occurred during audio conversion"

    client_socket.send(response.encode())
    client_socket.close()

    
def start_socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 3000))
    server.listen(5)
    logging.info("Listening on 0.0.0.0:3000")    #監聽客戶端連接

    while True:
        client_sock, address = server.accept()
        logging.info(f"Accepted connection from {address[0]}:{address[1]}")
        logging.info(f"Current active thread count: {active_count()}")
        client_handler = Thread(  
            target=handle_client_connection,
            args=(client_sock,)
        )
        client_handler.start()

Thread(target=start_socket_server).start()