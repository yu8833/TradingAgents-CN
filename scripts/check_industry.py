
from pymongo import MongoClient

client = MongoClient('mongodb://admin:tradingagents123@mongodb:27017/')
db = client['tradingagentscn']
collection = db['stock_basic_info']

# 检查有多少 akshare 股票中有多少股票的 industry 字段
total = collection.count_documents({'source': 'akshare'})
has_industry = collection.count_documents({
    'source': 'akshare',
    'industry': {'$exists': True, '$ne': None, '$ne': '', '$ne': '未知'}
})
unknown_industry = collection.count_documents({
    'source': 'akshare',
    '$or': [
        {'industry': {'$exists': False}},
        {'industry': None},
        {'industry': ''},
        {'industry': '未知'}
    ]
})

print(f'akshare 总股票数: {total}')
print(f'有 industry 字段且非空: {has_industry}')
print(f'industry 为未知/空: {unknown_industry}')

# 检查 industry 的去重列表
distinct_industries = sorted(collection.distinct('industry', {'source': 'akshare'}))
print(f'去重的 industry 列表: {distinct_industries[:30]}')

client.close()
