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

    # Clear the Wordpress tables
    cls_sql="TRUNCATE TABLE "+wp_prefix+"terms"
    c.execute(cls_sql)
    cls_sql="TRUNCATE TABLE "+wp_prefix+"term_taxonomy"
    c.execute(cls_sql)
        
    # Create the meta tags in wordpress
    for k, v in id_to_tag.iteritems():
        ins_sql="INSERT into "+wp_prefix+"terms (name, slug) VALUES ('"+v+"', '"+v+"')"
        print "SQL: %s" % (ins_sql)
        try:
            c.execute(ins_sql)
        except:
            print "Failed to insert meta tag: %s" % (ins_sql)
        # Now map PW id to new WP id
        c.execute("SELECT term_id FROM "+wp_prefix+"terms WHERE name='"+v+"'")
        wp_key = c.fetchone()
        print "Found meta key: %s as WP term %d" % (v, wp_key[0])
        pwid_to_wpid[k]=wp_key[0]
        # Update the taxonomy table
        ins_sql="INSERT into "+wp_prefix+"term_taxonomy (term_id, taxonomy) VALUES ('"+wp_key[0].__str__()+"', 'post_tag')"
        try:
            c.execute(ins_sql)
        except:
            print "Failed to update taxonomy table: %s" % (ins_sql)

    # Clear the Wordpress tables
    cls_sql="TRUNCATE TABLE "+wp_prefix+"term_relationships"
    c.execute(cls_sql)
    cls_sql="TRUNCATE TABLE "+wp_prefix+"posts"
    c.execute(cls_sql)

    # And commit those changes
    c.close()
    conn.commit()
      
    # Now its time to do the  articles
    pwl_c = conn.cursor()
    pwl_c.execute("SELECT title, tid, updated, body, more FROM entries")
    while (1):
        r = pwl_c.fetchone()
        if r == None:
            print "Got a null"
            break
        title=MySQLdb.escape_string(r[0])
        print "Processing: %s" % (title)
        pwid=r[1]
        unixtime=r[2]
        updated=datetime.datetime.fromtimestamp(unixtime)
        posttime=updated.__str__()
        post=MySQLdb.escape_string(r[3]+r[4])
        insert="INSERT into "+wp_prefix+"posts "
        fields="post_date, post_date_gmt, post_content, post_title"
        ins_sql=insert+"("+fields+") VALUES ('"+posttime+"', '"+posttime+"', '"+post+"', '"+title+"')"
        try:
            wp_c=conn.cursor()
            ins=wp_c.execute(ins_sql)
            # fetch last ID
            wp_c.execute("SELECT LAST_INSERT_ID()")
            ir=wp_c.fetchone()
            post_id=ir[0]
            print "INSERT done (post %d)" % (post_id)
            try:
                # What tag shall we use?
                wpm_c=conn.cursor()
                wp_id=pwid_to_wpid[pwid]
                ins_meta_sql="INSERT into "+wp_prefix+"term_relationships (object_id, term_taxonomy_id) VALUES ('"+post_id.__str__()+"', '"+wp_id.__str__()+"')"
                wpm_c.execute(ins_meta_sql)
                wpm_c.close()
            except:
                print "Failed meta insert: (%s/%s)" % (sys.exc_type, sys.exc_value)
                sys.exit(2)

            # commit those changes
            wp_c.close()
            conn.commit()
            
        except:
            print "Failed to run: %s (%s/%s)" % (ins_sql, sys.exc_type, sys.exc_value)
            sys.exit(1)
        
    #
    pwl_c.close()
    conn.commit()
        

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
