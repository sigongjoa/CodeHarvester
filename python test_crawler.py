from github_crawler import GithubCrawler
import json

def test_wanted_crawler():
    print("🔍 WantedImprovedCrawler 테스트 시작")

    test_url = "https://www.wanted.co.kr/search?query=python"
    crawler = GithubCrawler()
    results = crawler.crawl(test_url, max_jobs=1)

    assert isinstance(results, list), "결과는 리스트여야 합니다"
    assert len(results) > 0, "결과 리스트가 비어 있습니다"

    job = results[0]

    # 필수 필드 검증
    required_fields = ["company_name", "title", "description", "deadline", "experience", "location", "url", "crawled_at"]
    for field in required_fields:
        assert field in job, f"필드 누락: {field}"
        assert job[field], f"필드 값이 비어 있음: {field}"

    print("✅ 테스트 통과!")
    print(json.dumps(job, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_wanted_crawler()
