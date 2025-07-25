import cv2 
import numpy as np
import hashlib
import time
from cryptography.fernet import Fernet
import numpy as np
from PIL import Image
from tinydb import TinyDB, Query
from sklearn.neighbors import LocalOutlierFactor
import os

# Database setup 
db = TinyDB('db.json')

def add_user(username, password):
    db.insert({'username': username, 'password': password})

def authenticate_user(username, password):
    User = Query()
    result = db.search((User.username == username) & (User.password == password))
    return len(result) > 0

# Block class for blockchain
class Block:
    def __init__(self, index, timestamp, image_hash, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.image_hash = image_hash
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        sha = hashlib.sha256()
        sha.update(f'{self.index}{self.timestamp}{self.image_hash}{self.previous_hash}'.encode('utf-8'))
        return sha.hexdigest()

class Blockchain:
    def __init__(self):  
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.hash = new_block.calculate_hash()
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

# Encryption and Blockchain Integration
def generate_key():
    os.makedirs('keys', exist_ok=True)
    key = Fernet.generate_key()
    with open('keys/secret.key', 'wb') as key_file:
        key_file.write(key)

def load_key():
    return open('keys/secret.key', 'rb').read()

def load_image(image_path):
    return np.array(Image.open(image_path))

def save_image(image_array, save_path):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    image = Image.fromarray(image_array)
    image.save(save_path)

def encrypt_image(image_path):
    key = load_key()
    fernet = Fernet(key)
    image = load_image(image_path)
    image_bytes = image.tobytes()
    encrypted_bytes = fernet.encrypt(image_bytes)
    encrypted_image = np.frombuffer(encrypted_bytes, dtype=np.uint8)
    encrypted_image = encrypted_image[:image.size].reshape(image.shape)
    return encrypted_image, encrypted_bytes

def decrypt_image(encrypted_bytes, image_shape):
    key = load_key()
    fernet = Fernet(key)
    decrypted_bytes = fernet.decrypt(encrypted_bytes)
    decrypted_image = np.frombuffer(decrypted_bytes, dtype=np.uint8).reshape(image_shape)
    return decrypted_image

def add_image_to_blockchain(image_hash, blockchain):
    latest_block = blockchain.get_latest_block()
    new_block = Block(len(blockchain.chain), time.time(), image_hash, latest_block.hash)
    blockchain.add_block(new_block)

if __name__ == "__main__":
    
    add_user('admin', 'admin123')
    username = input("Enter your username: ")
    password = input("Enter your password: ")

    if authenticate_user(username, password):
        print("Access Granted")

        # Initialize blockchain
        blockchain = Blockchain()

        # Generate encryption key and encrypt image
        generate_key()
        encrypted_image, encrypted_bytes = encrypt_image('brain_mri.jpg')

        # Compute image hash and add it to the blockchain
        image_hash = hashlib.sha256(encrypted_bytes).hexdigest()
        add_image_to_blockchain(image_hash, blockchain)

        # Validate the blockchain
        if blockchain.is_chain_valid():
            print("Blockchain is valid. Image securely stored and transmitted.")
            
            # Display blockchain content
            print("\nBlockchain Content:")
            for block in blockchain.chain:
                print(f"Block {block.index}:")
                print(f"Timestamp: {block.timestamp}")
                print(f"Image Hash: {block.image_hash}")
                print(f"Previous Hash: {block.previous_hash}")
                print(f"Block Hash: {block.hash}\n")
        else:
            print("Blockchain validation failed.")

        # Decrypt the image  
        decrypted_image = decrypt_image(encrypted_bytes, encrypted_image.shape)
        print("Displaying decrypted image:")
        Image.fromarray(decrypted_image).show()

    else:
        print("Access Denied")


def detect_altered_regions(original_path, uploaded_path):
    """Identify which brain regions are altered in the uploaded MRI compared to the original."""
    original = cv2.imread(original_path, cv2.IMREAD_GRAYSCALE)
    uploaded = cv2.imread(uploaded_path, cv2.IMREAD_GRAYSCALE)

    if original is None or uploaded is None:
        return []

    # Resize if necessary
    if original.shape != uploaded.shape:
        uploaded = cv2.resize(uploaded, (original.shape[1], original.shape[0]))

    # Compute absolute difference
    diff = cv2.absdiff(original, uploaded)
    
    # Threshold the difference to focus on significant changes
    _, thresholded = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

    height, width = thresholded.shape

    # Define approximate region boundaries
    regions = {
        "Left Frontal Lobe": (0, 0, width // 2, height // 3),
        "Right Frontal Lobe": (width // 2, 0, width, height // 3),
        "Left Temporal Lobe": (0, height // 3, width // 2, 2 * height // 3),
        "Right Temporal Lobe": (width // 2, height // 3, width, 2 * height // 3),
        "Parietal Lobe": (0, 2 * height // 3, width, height),
        "Occipital Lobe": (width // 4, 2 * height // 3, 3 * width // 4, height)
    }

    altered_regions = []

    for region, (x1, y1, x2, y2) in regions.items():
        region_diff = thresholded[y1:y2, x1:x2]
        if np.sum(region_diff) > 5000:  # If significant changes detected
            altered_regions.append(region)

    return altered_regions
