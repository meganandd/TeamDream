from google.appengine.ext import ndb

class Dream(ndb.Model):
    title = ndb.StringProperty(required = True)
    dream_text = ndb.StringProperty(required = True)
    dream_sentiment = ndb.StringProperty(required = True)
    dream_date = ndb.StringProperty(required = True)

class Acc(ndb.Model):
    username = ndb.StringProperty(required = True)
    password = ndb.StringProperty(required = True)
    
