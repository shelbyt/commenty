import sys
reload(sys)
sys.setdefaultencoding('utf-8')
# SQL Stuff
import MySQLdb as my

profile_url = []
unique_users = []

secret_login = ""
secret_comments = ""
secret_prefix = ""
secret_suffix = ""


def load_secret():
    fname = "secret_sauce.dat"
    f = open(fname,"r")
    global secret_login
    secret_login = f.readline().split(' ')[1].rstrip()
    global secret_comments
    secret_comments = f.readline().split(' ')[1].rstrip()
    global secret_prefix
    secret_prefix = f.readline().split(' ')[1].rstrip()
    global secret_suffix
    secret_suffix = f.readline().split(' ')[1].rstrip()
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


def get_unique_user_list(db,cursor):

    # Get list of users from the table so we don't reinsert them
    sql='select distinct user_id from Members'
    num_rows=cursor.execute(sql)
    db.commit()

    db_list = list(cursor.fetchall())

    # Things are returned as a list tuple so need extra array index
    for i in range(0,len(db_list)):
        unique_users.append(str(secret_prefix + str(db_list[i][0]) + secret_suffix))

def transfer_users(db,cursor):
    for user_url in unique_users:
        sql="insert ignore into profile_url(p_url,state) VALUES (%s,%s)"
        # State 2 means that this user is complete
        num_rows=cursor.execute(sql,(user_url, 2))
        db.commit()

if __name__ == '__main__':

    db = load_db()
    cursor = db.cursor()
    load_secret()
    get_unique_user_list(db,cursor)
    transfer_users(db,cursor)
    close_db(db)



