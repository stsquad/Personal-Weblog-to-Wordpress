#!/usr/bin/python
#
# Convert from Personal Weblog to Wordpress
# PW: http://www.kyne.com.au/~mark/software/weblog.php
# WP: http://wordpress.org
#
# (C)opyright Alex Bennee (alex@bennee.com).
# License: GPLv3 (or later)

import getopt
import sys
import MySQLdb
import datetime

# Params
wp_prefix="wp_"
database=""
username=""
password=""

# Mappings
id_to_tag={}
pwid_to_wpid={}
articles=[]

def do_conversion():
    # First connect
    conn = MySQLdb.connect(host="localhost", user=username, passwd=password, db=database)
    c = conn.cursor()
    c.execute("SELECT tid, name FROM topics")
    while (1):
        r = c.fetchone()
        if r == None:
            break
        tid = r[0]
        name = r[1].lower()
        id_to_tag[tid] = name

    # Create the meta tags in wordpress
    for k, v in id_to_tag.iteritems():
        ins_sql="INSERT into "+wp_prefix+"terms (name, slug) VALUES ('"+v+"', '"+v+"')"
        print "SQL: %s" % (ins_sql)
        try:
            c.execute(ins_sql)
            c.execute("SELECT term_id FROM "+wp_prefix+"terms WHERE name='"+v+"'")
            wp_key = c.fetchone()
            print "added meta key: %s as WP term %d" % (v, wp_key[0])
            pwid_to_wpid[k]=wp_key[0]
        except:
            print "Failed to run: %s" % (ins_sql)
        

        
    # Now grab the articles
    c.execute("SELECT title, tid, updated, body, more FROM entries")
    while (1):
        r = c.fetchone()
        if r == None:
            print "Got a null"
            break
        title=MySQLdb.escape_string(r[0])
        print "Processing: %s" % (title)
        unixtime=r[2]
        updated=datetime.datetime.fromtimestamp(unixtime)
        posttime=updated.__str__()
        post=MySQLdb.escape_string(r[3]+r[4])
        tag=id_to_tag[r[1]]
        insert="INSERT into "+wp_prefix+"posts "
        fields="post_date, post_date_gmt, post_content, post_title"
        ins_sql=insert+"("+fields+") VALUES ('"+posttime+"', '"+posttime+"', '"+post+"', '"+title+"')"
        try:
            ic=conn.cursor()
            ins=ic.execute(ins_sql)
            print "INSERT done"
        except:
            print "Failed to run: %s (%s/%s)" % (ins_sql, sys.exc_type, sys.exc_value)
            sys.exit(1)
        
        
        

# Start of code
if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:p:d:", ["user=", "db=", "pw="])
    except getopt.GetoptError, err:
        usage()

    for o,a in opts:
        if o in ("-u"):
            username=a
        if o in ("-p"):
            password=a
        if o in ("-d", "--db"):
            database=a


    do_conversion()
