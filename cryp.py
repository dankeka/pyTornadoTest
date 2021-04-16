import yaml
import json
from Crypto.Cipher import DES

class Crpt:
  conf = yaml.safe_load(open('config.yaml'))
  
  def __init__(self):
    self.key = self.conf['crypto']['key'].encode('utf-8')
  
  def pad(self, text):
    while len(text) % 8 != 0:
      text += ' '
      
    return text
  
  def encryp(self, text):
    des = DES.new(self.key, DES.MODE_ECB)
    padded_text = self.pad(text)
    encrypted_text = des.encrypt(padded_text.encode('utf-8'))
    
    return encrypted_text
    
  def decryp(self, text: bytes):
    des = DES.new(self.key, DES.MODE_ECB)
    res = des.decrypt(text).decode('utf-8')
    
    if res.endswith(" "):
      while res.endswith(" "):
        res = res[:-1]
        
    return res
  
  def encrypCookie(self, jsonData):
    jsonDump = json.dumps(jsonData)
    
    return self.encryp(jsonDump)
  
  def decrypCookie(self, cookie):
    jsonStr = self.decryp(cookie)
    
    return json.loads(jsonStr)
