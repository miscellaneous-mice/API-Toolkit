from utils.encrypt import EncryptionUtils
import yaml

with open('configs/config.yaml') as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)

ss = EncryptionUtils()
encrypted_data = ss.encrypt(config['password'])
print("After Encryption: ", encrypted_data)
decrypted_data = ss.decrypt(encrypted_data)
print("After Decryption: ", decrypted_data)


