from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
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
import pickle

db_user_id = ""
db_user_name = ""
db_date = ''
db_time = ''
db_comment = ""
db_article_name = ""
db_likes = ""

profile_url = []
unique_users = []

secret_login = ""
secret_comments = ""


def month_to_num(short_date):
    if short_date == "Jan": return 1
    if short_date == "Feb": return 2
    if short_date == "Mar": return 3
    if short_date == "Apr": return 4
    if short_date == "May": return 5
    if short_date == "Jun": return 6
    if short_date == "Jul": return 7
    if short_date == "Aug": return 8
    if short_date == "Sep": return 9
    if short_date == "Oct": return 10
    if short_date == "Nov": return 11
    if short_date == "Dec": return 12
    return -1

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

def load_creds_login():
    fname="wsjcreds.dat"
    f = open(fname,"r")
    uname = f.readline().split(' ')[1]
    pw = f.readline().split(' ')[1]
    f.close()
    # Input username
    loginID = browser.find_element_by_id("username").send_keys(uname)             
    # Input password
    loginPass = browser.find_element_by_id("password").send_keys(pw)    
    loginReady = browser.find_element_by_class_name("basic-login-submit")
    loginReady.submit()
    time.sleep(10) #this is needed because it takes time to login

def sel_init():
    options = Options()
    #options.add_argument("--headless")
    browser = webdriver.Firefox(firefox_options=options, executable_path='/home/shelbyt/geckodriver')
    return browser
    
def profile_comment_load(browser):
    #for i in range(0,3):
    #    print "range"
    #    load_more = browser.find_element_by_class_name("load-more").click()
    #    #load_more.submit()
    #    time.sleep(3)
    
    # Use this to press the 'load more' button until there is nothing left'
    # can also use the 'page num' selector from the page itself to find how many pages to iterate
    index = 0

    while True:
        try:
            load_more = browser.find_element_by_class_name("load-more").click()
            time.sleep(3)
            index = index + 1
            if (index%50) == 0:
                print "50 Pages loaded"
        except Exception as e:
            print e
            print index
            break
    print "Complete Loading User Comment Page" 

def gather_comments(browser,db,cursor):

    # Need to store date_time processing
    t_arr= []
    date_time = []

    ############# OBTAIN THESE ONCE PER PROFILE ##################
    # username appears once
    db_user_name= str(browser.find_elements_by_class_name("info-username")[0].text)
    
    # get the uid returned using URL method
    #url = browser.current_url
    #match = re.search('.*\/(.*)\?',url)
    #db_user_id = str(match.group(1)) 
    
    
    # get the uid returned using css method
    db_user_id = str(browser.find_element_by_css_selector("div.module.module-profile").get_attribute("data-vxid"))

    # If we just grab this module we get EVERYTHING we need excluding the userID
    # uid = browser.find_elements_by_class_name("module")
    # print uid
    # for elem in uid:
    #     print elem.text
    
    ############# ITERATE EACH COMMENT BLOCK ##################

    for cblock in browser.find_elements_by_class_name("module-comments"):

        likes = cblock.find_elements_by_class_name("comments-recommendations")[0]
        # need to convert it to utf-8 or str format or else can't use string operators like split
        likes= str(likes.text)
        #The likes text looks like " 7 likes" so i just want the 7 part
        likes = likes.split(' ')[0]
        #ignore the header child and get the a-href text

        headline = cblock.find_elements_by_class_name("comments-headline")[0].find_element_by_tag_name("a")

        comment = cblock.find_elements_by_class_name("comments-content")[0]

        time =  cblock.find_elements_by_class_name("comments-time")[0]
        real_t = time.text
        real_t_arr = [x.encode('utf-8') for x in real_t.split()]
        real_t_arr[1] = real_t_arr[1][:-1] # remove last comma
        [hour,mins] = [int (x) for x in real_t_arr[3].split(':')]
        t_format = datetime.timedelta(hours=hour,minutes=mins)
        date_time.insert(0, datetime.datetime(int(real_t_arr[2]),
                 int(month_to_num(real_t_arr[0])),int(real_t_arr[1])))
    
        if real_t_arr[4] == "PM": # for some reason using "IS" doesn't work here
            if real_t_arr[3].split(':')[0] != "12":
                t_format = t_format + datetime.timedelta(hours=12) # add 12 hours if it is PM

        # I dont think this format() call is needed
        date_time.insert(1,format(t_format))
        t_arr.append(date_time) # append into final time array the sequence of times
      
        ################## INSERT EVERYTHING INTO THE GLOBAL DB STRINGS ##############

        # just use the date part of date_time
        db_date = datetime.datetime(int(real_t_arr[2]),
                 int(month_to_num(real_t_arr[0])),int(real_t_arr[1])).date().strftime("%Y-%m-%d")
        db_time=t_format

        # without this str encoding i get a 'latin-1 codec cant encode character'
        # use ascii ignore to remove any weird characters
        db_comment = str(comment.text).encode('ascii','ignore')
        db_article_name = str(headline.text).encode('ascii','ignore')
        db_likes = likes

        ################## PERFORM SQL QUERY ##############
   
        # This works but it causes weird formatting issues because I'm not specifiyng the column
        # sql="insert into Members values ('%s', '%s','%s','%s','%s','%s','%s')" 
        #     % (db_user_id,db_user_name,db_date,db_time,db_comment,db_article_name,db_likes)

        sql="insert into Members(user_id,user_name,date,time,comment,article_name,likes) VALUES (%s, %s,%s,%s,%s,%s,%s)"
        num_rows=cursor.execute(sql,(db_user_id,db_user_name,db_date,db_time,db_comment,db_article_name,db_likes))
        db.commit()
        date_time = []

def article_comments_load(browser,article_url):

    global profile_url

    # Access comments
    print secret_comments
    comment_url = secret_comments+str(article_url)
    print comment_url
    # Load browser
    browser.get(comment_url)
    time.sleep(10)

    # First load the entire page by clicking the button, works for up to 1000 comments
    while True:
        try:
            loader = browser.find_elements_by_xpath("//*[@class='talk-load-more']/button")
            # The last button on the page will be the one to load more. Other buttons on the page
            # Are for loading replies. Don't think replies are that useful
            loader[len(loader)-1].click()
            time.sleep(5)
        except Exception as e:
            print e
            break
    print "Complete Loading Article Comments"

    # We want to keep a list of the profile urls so we can access later
    url_list = browser.find_elements_by_xpath("//*[@class='talk-stream-comment-container']/div/div/div/a")

    # Insert into global list here
    for user in url_list:
        # Need to test if this works to maintain a unique list within article
        # This is useful especially if we're getting replies
        # If a user comments twice, only keep one.
        if user not in profile_url:
            # Get the actual users profile url here
            # TODO(shelbyt): Fix bad naming user is a userblock
            match = re.search('.*\/(.*)\?',user.get_attribute("href"))
            # Returns a user_id which we can match with the database list
            article_user_id = str(match.group(1)) 
            # If the user_id from the url isn't found in the database list then
            #    we can insert it.
            if article_user_id not in unique_users:
                profile_url.append(user.get_attribute("href"))
    return len(profile_url)

def insert_article_user_comments(browser, db, cursor):
    login_flag = 0

    for profile in profile_url:
        print "Trying to load = " + profile
        browser.get(profile)
        if login_flag == 0:
            load_creds_login()
            login_flag = 1

        profile_comment_load(browser)
        gather_comments(browser,db,cursor)
        print "Captured User Sucessfully"

def get_unique_user_list(db,cursor):
    # Get list of users from the table so we don't reinsert them
    sql='select distinct user_id from Members'
    num_rows=cursor.execute(sql)
    db.commit()

    db_list = list(cursor.fetchall())

    # Things are returned as a list tuple so need extra array index
    for i in range(0,len(db_list)):
        unique_users.append(db_list[i][0])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--profile',required=True)
    parser.add_argument('-a','--article',required=True)
    parser.add_argument('-gc','--getcookie',required=False,action='store_false')
    parser.add_argument('-lc','--loadcookie',required=False,action='store_false')

    args = vars(parser.parse_args())
    profile = args['profile']
    article_url = args['article']
    get_cookie = args['getcookie']
    load_cookie = args['loadcookie']

    
    # To get cookie to work first, we login using profile page then
    # move to the article page. Get cookies from there.

    # When loading, navitage to ARTICLE page then load cookies then
    # navigate to profile page

    # Based on https://stackoverflow.com/questions/15058462/how-to-save-and-load-cookies-using-python-selenium-webdriver

    browser = sel_init()

    if (get_cookie):
        print "Going to profile to get login"
        browser.get(profile)

        print "Logging in"
        load_creds_login()

        print "Going to Article Url"
        browser.get(article_url)

        print "Dumping cookie"
        pickle.dump( browser.get_cookies() , open("cookies.pkl","wb"))

    if (load_cookie):
        print "Going to Article Url Page"
        browser.get(article_url)

        print "Loading cookie"
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
                browser.add_cookie(cookie)

        print "Navigating to Profile WITHOUT LOGGING IN"
        browser.get(profile)


