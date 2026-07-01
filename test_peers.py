import requests
import re
import json

headers = {
    'Referer': 'https://finance.sina.com.cn/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 先获取行业列表，找到正确的行业代码
url = 'https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php'
r = requests.get(url, headers=headers, timeout=10)
match = re.search(r'= ({.*?});', r.text, re.DOTALL)
if match:
    industry_data = json.loads(match.group(1))
    industries = []
    for k, v in industry_data.items():
        parts = v.split(',')
        industries.append({
            'code': k,
            'name': parts[1],
            'count': parts[2],
        })
    
    # 找军工相关
    print("=== 军工相关行业 ===")
    for ind in industries:
        if '军' in ind['name'] or '航' in ind['name']:
            print(f"  {ind['code']}: {ind['name']} ({ind['count']}只)")
    
    # 测试行业成分股 - 试几种格式
    test_codes = ['new_jgcy', 'new_hkjg', 'new_gfjg']
    print()
    print("=== 测试行业成分股接口 ===")
    for tc in test_codes:
        url2 = f'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=5&sort=changepercent&asc=0&node={tc}'
        r2 = requests.get(url2, headers=headers, timeout=10)
        print(f"{tc}: status={r2.status_code}, len={len(r2.text)}, content={r2.text[:200]}")
        print()
