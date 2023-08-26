import socket
from threading import Thread
import pyaudio
import wave

def record():
    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 2
    fs = 44100
    seconds = 5
    filename = "re.wav"

    p = pyaudio.PyAudio()

    print("開始錄音...")

    stream = p.open(format=sample_format, channels=channels, rate=fs, frames_per_buffer=chunk, input=True)

    frames = []

    for i in range(0, int(fs / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    print('錄音結束...')

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()

def handle_client_connection(client_socket):
    request = client_socket.recv(1024)
    print(f"Received: {request}")

    record()

    response = "錄音完成"
    client_socket.send(response.encode())
    client_socket.close()

def start_socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 3000))
    server.listen(5)
    print("Listening on 0.0.0.0:3000")

    while True:
        client_sock, address = server.accept()
        print(f"Accepted connection from {address[0]}:{address[1]}")
        client_handler = Thread(
            target=handle_client_connection,
            args=(client_sock,)
        )
        client_handler.start()

Thread(target=start_socket_server).start()
