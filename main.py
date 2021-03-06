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

class MainPage(BaseHandler):
    def get(self):
        home_template = JINJA_ENVIRONMENT.get_template('templates/home.html')

        if 'username' in self.session:
            self.response.write(home_template.render(username=self.session['username']))
        else:
            self.response.write(home_template.render())

        #if session.get("username")==True:
            #greeting={"greeting_message":"Hello " + user_name + "."}
            #self.response.write(acc_template.render(greeting))

class AboutPage (webapp2.RequestHandler):
    def get(self):
        about_template = JINJA_ENVIRONMENT.get_template('templates/About.html')
        self.response.write(about_template.render())

class LogIn(BaseHandler):
    def get(self):
        print "LogIn Handler!"
        login_template=JINJA_ENVIRONMENT.get_template('templates/login.html')
        welcome_template=JINJA_ENVIRONMENT.get_template('templates/submit.html')
        acc_name=self.request.get("acc-name")
        acc_pass=self.request.get("acc-pass")
        print acc_name
        if acc_name=="":
            self.response.write(login_template.render())

        elif Acc.query().filter(Acc.username == acc_name).fetch() and Acc.query().filter(Acc.password == acc_pass).fetch():
            self.session["username"]=acc_name
            self.session["password"]=acc_pass
            self.response.write(welcome_template.render())

        else:
            error= "Username or password incorrect"
#print ("The user name " + user_name + " is already taken. Please try something else.")
            self.response.write(login_template.render(error=error))
            #print("Username or Password is incorrect")
            #self.response.write(login_template.render())

        # allpasswords=Acc.query().filter(Acc.password == acc_pass).fetch()

class AllDreams (BaseHandler):
    def get(self):
        #all_dreams = Dream.query().order(Dream.dream_date).fetch()
        #dream_dict = {
        #"all_dreams" : all_dreams}
        acc_template=JINJA_ENVIRONMENT.get_template('templates/login.html')
        all_template = JINJA_ENVIRONMENT.get_template('templates/alldreams.html')
        owner = self.session.get("username")
        owner_dreams = Dream.query().filter(Dream.owner==owner).fetch()

        owner_dict = {
        "all_dreams" : owner_dreams

        }
        print(owner_dict)
        self.response.write(all_template.render(owner_dict))

class CreateAccount(BaseHandler):
    def get(self):
        print "CreateAccount Get"
        acc_template=JINJA_ENVIRONMENT.get_template('templates/CreateAccount.html')
        self.response.write(acc_template.render())

    def post(self):

        welcome_template=JINJA_ENVIRONMENT.get_template('templates/submit.html')
        acc_template=JINJA_ENVIRONMENT.get_template('templates/CreateAccount.html')
        user_name = self.request.get("user-name") #get the title from the respective input tag in submit.html
        pass_word = self.request.get("pass-word")
        self.session["username"]=user_name
        self.session["password"]=pass_word
        account = Acc(username=user_name, password=pass_word)
        if Acc.query().filter(Acc.username == user_name).fetch():
            error={"error_message":"The user name " + user_name + " is already taken. Please try something else."}
            #print ("The user name " + user_name + " is already taken. Please try something else.")
            self.response.write(acc_template.render(error))
        else:
            account.put()
            self.response.write(welcome_template.render())



class LogoutHandler(BaseHandler):
    def get(self):
        home_template=JINJA_ENVIRONMENT.get_template('templates/home.html')
        self.session.clear()
        acc_name=self.request.get("acc-name")
        acc_name=" "
        if acc_name==" ":
            self.response.write(home_template.render())
#if continue as guest is clicked, self.session["hmm"]=guest

class EnterInfoHandler(webapp2.RequestHandler):
    def get(self):
        welcome_template = JINJA_ENVIRONMENT.get_template('templates/submit.html')
        self.response.write(welcome_template.render())

class ShowDreamHandler(BaseHandler):
    def get(self):
        results_template = JINJA_ENVIRONMENT.get_template('templates/results.html')
        #self.response.headers['Content-Type'] = 'text/plain'

        self.response.write(results_template.render(dream_dict))

    def post(self):
        results_template = JINJA_ENVIRONMENT.get_template('templates/results.html')
        login_template=JINJA_ENVIRONMENT.get_template('templates/login.html')
        dream_title = self.request.get("dream-title") #get the title from the respective input tag in submit.html
        dream_date = self.request.get("dream-date")
        dream_summary = self.request.get("dream-summary") #get the summary from the rescpetive input tag in submit.html
        url = "https://gateway.watsonplatform.net/tone-analyzer/api/v3/tone?version=2017-09-21&text=" + dream_summary

        r = requests.get(url, auth=("12b8c206-770b-4989-9909-2c1c625c9a8d", "nMHwFGhjTHIT"))

        try:
            dream_sentiment = json.loads(r.text)["document_tone"]["tones"][0]["tone_name"]
        except IndexError:
            dream_sentiment = "Null"

        owner = self.session.get("username")

        dream = Dream(title=dream_title,
                    dream_date=dream_date,
                    dream_text=dream_summary,
                    dream_sentiment=dream_sentiment,
                    owner=owner)
        dream.put()

        all_dreams = Dream.query().fetch()

        dream_dict = {"title" : dream_title,
        "date" : dream_date,
        "dream_summary" : dream_summary,
        "sentiment" : dream_sentiment,
        "all_dreams" : all_dreams}

        self.response.write(results_template.render(dream_dict))

class DreamDataHandler(BaseHandler):
    def get(self):
        data_template = JINJA_ENVIRONMENT.get_template('templates/data.html')

        #get occurance of each sentiment in all dreams in DataStore

        possible_sentiments = ["Fear", "Anger", "Joy", "Confident", "Analytical", "Sadness", "Tentative", "Null"]

        owner = self.session.get("username")
        current_owner_dreams = Dream.query().filter(Dream.owner==owner).fetch()

        vardict = {}
        for i in possible_sentiments:
            vardict[i] = 0
            vardict[i] = len(Dream.query().filter(Dream.owner==owner).filter(Dream.dream_sentiment==i).fetch())

        #get total number of dreams
        total_dreams = len(current_owner_dreams)
        vardict["total"] = total_dreams

        #get day of the week frequency#date frequency
        all_dates = []
        for dream in current_owner_dreams:
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

        for dream in current_owner_dreams:
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
    ('/login',LogIn),
    ('/logout',LogoutHandler)
], debug=True, config=config)
