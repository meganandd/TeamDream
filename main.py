# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import webapp2
import jinja2
import os
from model import Dream
from aylienapiclient import textapi

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainPage (webapp2.RequestHandler):
    def get(self):
        home_template = JINJA_ENVIRONMENT.get_template('templates/home.html')
        self.response.write(home_template.render())

class EnterInfoHandler(webapp2.RequestHandler):
    def get(self):
        welcome_template = JINJA_ENVIRONMENT.get_template('templates/submit.html')
        self.response.write(welcome_template.render())

class ShowDreamHandler(webapp2.RequestHandler):
    def get(self):
        results_template = JINJA_ENVIRONMENT.get_template('templates/results.html')
        #self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(results_template.render(dream_dict))

    def post(self):
        client = textapi.Client("f02d5bcf", "f1bd4de2fe8c8bf3ea53946580b1afd4")
        results_template = JINJA_ENVIRONMENT.get_template('templates/results.html')
        dream_title = self.request.get("dream-title")
        dream_summary = self.request.get("dream-summary")
        sentiment = client.Sentiment({'text': dream_summary})
        dream_sentiment = sentiment["polarity"]
        print dream_sentiment

        dream = Dream(title=dream_title,
                    dream_text=dream_summary,
                    dream_sentiment=dream_sentiment)
        dream.put()

        all_dreams = Dream.query().fetch()

        dream_dict = {"title" : dream_title,
        "dream_summary" : dream_summary,
        "sentiment" : dream_sentiment,
        "all_dreams" : all_dreams}

        self.response.write(results_template.render(dream_dict))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/submit', EnterInfoHandler),
    ('/showdream', ShowDreamHandler),
], debug=True)
