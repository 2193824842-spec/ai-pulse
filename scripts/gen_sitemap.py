import json
with open('./site/posts/index.json', encoding='utf-8') as f:
    en_posts = json.load(f)
with open('./site/zh/posts/index.json', encoding='utf-8') as f:
    zh_posts = json.load(f)
base = 'https://2193824842-spec.github.io/ai-pulse'
parts = ['<?xml version="1.0" encoding="UTF-8"?>',
'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
'  <url><loc>'+base+'/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>',
'  <url><loc>'+base+'/blog.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>',
'  <url><loc>'+base+'/zh/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>',
'  <url><loc>'+base+'/zh/blog.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>',
]
for p in en_posts:
    parts.append('  <url><loc>'+base+'/posts/'+p['slug']+'.html</loc><lastmod>'+p['date']+'</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>')
for p in zh_posts:
    parts.append('  <url><loc>'+base+'/zh/posts/'+p['slug']+'.html</loc><lastmod>'+p['date']+'</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>')
parts.append('</urlset>')
with open('./site/sitemap.xml', 'w', encoding='utf-8') as f:
    f.write('\n'.join(parts))
print('Sitemap OK: EN=%d ZH=%d' % (len(en_posts), len(zh_posts)))
