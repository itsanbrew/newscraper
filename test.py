from newsplease import NewsPlease

url = 'https://www.bbc.com/news/articles/c4gkm0243wzo'
article = NewsPlease.from_url(url)

if article:
    print("=== CORE ARTICLE DATA ===")
    print(f"Title: {article.title}")
    print(f"Description: {article.description}")
    print(f"Authors: {article.authors}")
    print(f"Publication Date: {article.date_publish}")
    print(f"Language: {article.language}")
    print(f"Source Domain: {article.source_domain}")
    print(f"URL: {article.url}")
    print(f"Image URL: {article.image_url}")
    print(f"Download Date: {article.date_download}")
    print(f"Modify Date: {article.date_modify}")
    print(f"Filename: {article.filename}")
    print(f"Local Path: {article.localpath}")
    print("\n=== MAIN TEXT (first 200 chars) ===")
    print(f"{article.maintext[:200]}..." if article.maintext else "No main text available")
else:
    print("Failed to extract article data")