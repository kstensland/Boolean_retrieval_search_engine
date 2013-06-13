from HTMLParser import *
from BeautifulSoup import BeautifulSoup, Comment
import sys, os
import re

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    soup = BeautifulSoup(html)
    print "LEN: ", len(html)
    for tag in soup.findAll(True):
        tag.attrs = None
        
            
        script = tag.script
        if script is not None:
            #print "Found a script"
            #print type(script)
            #print script
            #print
            script.extract()
        #tag.extract()
    #remove things in script tags
    
    """
    commentsAndScript = soup.findAll(['script', text=lambda text:isinstance(text, Comment)])
    for comment in commentsAndScript:
        comment.extract()
    """
    page = unicode(soup)
    print "LEN 2: ", len(page)
    
    try:
        s.feed(page)
    except HTMLParseError, e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]      
        print(exc_type, fname, exc_tb.tb_lineno)
        print e
        
        s.handle_decl(e)
    
    return s.get_data()
    
    #except:
        #print "could not read that page. Possibly because of unicode stuff."
        #return None
def writeBodyToFile(fileName):
    f = open(fileName, 'r')
    newFileName = fileName.replace('raw', 'bodies')
    newFile = open(newFileName, 'w')
    lines = f.readlines()
    inBody = False
    inTitle = False
    inScript = False
    title = ""

    for line in lines:
        words = line.split(' ')
        for word in words:

            if word.count('<title') > 0:
                inTitle = True
            if word.count('</title'):
                newFile.write(word)
                title = title + word
                inTitle = False

            if word.count('<body') > 0:
                inBody = True
            if word.count('</body'):
                inBody = False
                newFile.write(word)
                
            if word.count('<script') > 0:
                inScript = True
            if word.count('</script') > 0:
                inScript = False

            if (inBody or inTitle) and not inScript:
                newFile.write(word + " ")
            if inTitle:
                title = title + word + " "

                
    return newFileName
            #if re.match(r'<body[\w]*>', word) or re.match('</body>', word):
