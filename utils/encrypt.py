from hashlib import md5
from Cryptodome import Random
from Cryptodome.Cipher import AES
import base64

# pip install pycryptodomex

class EncryptionUtils:
    def __init__(self):
        self.key = bytes("c2VjcmV0cGFzc3dvcmRwaHJhc2U=", "utf-8")

    def bytes_to_key(self, data, salt, output=48):
        """creates key_iv"""
        assert len(salt) == 8, len(salt)
        data += salt
        key = md5(data).digest()
        final_key = key
        while len(final_key) < output:
            key = md5(key + data).digest()
            final_key += key
        return final_key[:output]
     
    def pad(self, data):
        bs = 16
        return data + (bs - len(data) % bs) * chr(bs - len(data) % bs)

    def unpad(self, data):
        """doing unpaddling"""
        return data[: -(data[-1] if type(data[-1]) == int else ord(data[-1]))]    
    
    def encrypt(self, input_data):
        """Encrypts password"""
        data = self.pad(input_data)
        salt = Random.new().read(8)
        key_iv = self.bytes_to_key(self.key, salt, 32 + 16)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = AES.new(key, AES.MODE_CBC, iv)
        self.encrypted_data = base64.b64encode(b"Salted__" + salt + aes.encrypt(bytes(data, "utf-8"))).decode('ascii')
        return self.encrypted_data


    def decrypt(self, encoded_data):
        """Decrypts password"""
        encrypted = base64.b64decode(encoded_data)
        assert encrypted[0:8] == b"Salted__"
        salt = encrypted[8:16]
        key_iv = self.bytes_to_key(self.key, salt, 32 + 16)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = AES.new(key, AES.MODE_CBC, iv)
        return self.unpad(aes.decrypt(encrypted[16:])).decode("utf-8")

if __name__ == '__main__':
    username = 'Tdw!us3r'
    print("Original data: ", username)
    ss = EncryptionUtils()
    encrypted_data = ss.encrypt(username)
    print("After Encryption: ", encrypted_data)
    decrypted_data = ss.decrypt('U2FsdGVkX19b/1HAmr/s3RYqjGjRdYr056oYUvgiu2w=')
    print("After Decryption: ", decrypted_data)