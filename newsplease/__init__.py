import concurrent.futures as cf
import datetime
import os
import sys
import urllib
import requests
from urllib.parse import urlparse

from bs4.dammit import EncodingDetector
from six.moves import urllib

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from newsplease.NewsArticle import NewsArticle


class EmptyResponseError(ValueError):
    pass


class NewsPlease:
    """
    Access news-please functionality via this interface
    """

    @staticmethod
    def from_warc(warc_record, decode_errors="replace", fetch_images=True):
        """
        Extracts relevant information from a WARC record. This function does not invoke scrapy but only uses the article
        extractor.
        :return:
        """
        raw_stream = warc_record.raw_stream.read()
        encoding = None
        try:
            encoding = (
                warc_record.http_headers.get_header("Content-Type")
                .split(";")[1]
                .split("=")[1]
            )
        except:
            pass
        if not encoding:
            encoding = EncodingDetector.find_declared_encoding(raw_stream, is_html=True)
        if not encoding:
            # assume utf-8
            encoding = "utf-8"

        try:
            html = raw_stream.decode(encoding, errors=decode_errors)
        except LookupError:
            # non-existent encoding: fallback to utf-9
            html = raw_stream.decode("utf-8", errors=decode_errors)
        if not html:
            raise EmptyResponseError()
        url = warc_record.rec_headers.get_header("WARC-Target-URI")
        download_date = warc_record.rec_headers.get_header("WARC-Date")
        article = NewsPlease.from_html(
            html, url=url, download_date=download_date, fetch_images=fetch_images
        )
        return article

    @staticmethod
    def from_html(html, url=None, download_date=None, fetch_images=True):
        """
        Simplified HTML extraction using newspaper4k.
        """
        if bool(html) is False:
            return None

        try:
            from newspaper import Article
            import re
            
            # Create article object
            article = Article(url)
            article.set_html(html)
            article.parse()
            
            # Extract domain from URL
            domain = ""
            if url:
                parsed = urlparse(url)
                domain = parsed.netloc
            
            # Create NewsArticle object
            news_article = NewsArticle()
            news_article.url = url or ""
            news_article.title = article.title or ""
            news_article.text = article.text or ""
            news_article.description = article.meta_description or ""
            news_article.author = ", ".join(article.authors) if article.authors else ""
            news_article.date_publish = article.publish_date.isoformat() if article.publish_date else ""
            news_article.source_domain = domain
            news_article.language = article.meta_lang or ""
            
            return news_article
            
        except Exception as e:
            print(f"Error extracting article: {e}")
            return None

    @staticmethod
    def from_url(url, request_args=None, fetch_images=True):
        """
        Crawls the article from the url and extracts relevant information.
        """
        try:
            from newspaper import Article
            
            # Create article object and download
            article = Article(url)
            article.download()
            article.parse()
            
            # Extract domain from URL
            domain = ""
            if url:
                parsed = urlparse(url)
                domain = parsed.netloc
            
            # Create NewsArticle object
            news_article = NewsArticle()
            news_article.url = url
            news_article.title = article.title or ""
            news_article.text = article.text or ""
            news_article.description = article.meta_description or ""
            news_article.authors = article.authors if article.authors else []
            news_article.date_publish = article.publish_date.isoformat() if article.publish_date else ""
            news_article.source_domain = domain
            news_article.language = article.meta_lang or ""
            
            return news_article
            
        except Exception as e:
            print(f"Error fetching article from {url}: {e}")
            return None

    @staticmethod
    def from_urls(urls, request_args=None, fetch_images=True):
        """
        Crawls articles from the urls and extracts relevant information.
        """
        results = {}
        
        for url in urls:
            article = NewsPlease.from_url(url, request_args, fetch_images)
            results[url] = article
            
        return results

    @staticmethod
    def from_file(path):
        """
        Crawls articles from the urls and extracts relevant information.
        :param path: path to file containing urls (each line contains one URL)
        :return: A dict containing given URLs as keys, and extracted information as corresponding values.
        """
        with open(path) as f:
            content = f.readlines()
        content = [x.strip() for x in content]
        urls = list(filter(None, content))

        return NewsPlease.from_urls(urls)
