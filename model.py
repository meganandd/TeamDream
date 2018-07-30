from google.appengine.ext import ndb

class Dream(ndb.Model):
    title = ndb.StringProperty(required = True)
    dream_text = ndb.StringProperty(required = True)
    dream_sentiment = ndb.StringProperty(required = True)
