#!/usr/bin/env python
#
# Copyright 2008 Brian Hartvigsen
#

import wsgiref.handlers
import pngcanvas, struct, base64, re

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.api import mail

class Email(db.Model):
    user = db.UserProperty()
    email = db.StringProperty()
    data = db.BlobProperty()
    activated = db.BooleanProperty()
    added = db.DateProperty(auto_now_add=True)
    
class ConfirmHandler(webapp.RequestHandler):
    def get(self):
        key = self.request.get('i')
        if not key == '':
            try:
                e = db.get(db.Key(key))
                if e is not None:
                    e.activated = True
                    email = e.email
                    e.email = ''
                    
                    f = open('font.png', 'rb')
                    img = pngcanvas.PNGCanvas(len(email) * 6, 11)
                    font = pngcanvas.PNGCanvas(1,1)
                    font.load(f)
                    f.close()
                    i = 0
                    for c in email:
                        delta = ord(c)
                        
                        if (delta >= 97 and delta <= 122):
                            delta = delta - 97
                        elif (delta >= 48 and delta <= 57):
                            delta = delta - 48 + 26
                        elif c == '-':
                            delta = 36
                        elif c == '_':
                            delta = 37
                        elif c == '+':
                            delta = 38
                        elif c == '.':
                            delta = 39
                        elif c == '@':
                            delta = 40
                        
                        font.copyRect(delta * 6, 0, delta * 6 + 5, 10, i * 6, 0, img)
                        i = i + 1
                        
                    e.data = img.dump()
                    
                    e.put()
                    if users.get_current_user() is not None:
                        self.redirect('/manage?m=%s' % base64.b64encode("%s successfully confirmed, address has been purged" % email))
                    else:
                        self.redirect('/')
                else:
                    if users.get_current_user() is not None:
                        self.redirect('/manage?m=%s' % base64.b64encode('Key not found'))
                    else:
                        self.redirect('/')
            except db.BadKeyError:
                self.redirect('/')
        else:
            if users.get_current_user() is not None:
                self.redirect('/manage?m=%s' % base64.b64encode('No key given'))
            else:
                self.redirect('/')

class DeleteHandler(webapp.RequestHandler):
    def get(self):
        key = self.request.get('i')
        if not key == '':
            try:
                e = db.get(db.Key(key))
                if e is None or not e.user == users.get_current_user():
                    self.redirect('/manage?m=%s' % base64.b64encode('Not your email address'))
                else:
                    e.delete()
                    self.redirect('/manage?m=%s' % base64.b64encode('Successfully deleted'))
            except db.BadKeyError:
                self.redirect('/manage?m=%s' % base64.b64encode('Key not found'))
        else:
            self.redirect('/manage')

class ManageHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        q = Email.gql("WHERE user = :1", user)
        message = self.request.get('m')
        if message == '':
            message = False
        else:
            message = base64.b64decode(message)
        
        values = {
            'greeting': "Welcome %s!" % user.nickname(),
            'url': users.create_logout_url("/"),
            'link': 'sign out',
            'emails': q.fetch(25),
            'message': message
        }
        
        self.response.out.write(template.render('manage.html', values))

    def post(self):
        email = self.request.get("email").lower()
        if mail.is_email_valid(email) and re.match("[a-z0-9.+_-]+@[a-z0-9._-]+\.[a-z]+", email, re.I) is not None:
            e = Email()
            e.email = email
            e.user = users.get_current_user()
            e.activated = False
            e.put()
            sender_address = "tresni@gmail.com"
            subject = "[StringImage] Confirm email address"
            body = """
Thank you for protecting %s with StringImage.  Please confirm that this is an email address you control by clicking on the link below:

http://stringimage.appspot.com/confirm?i=%s
""" % (email, e.key())
            mail.send_mail(sender_address, email, subject, body)
            self.redirect("/manage?m=%s" % base64.b64encode('An email has been sent to %s.  Click the link in the email to activate StringImage' % email))
        else:
            self.redirect("/manage?m=%s" % base64.b64encode("Email address does not appear valid.  We support email addresses using alpha-numeric characters, plus signs, hyphens, underscores, and periods."))

class ImageHandler(webapp.RequestHandler):
    def get(self):
        img = self.request.get('i')
        if img != '':
            data = memcache.get(img)
            if data is None:
                try:
                    email = db.get(db.Key(img))
                    if email is None:
                        self.redirect('/error.png')
                        return
                    elif email.activated == True:
                        data = email.data
                        memcache.add(img, data)
                    else:
                        self.redirect('/not-validated.png')
                        return
                except db.BadKeyError:
                    self.redirect('/error.png')
                    return
                    
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(data)
        else:
            self.redirect('/error.png')

class MainHandler(webapp.RequestHandler):   
  def get(self):
    user = users.get_current_user()
    if user is not None:
        greeting = "Welcome %s!" % user.nickname()
        url = users.create_logout_url("/")
        link = "sign out"
    else:
        greeting = "Welcome!"
        url = users.create_login_url("/manage")
        link = "sign in"
        
    values = {
        'greeting': greeting,
        'url': url,
        'link': link
    }
    self.response.out.write(template.render('index.html', values))
    
class AdminHandler(webapp.RequestHandler):
    def get(self):           
        stats = memcache.get_stats()
        values = {
            'greeting': "Welcome %s!" % users.get_current_user().nickname(),
            'url': users.create_logout_url("/"),
            'link': 'sign out',
            'hits': stats['hits'],
            'misses': stats['misses']
        }
        self.response.out.write(template.render('admin.html', values))

def main():
  application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/image', ImageHandler),
    ('/manage', ManageHandler),
    ('/confirm', ConfirmHandler),
    ('/delete', DeleteHandler),
    ('/admin', AdminHandler)
  ], debug=True)
  
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
