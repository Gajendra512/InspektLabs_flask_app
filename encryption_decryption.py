from cryptography.fernet import Fernet

class EncryptionDecryption:
    def __init__(self, key):
        self.cipher_suite = Fernet(key)

    def encrypt_data(self, data):
        # Encrypt the data 
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return encrypted_data.decode()

    def decrypt_data(self, encrypted_data):
        # Decrypt the data 
        decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        return decrypted_data
