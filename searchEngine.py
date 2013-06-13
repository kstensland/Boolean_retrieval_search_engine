"""
Author: Kristofer Stensland
Date Last Modified: October, 1 2012
Description: A search engine over a series of web-page meta-data that is stored
             in a python dictionary. Searches are performed using different 
             methods of boolean retrieval queries: single token; two token; 
             AND; OR; and near. 
"""

import sqlite3
import pickle
import os

# The stemmer will stem the queries.
from portStemmer import PorterStemmer

# Creates the dictionary if it is not found.
from makeBigDict import scanCleanDir

"""
Handles all search queries, makes database queries and runs the user interface
for all searches. 

Properties: tokens - the dictionary of meta-data for all the tokens and documents.

Methods: dbQuery - Handles SQL queries to the sqlite database
         singleToken - Single token search query
         orQuery - Performs an OR search query containing two tokens
         andQuery - Performs an AND search query containing two tokens
         phraseQuery - Performs a regular query with a two-token phrase.
         nearQuery - Performs a query using two tokens, based on how near 
                     to each other they are in the document. 

"""
class Searcher:
    # Constructor. Opens the dictionary of token meta-data
    def __init__(self):
        self.stemmer = PorterStemmer()

        """
        self.tokens is a dictionary containing all the meta-data for all of the tokens and documents.
        It has the structure:
        {(Token): 
           {(Document Number):
              [(list of all the positions of the token in that document.)]
           }
        }
        """
        try:
            f = open(os.getcwd() + "/data/tokensDict.p", "r")
            self.tokens = pickle.load(f)
        except:
            print "Pickle file not found"
            print "Creating the dictionary of meta-data."
            self.tokens = scanCleanDir()
            f = open(os.getcwd() + "/data/tokensDict.p", "w")
            pickle.dump(self.tokens, f)

    # Connects to the sqlite database, performs a given search query and 
    # returns a list conaining each row of the resulting table. 
    def dbQuery(self, query, args = ()):
        conn = sqlite3.connect(os.getcwd() + '/data/cache.db')
        db = conn.cursor()
        
        # args should be a tuple of the arguments in the query
        db.execute(query, args)
        
        # get all the rows of the results from the sql query.
        rows = db.fetchall()
        conn.close()
        
        return rows

    """
    Searches for a single token in all the databases and displays all the 
    resulting documents, how many times the token occured in each document,
    and which document had the most instances of that token. 
    """
    def singleToken(self):
        # Get the token from the user, format it correctly and stem it. 
        print
        word = raw_input("Enter your one word query: ")
        token = word.lower()
        token = self.stemmer.stem(token, 0, len(token) - 1)

        # If the token is not found in any of the documents, end the search. 
        try: 

            wordDict = self.tokens[token]
        except:
            print word, "does not seem to exist in our files. Please try a different word"
            print 
            return
            
        # The number of times the token occurs across all documents.
        occurenceTotal = 0

        # Contains the documents with the highest frequency of document occurences.
        highestFreq = {'freq': 0, 'docs':[]}
        
        i = 1
        for doc in wordDict.keys():
            freq = len(wordDict[doc])
            occurenceTotal += freq

            linksQuery = """
                         SELECT webPage.linkText, item.itemName FROM (
                         SElECT itemToWebPage.webPageId, itemToWebPage.itemId
                         FROM itemToWebPage
                         WHERE webPageId = ?) AS linkItem
                         JOIN item
                         ON item.itemId = linkItem.itemId
                         JOIN webPage
                         ON webPage.webPageId = linkItem.webPageId;
                         """
            # Get the URL for each valid web-page document found.                          
            linksRow = self.dbQuery(linksQuery, (doc,))
            
            # Display the current document and it's frequency
            print 
            print i,"\t",linksRow[0][0]
            print "\t item: ",linksRow[0][1]
            print "\t occured ",freq,"times"
            i += 1
            
            # Update the document[s] with the highest frequency
            if freq > highestFreq['freq']:
                highestFreq['freq'] = freq
                highestFreq['docs'] = [linksRow[0][0]]
                
            elif freq == highestFreq['freq']:
                highestFreq['docs'].append(doc)
            
        # Display the most relevant document[s]
        print
        print "Total occurence of", word, "is", occurenceTotal, "times"
        print "Highest frequency: ", highestFreq['freq'], " times in: ",
        for i in range(len(highestFreq['docs'])):
            if i > 0:
                print "and"
            print highestFreq['docs'][i]
        print

    """
    Takes two tokens, gets all the documents that either or both tokens 
    appear in and displays the results.
    """
    def orQuery(self):
        print

        # Get the two tokens, format and stem them. 
        word1 = raw_input("Enter the first word of your query: ")
        word2 = raw_input("Enter the second word of your query: ")
        token1 = word1.lower()
        token1 = self.stemmer.stem(token1, 0, len(token1) - 1)
        token2 = word2.lower()
        token2 = self.stemmer.stem(token2, 0, len(token2) - 1)

        try: 
            docs = self.tokens[token1].keys()
        except:
            print word1, "does not seem to exist in our files. Please try a different word"
            print 
            return

        try: 
            docs2 = self.tokens[token2].keys()
        except:
            print word2, "does not seem to exist in our files. Please try a different word"
            print 
            return

        # Collect all documents where either or both tokens appear in.
        # Store them in keys
        for doc in docs2:
            if doc not in docs:
                docs.append(doc)

        # Total number of times either token occurs accross all documents.
        occurenceTotal = 0
        i = 1
        # Keep track of which documents have the highest token frequency
        highestFreq = {'freq': 0, 'docs':[]}
        for doc in docs:
            freq1 = 0
            freq2 = 0

            try:
                freq1 = len(self.tokens[token1][doc])
            except:
                None

            try:
                freq2 = len(self.tokens[token2][doc])
            except:
                None

            # Combine the frequency of each token for the current document.
            freq = freq1 + freq2
            occurenceTotal += freq
            
            linksQuery = """
                         SELECT webPage.linkText, item.itemName FROM (
                         SElECT itemToWebPage.webPageId, itemToWebPage.itemId
                         FROM itemToWebPage
                         WHERE webPageId = ?) AS linkItem
                         JOIN item
                         ON item.itemId = linkItem.itemId
                         JOIN webPage
                         ON webPage.webPageId = linkItem.webPageId;
                         """
            # Get the URL for each valid web-page document found.                          
            linksRow = self.dbQuery(linksQuery, (doc,))

            # Display the current document and it's frequency
            print 
            print i,"\t",linksRow[0][0]
            print "\t item: ",linksRow[0][1]
            print "\t occured ",freq,"times"
            i += 1
            
            # Update which document[s] have the highest frequency for both tokens
            if freq > highestFreq['freq']:
                highestFreq['freq'] = freq
                highestFreq['docs'] = [linksRow[0][0]]
                
            elif freq == highestFreq['freq']:
                highestFreq['docs'].append(doc)
        
        # Display which Document[s] have the highest frequency for both tokens
        print
        print "Total occurence of", word1, "or", word2, "is", occurenceTotal, "times"
        print "Highest frequency: ", highestFreq['freq'], " times in: ",
        for i in range(len(highestFreq['docs'])):
            if i > 0:
                print "and"
            print highestFreq['docs'][i]
        print

    """
    Takes two tokens, gets all the documents that ONLY BOTH tokens 
    appear in and displays the results.
    """
    def andQuery(self):
        print

        # Get each token, format and stem both of them. 
        word1 = raw_input("Enter the first word of your query: ")
        word2 = raw_input("Enter the second word of your query: ")
        token1 = word1.lower()
        token1 = self.stemmer.stem(token1, 0, len(token1) - 1)
        token2 = word2.lower()
        token2 = self.stemmer.stem(token2, 0, len(token2) - 1)
        
        # Will contain all documents where both tokens appear in
        docs = []

        # If either of the tokens is not found in any document, stop the search
        try: 
            docs1 = self.tokens[token1].keys()
        except:
            print word1, "does not seem to exist in our files. Please try a different word"
            print 
            return

        try: 
            docs2 = self.tokens[token2].keys()
        except:
            print word2, "does not seem to exist in our files. Please try a different word"
            print 
            return

        # Collect all documents where both tokens appear in.
        # Store them in keys
        for doc in docs1:
            if doc in docs2:
                docs.append(doc)

        # Total number of times either token occurs accross all documents 
        # that contain both tokens.
        occurenceTotal = 0
        i = 1
        
        # Keep track of which documents have the highest token frequency
        highestFreq = {'freq': 0, 'docs':[]}
        for doc in docs:
            freq1 = 0
            freq2 = 0

            try:
                freq1 = len(self.tokens[token1][doc])
            except:
                None

            try:
                freq2 = len(self.tokens[token2][doc])
            except:
                None

            # Combine the frequency of each token for the current document.
            freq = freq1 + freq2
            occurenceTotal += freq
            
            linksQuery = """
                         SELECT webPage.linkText, item.itemName FROM (
                         SElECT itemToWebPage.webPageId, itemToWebPage.itemId
                         FROM itemToWebPage
                         WHERE webPageId = ?) AS linkItem
                         JOIN item
                         ON item.itemId = linkItem.itemId
                         JOIN webPage
                         ON webPage.webPageId = linkItem.webPageId;
                         """
            # Get the URL for each valid web-page document found.                          
            linksRow = self.dbQuery(linksQuery, (doc,))

            # Display the current document and it's frequency
            print 
            print i,"\t",linksRow[0][0]
            print "\t item: ",linksRow[0][1]
            print "\t occured ",freq,"times"
            i += 1

            # Update which document[s] have the highest frequency for both tokens
            if freq > highestFreq['freq']:
                highestFreq['freq'] = freq
                highestFreq['docs'] = [linksRow[0][0]]
                
            elif freq == highestFreq['freq']:
                highestFreq['docs'].append(doc)

        #Display which Document[s] have the highest frequency for both tokens
        print
        print "Total occurence of", word1, "and", word2, "is", occurenceTotal, "times"
        print "Highest frequency: ", highestFreq['freq'], " times in: ",
        for i in range(len(highestFreq['docs'])):
            if i > 0:
                print "and"
            print highestFreq['docs'][i]
        print

    """
    Takes a two token phrase and finds all the documents where that phrase occurs
    exactly as it is in the query (token1 followed by token2). 

    Works exactly like the andQuery, except that it checks to make sure the 
    position of token2 occurs immediately after token1. 
    """
    def phraseQuery(self):
        print

        # Get the two-word phrase and get each token from it. 
        phrase = raw_input("Enter a two word phrase: ")

        while len(phrase.split(' ')) != 2:
            phrase = raw_input("Make sure your phrase is two words (e.g. 'hello goodbye'): ")
            
        # Format and stem each token. 
        words = phrase.split(' ')
        word1 = words[0]
        word2 = words[1]
        token1 = word1.lower()
        token1 = self.stemmer.stem(token1, 0, len(token1) - 1)
        token2 = word2.lower()
        token2 = self.stemmer.stem(token2, 0, len(token2) - 1)
        
        # Will contain all documents where both tokens appear in
        docs = []

        # If either of the tokens is not found in any document, stop the search
        try: 
            docs1 = self.tokens[token1].keys()
        except:
            print word1, "does not seem to exist in our files. Please try a different word"
            print 
            return

        try: 
            docs2 = self.tokens[token2].keys()
        except:
            print word2, "does not seem to exist in our files. Please try a different word"
            print 
            return

        # Collect all documents where both tokens appear.
        # Store them in keys
        phraseDict = {}

        # Check which documents have both words
        for doc in docs1:
            if doc in docs2:
                doc1Pos = self.tokens[token1][doc]
                doc2Pos = self.tokens[token2][doc]

                # Check which documents have the phrase in the correct order
                freq = 0
                for pos1 in doc1Pos:
                    for pos2 in doc2Pos:
                        if pos2 == pos1 + 1:
                            freq += 1
                
                # Keep track of only the docuements where the phrase occurs.
                if freq > 0:
                    phraseDict[doc] = freq
        
        #Total number of times the phrase occurs
        occurenceTotal = 0

        i = 1
        
        # Keep track of the documents with the highest frequency
        highestFreq = {'freq': 0, 'docs':[]}
        for doc in phraseDict.keys():
            
            freq = phraseDict[doc]
            occurenceTotal += freq
        
            linksQuery = """
                         SELECT webPage.linkText, item.itemName FROM (
                         SElECT itemToWebPage.webPageId, itemToWebPage.itemId
                         FROM itemToWebPage
                         WHERE webPageId = ?) AS linkItem
                         JOIN item
                         ON item.itemId = linkItem.itemId
                         JOIN webPage
                         ON webPage.webPageId = linkItem.webPageId;
                         """
            # Get the URL for each valid web-page document found.                          
            linksRow = self.dbQuery(linksQuery, (doc,))
        
            # Display the current document and it's frequency
            print 
            print i,"\t",linksRow[0][0]
            print "\t item: ",linksRow[0][1]
            print "\t occured ",freq,"times"
            i += 1
            
            # Update which document[s] have the highest frequency for both tokens
            if freq > highestFreq['freq']:
                highestFreq['freq'] = freq
                highestFreq['docs'] = [linksRow[0][0]]
                
            elif freq == highestFreq['freq']:
                highestFreq['docs'].append(doc)

        # Displat the document[s] with the highest frequency for the two-token phrase.
        print
        print "Total occurence of",phrase, "is", occurenceTotal, "times"
        print "Highest frequency: ", highestFreq['freq'], " times in: ",
        for i in range(len(highestFreq['docs'])):
            if i > 0:
                print "and"
            print highestFreq['docs'][i]
        print

    """
    Performs a query using two tokens and an integer. The integer represents
    a distance between two words.

    Collects all the documents where both tokens occur within the given 
    distance from each other and displays the results. For example in the 
    document, "and i think to myself what a wonderful world" The two tokens "think"
    and "myself" occur within a distance of two words from each other.
    """
    def nearQuery(self):
        print

        # Get both tokens and the distance
        word1 = raw_input("Enter the first word: ")
        word2 = raw_input("Enter the second word: ")
        distance = input ("Enter the number of positions away you want to look: ")
        
        # Format and stem each token
        token1 = word1.lower()
        token1 = self.stemmer.stem(token1, 0, len(token1) - 1)
        token2 = word2.lower()
        token2 = self.stemmer.stem(token2, 0, len(token2) - 1)   
        
        # Will contain all documents where both tokens appear in, within the given
        # distance of each other.
        docs = []

        # If either token does not appear in any document, stop the search.
        try: 
            docs1 = self.tokens[token1].keys()
        except:
            print word1, "does not seem to exist in our files. Please try a different word"
            print 
            return

        try: 
            docs2 = self.tokens[token2].keys()
        except:
            print word2, "does not seem to exist in our files. Please try a different word"
            print 
            return

        # Collect all documents where both tokens appear.
        # Store them in keys
        phraseDict = {}

        # Check which documents have both words
        for doc in docs1:
            if doc in docs2:
                doc1Pos = self.tokens[token1][doc]
                doc2Pos = self.tokens[token2][doc]

                # Check which documents have the words within the allotted distance of each other
                freq = 0
                for pos1 in doc1Pos:
                    for pos2 in doc2Pos:
                        if (pos2 - pos1 >= 0 - distance) and (pos2 - pos1 <= distance):
                            freq += 1
                
                if freq > 0:
                    phraseDict[doc] = freq
        
        #Total number of times the two tokens occur within each other across all docs
        occurenceTotal = 0
        i = 1
        
        # Keep track of the documents with the highest frequency
        highestFreq = {'freq': 0, 'docs':[]}
        for doc in phraseDict.keys():
            
            freq = phraseDict[doc]
            occurenceTotal += freq
        
            linksQuery = """
                         SELECT webPage.linkText, item.itemName FROM (
                         SElECT itemToWebPage.webPageId, itemToWebPage.itemId
                         FROM itemToWebPage
                         WHERE webPageId = ?) AS linkItem
                         JOIN item
                         ON item.itemId = linkItem.itemId
                         JOIN webPage
                         ON webPage.webPageId = linkItem.webPageId;
                         """
            # Get the URL for each valid web-page document found.                          
            linksRow = self.dbQuery(linksQuery, (doc,))
            
            # Display the current document and it's frequency
            print 
            print i,"\t",linksRow[0][0]
            print "\t item: ",linksRow[0][1]
            print "\t occured ",freq,"times"
            i += 1
            
            # Update the document with the highest frequency. 
            if freq > highestFreq['freq']:
                highestFreq['freq'] = freq
                highestFreq['docs'] = [linksRow[0][0]]
                
            elif freq == highestFreq['freq']:
                highestFreq['docs'].append(doc)

        # Display the document with the highest frequency. 
        print
        print "Total occurence of",word1, "within ", distance, "positions of", word2, "was",occurenceTotal, "times"
        print "Highest frequency: ", highestFreq['freq'], " times in: ",
        for i in range(len(highestFreq['docs'])):
            if i > 0:
                print "and"
            print highestFreq['docs'][i]
        print
    
    def searchMenu(self):
        print
        print "-----------------------------------------------------------"
        print "\t       Welcome to Stensland-ipedia!"
        print "\tWhere you can search to your hearts content!"
        print "-----------------------------------------------------------"
        print 
        
        menu = True
        while menu:
            print "Choose the number corresponding to the query you would like to perform"
            print "---------------------------------------------------------------------"
            print "1.\tSingle token query."
            print "2.\tAND query."
            print "3.\tOR query."
            print "4.\t2-Token query."
            print "5.\tNear query."
            print "6.\tQuit"
            
            choice = raw_input("Enter your choice: ")
            
            if choice == '1':
                self.singleToken()
                
            elif choice == '2':
                self.andQuery()
                
            elif choice == '3':
                self.orQuery()

            elif choice == '4':
                self.phraseQuery()

            elif choice == '5':
                self.nearQuery()
                 
            elif choice == '6':
                menu = False
                print "\n"
                
            else:
                print "That is not a thing I understand."
                print 
                
        print
        print "Thank you for being my friend!"
        print 
        
def main():
    print "Preparing the search engine..."
    stenslandipedia = Searcher()
    stenslandipedia.searchMenu()

if __name__ == "__main__":
    main()

