
############################################################################
#    Copyright (C) 2010 by math2gold                       #
#    Twitter:@math2gold                            #
#                                      #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                   #
#                                      #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of    #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     #
#    GNU General Public License for more details.              #
#                                      #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the             #
#    Free Software Foundation, Inc.,                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.         #
############################################################################

from google.appengine.ext import db
from google.appengine.api import xmpp
from google.appengine.api import memcache
import logging
import string
import time
import xml.dom.minidom
import md5
import chatbridge
import m2ggg_config

class xmppUsageType(db.Model):
    nick_name = db.StringProperty(required=True,indexed=True)
    usage_type = db.IntegerProperty(required=True,indexed=True)
    count = db.IntegerProperty(required=True,indexed=True)

class cmdUsage(db.Model):
    nick_name = db.StringProperty(required=True,indexed=True)
    xcmd = db.StringProperty(required=True,indexed=True)
    count = db.IntegerProperty(required=True,indexed=True)

class UserListOutside(db.Model):
    nick_name = db.StringProperty(required=True,indexed=True)

class BlockUser(db.Model):
    from_name = db.StringProperty()
    to_name=db.StringProperty()

class BlockUserExt(db.Model):
    from_user_str = db.StringProperty()
    to_user_str = db.StringProperty()
    from_hub_str = db.StringProperty()
    from_name = db.StringProperty()
    to_name=db.StringProperty()

class UserListExpNewExt(db.Model):
    nick_name = db.StringProperty(required=True,indexed=True)
    fix_name = db.StringProperty(required=True,indexed=True)
    usertype = db.IntegerProperty(required=True,indexed=True)
    is_admin = db.BooleanProperty(required=True,indexed=True)
    is_blacklist = db.BooleanProperty(required=True,indexed=True)
    open_time = db.IntegerProperty(required=True,indexed=True)

class OutLinkGroup(db.Model):
    linker_name = db.StringProperty(required=True,indexed=True)
    linker_url = db.StringProperty(required=True,indexed=True)
    linker_key1 = db.StringProperty(required=True,indexed=True)
    linker_key2 = db.StringProperty(required=True,indexed=True)

######################Deprecated
class UserListExpNew(db.Model):
    nick_name = db.StringProperty(required=True,indexed=True)
    type = db.IntegerProperty(required=True,indexed=True)
    is_admin = db.BooleanProperty(required=True,indexed=True)
    is_blacklist = db.BooleanProperty(required=True,indexed=True)
    open_time = db.IntegerProperty(required=True,indexed=True)
#######################

class XmppStatusCache():
    Status=False
    def get_cached_xmpp_status(self,username):
        data = memcache.get(username)
        if data is not None:
            #DEBUG:logging.error(username+data)
            n=data.split(',')
            over=int(round(time.time()))-int(n[0])
            if over <60:
                self.Status=(n[1]=='True')
                return True
        return False

def xmlnodes_getText(nodelist):
    rc = ""
    for node in nodelist:
    if node.nodeType == node.TEXT_NODE:
        rc = rc + node.data
    return rc

def set_cached_xmpp_status(username,s):
    w=str(int(round(time.time())))+','+str(s)
    #DEBUG:logging.error("W:"+username+":"+w)
    if not memcache.set(username,w,60):
        memcache.add(username,w,60)

def cached_xmpp_user_check(username):
    xc=XmppStatusCache()
    if (xc.get_cached_xmpp_status(username)):
        return xc.Status;
    else:
        r=xmpp.get_presence(username)
        set_cached_xmpp_status(username,r)
        return r;

def type_increment_counter(key,nickname,utype):
    obj=xmppUsageType.get_by_key_name(key)
    if (obj==None):
        obj=xmppUsageType(key_name=key,nick_name=nickname,usage_type=utype,count=0)
    obj.count += 1
    obj.put()

def cmd_increment_counter(key,nickname,ucmd):
    obj=cmdUsage.get_by_key_name(key)
    if (obj==None):
        obj=cmdUsage     (key_name=key,nick_name=nickname,xcmd=ucmd,count=0)
    obj.count += 1
    obj.put()

def activeresouce_record(from_name,utype):
    key=str(utype)+"<#>"+from_name;
    #db.run_in_transaction(type_increment_counter,key,from_name,utype)
    type_increment_counter(key,from_name,utype)
    #update user's count [user,type,n]

def activeresouce_record_usage(from_name,cmd):
    key=cmd+"<#>"+from_name;
    db.run_in_transaction(cmd_increment_counter,key,from_name,cmd)
    #record command      [user,cmd,n]

class UserView():
    nickname=""
    idf=""
    is_admin=False
    is_blacklist=False
    usertype=0
    def checklist(self,from_name):
        r=UserListExpNewExt.get_by_key_name(from_name)
        if not (r==None) :
            self.nickname=r.nick_name
            self.idf=r.fix_name
            self.usertype=r.usertype
            try:
                self.is_admin= r.is_admin
                self.is_blacklist=r.is_blacklist
            except:
                pass
            return True
        return False


def sendmsg(msg,e):
    chat_sent=False
    #if xmpp.get_presence(e):
    if cached_xmpp_user_check(e):
        status_code = xmpp.send_message(e,msg)
        chat_sent= (status_code == xmpp.NO_ERROR)
        set_cached_xmpp_status(e,chat_sent)
    return chat_sent

def machine_passcode_encode(msg,nickname,idf):
    impl=xml.dom.minidom.getDOMImplementation()
    newdoc=impl.createDocument(None,"a",None)
    name=newdoc.documentElement.appendChild(newdoc.createElement('n'))
    msg=newdoc.documentElement.appendChild(newdoc.createElement('m'))
    id=newdoc.documentElement.appendChild(newdoc.createElement('i'))
    name.appendChild(newdoc.createTextNode(nickname))
    msg.appendChild(newdoc.createTextNode(msg))
    id.appendChild(newdoc.createTextNode(idf))
    return newdoc.toxml()

class machine_passcode_decoder():
    idf=""
    msg=""
    nickname=""
    def decode(self,msg):
        b=xml.dom.minidom.parseString(msg)
        self.idf=b.getElementsByTagName("a")[0].getElementsByTagName("i")[0]
        self.msg=b.getElementsByTagName("a")[0].getElementsByTagName("m")[0]
        self.nickname=b.getElementsByTagName("a")[0].getElementsByTagName("n")[0]
        return msg

def direct_show_encode(msg,nickname,idf):
    return nickname+' ('+idf+'): '+msg


def get_user_by_id(fix_name):
    l=db.GqlQuery("SELECT * FROM UserListExpNewExt WHERE fix_name = :1",fix_name)
    return l

def make_idcode(from_name):
    mdd=md5.new()
    mdd.update( m2ggg_config.protect_key1+from_name.encode("UTF-8")+m2ggg_config.protect_key2  )
    return mdd.hexdigest()[0:32]

def add_block(from_u,to_u):
    e=BlockUser(key_name=from_u+'@'+to_u,from_name=from_u,to_name=to_u)
    e.put()
    return

def remove_block(from_user,to_user):
    q = db.GqlQuery("SELECT * FROM BlockUser WHERE from_name = :1 AND to_name = :2", from_user,to_user)
    results = q.fetch(1)
    for result in results:
        result.delete()
    return

def check_hash(h,name):
    try:
        return h[name]
    except:
        return False

def check_hash_none(h,name):
    try:
        return h[name]
    except:
        return None


def send_all_inner(msg,ex,from_hub=""):
    l=db.GqlQuery("SELECT * FROM UserListExpNewExt WHERE is_blacklist = :1 AND open_time<:2",False,int(round(time.time())))
    uid=make_idcode(ex);
    ##TODO: add from_name IN :2 (HUB) or from_name = :2 (source hub) [source hub or relay hub?]
    hid=make_idcode("@@"+from_hub+"||");
    if from_hub=="":
        blk=db.GqlQuery("SELECT * FROM BlockUser WHERE from_name = :1",uid);
    else:
        ##open the following code while param idf exists.
        #uid=make_idcode("@@"+from_hub+"||"+idf);
        blk=db.GqlQuery("SELECT * FROM BlockUser WHERE from_name IN ( :1 , :2 )",uid,hid);
    blkh={}
    for x in blk:
        blkh[x.to_name]=True
    for e in l:
        if (not ( e.key().name() == ex ) ) and (not check_hash(blkh,make_idcode(e.key().name()))):
            try:
                sendmsg(msg,e.key().name())
            except:
                logging.error(e.key().name()+"|"+msg)


def send_all(nickname,idf,msg,ex,HUB={},from_hub=""):
    l=db.GqlQuery("SELECT * FROM UserListExpNewExt WHERE is_blacklist = :1 AND open_time<:2",False,int(round(time.time())))
    uid=make_idcode(ex);
    ##TODO: add from_name IN :2 (HUB) or from_name = :2 (source hub) [source hub or relay hub?]
    hid=make_idcode("@@"+from_hub+"||");
    if from_hub=="":
        blk=db.GqlQuery("SELECT * FROM BlockUser WHERE from_name = :1",uid);
    else:
        uid=make_idcode("@"+idf);
        blk=db.GqlQuery("SELECT * FROM BlockUser WHERE from_name IN ( :1 , :2 )",uid,hid);
    blkh={}
    b=0
    BAS=chatbridge.BridgeAsyncSendOp();
    BAS.send_msg_all(HUB,msg,uid,idf,nickname,str(int(round(time.time()))))
    for x in blk:
        b=b+1
        blkh[x.to_name]=True
    #DEBUG:logging.error(str(blkh)+"@"+uid+"@"+str(b))
    for e in l:
        if (not ( e.key().name() == ex ) ) and (not check_hash(blkh,make_idcode(e.key().name()))):
            try:
                #if (e.usertype == 0) :
                sendmsg(direct_show_encode(msg,nickname,idf),e.key().name())
                #else :
                #   sendmsg(machine_passcode_encode(msg,nickname,idf),e.key().name())
            except:
                logging.error(e.key().name()+"|"+msg)
    BAS.invoke()

def send_all_admin(msg,ex):
    l=db.GqlQuery("SELECT __key__ FROM UserListExpNewExt WHERE is_admin = :1",True)
    for e in l:
        if not ( e.name() == ex ) :
            try:
                sendmsg(msg,e.name())
            except:
                logging.error(e.name()+"|"+msg)

def get_mail_name(mailstr):
    try:
        return mailstr[:mailstr.find('/')]
    except:
        return ""

def is_validfid(x):
    for i in range(0,len(x)):
        h=x[i:i+1]
        if  (h=='@') or (not (h.isalnum() or h=='_' )):
             return False
    return True


#run a command
class cmdop():
    reply=""
    cmdname="*"
    def is_all_cmd(self,str,user,nick,idf=""):
        if str[0:2]!="//":
            return False
        v=string.find(str," ")
        if (v<0):
            v=len(str)
        cmdc=str[2:v]
        if cmdc=="showinfo":
            fix_name=str[10:].strip()
            l=get_user_by_id(fix_name)
            if not l==None:
                self.reply=""
                try:
                    for e in l:
                        self.reply+=fix_name+":\nID:"+make_idcode(e.key().name())+"\nNick:"+e.nick_name+"\nFID:"+e.fix_name+"\n\n";
                except:
                    pass
            else:
                self.reply="not exists"
            return True
        if cmdc=="setid":
            self.cmdname=str[0:6]
            try:
                n=str[8:].strip()
                if not is_validfid(n):
                    self.reply="error: only for a-z,A-Z,0-9 and _ sequence"
                    return True
                t=UserListExpNewExt.get_by_key_name(user)
                if not t==None:
                    try:
                        if ((string.find(t.fix_name,"@")==-1)):
                            self.reply="CAN NOT CHANGE AGAIN!"
                            return True
                    except:
                        pass
                l=db.GqlQuery("SELECT __key__ FROM UserListExpNewExt WHERE fix_name = :1",n)
                if l==None or l.count()<1 :
                    nk=UserListExpNewExt.get_by_key_name(user)
                    bf=nk.fix_name
                    nk.fix_name=n
                    nk.put()
                    send_all_inner(bf+" changed his fid to "+n,user)
                    self.reply="FID CHANGED!"
                    return True
            except:
                logging.error(user+"|"+str)
            return False
        if cmdc=="block":
            fix_name=str[7:].strip()
            nc=parse_multiId(fix_name)
            if not (nc==None):
                __hub=nc[0]
                __user=nc[1]
                #v=chatbridge.fetch_user_id_by_fid_from_hub(__hub,__user);
                #if not (v==None):
                #   if (v[0:1]=="*"):
                self.reply="Block ok!"
                ##TODO BLOCKIT
                add_block(make_idcode("@@"+__hub+"||"+__user),make_idcode(user))
                #   else:
                #   self.reply="strange:"+v
                #else:
                #   self.reply="Block failed"
                return True
            l=get_user_by_id(fix_name)
            if not l==None:
                self.reply=""
                try:
                    for e in l :
                        add_block(make_idcode(e.key().name()),make_idcode(user))
                        self.reply+="BLOCK:"+e.key().name()+"\n"
                except:
                    self.reply+="WRONG AT BLOCKING:"+e.key().name()+"\n"
                    pass
            else:
                self.reply="not exists"
            return True
        if cmdc=="unblock":
            fix_name=str[9:].strip()
            nc=parse_multiId(fix_name)
            if not (nc==None):
                __hub=nc[0]
                __user=nc[1]
                #v=chatbridge.fetch_user_id_by_fid_from_hub(__hub,__user);
                #if not (v==None):
                #   if (v[0:1]=="*"):
                self.reply="unBlock ok!"
                ##TODO BLOCKIT
                remove_block(make_idcode("@@"+__hub+"||"+__user),make_idcode(user))
                #   else:
        #   self.reply="strange:"+v
                #else:
                #   self.reply="unBlock failed"
                return True
            l=get_user_by_id(fix_name)
            if not l==None:
                self.reply=""
                try:
                    for e in l :
                        remove_block(make_idcode(e.key().name()),make_idcode(user))
                        self.reply+="UNBLOCK:"+e.key().name()+"\n"
                except:
                    self.reply+="WRONG AT BLOCKING:"+e.key().name()+"\n"
                    pass
            else:
                self.reply="not exists"
            return True
        if cmdc=="continue":
            self.cmdname=str[0:10]
            n=-1
            l=UserListExpNewExt.get_by_key_name(user)
            if not (l==None):
                l.open_time=int(round(time.time()))+n
                l.put()
                self.reply="ok,continue,stop:  %ld" % n
            else:
                self.reply="failed."
            return True
        if cmdc=="stop":
            self.cmdname=str[0:6]
            n=str[6:].strip()
            try:
                n=int(n)
            except:
                n=86400

            l=UserListExpNewExt.get_by_key_name(user)
            if not (l==None):
                l.open_time=int(round(time.time()))+n
                l.put()
                self.reply="ok,stop:  %ld" % n
            else:
                self.reply="failed."
            return True
        if cmdc=="iam":
            self.cmdname=str[0:5]
            l=UserListExpNewExt.get_by_key_name(user)
            if not (l==None):
                self.reply="user:"+user+"\n"
                self.reply+="nick:"+l.nick_name+"\n"
                self.reply+="fid:"+l.fix_name
            else:
                self.reply="???!"
            return True
        if cmdc=="help":
            self.cmdname=str[0:6]
            self.reply=m2ggg_config.msg_str_help_usr
            return True
        if cmdc=="nick":
            self.cmdname=str[0:6]
            try:
                n=str[7:].strip()
                if (len(n)>32):
                    self.reply="nick too long"
                    return True
                if not (string.find(n,"@")==-1):
                    self.reply="error:contains '@'"
                    return True
                l=db.GqlQuery("SELECT __key__ FROM UserListExpNewExt WHERE nick_name = :1",n)
                if l==None or l.count()<1 :
                    nk=UserListExpNewExt.get_by_key_name(user)
                    nk.nick_name=n
                    nk.put()
                    send_all_inner(nk.fix_name+" changed his nick to "+n,user)
                    self.reply="NICK CHANGED!"
                    return True
            except:
                logging.error(user+"|"+str)
            return False
        if cmdc=="m":
            self.cmdname=str[0:3]
            n=str#.encode("UTF-8")
            v=string.find(n," ")
            u=string.find(n," ",v+1)
            us=n[v+1:u]#.decode()
            wd=n[u+1:]#.decode()
            logging.error("NAME_x:"+us)
            l=db.GqlQuery("SELECT __key__ FROM UserListExpNewExt WHERE fix_name = :1 AND usertype = :2 AND open_time < :3",us,0,int(round(time.time())))
            ##block someone function check
            uid=make_idcode(user);
            blk=db.GqlQuery("SELECT * FROM BlockUser WHERE from_name = :1",uid);
            blkh={}
            for x in blk:
                blkh[x.to_name]=True
            self.reply="FAILED"
            for e in l:
                logging.error("NAME:"+e.name())
                if (not check_hash(blkh,make_idcode(e.name()))):
                    if sendmsg('@[m] '+nick+"("+idf+") : "+wd,e.name()):
                        self.reply="OK"
            return True;
        if cmdc=="online":
            self.cmdname=str[0:8]

            try:
                l=db.GqlQuery("SELECT * FROM UserListExpNewExt WHERE is_blacklist = :1",False)
                if (l==None):
                    logging.error("OH!");
                    return True;
                self.reply="\n"
                g=0
                for e in l:
                    mid=e.fix_name
                    try:
                        if cached_xmpp_user_check((e.key().name())):
                            self.reply+=e.nick_name+"("+mid+")\n"
                            g=g+1
                    except:
                        pass
                self.reply+="\n total:"
                b="%ld" % g
                self.reply+=b
                #### ####
                return True;
            except:
                logging.error("Some!");
                return False
        return False

#check if is a command
    def is_cmd(self,str):
        if str[0:2]!="//":
            return False
        v=string.find(str," ")
        if (v<0):
            v=len(str)
        cmdc=str[2:v]
        if cmdc=="whois":
            self.cmdname=str[0:7]
            n=str[8:]
            l=db.GqlQuery("SELECT __key__ FROM UserListExpNewExt WHERE fix_name = :1 AND usertype = :2",n,0)
            if not (l==None) :
                try:
                    self.reply=l.name();
                except:
                    self.reply=""
                    try:
                        for e in l :
                            self.reply+=e.name()+"\n";
                    except:
                        pass
            else:
                self.reply="not exists or is hidden"
            return True
        if cmdc=="blacklist":
            self.cmdname=str[0:11]
            n=str[12:].lower().strip()
            nk=UserListExpNewExt.get_by_key_name(n)
            nk.is_blacklist=True;
            nk.put()
            self.reply=""+n+" turn to Black now."
            return True
        if cmdc=="pass":
            self.cmdname=str[0:6]
            n=str[7:].lower().strip()
            nk=UserListExpNewExt.get_by_key_name(n)
            nk.is_blacklist=False
            nk.put()
            self.reply=""+n+" Black sign has removed."
            return True
        if cmdc=="admin":
            self.cmdname=str[0:7]
            n=str[8:].lower().strip()
            nk=UserListExpNewExt.get_by_key_name(n)
            nk.is_admin=True
            nk.put()
            self.reply=""+n+" is admin now"
            return True
        if cmdc=="unadmin":
            self.cmdname=str[0:9]
            n=str[10:].lower().strip()
            nk=UserListExpNewExt.get_by_key_name(n)
            nk.is_admin=False
            nk.put()
            self.reply=""+n+" Admin sign has removed."
            return True
        if cmdc=="add":
            self.cmdname=str[0:5]
            n=str[6:].lower().strip()
            l=db.GqlQuery("SELECT __key__ FROM UserListExpNewExt WHERE nick_name = :1",n)
            if l==None or l.count()<1 :
                e=UserListExpNewExt(key_name=n,fix_name='@'+make_idcode(n),nick_name=n,usertype=0,is_admin=False,is_blacklist=False,open_time=0)
                e.put()
                self.reply="ADD NEW: "+n
                if sendmsg('你已经加入本群。要设置昵称请使用 //nick 你的昵称',n):
                    self.reply+="\nOK"
                else:
                    self.reply+="\nFAILED"
                try:
                    deleteOutside(n)
                except:
                    logging.error("delete failed")
            else:
                self.reply+="User exists."
            return True
        if cmdc=="addroutesend":
            self.cmdname=str[0:14]
            n=str[15:].lower().strip() # name key url
            q1=string.find(n," ")
            if (q1==-1):
                return False
            s2=n[q1+1:]
            q2=string.find(s2," ")
            if (q2==-1):
                return False
            s1=n[0:q1]
            s3=s2[q2+1:]
            s2=s2[0:q2]
            chatbridge.add_link_hub_send(s1,s2,s3)
            self.reply+="ADD OK "+s1+":"+s2+":"+s3+":"
            return True
        if cmdc=="addrouterecv":
            self.cmdname=str[0:14]
            n=str[15:].lower().strip() # name key url
            q1=string.find(n," ")
            if (q1==-1):
                return False
            s2=n[q1+1:]
            q2=string.find(s2," ")
            if (q2==-1):
                return False
            s1=n[0:q1]
            s3=s2[q2+1:]
            s2=s2[0:q2]
            chatbridge.add_link_hub_recv(s1,s2,s3)
            self.reply+="ADD OK "+s1+":"+s2+":"+s3+":"
            return True
        if cmdc=="help":
            self.reply=m2ggg_config.msg_str_help_admin
            return True
        if cmdc=="allok":
            self.cmdname=str[0:10]
            ll=db.GqlQuery("SELECT * FROM UserListOutside LIMIT 0,20")
            for eh in ll :
                n=eh.key().name()
                e=UserListExpNewExt(key_name=n,fix_name='@'+make_idcode(n),nick_name=n,usertype=0,is_admin=False,is_blacklist=False,open_time=0)
                e.put()
                if sendmsg('你已经加入本群。要设置昵称请使用 //nick 你的昵称',n):
                    self.reply+="OK: "+n+"\n"
                else:
                    self.reply+="FAILED:"+n+"\n"
                try:
                    deleteOutside(n)
                except:
                    logging.error("delete failed")
                self.reply+="\nDone."
            return True
        if cmdc=="listuser":
            self.cmdname=str[0:10]
            self.reply=m2ggg_config.msg_str_reserved;
            return True
        return False

def deleteOutside(username):
    nk=UserListOutside.get_by_key_name(username)
    nk.delete()

def registerOutside(username):
    l=db.GqlQuery("SELECT __key__ FROM UserListOutside WHERE nick_name = :1",username)
    if l==None or l.count()<1 :
        e=UserListOutside(key_name=username,nick_name=username)
        e.put()

def parse_multiId(Q):
    g=string.find(Q,"||")
    if (Q[0:1]=="@" and g>0):
        return [ Q[1:g] , Q[g+2:] ]
    return None

# vim:se sw=4:
