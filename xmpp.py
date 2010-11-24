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

from google.appengine.api import xmpp
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import m2ggg_config
import m2ggg_core
import logging
import md5
import sys

class XMPPHandler(webapp.RequestHandler):
    def post(self):
        cmdOP=m2ggg_core.cmdop()
        userview=m2ggg_core.UserView()
        message =""
        try:
            message=xmpp.Message(self.request.POST)
        except xmpp.InvalidMessageError, e:
            logging.error("Invalid XMPP request: %s", e[0])
            logging.error(self.request.body)
            logging.error(self.request.POST)
            return
        except:
            from_name=m2ggg_core.get_mail_name(self.request.get('from')).lower()
            m2ggg_core.activeresouce_record(from_name,4);
            logging.error(sys.exc_info()[0])
            raise "under attack:" +from_name.encode("UTF-8");
            return
        #if message.body[0:5].lower() == 'hello':
        #message.reply("Greetings!")
        from_name=m2ggg_core.get_mail_name(self.request.get('from')).lower()
        c1= ( from_name==m2ggg_config.root_gmail )
        c2= userview.checklist(from_name)
        if ( (not c2) and (not userview.is_blacklist) ) :
            try:
                logging.info(from_name.encode("UTF-8")+" : "+message.body );
                m2ggg_core.registerOutside(from_name);
            except:
                pass
            #logging.error(from_name.encode("UTF-8")+"|"+str)
            m2ggg_core.activeresouce_record(from_name,1);
            m2ggg_core.send_all_admin( from_name+'(is not member now , use //add '+from_name+' to make him to be one ) said outside: '+message.body,from_name );

        if c1 or c2 :
            if ( (from_name==m2ggg_config.root_gmail or userview.is_admin) and cmdOP.is_cmd(message.body.strip()) ) or ( cmdOP.is_all_cmd(message.body.strip(),from_name,userview.nickname,userview.idf) ) :
                m2ggg_core.activeresouce_record(from_name,3);
                m2ggg_core.activeresouce_record_usage(from_name,cmdOP.cmdname);
                m2ggg_core.set_cached_xmpp_status(from_name,True);
                message.reply(cmdOP.reply)
            else:
                #mdd=md5.new()
                #mdd.update( from_name.encode("UTF-8")  )
                #qd=mdd.hexdigest()[0:10]
                if (not userview.is_blacklist):
                    try:
                        m2ggg_core.set_cached_xmpp_status(from_name,True);
                        m2ggg_core.activeresouce_record(from_name,2);
                    except:
                        pass
                    if (not userview.usertype==1):
                        m2ggg_core.send_all(userview.nickname,userview.idf,message.body,from_name)
                    else:
                        ext=machine_passcode_decoder()
                        ext.decode(message.body)
                        m2ggg_core.send_all(userview.nickname+"/"+ext.nickname,userview.idf+"/"+ext.idf,ext.msg,from_name)
        #if from_name==m2ggg_config.root_gmail:
        #   logging.error(message.body)

        else:
            pass




application = webapp.WSGIApplication([('/_ah/xmpp/message/chat/', XMPPHandler)],
                     debug=False)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

# vim:se sw=4:
