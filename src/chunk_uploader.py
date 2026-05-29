import socket
import json
import base64
import os
import datetime
import pyDes
from src import security_utils 

def start_chunk_uploader():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('', 6001))
    tcp_socket.listen(5)
    
    print("Chunk Uploader is persistently listening on port 6001...")

    try:
        while True:
            client_socket, addr = tcp_socket.accept()
            ip_address = addr[0]
            shared_secret = None 
            
            try:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break 
                        
                    payload = json.loads(data.decode('utf-8'))
                    upload_dir = "./upload_files" 
                    
                    if "key" in payload:
                        peer_public_key = int(payload["key"])
                        
                        my_private_key = security_utils.generate_private_key()
                        my_public_key = security_utils.calculate_public_key(my_private_key)
                        shared_secret = security_utils.calculate_shared_secret(peer_public_key, my_private_key)
                        
                        response_data = {"key": str(my_public_key)}
                        client_socket.send(json.dumps(response_data).encode('utf-8'))
                        
                    elif "requested_secured_content" in payload:
                        requested_chunk = payload["requested_secured_content"]
                        file_path = os.path.join(upload_dir, requested_chunk)
                        
                        if not shared_secret:
                            error_msg = {"error": "Key exchange not completed."}
                            client_socket.send(json.dumps(error_msg).encode('utf-8'))
                            break
                            
                        if os.path.exists(file_path):
                            with open(file_path, 'rb') as f:
                                raw_bytes = f.read()
                                
                            des_key_bytes = security_utils.get_des_key_bytes(shared_secret)
                            encrypted_bytes = pyDes.des(des_key_bytes, pyDes.ECB, pad=None, padmode=pyDes.PAD_PKCS5).encrypt(raw_bytes)
                            json_safe_string = base64.b64encode(encrypted_bytes).decode('utf-8')
                            
                            response_data = {
                                "chunk name": requested_chunk,          
                                "encrypted chunk": json_safe_string     
                            }
                            client_socket.send(json.dumps(response_data).encode('utf-8'))
                            
                            peer_name = "Unknown"
                            if os.path.exists('user_dictionary.json'):
                                try:
                                    with open('user_dictionary.json', 'r') as f:
                                        user_dict = json.load(f)
                                        peer_name = user_dict.get(ip_address, "Unknown")
                                except Exception:
                                    pass

                            with open("upload_log.txt", "a") as log:
                                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                log.write(f"[{timestamp}] SENT SECURE '{requested_chunk}' to {peer_name} ({ip_address})\n")
                        else:
                            error_msg = {"error": "Chunk not found"}
                            client_socket.send(json.dumps(error_msg).encode('utf-8'))
                        
                        break 
                        
                    elif "requested_content" in payload:
                        requested_chunk = payload["requested_content"]
                        file_path = os.path.join(upload_dir, requested_chunk)
                        
                        if os.path.exists(file_path):
                            with open(file_path, 'rb') as f:
                                raw_bytes = f.read()
                            
                            json_safe_string = base64.b64encode(raw_bytes).decode('utf-8')

                            response_data = {
                                "chunk name": requested_chunk,
                                "data": json_safe_string
                            }
                            client_socket.send(json.dumps(response_data).encode('utf-8'))
                            
                            peer_name = "Unknown"
                            if os.path.exists('user_dictionary.json'):
                                try:
                                    with open('user_dictionary.json', 'r') as f:
                                        user_dict = json.load(f)
                                        peer_name = user_dict.get(ip_address, "Unknown")
                                except Exception:
                                    pass

                            with open("upload_log.txt", "a") as log:
                                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                log.write(f"[{timestamp}] SENT UNSECURE '{requested_chunk}' to {peer_name} ({ip_address})\n")
                        else:
                            error_msg = {"error": "Chunk not found"}
                            client_socket.send(json.dumps(error_msg).encode('utf-8'))
                            
                        break 
                        
            except json.JSONDecodeError:
                pass 
            except Exception as e:
                print(f"Server error during transfer: {e}")
            finally:
                client_socket.close()
                
    except KeyboardInterrupt:
        pass
    finally:
        tcp_socket.close()

if __name__ == "__main__":
    start_chunk_uploader()