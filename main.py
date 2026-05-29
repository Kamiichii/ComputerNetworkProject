import threading
import time
import json
from src import chunk_downloader
from src import chunk_announcer
from src import content_discovery
from src import chunk_uploader


def load_network_data():
    try:
        with open('content_dictionary.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("\n[!] Error: 'content_dictionary.json' not found.")
        print("Make sure content_discovery.py is running and saving data.")
        return {}

def load_username_to_ip():
    try:
        with open('username_to_ip.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def view_contents():
    network_data = load_network_data()
    if not network_data:
        return

    print("\n--- Available Content in Network ---")
    available_files = set()
    for chunk_name in network_data.keys():
        base_name = chunk_name.rsplit('_', 1)[0] 
        available_files.add(base_name)
    
    for file in available_files:
        print(f"- {file}")
    print("------------------------------------")

def download_content():
    network_data = load_network_data()
    if not network_data:
        print("\n[!] No network data available.")
        return
        
    available_files_set = set()
    for chunk_name in network_data.keys():
        base_name = chunk_name.rsplit('_', 1)[0] 
        available_files_set.add(base_name)
        
    available_files_list = sorted(list(available_files_set))

    print("\n--- Available Files ---")
    for index, file_name in enumerate(available_files_list, 1):
        print(f"{index}. {file_name}")
    print("-----------------------")

    try:
        choice = int(input("\nSelect the number of the file you want to download: "))
        
        if choice < 1 or choice > len(available_files_list):
            print("[!] Invalid selection.")
            return
            
        target_file = available_files_list[choice - 1]
        
    except ValueError:
        print("[!] Please enter a valid number, not a word.")
        return
        
    security_choice = input("Do you want to download securely? (yes/no): ").strip().lower()
    is_secure = (security_choice == 'yes')

    print(f"\n[System] Initiating download for '{target_file}'...")
    
    all_chunks_downloaded = True
    ip_lookup = load_username_to_ip()

    for i in range(1, 4):
        chunk_name = f"{target_file}_{i}"

        if chunk_name not in network_data or not network_data[chunk_name]:
            print(f"CHUNK {chunk_name} CANNOT BE DOWNLOADED FROM ONLINE PEERS.")
            all_chunks_downloaded = False
            break
            
        chunk_downloaded = False
        
        for target_user in network_data[chunk_name]:
            
            target_ip = ip_lookup.get(target_user)
            if not target_ip:
                continue
                
            print(f"Requesting {chunk_name} from {target_user} ({target_ip})...")
            
            success, message = chunk_downloader.fetch_chunk(target_ip, chunk_name, is_secure)
            
            if success:
                print(f"-> {message}")
                chunk_downloaded = True
                break 
            else:
                print(f"-> Failed: {message}")
                
        if not chunk_downloaded:
            print(f"CHUNK {chunk_name} CANNOT BE DOWNLOADED FROM ONLINE PEERS.")
            all_chunks_downloaded = False
            break

    if all_chunks_downloaded:
        print(f"\nMerging chunks for '{target_file}'...")
        merge_success, merge_result = chunk_downloader.merge_chunks(target_file)
        
        if merge_success:
            print(f"-> SUCCESS! File merged and saved as '{merge_result}'")
        else:
            print(f"-> Failed to merge: {merge_result}")
    else:
        print("\n[!] Download aborted due to missing chunks.")

def view_history():
    try:
        with open("download_log.txt", "r") as f:
            print("\n--- Download History ---")
            print(f.read())
            print("------------------------")
    except FileNotFoundError:
        print("\nNo download history found yet.")

def start_background_services(user_name):
    print("\n[System] Booting up network nodes...")
    
    # 1. Start the UDP Announcer
    announcer_thread = threading.Thread(target=chunk_announcer.start_announcer, args=(user_name,), daemon=True)
    announcer_thread.start()
    
    # 2. Start the UDP Content Discovery
    discovery_thread = threading.Thread(target=content_discovery.start_content_discovery, daemon=True)
    discovery_thread.start()
    
    # 3. Start the TCP Chunk Uploader
    uploader_thread = threading.Thread(target=chunk_uploader.start_chunk_uploader, daemon=True)
    uploader_thread.start()

    time.sleep(1.5)
    print("[System] All background services running!\n")

def main_menu():
    while True:
        print("\n=== P2P File Sharing ===")
        print("1. View Available Contents")
        print("2. Download Content")
        print("3. View Download History")
        print("4. Exit")
        
        choice = input("Select an option (1-4): ").strip()
        
        if choice == '1':
            view_contents()
        elif choice == '2':
            download_content()
        elif choice == '3':
            view_history()
        elif choice == '4':
            print("Shutting down nodes and exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    print("=== System Initialization ===")
    user_name = input("Enter your username: ").strip()
    
    master_file = input("Enter the path to the file you want to host (e.g., ./forest.png): ").strip()
    
    success = chunk_announcer.split_file_into_chunks(master_file)
    
    if success:
        start_background_services(user_name)
        main_menu()
    else:
        print("\nSystem boot failed. Check your file path and try again.")