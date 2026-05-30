import socket
import json
import base64
import datetime
import pyDes
import os
from src import security_utils

def log_download(chunk_name, ip_address):
    peer_name = "Unknown"
    
    if os.path.exists('user_dictionary.json'):
        try:
            with open('user_dictionary.json', 'r') as f:
                user_dict = json.load(f)
                peer_name = user_dict.get(ip_address, "Unknown")
        except Exception:
            pass

    with open("download_log.txt", "a") as log:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{timestamp}] RECEIVED '{chunk_name}' from {peer_name} ({ip_address})\n")

def merge_chunks(base_filename, num_chunks=3, download_dir="./upload_files"):
    os.makedirs(download_dir, exist_ok=True)
    
    name, ext = os.path.splitext(base_filename)
    output_filename = f"{name}_merged{ext}"
    output_filepath = os.path.join(download_dir, output_filename)
    
    try:
        with open(output_filepath, 'wb') as outfile:
            for i in range(1, num_chunks + 1):
                chunk_name = f"{base_filename}_{i}"
                chunk_filepath = os.path.join(download_dir, chunk_name)
                
                with open(chunk_filepath, 'rb') as infile:
                    outfile.write(infile.read())
        return True, output_filepath
    except Exception as e:
        return False, str(e)

def fetch_chunk(target_ip, chunk_name, is_secure=False, download_dir="./upload_files"):
    target_port = 6001
    tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    os.makedirs(download_dir, exist_ok=True)
    chunk_filepath = os.path.join(download_dir, chunk_name)
    
    try:
        tcp_client.settimeout(5.0) 
        tcp_client.connect((target_ip, target_port))
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Requesting chunk '{chunk_name}' from {target_ip}...")
        
        if is_secure:
            my_private_key = security_utils.generate_private_key()
            my_public_key = security_utils.calculate_public_key(my_private_key)
            
            key_payload = {"key": str(my_public_key)}
            tcp_client.send(json.dumps(key_payload).encode('utf-8'))
            
            key_response_data = tcp_client.recv(65536) 
            if not key_response_data:
                return False, "Server dropped connection during key exchange."
                
            key_response = json.loads(key_response_data.decode('utf-8'))
            if "key" not in key_response:
                return False, "Server failed to return a valid public key."
                
            server_public_key = int(key_response["key"])
            shared_secret = security_utils.calculate_shared_secret(server_public_key, my_private_key)
            
            request_payload = {"requested_secured_content": chunk_name}
            tcp_client.send(json.dumps(request_payload).encode('utf-8'))
            
            response_data = b""
            while True:
                packet = tcp_client.recv(65536)
                if not packet:
                    break
                response_data += packet
                
            if not response_data:
                return False, "No data received for secure file."
                
            response = json.loads(response_data.decode('utf-8'))
            
            if "encrypted chunk" in response:
                encrypted_bytes = base64.b64decode(response["encrypted chunk"])
                des_key_bytes = security_utils.get_des_key_bytes(shared_secret)
                raw_bytes = pyDes.des(des_key_bytes, pyDes.ECB, pad=None, padmode=pyDes.PAD_PKCS5).decrypt(encrypted_bytes)
                
                with open(chunk_filepath, 'wb') as f:
                    f.write(raw_bytes)
                
                log_download(chunk_name, target_ip)
                return True, f"Successfully and securely downloaded {chunk_name}"
                
            elif "error" in response:
                return False, f"Server error: {response['error']}"
            else:
                return False, "Unknown response format from peer."

        else:
            request_payload = {"requested_content": chunk_name}
            tcp_client.send(json.dumps(request_payload).encode('utf-8'))
            
            response_data = b""
            while True:
                packet = tcp_client.recv(65536)
                if not packet:
                    break
                response_data += packet
                
            if not response_data:
                return False, "No data received from peer."
                
            response = json.loads(response_data.decode('utf-8'))
            
            if "data" in response:
                raw_bytes = base64.b64decode(response["data"])
                
                with open(chunk_filepath, 'wb') as f:
                    f.write(raw_bytes)
                
                log_download(chunk_name, target_ip)
                return True, f"Successfully downloaded {chunk_name}"
                
            elif "error" in response:
                return False, f"Server error: {response['error']}"
            else:
                return False, "Unknown response format from peer."
                
    except socket.timeout:
        return False, "Connection timed out."
    except ConnectionRefusedError:
        return False, "Connection refused. Is the peer's uploader running?"
    except Exception as e:
        return False, str(e)
    finally:
        tcp_client.close()