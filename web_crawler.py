import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import argparse
import random

# Configuration
DOMAIN_CONFIG = {
    'tdr_bio': {
        'url': 'https://tdr.bio',
        'output_path': 'migration_data/tdr_bio',
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
    },
    'danakosha': {
        'url': 'https://danakosha.org',
        'output_path': 'migration_data/danakosha',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
}

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# WordPress mapping templates
WP_MAPPING = {
    'page': {
        'post_type': 'page',
        'meta_input': ['template', 'header_image']
    },
    'post': {
        'post_type': 'post',
        'taxonomies': ['category', 'post_tag']
    }
}

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    return os.path.abspath(path)

def crawl_domain(domain_config):
    """Crawl a single domain"""
    start_url = domain_config['url']
    output_path = domain_config['output_path']
    
    # Create output directories
    create_directory(output_path)
    create_directory(os.path.join(output_path, 'pages'))
    create_directory(os.path.join(output_path, 'images'))
    create_directory(os.path.join(output_path, 'metadata'))
    visited = set()
    to_visit = [start_url]
    css_files = set()
    
    while to_visit:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        
        # Create URL-specific directories
        parsed_url = urlparse(url)
        page_path = os.path.join(output_path, 'pages', parsed_url.path[1:])
        asset_path = os.path.join(output_path, 'assets', parsed_url.netloc)
        create_directory(page_path)
        create_directory(asset_path)
        
        # Random user-agent
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Save page content
            with open(os.path.join(output_path, 'pages', urlparse(url).path[1:] + '.html'), 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            print(f"Crawled: {url}")
            
            # Download CSS assets
            soup = BeautifulSoup(response.text, 'html.parser')
            for css in soup.find_all('link', rel='stylesheet'):
                css_url = urljoin(url, css['href'])
                try:
                    css_resp = requests.get(css_url, headers=headers, timeout=5)
                    css_resp.raise_for_status()
                    css_path = os.path.join(asset_path, 'css', os.path.basename(css_url))
                    create_directory(os.path.dirname(css_path))
                    with open(css_path, 'w', encoding='utf-8') as f:
                        f.write(css_resp.text)
                    print(f"Downloaded CSS: {css_url}")
                except Exception as e:
                    print(f"Error downloading CSS {css_url}: {str(e)}")
            
            # Download JavaScript assets
            for js in soup.find_all('script', src=True):
                js_url = urljoin(url, js['src'])
                try:
                    js_resp = requests.get(js_url, headers=headers, timeout=5)
                    js_resp.raise_for_status()
                    js_path = os.path.join(asset_path, 'js', os.path.basename(js_url))
                    create_directory(os.path.dirname(js_path))
                    with open(js_path, 'w', encoding='utf-8') as f:
                        f.write(js_resp.text)
                    print(f"Downloaded JS: {js_url}")
                except Exception as e:
                    print(f"Error downloading JS {js_url}: {str(e)}")
            
            # Download Image assets
            for img in soup.find_all('img', src=True):
                img_url = urljoin(url, img['src'])
                try:
                    img_resp = requests.get(img_url, headers=headers, timeout=5, stream=True)
                    img_resp.raise_for_status()
                    img_path = os.path.join(asset_path, 'images', os.path.basename(urlparse(img_url).path))
                    create_directory(os.path.dirname(img_path))
                    with open(img_path, 'wb') as f:
                        for chunk in img_resp.iter_content(1024):
                            f.write(chunk)
                    print(f"Downloaded image: {img_url}")
                except Exception as e:
                    print(f"Error downloading image {img_url}: {str(e)}")
            
            # Find all links
            for link in soup.find_all('a', href=True):
                full_url = urljoin(start_url, link['href'])
                parsed = urlparse(full_url)
                
                # Check if URL belongs to the current domain
                if parsed.netloc == urlparse(start_url).netloc:
                    if full_url not in visited and full_url not in to_visit:
                        to_visit.append(full_url)
                        print(f"Found: {full_url}")
                        
        except requests.exceptions.RequestException as e:
            print(f"Error crawling {url}: {str(e)}")
            continue

def main():
    parser = argparse.ArgumentParser(description='Web Crawler for migration')
    parser.add_argument('--domain', type=str, required=True, choices=['tdr_bio', 'danakosha'],
                      help='Domain to crawl (tdr_bio or danakosha)')
    args = parser.parse_args()
    
    domain_config = DOMAIN_CONFIG.get(args.domain)
    if not domain_config:
        print("Invalid domain specified")
        return
        
    print(f"Starting crawl for: {args.domain}")
    crawl_domain(domain_config)
    print("Crawl completed successfully")

if __name__ == "__main__":
    main()