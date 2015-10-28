
# RSS Feed Filter

import feedparser
import string
import time
from project_util import translate_html
from Tkinter import *


#-----------------------------------------------------------------------
#

#======================
# Code for retrieving and parsing RSS feeds
#======================

def process(url):
    """
    Fetches news items from the rss url and parses them.
    Returns a list of NewsStory-s.
    """
    feed = feedparser.parse(url)
    entries = feed.entries
    ret = []
    for entry in entries:
        guid = entry.guid
        title = translate_html(entry.title)
        link = entry.link
        summary = translate_html(entry.summary)
        try:
            subject = translate_html(entry.tags[0]['term'])
        except AttributeError:
            subject = ""
        newsStory = NewsStory(guid, title, subject, summary, link)
        ret.append(newsStory)
    return ret
#======================
#storing news story information in an object that we can then pass around in the rest of our program
#designing the data structure
#======================
class NewsStory:
    def __init__(self,guid, title, subject, summary, link):
        self.guid=guid
        self.title=title
        self.subject=subject
        self.summary=summary
        self.link=link
    
    def getGuid(self):
        return self.guid
    def getTitle(self):
        return self.title
    def getSubject(self):
        return self.subject
    def getSummary(self):
        return self.summary
    def getLink(self):    
        return self.link
#======================
# Triggers
#======================

class Trigger(object):
    def evaluate(self, story):
        """
        Returns True if an alert should be generated
        for the given news item, or False otherwise.
        """
        raise NotImplementedError


"""
You may want to be alerted only if a feed contains a particular word.WordTrigger inherits from Trigger
"""
# Whole Word Triggers
class WordTrigger(Trigger):
    def __init__(self,word):
        self.word=word.lower()
    def isWordIn(self,text):
        #taking care of punctuation
        punc=string.punctuation
        for letter in text:
            if letter in punc:
                text=text.replace(letter," ")
        
        #getting list of all the words
        words=text.split(" ")
        #return true if required word found in the list
        if self.word in words:
            return True
        else:
            return False

"""
TitleTrigger,SubjectTrigger and SummaryTrigger inherit from WordTrigger.They get fired if word is found in the tile,subject,summary respectively 
"""
class TitleTrigger(WordTrigger):
    def evaluate(self, story):
        testtitle=story.getTitle().lower()
        return self.isWordIn(testtitle)
        
class SubjectTrigger(WordTrigger):
    def evaluate(self, story):
        testsubject=story.getSubject().lower()
        
        return self.isWordIn(testsubject)
        
class SummaryTrigger(WordTrigger):
    def evaluate(self, story):
        testsummary=story.getSummary().lower()
        return self.isWordIn(testsummary)


# Composite Triggers - Trigger only when multiple words present -- a combination of some form: Not ,And ,Or

class NotTrigger(Trigger):
    def __init__(self,triggerobj):
        self.T=triggerobj
    def evaluate(self,x):
        
        return not self.T.evaluate(x)
        
    
class AndTrigger(Trigger):
    def __init__(self,triggerobj1,triggerobj2):
        self.T1=triggerobj1
        self.T2=triggerobj2
    def evaluate(self,x):
        
        return self.T1.evaluate(x) and self.T2.evaluate(x)
        
class OrTrigger(Trigger):
    def __init__(self,triggerobj1,triggerobj2):
        self.T1=triggerobj1
        self.T2=triggerobj2
    def evaluate(self,x):
        
        return self.T1.evaluate(x) or self.T2.evaluate(x)
        
#Trigger fires when specific phrase found
class PhraseTrigger(Trigger):
    def __init__(self,phrase):
        self.phrase=phrase
    def evaluate(self,x):
        
        
        if self.phrase in x.getSubject() or self.phrase in x.getTitle() or self.phrase in x.getSummary():
            
            return True
        else:
            
            return False

#======================
# Filtering
#======================

def filterStories(stories, triggerlist):
    """
    Takes in a list of NewsStory instances.

    Returns: a list of only the stories for which a trigger in triggerlist fires.
    """
    filterstories=[]
    for trigger in triggerlist:
        for story in stories:
            if trigger.evaluate(story)==True and story not in filterstories:
                filterstories.append(story)
                

    return filterstories

#======================
# Switch programmatic control to let user define their own triggers
# User-Specified Triggers
#======================

def makeTrigger(triggerMap, triggerType, params, name):

    """

    Modifies triggerMap, adding a new key-value pair for this trigger.

    Returns a new instance of a trigger (ex: TitleTrigger, AndTrigger).
    """

     trigger = None

    if triggerType == "TITLE":
        trigger = TitleTrigger(params[0])
    elif triggerType == "SUBJECT":
        trigger = SubjectTrigger(params[0])
    elif triggerType == "SUMMARY":
        trigger = SummaryTrigger(params[0])
    elif triggerType == "NOT":
        trigger = NotTrigger(triggerMap[params[0]])
    elif triggerType == "AND":
        trigger = AndTrigger(triggerMap[params[0]], triggerMap[params[1]])
    elif triggerType == "OR":
        trigger = OrTrigger(triggerMap[params[0]], triggerMap[params[1]])
    elif triggerType == "PHRASE":
        trigger = PhraseTrigger(" ".join(params))

    triggerMap[name] = trigger
    return trigger    
    
    
def readTriggerConfig(filename):
    #Returns a list of trigger objects that correspond to the rules set in the file filename

    
    # to read in the file and eliminate blank lines and comments
    triggerfile = open(filename, "r")
    all = [ line.rstrip() for line in triggerfile.readlines() ] 
    lines = []
    for line in all:
        if len(line) == 0 or line[0] == '#':
            continue
        lines.append(line)

    triggers = []
    triggerMap = {}

    for line in lines:

        linesplit = line.split(" ")

        # Making a new trigger
        if linesplit[0] != "ADD":
            trigger = makeTrigger(triggerMap, linesplit[1],
                                  linesplit[2:], linesplit[0])

        # Add the triggers to the list
        else:
            for name in linesplit[1:]:
                triggers.append(triggerMap[name])      #add means we simply add trigger value to list of triggers and not make 1

    return triggers
    
import thread

SLEEPTIME = 60 #seconds -- how often we poll


def main_thread(master):
    # A sample trigger list
    try:
        # These will probably generate a few hits...
        t1 = TitleTrigger("Obama")
        t2 = SubjectTrigger("Romney")
        t3 = PhraseTrigger("Election")
        t4 = OrTrigger(t2, t3)
        triggerlist = [t1, t4]
        
        #triggerlist = readTriggerConfig("D:/vatsala/python/feed/triggers.txt")

        # **** from here down is about drawing ****
        frame = Frame(master)
        frame.pack(side=BOTTOM)
        scrollbar = Scrollbar(master)
        scrollbar.pack(side=RIGHT,fill=Y)
        
        t = "Google & Yahoo Top News"
        title = StringVar()
        title.set(t)
        ttl = Label(master, textvariable=title, font=("Helvetica", 18))
        ttl.pack(side=TOP)
        cont = Text(master, font=("Helvetica",14), yscrollcommand=scrollbar.set)
        cont.pack(side=BOTTOM)
        cont.tag_config("title", justify='center')
        button = Button(frame, text="Exit", command=root.destroy)
        button.pack(side=BOTTOM)

        # Gather stories
        guidShown = []
        def get_cont(newstory):
            if newstory.getGuid() not in guidShown:
                cont.insert(END, newstory.getTitle()+"\n", "title")
                cont.insert(END, "\n---------------------------------------------------------------\n", "title")
                cont.insert(END, newstory.getSummary())
                cont.insert(END, "\n*********************************************************************\n", "title")
                guidShown.append(newstory.getGuid())

        while True:

            print "Polling . . .",
            # Get stories from Google's Top Stories RSS news feed
            stories = process("http://news.google.com/?output=rss")

            # Get stories from Yahoo's Top Stories RSS news feed
            stories.extend(process("http://rss.news.yahoo.com/rss/topstories"))

            # Process the stories
            stories = filterStories(stories, triggerlist)

            map(get_cont, stories)
            scrollbar.config(command=cont.yview)


            print "Sleeping..."
            time.sleep(SLEEPTIME)

    except Exception as e:
        print e


if __name__ == '__main__':

    root = Tk()
    root.title("Some RSS parser")
    thread.start_new_thread(main_thread, (root,))
    root.mainloop()

