import requests
import re
import json

headers = {
    'Referer': 'https://finance.sina.com.cn/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 获取行业列表
url = 'https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php'
r = requests.get(url, headers=headers, timeout=10)
data_str = r.text

# 解析
match = re.search(r'= ({.*?});', data_str, re.DOTALL)
if match:
    industry_data = json.loads(match.group(1))
    print('行业总数:', len(industry_data))
    for k, v in industry_data.items():
        parts = v.split(',')
        name = parts[1]
        if '军' in name or '航' in name or '国防' in name or '兵器' in name:
            print(f'  {k}: {name}, 成分股数: {parts[2]}, 领涨股: {parts[-1]}({parts[-4]})')

print()
print('=== 测试行业成分股接口 ===')
test_code = 'new_jgcy'
url2 = f'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=10&sort=changepercent&asc=0&node={test_code}'
try:
    r2 = requests.get(url2, headers=headers, timeout=10)
    print('状态码:', r2.status_code)
    print('内容前800字:', r2.text[:800])
except Exception as e:
    print('失败:', e)
