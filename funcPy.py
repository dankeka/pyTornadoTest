import hashlib

def heshPass(password, salt):
  passAndSalt = password + salt
  password = hashlib.md5(passAndSalt.encode()).hexdigest()
  
  return password
