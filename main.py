#!/usr/bin/env python3
import tornado.ioloop
import tornado.web
import tornado.websocket
import yaml
from sqlalchemy import func, desc

import db
import funcPy
import cryp as crypLib

import os
import json


class MainHandler(tornado.web.RequestHandler):
  yaml = yaml.safe_load(open('config.yaml'))
  cryp = crypLib.Crpt()
  
  async def get_current_user(self):
    user = self.get_secure_cookie("user") 
    
    if user != None:
      return self.cryp.decrypCookie(user)
    
    return None
    

class WebSoket(tornado.websocket.WebSocketHandler):
  connections = set()
  cryp = crypLib.Crpt()
  
  def get_current_user(self):
    user = self.get_secure_cookie("user") 
    
    if user != None:
      return self.cryp.decrypCookie(user)
    
    return None
  
  def open(self):
    self.connections.add(self)
 
  def on_message(self, message):
    try:
      message = json.loads(message)
      userCookie = self.get_current_user()
      
      assert str(userCookie['id']) == message['user_id']
      
      session = db.Session()
      
      newMsg = db.Message(user_id=message['user_id'], text=message['text'])
      
      session.add(newMsg)
      session.commit()
      
      self.write_message({
        'err': None,
        'username': session.query(db.User.name).filter(db.User.id==message['user_id']).first()[0],
        'textMsg': message['text'],
      })
    except:
      self.write_message({'err': 404})
 
  def on_close(self):
    self.connections.remove(self)


class Index(MainHandler):
  async def get(self):
    try:
      context = dict()

      context['user'] = await self.get_current_user()
      
      session = db.Session()
      
      messages = session.query(db.Message).all()
      
      for m in range(0, len(messages)):
        msg = {
          'id': messages[m].id,
          'text': messages[m].text,
          'date': messages[m].date,
        }
        
        username = session.query(db.User.name).filter(db.User.id==messages[m].user_id).first()[0]
        
        msg['username'] = username
        messages[m] = msg
        
      context['messages'] = messages
      context['ws'] = self.yaml['settings']['webSoketUrl']
      
      self.render('templates/index.html', data=context)
    except:
      raise tornado.web.HTTPError(
        status_code=404,
        reason="Error"
      )


class Register(MainHandler):
  async def get(self):
    getErr = self.get_secure_cookie('errRegister')
    context = {'err': None}
    
    if getErr != None:
      context['err'] = getErr.decode()
      self.clear_cookie('errRegister')
      
    self.render('templates/register.html', data=context)
    
  async def post(self):
    try:
      userData = {
        "name": self.get_body_argument("username", default=None, strip=False),
        "password1": self.get_body_argument("password1", default=None, strip=False),
        "password2": self.get_body_argument("password2", default=None, strip=False),
      }
      
      assert userData["password1"] == userData["password2"]
      assert len(userData["password1"]) > 7
      
      session = db.Session()
      
      checkUserId = session.query(db.User.id).filter(db.User.name==userData['name']).first()
      
      if checkUserId != None:
        self.set_secure_cookie('errRegister', 'Никнейм занят!')
        self.redirect('/register')
      
      maxUserId = session.query(db.User.id).order_by(desc(db.User.id)).first()[0]
      
      newUser = db.User(id=maxUserId+1, name=userData['name'], password=userData['password1'])
      session.add(newUser)
      
      session.commit()
      
      self.redirect('/login')
    except:
      raise tornado.web.HTTPError(
        status_code=404,
        reason="Error"
      )
      

class Login(MainHandler):
  async def get(self):
    errLogin = self.get_secure_cookie('errLogin')
    context = {'err': None}
    
    if errLogin != None:
      context['err'] = errLogin.decode()
      self.clear_cookie('errLogin')
    
    self.render('templates/login.html', data=context)
    
  async def post(self):
    try:
      userData = {
        'name': self.get_body_argument("username", default=None, strip=False),
        'password': funcPy.heshPass(
          self.get_body_argument("password", default=None, strip=False),
          self.yaml['db']['salt'],
        ),
      }
      
      session = db.Session()
      
      userId = session.query(db.User.id).filter(
        db.User.name == userData['name'] and db.User.password == userData['password']
      ).first()
      
      if userId == None:
        self.set_secure_cookie('errLogin', 'Такого пользователя не существует!')
        self.redirect('/login')
      
      cookieUser = {'id': userId[0], 'name': userData['name']}
      enCookieUser = self.cryp.encrypCookie(cookieUser)

      self.set_secure_cookie('user', enCookieUser, expires_days=30)
      
      self.redirect('/')
    except:
      raise tornado.web.HTTPError(
        status_code=404,
        reason="Error"
      )
    


class Application(tornado.web.Application):
  def __init__(self):
    f = open('config.yaml')
    self.config = yaml.safe_load(f)
    
    handlers = [
      (r"/", Index),
      (r"/register", Register),
      (r"/login", Login),
      (r"/websocket", WebSoket),
    ]
    
    settings = dict(
      cookie_secret = self.config['settings']['secrytKey'],
      static_path = os.path.join(os.path.dirname(__file__), "static"),
      templates_path = os.path.join(os.path.dirname(__file__), "templates"),
      xsrf_cookies = True,
    )
    
    super(Application, self).__init__(handlers, **settings)
  

def main():
  app = Application()
  app.listen(app.config['settings']['port'])
  
  print("RUN SERVER")
  tornado.ioloop.IOLoop.current().start()
  print("STOP SERVER")
  

if __name__ == '__main__':
  main()
