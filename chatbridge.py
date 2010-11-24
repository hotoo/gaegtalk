############################################################################
#    Copyright (C) 2010 by math2gold                                       #
#    Twitter:@math2gold                                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

import urllib
import md5
import m2ggg_core
import xml.dom.minidom
from google.appengine.ext import db
from google.appengine.api import xmpp
from google.appengine.api import memcache
from google.appengine.api import urlfetch
class BridgeHubInfo(db.Model):
	name = db.StringProperty(required=True,indexed=True)
	key1 = db.StringProperty(required=True,indexed=True)
	key2 = db.StringProperty(required=True,indexed=True)
	url  = db.StringProperty(required=True,indexed=True)
	flag = db.IntegerProperty(required=True,indexed=True)
	disabled = db.BooleanProperty(required=True,indexed=True)

def add_link_hub_send(idname,key,_url):
	p=len(key)
	q=p/2
	e=BridgeHubInfo(key_name="0:"+idname,name=idname,key1=key[0:q],key2=key[q:p],url=_url,flag=0,disabled=False)
	e.put()
	return

def add_link_hub_recv(idname,key,_url):
	p=len(key)
	q=p/2
	e=BridgeHubInfo(key_name="1:"+idname,name=idname,key1=key[0:q],key2=key[q:p],url=_url,flag=1,disabled=False)
	e.put()
	return

def remove_link_hub_send ( idname ):
	nk=BridgeHubInfo.get_by_key_name("0:"+idname)
	nk.delete()
	return

def remove_link_hub_recv ( id ):
	nk=BridgeHubInfo.get_by_key_name("1:"+idname)
	nk.delete()
	return

def convert_params_to_xml(params):
	impl=xml.dom.minidom.getDOMImplementation()
	newdoc=impl.createDocument(None,"a",None)
	for k in params:
		l=newdoc.documentElement.appendChild(newdoc.createElement(k))
		l.appendChild(newdoc.createTextNode(params[k]))
	return newdoc.toxml()

def convert_xml_to_params(xmlstr):
	params={}
	b=xml.dom.minidom.parseString(xmlstr)
	c=b.getElementsByTagName("a")[0].childNodes
	for h in c:
		params[h.nodeName] = h.childNodes[0].data
	return params

def make_params_sec(params,key1,key2):
	x=params.keys()
	x.sort()
	v=''
	for g in x:
		v+=('@'+params[g]+'@');
	v=key1+v+key2;
	mdd=md5.new()
	mdd.update(v.encode("UTF-8"))
	params["seckey"]=mdd.hexdigest()
	params["sectype"]="md5"
	return params

def check_params_sec(params,key1,key2):
	seckey=params["seckey"]
	sectype=params["sectype"]
	if not (sectype == "md5"):
		return None
	del params["sectype"]
	del params["seckey"]
	g=make_params_sec(params,key1,key2)
	if g["sectype"]==sectype and g["seckey"]==seckey:
		return params
	return None

class BridgeAsyncSendOp():
	rpcs=[];

	def reset_rpclist(self):
		self.rpcs=[];

	def send_one(self,to_hub,params):
		nk=BridgeHubInfo.get_by_key_name("0:"+to_hub)
		params["id"]=nk.name;
		data=convert_params_to_xml(make_params_sec(params,nk.key1,nk.key2));
		rpc = urlfetch.create_rpc()
		self.rpcs.append(rpc);
		urlfetch.make_fetch_call(rpc, url=nk.url,payload=data,method=urlfetch.POS,headers={'Content-Type': 'text/xml'})
		return

	def send_all(self,exclude,params):
		l=db.GqlQuery("SELECT * FROM BridgeHubInfo WHERE flag = :1 AND disabled = :2",0,False);
		ret=[]
		for e in l:
			if not m2ggg_core.check_hash(exclude,e.name):
				params["id"]=e.name;
				data=convert_params_to_xml(make_params_sec(params,e.key1,e.key2));
				rpc = urlfetch.create_rpc()
				self.rpcs.append(rpc);
				urlfetch.make_fetch_call(rpc, url=e.url,
                        payload=data.encode("UTF-8"),
                        method=urlfetch.POST,
                        headers={'Content-Type': 'text/xml'})
		return

	def send_msg(self,to_hub,msg,userid,userfid,user_nick,timestamp):
		params={}
		params["userid"]=userid;
		params["userfid"]=userfid;
		params["user_nick"]=user_nick;
		params["msg"]=msg;
		params["ts"]=timestamp;
		params["cmd"]="msg";
		return self.send_one(to_hub,params)

	def send_msg_all(self,exclude,msg,userid,userfid,user_nick,timestamp):
		params={}
		#params["from_user"]=from_user;
		params["userid"]=userid;
		params["userfid"]=userfid;
		params["user_nick"]=user_nick;
		params["msg"]=msg;
		params["ts"]=timestamp;
		params["cmd"]="msg";
		return self.send_all(exclude,params)

	def invoke(self):
		for g in self.rpcs:
			try:
				result = g.get_result()
			except urlfetch.DownloadError:
				pass
		self.reset_rpclist()
		return


def bridge_send_cmd(to_hub,params):
	nk=BridgeHubInfo.get_by_key_name("0:"+to_hub)
	params["id"]=nk.name;
	data=convert_params_to_xml(make_params_sec(params,nk.key1,nk.key2));
	return urlfetch.fetch(url=nk.url,
                        payload=data,
                        method=urlfetch.POST,
                        headers={'Content-Type': 'text/xml'})

def bridge_send_to_all(exclude,params):
	l=db.GqlQuery("SELECT * FROM BridgeHubInfo WHERE flag = :1 AND disabled = :2",0,False);
	ret=[]
	for e in l:
		if not m2ggg_core.check_hash(exclude,e.name):
			p=None
			try:
				params["id"]=e.name;
				data=convert_params_to_xml(make_params_sec(params,e.key1,e.key2));
				p=urlfetch.fetch(url=e.url,
                	        payload=data.encode("UTF-8"),
        	                method=urlfetch.POST,
	                        headers={'Content-Type': 'text/xml'})
			except:
				pass
			ret.append(p);
	return ret

def fetch_user_id_by_fid_from_hub(hub,user):
	params={}
	params["fid"]=user
	params["cmd"]="getid"
	V=bridge_send_cmd(hub,params)
	if (V.status_code==200):
		return V.content; 
	return "#"+str(V.status_code);

def bridge_send_msg(to_hub,msg,userid,userfid,user_nick,timestamp):
	params={}
	#params["from_user"]=from_user;
	params["userid"]=userid;
	params["userfid"]=userfid;
	params["user_nick"]=user_nick;
	params["msg"]=msg;
	params["ts"]=timestamp;
	params["cmd"]="msg";
	return bridge_send_cmd(to_hub,params)

def bridge_send_msg_all(exclude,msg,userid,userfid,user_nick,timestamp):
	params={}
	#params["from_user"]=from_user;
	params["userid"]=userid;
	params["userfid"]=userfid;
	params["user_nick"]=user_nick;
	params["msg"]=msg;
	params["ts"]=timestamp;
	params["cmd"]="msg";
	return bridge_send_to_all(exclude,params)

def bridge_recv_msg(buf):
	params=convert_xml_to_params(buf);
	name=params["id"]
	nk=BridgeHubInfo.get_by_key_name("1:"+name)
	if nk == None:
		return None
	return check_params_sec(params,nk.key1,nk.key2);


def bridge_recv_handler(params):
	if not (params==None):
		d=m2ggg_core.check_hash_none(params,"cmd")
		if d==None:
			return "Format Error"
		if d=="msg":
			nickname=params["user_nick"];
			idf=params["userfid"];
			msg=params["msg"];
			ex=params["userid"]
			h={}
			nk=BridgeHubInfo.get_by_key_name("1:"+params["id"])
			if not (nk==None):
				h[nk.url]=True
			m2ggg_core.send_all(nickname,"@"+params["id"]+"||"+idf,msg,ex,h,params["id"])
			return "Send Msg"
		if d=="getid":
			fix_name=params["fid"]
			l=m2ggg_core.get_user_by_id(fix_name)
			if not l==None:
				try:
					for e in l:
						return "*"+m2ggg_core.make_idcode(e.key().name());
				except:
					pass
			else:
				return "#not exists"
			return "#error"
	return "Format Error"
