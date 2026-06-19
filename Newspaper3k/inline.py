import newspaper
from newspaper import Config

def fetch_top_articles(site_url, site_name, limit=3):
    # 設定の構築（User-Agentの設定と日本語の指定）
    config = Config()
    config.browser_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    config.language = 'ja'
    
    # サイトのビルド（memoize_articles=Falseでキャッシュを無効化）
    paper = newspaper.build(site_url, config=config, memoize_articles=False)
    
    print(f"\n{'='*20} {site_name} から記事を取得中 (計 {len(paper.articles)} 件発見) {'='*20}")
    
    count = 0
    for article in paper.articles:
        if count >= limit:
            break
        
        try:
            article.download()
            article.parse()
            
            print(f"\n[記事 {count + 1}]")
            print(f"タイトル: {article.title}")
            print(f"URL: {article.url}")
            print(f"内容:\n{article.text}\n")
            print("-" * 50)
            count += 1
        except Exception as e:
            print(f"エラーが発生しました ({article.url}): {e}")

if __name__ == "__main__":
    fetch_top_articles("https://www.itmedia.co.jp/", "ITmedia")
    fetch_top_articles("https://thebridge.jp/", "THE BRIDGE")
    fetch_top_articles("https://www.bloomberg.co.jp/", "Bloomberg")
