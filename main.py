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
import requests
import requests_toolbelt.adapters.appengine
from google.appengine.api import urlfetch
import json

requests_toolbelt.adapters.appengine.monkeypatch()

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
        results_template = JINJA_ENVIRONMENT.get_template('templates/results.html')

        dream_title = self.request.get("dream-title") #get the title from the respective input tag in submit.html
        dream_date = self.request.get("dream-date")
        dream_summary = self.request.get("dream-summary") #get the summary from the rescpetive input tag in submit.html
        url = "https://gateway.watsonplatform.net/tone-analyzer/api/v3/tone?version=2017-09-21&text=" + dream_summary

        r = requests.get(url, auth=("12b8c206-770b-4989-9909-2c1c625c9a8d", "nMHwFGhjTHIT"))
        json_result = json.loads(r.text)["document_tone"]["tones"][0]["tone_name"]

        dream_sentiment = json_result

        dream = Dream(title=dream_title,
                    dream_date=dream_date,
                    dream_text=dream_summary,
                    dream_sentiment=dream_sentiment)
        dream.put()

        all_dreams = Dream.query().fetch()

        dream_dict = {"title" : dream_title,
        "date" : dream_date,
        "dream_summary" : dream_summary,
        "sentiment" : dream_sentiment,
        "all_dreams" : all_dreams}

        self.response.write(results_template.render(dream_dict))

class DreamDataHandler(webapp2.RequestHandler):
    def get(self):
        data_template = JINJA_ENVIRONMENT.get_template('templates/data.html')

        #get occurance of each sentiment in all dreams in DataStore
        sentiments = []
        possible_sentiments = ["Fear", "Anger", "Joy", "Confident", "Analytical", "Sadness", "Tentative"]

        vardict = {}
        for i in possible_sentiments:
            vardict[i] = 0
            vardict[i] = len(Dream.query().filter(Dream.dream_sentiment==i).fetch())

        #get total number of dreams
        total_dreams = len(Dream.query().fetch())
        vardict["total"] = total_dreams

        #get day of the week frequency

        print vardict
    



        self.response.write(data_template.render(vardict))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/submit', EnterInfoHandler),
    ('/showdream', ShowDreamHandler),
    ('/showdata', DreamDataHandler),
], debug=True)
