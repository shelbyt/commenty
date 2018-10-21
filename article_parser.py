from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
import time
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import datetime
import re
import argparse

#Without this we get an error"ascii codec cant encode character"
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


#SQL Stuff
import MySQLdb as my

parser = argparse.ArgumentParser()
parser.add_argument('-p','--profile',required=True)
args = vars(parser.parse_args())
profile = args['profile']
print "printing profile"
print profile



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

db_user_id = ""
db_user_name = ""
db_date = ''
db_time = ''
db_comment = ""
db_article_name = ""
db_likes = ""

cursor=db.cursor()


options = Options()
options.add_argument("--headless")


## Loading URL
extractItems = []
#browser = webdriver.Firefox()


browser = webdriver.Firefox(firefox_options=options, executable_path='/home/shelbyt/geckodriver')

browser.get(profile)



# ==============================================================================
## Login Credentials
#login = browser.find_element_by_link_text("Log In").click()
fname="wsjcreds.dat"
f = open(fname,"r")
uname = f.readline().split(' ')[1]
pw = f.readline().split(' ')[1]
f.close()

loginID = browser.find_element_by_id("username").send_keys(uname)             # Input username
loginPass = browser.find_element_by_id("password").send_keys(pw)     # Input password
loginReady = browser.find_element_by_class_name("basic-login-submit")
loginReady.submit()
# ==============================================================================

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


time.sleep(10) #this is needed because it takes time to load

t_arr= []
date_time = []
#for i in range(0,3):
#    print "range"
#    load_more = browser.find_element_by_class_name("load-more").click()
#    #load_more.submit()
#    time.sleep(3)


#Use this to press the 'load more' button until there is nothing left'
#can also use the 'page num' selector from the page itself to find how many pages to iterate

while True:
    try:
        load_more = browser.find_element_by_class_name("load-more").click()
        time.sleep(3)
    except Exception as e:
        print e
        break

print "Complete Loading Comments"


#username appears once
db_user_name= str(browser.find_elements_by_class_name("info-username")[0].text)

#get the uid returned using URL method but sometimes it doesnt load into the db
#url = browser.current_url
#match = re.search('.*\/(.*)\?',url)
#db_user_id = str(match.group(1)) 


#get the uid returned using css method
db_user_id = str(browser.find_element_by_css_selector("div.module.module-profile").get_attribute("data-vxid"))
######If we just grab this module we get EVERYTHING we need excluding the userID ####
#uid = browser.find_elements_by_class_name("module")
#print uid
#for elem in uid:
#    print elem.text

##############################################################################

for cblock in browser.find_elements_by_class_name("module-comments"):
    likes = cblock.find_elements_by_class_name("comments-recommendations")[0]
    #print likes
    # need to convert it to utf-8 or str format or else can't use string operators like split
    likes= str(likes.text)
    #The likes text looks like " 7 likes" so i just want the 7 part
    likes = likes.split(' ')[0]
    #headline = cblock.find_elements_by_class_name("comments-headline")[0].find_elements_by_tag_name('h2#href')

    #ignore the header child and get the a-href text
    headline = cblock.find_elements_by_class_name("comments-headline")[0].find_element_by_tag_name("a")

    #headline = cblock.find_elements_by_css_selector("comments-headline a").get_attribute("href")
    #print headline.text
    comment = cblock.find_elements_by_class_name("comments-content")[0]
    #print comment.text
    time =  cblock.find_elements_by_class_name("comments-time")[0]
    #print time.text
    real_t = time.text
    real_t_arr = [x.encode('utf-8') for x in real_t.split()]
    real_t_arr[1] = real_t_arr[1][:-1] # remove last comma
    #print real_t_arr
    #[hour,mins] = int(x) for x in real_t_arr[3].split(':')
    [hour,mins] = [int (x) for x in real_t_arr[3].split(':')]
    t_format = datetime.timedelta(hours=hour,minutes=mins)
    date_time.insert(0, datetime.datetime(int(real_t_arr[2]),
             int(month_to_num(real_t_arr[0])),int(real_t_arr[1])))

    #print t_format
    #print real_t_arr[4]
    if real_t_arr[4] == "PM": # for some reason using "IS" doesn't work here
        if real_t_arr[3].split(':')[0] != "12":
            t_format = t_format + datetime.timedelta(hours=12) # add 12 hours if it is PM
    #print t_format.strftime("%H")
    #print format(t_format)
    # I dont think this format() call is needed
    #print format(t_format)
    date_time.insert(1,format(t_format))
    #real_t_arr[3] = format(t_format) # add time into FOURTH element (index 3)
    #real_t_arr = real_t_arr[:-1] # remove am/pm
    #print date_time
    t_arr.append(date_time) # append into final time array the sequence of times

   
    # just use the date part of it
    db_date = datetime.datetime(int(real_t_arr[2]),
             int(month_to_num(real_t_arr[0])),int(real_t_arr[1])).date().strftime("%Y-%m-%d")
    db_time=t_format
    #without this str encoding i get a 'latin-1 codec cant encode character'
    #use ascii ignore to remove any weird characters
    db_comment = str(comment.text).encode('ascii','ignore')
    db_article_name = str(headline.text).encode('ascii','ignore')

    db_likes = likes

    #sql="insert into Members values ('%s', '%s','%s','%s','%s','%s','%s')" % (db_user_id,db_user_name,db_date,db_time,db_comment,db_article_name,db_likes) #this works
    sql="insert into Members(user_id,user_name,date,time,comment,article_name,likes) VALUES (%s, %s,%s,%s,%s,%s,%s)"

    #print "Insert this comment: " + db_comment

    num_rows=cursor.execute(sql,(db_user_id,db_user_name,db_date,db_time,db_comment,db_article_name,db_likes))
    #this works
    db.commit()
    date_time = []

#after putting in all comments close it
db.close()
    

df = pd.DataFrame(columns=['date','time'])
#print t_arr
#print len(t_arr)

for i in range(len(t_arr)):
    df.loc[i]=t_arr[i]

#print df
#df.to_csv("name.csv")

#ax = sns.scatterplot(x="date", y="time", data=df)
#plt.show()

