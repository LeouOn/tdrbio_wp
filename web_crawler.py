#!/usr/bin/env python3
"""
Web Crawler for Migration

This script crawls a specified domain starting from a given URL,
downloads HTML pages and associated assets (CSS, JavaScript, images),
and saves them to designated output directories for migration purposes.
It also supports limiting the crawl depth via a command-line argument.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import argparse
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

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

# WordPress mapping templates (for potential future use)
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
        logging.info(f"Created directory: {path}")
    return os.path.abspath(path)

def sanitize_filename(filename):
    """Sanitize filename by removing non-ASCII characters"""
    return ''.join(char for char in filename if ord(char) < 128)

def get_page_filename(url):
    """Generate a filename for a given URL path"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        filename = "index.html"
    else:
        filename = f"{path}.html" if not path.endswith('.html') else path
    return sanitize_filename(filename)

def crawl_domain(domain_config, max_depth):
    """Crawl a single domain with an optional maximum depth for crawling"""
    start_url = domain_config['url']
    output_path = domain_config['output_path']
    
    # Create output directories
    create_directory(output_path)
    create_directory(os.path.join(output_path, 'pages'))
    create_directory(os.path.join(output_path, 'images'))
    create_directory(os.path.join(output_path, 'metadata'))
    
    visited = {}
    to_visit = [(start_url, 0)]  # tuple (url, depth)
    
    while to_visit:
        url, depth = to_visit.pop(0)
        if url in visited:
            continue
        if depth > max_depth:
            continue
        visited[url] = True
        
        parsed_url = urlparse(url)
        page_filename = get_page_filename(url)
        page_filepath = os.path.join(output_path, 'pages', page_filename)
        asset_path = os.path.join(output_path, 'assets', parsed_url.netloc)
        create_directory(os.path.dirname(page_filepath))
        create_directory(asset_path)
        
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Save page content
            with open(page_filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logging.info(f"Crawled: {url}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Download CSS assets
            for css in soup.find_all('link', rel='stylesheet'):
                css_url = urljoin(url, css.get('href'))
                try:
                    css_resp = requests.get(css_url, headers=headers, timeout=5)
                    css_resp.raise_for_status()
                    css_dir = os.path.join(asset_path, 'css')
                    create_directory(css_dir)
                    css_filename = os.path.basename(urlparse(css_url).path)
                    css_path = os.path.join(css_dir, css_filename)
                    try:
                        with open(css_path, 'w', encoding='utf-8') as f:
                            f.write(css_resp.text)
                    except FileNotFoundError:
                        logging.error(f"File not found when saving CSS: {css_url}")
                    logging.info(f"Downloaded CSS: {css_url}")
                except Exception as e:
                    logging.warning(f"Error downloading CSS {css_url}: {str(e)}")
            
            # Download JavaScript assets
            for js in soup.find_all('script', src=True):
                js_url = urljoin(url, js['src'])
                try:
                    js_resp = requests.get(js_url, headers=headers, timeout=5)
                    js_resp.raise_for_status()
                    js_dir = os.path.join(asset_path, 'js')
                    create_directory(js_dir)
                    js_filename = os.path.basename(urlparse(js_url).path)
                    js_path = os.path.join(js_dir, js_filename)
                    try:
                        with open(js_path, 'w', encoding='utf-8') as f:
                            f.write(js_resp.text)
                    except FileNotFoundError:
                        logging.error(f"File not found when saving JS: {js_url}")
                    logging.info(f"Downloaded JS: {js_url}")
                except Exception as e:
                    logging.warning(f"Error downloading JS {js_url}: {str(e)}")
            
            # Download image assets
            for img in soup.find_all('img', src=True):
                img_url = urljoin(url, img['src'])
                try:
                    img_resp = requests.get(img_url, headers=headers, timeout=5, stream=True)
                    img_resp.raise_for_status()
                    img_dir = os.path.join(asset_path, 'images')
                    create_directory(img_dir)
                    img_name = os.path.basename(urlparse(img_url).path)
                    if not img_name:
                        img_name = "image.jpg"
                    img_path = os.path.join(img_dir, img_name)
                    try:
                        with open(img_path, 'wb') as f:
                            for chunk in img_resp.iter_content(1024):
                                f.write(chunk)
                    except FileNotFoundError:
                        logging.error(f"File not found when saving image: {img_url}")
                    logging.info(f"Downloaded image: {img_url}")
                except Exception as e:
                    logging.warning(f"Error downloading image {img_url}: {str(e)}")
            
            # Find all internal links and queue them for crawling
            for link in soup.find_all('a', href=True):
                full_url = urljoin(start_url, link['href'])
                parsed_link = urlparse(full_url)
                if parsed_link.netloc == urlparse(start_url).netloc:
                    if full_url not in visited:
                        to_visit.append((full_url, depth + 1))
                        logging.info(f"Found link: {full_url}")
                        
        except requests.exceptions.RequestException as e:
            logging.error(f"Error crawling {url}: {str(e)}")
            if isinstance(e, requests.exceptions.Timeout):
                logging.warning(f"Timeout occurred while crawling {url}. Retrying...")
                time.sleep(5)  # Wait 5 seconds before retrying
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
            else:
                continue

def main():
    parser = argparse.ArgumentParser(description='Web Crawler for migration')
    parser.add_argument('--domain', type=str, required=True, choices=['tdr_bio', 'danakosha'],
                        help='Domain to crawl (tdr_bio or danakosha)')
    parser.add_argument('--max_depth', type=int, default=2, help='Maximum crawl depth')
    args = parser.parse_args()
    
    domain_config = DOMAIN_CONFIG.get(args.domain)
    if not domain_config:
        logging.error("Invalid domain specified")
        return
        
    logging.info(f"Starting crawl for: {args.domain} with max depth {args.max_depth}")
    crawl_domain(domain_config, args.max_depth)
    logging.info("Crawl completed successfully")

if __name__ == "__main__":
    main()