import random

P = 907
G = 7

def generate_private_key():
    return random.randint(2, P - 2)

def calculate_public_key(private_key):
    return pow(G, private_key, P)

def calculate_shared_secret(peer_public_key, private_key):
    return pow(peer_public_key, private_key, P)

def get_des_key_bytes(shared_secret_int):
    des_key_string = str(shared_secret_int).zfill(8)[:8]
    
    return des_key_string.encode('utf-8')

if __name__ == "__main__":
    alice_private = generate_private_key()
    alice_public = calculate_public_key(alice_private)
    print(f"Alice sends public key: {alice_public}")
    
    bob_private = generate_private_key()
    bob_public = calculate_public_key(bob_private)
    print(f"Bob sends public key: {bob_public}")
    
    alice_secret = calculate_shared_secret(bob_public, alice_private)
    bob_secret = calculate_shared_secret(alice_public, bob_private)
    
    print(f"Alice's calculated secret: {alice_secret}")
    print(f"Bob's calculated secret: {bob_secret}")
    print(f"Secrets match? {alice_secret == bob_secret}")
    
    des_key = get_des_key_bytes(alice_secret)
    print(f"Final pyDes Key: {des_key} (Length: {len(des_key)} bytes)")