import socket
import json
import time
import threading

ip_to_username = {}
content_dictionary = {}
last_seen_timestamps = {} 
username_to_ip = {} 

def wipe_old_entries():
    while True:
        time.sleep(10) 
        current_time = time.time()
        
        ips_to_remove = [ip for ip, ts in last_seen_timestamps.items() if current_time - ts > 60]
                
        if ips_to_remove:
            print(f"[System] Purging {len(ips_to_remove)} stale peers.")
            for ip in ips_to_remove:
                username = ip_to_username.get(ip)
                last_seen_timestamps.pop(ip, None)
                ip_to_username.pop(ip, None)
                if username:
                    username_to_ip.pop(username, None)
            
            with open('user_dictionary.json', 'w') as f:
                json.dump(ip_to_username, f)
            with open('username_to_ip.json', 'w') as f:
                json.dump(username_to_ip, f)

def start_content_discovery():
    threading.Thread(target=wipe_old_entries, daemon=True).start()
    
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(('', 6000))

    try:
        while True:
            data, addr = udp_socket.recvfrom(1024)
            ip_address = addr[0]
            
            try:
                payload = json.loads(data.decode('utf-8'))
                if "username" in payload and "chunks" in payload:
                    username = payload["username"]
                    chunks = payload["chunks"]
                    
                    ip_to_username[ip_address] = username
                    username_to_ip[username] = ip_address 
                    last_seen_timestamps[ip_address] = time.time()
                    
                    for chunk, users in list(content_dictionary.items()):
                        if username in users:
                            users.remove(username)
                        if not users:
                            del content_dictionary[chunk]
                    
                    for chunk in chunks:
                        if chunk not in content_dictionary:
                            content_dictionary[chunk] = []
                        if username not in content_dictionary[chunk]:
                            content_dictionary[chunk].append(username)
                            
                    print(f"\n[Discovery] {username}: {', '.join(chunks)}")
                    
                    with open('content_dictionary.json', 'w') as f:
                        json.dump(content_dictionary, f)
                        f.flush()
                    
                    with open('user_dictionary.json', 'w') as f:
                        json.dump(ip_to_username, f)
                        
                    with open('username_to_ip.json', 'w') as f:
                        json.dump(username_to_ip, f)
                        
            except json.JSONDecodeError:
                pass
    except Exception:
        pass
    finally:
        udp_socket.close()