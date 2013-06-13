"""
Author: Kristofer Stensland
Last Updated: October, 2012
Description: Sends search queries to Ask.com and harvests the top ten most relevant
             documents, storing all of their URLS in a sqlite database.
             Then Removes all of the HTML tags leaving only the tokens.
             Then cleans up the documents by formating and stemming each occurence 
             of a token in all the documents. 
"""

import pickle
import sqlite3
import os, glob
import urllib, urllib2, re, urlparse, cookielib
import poster

from portStemmer import *
from nltk.tokenize import *
from stripper import *

# Formats an ask.com search query.
def makeQuery(phrase):
    query = phrase.lower().replace(' ', '+')
    return query

# Sends a query to ask.com and collects the top ten documents from the query results.
def harvestAsk(phrase):
    query = makeQuery(phrase)

    # Send the query to ask.com and collect the first two pages of results in order to obtain
    # the top ten documents. 
    html = urllib2.urlopen("http://www.ask.com/web?qsrc=1&o=0&l=dir&q=" + query).read()

    # Using a regular expression, collect all the HTML tags that contain URLS to documents. 
    pageDataList = re.findall(r'<a id="(r[0-9]*_t)" href="([^"]*)" (.*)</a>', html)

    # Get the link to the second page of results.
    page2Link = re.findall(r'<div class="pgc"><a href="([^"]*)" class="pg title">2</a>', html)
    
    # We go to the second page because some results consist of media 
    # files, such as links to youtube videos or music streaming services. So since each page
    # only shows ten results, we go to the next page in order to get enough pages that mainly
    # consist of text. 
    if page2Link is not None and len(page2Link) > 0:
        html2 = urllib2.urlopen(page2Link[0], html)
        moreData = re.findall(r'<a id="(r[0-9]*_t)" href="([^"]*)" (.*)</a>', html)
        pageDataList = pageDataList + moreData

    # Store all the URLS in a list. 
    links = []
    for i in range(len(pageDataList)):
        links.append(pageDataList[i][1])
    return links

# Scan the directory containing all the files containing all the search queries. 
# In this lab we have different files for movies, books and music. 
def scanDir():
    #Get the text files from the item directory
    os.chdir(os.getcwd"/data/item")
    fileList = glob.glob("*.txt")

    """
    Dictionary of all the items we are going to search for and their URLS with the following structure:
    {(item type):
        {(item name aka. search query):
            [(list of all the URLS pertaining to that item.)]
        }
    }
    """
    itemsDict = {}
    print "Scanning directories for items."

    # Read each file. 
    for fileName in fileList:
        itemType = fileName.replace('.txt', '')
        print "Scanning items relating to",itemType

        itemsDict[itemType] = {}

        f = open(fileName, 'r')
        items = f.readlines()

        # Harvest the top 10 links for each search query
        for item in items:
            # Make the ask.com query
            print "scanning links for: ", item
            query = "\""+item.replace("\n", '')+"\" "+itemType
            
            # Get the list of links
            itemLinks = harvestAsk(query)
            itemsDict[itemType][item] = itemLinks
        print

    print "\nFound all the links"
    return itemsDict

# Harvests the website for each URL and stores the HTML, headers, and text data in text files 
def cacheData(itemDict):
    for keyword in itemDict.keys(): # =keyword: item
        for item in itemDict[keyword].keys(): # item: (movie title, book titles, artist, artist)
            print "Checking out", item
            conn = sqlite3.connect(os.getcwd'/data/cache.db')
            c = conn.cursor()
            
            c.execute("Select * from item WHERE itemName=?", (item,))
            rows = c.fetchall()

            # Check if item exists in the DB already, if not insert it.
            if (len(rows) < 1):
                c.execute("INSERT INTO item VALUES (NULL, ?)", (item,))
                conn.commit()
                c.execute("Select * from item WHERE itemName=?", (item,))
                rows = c.fetchall()
            
            print "ROWS:\t", rows
            itemId = rows[len(rows)-1][0]

            # Harvest all the pages for each URL.
            for link in itemDict[keyword][item]:#link to page
                print 
                print "Got that link! ", link
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.0; en-GB; rv:1.8.1.12) Gecko/20080201 Firefox/2.0.0.12',
                    'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
                    'Accept-Language': 'en-gb,en;q=0.5',
                    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                    'Connection': 'keep-alive'
                    }
                
                # Try downloading the page.
                try:
                    req = urllib2.Request(link, None, headers)
                    response = urllib2.urlopen(req)
                    page = response.read() 
                except:
                    print "Could not retrieve page: ", link
                    
                HTTPheader = response.info()# Get the header

                # After storing the page in the database we will get its unique ID.
                # That ID will be the files name in the cache.
                webPageId = storePageInfoInDatabase(link, item)
                if webPageId is not None:
                    writeDataToFiles(webPageId, page, HTTPheader)
                
# Store a URL and it's document in a sql database. 
def storePageInfoInDatabase(link, item):
    conn = sqlite3.connect(os.getcwd() + '/data/cache.db')
    c = conn.cursor()
    
    c.execute("SELECT * from webPage WHERE linkText=?", (link,))
    row = c.fetchone()
    
    # Check if the webpage already exists in the DB
    if row is None:
      # If not, insert into the webPage table
        print link, "not yet in the database"
        c.execute("INSERT INTO webPage VALUES (NULL, ?)", (link,))
        c.execute("SELECT * from webPage WHERE linkText=?", (link,))
        row = c.fetchone() #Get the row with the link
    
        print "The link: ", link," is now in the database"
    
    
        pageId = str(row[0]) #Get the id number of that row
        
        """    
        #insert into item                                                                  
        #Check if item exists already                                                      
        c.execute("Select * from item WHERE itemName=?", (item,))
        rows = c.fetchall()
        
        if (len(rows) < 1):
        c.execute("INSERT INTO item VALUES (NULL, ?)", (item,))
        conn.commit()
        c.execute("Select * from item WHERE itemName=?", (item,))
        rows = c.fetchall()
        
        print "ROWS:\t", rows
        itemId = rows[len(rows)-1][0]
        """
            
    else:
        print "That page already in the database"
        pageId = None
    # Insert into itemToWebPage, and get the item ID
    c.execute("Select itemId from item WHERE itemName=?", (item,))
    try:
        row = c.fetchone()
        itemId = row[0]
        c.execute("INSERT INTO itemToWebPage VALUES (NULL, ?, ?)", (itemId, pageId,))
    except:
        print 
        print "Could not find that ",item,"'s id"
        print 
        
            
    conn.commit()
    return pageId

# Write the HTTP header and the web-page document to a local text file.
def writeDataToFiles(ID, page, HTTPheader):
    # Make the file name for all the files
    # This will be the web pages unique ID in the data base
    fileName = convertIdToFileName(ID)

    # Write the raw HTML File
    rawFilePath = os.getcwd() + "/data/raw/"+(fileName.replace('txt', 'html'))
    rawFile = open(rawFilePath, 'w')
    rawFile.write(page)
    print "Wrote the raw HTML file"

    # Write the HTTP header File
    headFilePath = os.getcwd() + "/data/header/"+fileName
    headFile = open(headFilePath, 'w')
    headFile.write(str(HTTPheader))

    # Tokenize the raw HTML file and write it 
    tokenizeRawHTML(ID, rawFilePath)

# Removes all the HTML tags, thus leaving all the tokens in the document. 
# Then makes each line 
def tokenizeRawHTML(webPageId, rawFilePath):
    # Read in the body of the web-document and write it to a local file.
    print "Tokenizing the HTML file ", rawFilePath
    pageBodyFileName = writeBodyToFile(rawFilePath)
    pageBodyFile = open(pageBodyFileName, 'r')

    # Store the body in a string.
    pageBody = pageBodyFile.read()
    
    # Strip the HTML tags in the body
    strippedPage = strip_tags(pageBody)
    if strippedPage is None:
        print "Page: ", rawFilePath," not read"
        return
    
    print "Stripped the body"

    # Tokenize the words and write them to a file
    p = PorterStemmer()
    tokensFileName = convertIdToFileName(webPageId)
    
    # The text file of tokens. 
    tokensFile = open(os.getcwd() + "/data/clean/"+tokensFileName, 'w')
    
    # Get each line in the leftover body. 
    sentences = sent_tokenize(strippedPage)
    print "About to tokenize the stripped body"
    counter = 0
    for sentence in sentences:
        tokens = word_tokenize(sentence)
        for token in tokens:
            stem = p.stem(token, 0,len(token)-1)
            stem = stem.lower()
            try:
                stem = stem.encode('utf-8')
            except:
                print "Could not encode the token, trying a decode"
                print "Type: ", type(stem)
                stem = stem.decode('utf-8', 'replace')
            
            if (stem.isalpha() or stem.isdigit()) and not(stem in ['-', '_']):
                # Write token to the file
                tokensFile.write(stem + "\n")
                
                # Store token in database
                conn = sqlite3.connect(os.getcwd() + '/data/cache.db')
                c = conn.cursor()
                c.execute("SELECT * FROM token where word = ?", (stem,))
                row = c.fetchone()
                tokenId = 0
                if row is None:
                    try:
                        c.execute("INSERT INTO token VALUES (NULL, ?)",(stem,))
                        conn.commit()
                    
                    except:
                        print "Could not store token: ", stem, " into database."
                        continue
                    
                c.execute("SELECT tokenId FROM token WHERE word=?", (stem,))
                row = c.fetchone()
                try:
                    tokenId = row[0]
                except:
                    print "could not find ", stem," in token table."
                    continue
                
                c.execute("INSERT INTO tokenToWebPage VALUES"+
                          "(NULL, ?, ?, ?)", (tokenId, webPageId, counter,))
                conn.commit()
                counter = counter + 1
                
    # Delete the body fileName
    os.remove(pageBodyFileName)

    print "Tokens in ",tokensFileName
    
# Converts a db ID number to a string in order to create a file with that name.
def convertIdToFileName(ID):
    fileName = str(ID)
    # If the id has less than 6 digits, we want to add zeroes until it is 6 digits long.
    while len(fileName) < 6:
        fileName = "0" + fileName
    
    fileName += ".txt"
    return fileName

def main():
    try:
        f = open("saveItems.p", 'r')
        itemDict = pickle.load(f)
    except:
        print "Couldn't find the pickle file."
        f = open("saveItems.p", "r")

        #Collect the raw HTML files and store them in a dictionary.
        itemDict = scanDir()
        pickle.dump(itemDict, f)
    
    # Store all the token files 
    cacheData(itemDict)
    
    
    """
    STRUCTURE FOR itemDict 

    for key in itemDict.keys(): #keyword
        print key
        for key2 in itemDict[key].keys(): #item (movie title, book titles, artist name)
            print "\t",key2
            for link in itemDict[key][key2]:#link to page
                print "\t\t", link

    #Harvest Ask.com for links with query
    queryLinks = harvestAsk('poop')

    #Get requests for each link and store data in files
    VAR = getData(queryLinks)
    """
main()
