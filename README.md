# Discuz!利用SSRF+Redis缓存应用导致有条件代码执行
### 0x00漏洞简介
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
