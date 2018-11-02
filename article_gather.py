from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from datetime import timedelta, date
import time
import datetime
import re
import argparse
# Without this we get an error"ascii codec cant encode character"
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
# SQL Stuff
import MySQLdb as my

db_user_id = ""
db_user_name = ""
db_date = ''
db_time = ''
db_comment = ""
db_article_name = ""
db_likes = ""

profile_url = []
unique_users = []
date_list = []

secret_login = ""
secret_comments = ""

def load_secret():
    fname = "secret_sauce.dat"
    f = open(fname,"r")
    global secret_login
    secret_login = f.readline().split(' ')[1].rstrip()
    global secret_comments
    secret_comments = f.readline().split(' ')[1].rstrip()
    print secret_comments
    f.close()

def load_db():
    fname="dbcreds.dat" 
    f = open(fname,"r")
    #rstrip() is needde here or else it includse the newline from the creds file
    dbhost = f.readline().split(' ')[1].rstrip()
    dbuser = f.readline().split(' ')[1].rstrip()
    dbpw = f.readline().split(' ')[1].rstrip()
    dbdb = f.readline().split(' ')[1].rstrip()
    f.close()

    db = my.connect(host=dbhost,
            user=dbuser,
            passwd=dbpw,
            db=dbdb
            )
    return db

def close_db(db):
    db.close()

def sel_init():
    options = Options()
    options.add_argument("--headless")
    browser = webdriver.Firefox(firefox_options=options, executable_path='/home/shelbyt/geckodriver')
    return browser
    
# Works even if the date doesn't exist but is valid + works if there are just no articles
def archive_iterator(db,cursor,browser):
    for article_date in date_list:
        browser.get("http://www.wsj.com/public/page/archive-"+str(article_date)+".html")
        # create an array of article blocks
        blocks = browser.find_elements_by_xpath("//*[@class='newsItem']/li")
        if not blocks:
            # There are no articles for this day. Not sure if this works
            print "No articles"
        else:
            for block in blocks:
                article_title = ""
                article_url = ""
                article_blurb = ""
                article_state = 0 

                article_blurb = block.find_element_by_css_selector("p").text
                article_url = block.find_element_by_css_selector("h2>a").get_attribute('href')
                article_name = block.find_element_by_css_selector("h2").text

                sql="insert ignore into article_url(url,date,title,blurb,state) VALUES (%s,%s,%s,%s,%s)"
                cursor.execute(sql,(str(article_url), str(article_date),str(article_title), str(article_blurb), article_state))
                db.commit()

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

if __name__ == '__main__':
    start_date = date(2018, 01, 01)
    end_date = date(2018, 11, 01)
    
    for single_date in daterange(start_date, end_date):
        date_list.append(single_date.strftime("%Y-%m-%d"))
        #print single_date.strftime("%Y-%m-%d")

    print len(date_list)
    load_secret()

    db = load_db()
    cursor = db.cursor()
    browser = sel_init()
    archive_iterator(db,cursor,browser)
    close_db(db)
