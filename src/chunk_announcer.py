import socket
import time
import json
import os
import math

def split_file_into_chunks(filepath, output_dir="./upload_files"):

    if not os.path.exists(filepath):
        print(f"\n[!] Error: Original file '{filepath}' not found.")
        return False

    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.basename(filepath)
    
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return False
        
    chunk_size = math.ceil(file_size / 3)
    
    try:
        with open(filepath, 'rb') as f:
            for i in range(1, 4):
                chunk_data = f.read(chunk_size)
                
                chunk_filename = f"{base_name}_{i}"
                chunk_filepath = os.path.join(output_dir, chunk_filename)
                
                with open(chunk_filepath, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)
                    
        print(f"\n[System] Successfully generated 3 chunks for '{base_name}'")
        return True
    except Exception as e:
        print(f"[!] Error splitting file: {e}")
        return False

def get_available_chunks(directory="./upload_files"):
    chunks = []
    if not os.path.exists(directory):
        return chunks
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            if not filename.endswith(('.py', '.txt', '.json')) and "_merged" not in filename:
                chunks.append(filename)
    return chunks

def start_announcer(username):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_ip = "192.168.1.255"
    broadcast_port = 6000

    try:
        while True:
            current_chunks = get_available_chunks()
            live_data = {
                "username": username,
                "chunks": current_chunks
            }
            message_bytes = json.dumps(live_data).encode('utf-8')
            udp_socket.sendto(message_bytes, (broadcast_ip, broadcast_port))
            time.sleep(8)
    except KeyboardInterrupt:
        pass
    finally:
        udp_socket.close()