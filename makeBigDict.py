import pickle
import sqlite3
import os, glob
import poster

from portStemmer import *
from nltk.tokenize import *
from stripper import *

def scanCleanDir():
    # Save the current directory
    currDir = os.getcwd()

    # Set the current working directory to the directory of clean-token documents.
    os.chdir(currDir + "/data/clean")

    # fileList is a list of all the files in the clean directory (clean-token docs).
    fileList = glob.glob("*.txt")

    """
    A dictionary containing all the meta-data for all of the tokens and documents.
    It has the structure:
    {(Token): 
       {(Document Number):
          [(list of all the positions of the token in that document.)]
       }
    }
    """
    tokenDict = {}

    # Navigate through each document
    for fileName in fileList:
        f = open(fileName, 'r')

        # Each line is a new token.
        tokens = f.readlines()
        
        # The document name is a number.
        docNum = int(fileName.replace('.txt', ''))
        
        # Current position in the document.
        docPos = 0
        
        for token in tokens:
            token = token.replace('\n', '')

            if token not in tokenDict:
                # Create a new key for that token
                tokenDict[token] = {}

            # If the document number is not associated with that token.
            if docNum not in tokenDict[token]:
                # Associate the document with that token.
                tokenDict[token][docNum] = []
            
            # Add the current position of the current token in the current document 
            # to a list of positions in said document. 
            tokenDict[token][docNum].append(docPos)

            docPos = docPos + 1
    
    # Reset the current working directory to the previous working directory. 
    os.chdir(currDir)

    return tokenDict
            

        
def main():
    try:
        f = open(os.getcwd()+"/data/tokensDict.p", "r")
        tokens = pickle.load(f)
    except:
        print "Pickle file not found"
        tokens = scanCleanDir()
        f = open(os.getcwd()+"/data/tokensDict.p", "w")
        pickle.dump(tokens, f)

if __name__ == "__main__":
    main()
