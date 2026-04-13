#!/usr/bin/env python3
"""
批量更新所有文章的目录 JS 代码，添加滚动高亮功能
"""
import os
import re

# 旧的 JS 代码模式
OLD_SCRIPT_PATTERN = r'<script>\s*\(function\(\)\{.*?h2s\.forEach\(function\(h\)\{observer\.observe\(h\);\}\);\s*\}\)\(\);\s*</script>'

# 新的 JS 代码
NEW_SCRIPT = '''<script>
  (function(){
    var body=document.querySelector('.article-body');
    var toc=document.getElementById('toc-sidebar');
    if(!body||!toc)return;
    var h2s=body.querySelectorAll('h2');
    if(h2s.length<2){var d=document.querySelector('.article-toc');if(d)d.style.display='none';return;}
    var links=[];
    h2s.forEach(function(h,i){
      var id='s'+(i+1);
      h.id=id;
      var li=document.createElement('li');
      var a=document.createElement('a');
      a.href='javascript:void(0)';
      a.textContent=h.textContent;
      a.dataset.target=id;
      a.onclick=function(e){
        e.preventDefault();
        h.scrollIntoView({behavior:'smooth',block:'start'});
      };
      li.appendChild(a);
      toc.appendChild(li);
      links.push(a);
    });
    // Scroll spy - highlight based on scroll position
    function updateActive(){
      var scrollPos=window.scrollY+150; // offset from top
      var current=null;
      h2s.forEach(function(h){
        var top=h.offsetTop;
        if(scrollPos>=top){
          current=h.id;
        }
      });
      links.forEach(function(link){link.classList.remove('active');});
      if(current){
        var activeLink=links.find(function(link){return link.dataset.target===current;});
        if(activeLink)activeLink.classList.add('active');
      }
    }
    window.addEventListener('scroll',updateActive);
    window.addEventListener('load',updateActive);
    updateActive();
  })();
  </script>'''

def update_article(file_path):
    """更新单个文章的 JS 代码"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找并替换旧的 script 标签
    # 使用更宽松的匹配模式
    pattern = r'<script>\s*\(function\(\)\{.*?\}\)\(\);\s*</script>\s*</body>'

    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, NEW_SCRIPT + '\n</body>', content, flags=re.DOTALL)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True
    else:
        print(f"  [!] 未找到匹配的 script 标签: {file_path}")
        return False

def main():
    site_dir = 'site'

    # 英文文章
    en_posts_dir = os.path.join(site_dir, 'posts')
    en_files = [f for f in os.listdir(en_posts_dir) if f.endswith('.html') and f != '_template.html']

    print(f"更新英文文章 ({len(en_files)} 篇)...")
    for filename in en_files:
        file_path = os.path.join(en_posts_dir, filename)
        if update_article(file_path):
            print(f"  [OK] {filename}")
        else:
            print(f"  [FAIL] {filename}")

    # 中文文章
    zh_posts_dir = os.path.join(site_dir, 'zh', 'posts')
    zh_files = [f for f in os.listdir(zh_posts_dir) if f.endswith('.html') and f != '_template.html']

    print(f"\n更新中文文章 ({len(zh_files)} 篇)...")
    for filename in zh_files:
        file_path = os.path.join(zh_posts_dir, filename)
        if update_article(file_path):
            print(f"  [OK] {filename}")
        else:
            print(f"  [FAIL] {filename}")

    print("\n完成！")

if __name__ == '__main__':
    main()
