import re

email_list = ["XiaoWang@163.com", "XiaoWang@163.comheihei", "XiaoWang@qq.com"]
for email in email_list:
    ret = re.match(r'\w{4,20}@163\.com$', email)
    if ret:
        print(f'{ret.group()}是正确的邮箱')
    else:
        print(f'{email}不是正确的邮箱')
