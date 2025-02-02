import os
import xml.etree.ElementTree as ET
from datetime import datetime

PAGES_DIR = "migration_data/tdr_bio/pages"
OUTPUT_FILE = "migration_import.xml"

def gather_pages(pages_dir):
    pages = []
    for root, _, files in os.walk(pages_dir):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                title = os.path.splitext(file)[0]
                pages.append({"title": title, "content": content, "filepath": filepath})
    return pages

def create_wordpress_xml(pages):
    header = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:wfw="http://wellformedweb.org/CommentAPI/"
     xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:wp="http://wordpress.org/export/1.2/">
    <channel>
      <title>Tulku Dakpa Rinpoche</title>
      <link>https://tdr.bio</link>
      <description>WordPress export of migrated pages</description>
      <wp:wxr_version>1.2</wp:wxr_version>
      <language>en</language>
"""
    items = ""
    post_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for page in pages:
        item = f"""
      <item>
        <title>{page["title"]}</title>
        <link>{page["filepath"]}</link>
        <pubDate>{post_date}</pubDate>
        <dc:creator>admin</dc:creator>
        <guid isPermaLink="false">{page["filepath"]}</guid>
        <description></description>
        <content:encoded><![CDATA[{page["content"]}]]></content:encoded>
        <excerpt:encoded><![CDATA[]]></excerpt:encoded>
        <wp:post_date>{post_date}</wp:post_date>
        <wp:post_date_gmt>{post_date}</wp:post_date_gmt>
        <wp:comment_status>closed</wp:comment_status>
        <wp:ping_status>closed</wp:ping_status>
        <wp:post_name>{page["title"].lower().replace(" ", "-")}</wp:post_name>
        <wp:status>publish</wp:status>
        <wp:post_parent>0</wp:post_parent>
        <wp:menu_order>0</wp:menu_order>
        <wp:post_type>page</wp:post_type>
        <wp:post_password></wp:post_password>
        <wp:is_sticky>0</wp:is_sticky>
      </item>
"""
        items += item
    footer = """
    </channel>
</rss>
"""
    return header + items + footer

def main():
    pages = gather_pages(PAGES_DIR)
    if not pages:
        print("No HTML pages found in", PAGES_DIR)
        return
    xml_content = create_wordpress_xml(pages)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f"Migration XML generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()