import sqlite3, os

def main():
    lab2 = '/Users/kristofer/comp_490/2lab/data/cache.db'
    
    database = sqlite3.connect(lab2)
    commands = database.cursor()

    commands.execute("CREATE TABLE webPage (webPageId integer primary key,"+
                     "linkText varchar(512) not null)")

    commands.execute("CREATE TABLE item (itemId integer primary key,"+
                     "itemName varchar(128) not null)")

    commands.execute("CREATE TABLE itemToWebPage (id integer primary key,"+
                     "itemId integer,"+
                     "webPageId integer,"+
                     "FOREIGN KEY(itemId) REFERENCES item(itemId),"+
                     "FOREIGN KEY(webPageId) REFERENCES webPage(webPageId))")

    commands.execute("CREATE TABLE token (tokenId integer primary key,"+
                     "word varchar(128) not null)")

    commands.execute("CREATE TABLE tokenToWebPage (id integer primary key,"+
                     "tokenId integer,"+
                     "webPageId integer,"+
                     "position integer,"+
                     "FOREIGN KEY(tokenId) REFERENCES token(tokenId),"+
                     "FOREIGN KEY(webPageId) REFERENCES webPage(webPageId))")
    database.commit()
    commands.close()
main()
