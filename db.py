import sqlalchemy as sq
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import yaml

import hashlib

engine = sq.create_engine("sqlite:///db.db", echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
  __tablename__ = 'User'
  
  id = sq.Column(sq.Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
  name = sq.Column(sq.String, nullable=False, unique=True)
  password = sq.Column(sq.String, nullable=False)
  
  def __init__(self, id, name, password):
    self.id = id
    self.name = name
    self.password = password
    
    f = open('config.yaml')
    self.config = yaml.safe_load(f)
    
    self.hashPass()
  
  def __repr__(self):
    return self.name
  
  def hashPass(self):
    passAndSalt = self.password + self.config['db']['salt']
    self.password = hashlib.md5(passAndSalt.encode()).hexdigest()
  

class Message(Base):
  __tablename__ = 'Message'
  
  id = sq.Column(sq.Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
  user_id = sq.Column(sq.Integer, nullable=False)
  text = sq.Column(sq.Text)
  date = sq.Column(sq.DateTime, default=datetime.utcnow())
  
  def __repr__(self):
    return self.id
  

if __name__ == '__main__':
  Base.metadata.create_all(engine)