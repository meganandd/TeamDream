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
from model import Acc
import requests
import requests_toolbelt.adapters.appengine
from google.appengine.api import urlfetch
import json
import datetime
import operator
from webapp2_extras import sessions
requests_toolbelt.adapters.appengine.monkeypatch()

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainPage (webapp2.RequestHandler):
    def get(self):
        home_template = JINJA_ENVIRONMENT.get_template('templates/home.html')
        self.response.write(home_template.render())

class AboutPage (webapp2.RequestHandler):
    def get(self):
        about_template = JINJA_ENVIRONMENT.get_template('templates/About.html')
        self.response.write(about_template.render())

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
         #Returns a session using the default cookie key.
        return self.session_store.get_session()
class LogIn(BaseHandler):
    def get(self):
        login_template=JINJA_ENVIRONMENT.get_template('templates/login.html')
        acc_name=self.request.get("acc-name")
        acc_pass=self.request.get("acc-pass")

        if Acc.query().filter(Acc.username == acc_name).fetch() and Acc.query().filter(Acc.password == acc_pass).fetch():
            print ":)"
        else:
            print "Username or Password is incorrect"

        self.response.write(login_template.render())
        # allpasswords=Acc.query().filter(Acc.password == acc_pass).fetch()

class AllDreams (webapp2.RequestHandler):
    def get(self):
        all_dreams = Dream.query().order(Dream.dream_date).fetch()
        dream_dict = {
        "all_dreams" : all_dreams}
        all_template = JINJA_ENVIRONMENT.get_template('templates/alldreams.html')
        self.response.write(all_template.render(dream_dict))

class CreateAccount(BaseHandler):
    def get(self):

        acc_template=JINJA_ENVIRONMENT.get_template('templates/CreateAccount.html')
        user_name = self.request.get("user-name") #get the title from the respective input tag in submit.html
        pass_word = self.request.get("pass-word")

        account = Acc(username=user_name, password=pass_word)
        account.put()

        self.session["username"]=user_name
        self.session["password"]=pass_word
        self.response.write(acc_template.render())

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

        #get day of the week frequency#date frequency
        all_dates = []
        for dream in Dream.query().fetch():
            all_dates.append(dream.dream_date.split("-"))

        for entry in all_dates:
           for datepart in entry:
               datepart = int(datepart)

        new_all_dates = []
        for entry in all_dates:
            date_list = []
            for datepart in entry:
                date_list.append(int(datepart))
            new_all_dates.append(date_list)

        all_dates = new_all_dates

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekdays = []
        for entry in all_dates:
            day = datetime.date(entry[0], entry[1], entry[2])
            weekdaynum = day.weekday()
            weekdays.append(days[weekdaynum])

        for day in days:
            vardict[day] = 0
            for d in weekdays:
                if d == day:
                    vardict[day] += 1

        #word frequency
        def get_stop_words():
            with open('stop-words.txt') as f:
                content = ' '.join(f.readlines()).replace('\n','').replace('\r','').lower()
                return content.split(' ')

        all_text = []

        for dream in Dream.query().fetch():
            all_text.append(dream.dream_text)

        word_count = {}

        words = []
        for text in all_text:
            words.append(text.split())

        for entry in words:
            for word in entry:
                 if not word in word_count:
                     word_count[word] = 0
                 word_count[word] += 1

        sorted_map = list(reversed(sorted(word_count.items(), key=operator.itemgetter(1))))

        sorted_words = [sort[0] for sort in sorted_map]

        top_words = []
        for word in sorted_words:
            if word.lower() not in get_stop_words():
                top_words.append(word)

        places = ["first", "second", "third", "fourth", "fifth"]
        # Fixed bug here -- add to TeamDream
        if len(top_words) < 5:
            for i in range(len(top_words)):
                vardict[places[i]] = top_words[i]
        else:
            for i in range(5):
                vardict[places[i]] = top_words[i]

        self.response.write(data_template.render(vardict))

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'my-super-secret-key',
}

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/submit', EnterInfoHandler),
    ('/showdream', ShowDreamHandler),
    ('/showdata', DreamDataHandler),
    ('/AboutUs', AboutPage),
    ('/allDreams', AllDreams),
    ('/CreateAccount',CreateAccount),
    ('/login',LogIn)
], debug=True, config=config)
