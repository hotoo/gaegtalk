# vim:fileencoding=utf-8

from m2ggg_secure import *

msg_str_fail="FAIL"
msg_str_succ="SUCC"
msg_str_help_usr='''
命令列表：
//nick 新昵称:  更改昵称
//online:       查看在线用户
//m 昵称 消息:  PM某人
//iam:          自己的状态
//stop secs:    暂停
//continue:     继续(同 //stop -1)
//block FID:    阻止某人的消息
//unblock FID:  取消阻止
//setid FID:    更改自己的 FID (仅一次机会)
//showinfo FID: 查看某人的信息'''
msg_str_help_admin='''
//nick 新昵称:  更改昵称
//online:       查看在线用户
//m 昵称 消息:  PM某人
//allok:        许可全部人加入
//add GtalkID:  添加用户
//blacklist GtalkID: 拉黑名单
//pass GtalkID: 从黑名单中移除
to know one's email://whois Nickname 
My info: //iam 
Stop: //stop secs 
Continue: //continue (as //stop -1) 
//block FID -- Block someone 
//unblock FID -- Unblock someone  
//setid FID -- change your FID  (only one chance) 
//showinfo FID -- show one's info'''
msg_str_reserved="reversed...."

