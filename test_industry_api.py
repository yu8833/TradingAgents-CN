import akshare as ak
import pandas as pd

print("=== 测试能提供行业信息的接口 ===")

# 方法1: 上交所/深交所的股票列表
print("\n1. stock_info_sh_name_code")
try:
    df = ak.stock_info_sh_name_code(symbol="主板A股")
    print(f"  字段: {df.columns.tolist()[:10]}")
    print(f"  前3行: {df.head(3).to_string()}")
except Exception as e:
    print(f"  ❌ {type(e).__name__}: {str(e)[:80]}")

print("\n2. stock_info_sz_name_code")
try:
    df = ak.stock_info_sz_name_code(symbol="A股列表")
    print(f"  字段: {df.columns.tolist()[:10]}")
except Exception as e:
    print(f"  ❌ {type(e).__name__}: {str(e)[:80]}")

# 方法2: stock_zh_a_spot_em - 这个接口会返回所有A股的实时信息
print("\n3. stock_zh_a_spot_em (只取前10列)")
try:
    df = ak.stock_zh_a_spot_em()
    cols = df.columns.tolist()
    print(f"  总字段数: {len(cols)}")
    print(f"  字段: {cols}")
    # 找出与行业相关的字段
    industry_cols = [c for c in cols if '行业' in str(c) or '板块' in str(c)]
    if industry_cols:
        print(f"  ✅ 行业相关字段: {industry_cols}")
        for col in industry_cols:
            print(f"     {col} 示例: {df[col].head(5).tolist()}")
except Exception as e:
    print(f"  ❌ {type(e).__name__}: {str(e)[:80]}")

# 方法3: stock_board_industry_name_em - 行业列表
print("\n4. stock_board_industry_name_em")
try:
    df = ak.stock_board_industry_name_em()
    print(f"  字段: {df.columns.tolist()}")
    print(f"  前5个: {df.head(5).to_string()}")
except Exception as e:
    print(f"  ❌ {type(e).__name__}: {str(e)[:80]}")

# 方法4: stock_board_industry_cons_em - 行业成分股
print("\n5. stock_board_industry_cons_em(symbol='银行')")
try:
    df = ak.stock_board_industry_cons_em(symbol="银行")
    print(f"  字段: {df.columns.tolist()}")
    print(f"  前5行: {df.head(5).to_string()}")
except Exception as e:
    print(f"  ❌ {type(e).__name__}: {str(e)[:80]}")

print("\n=== 完成 ===")
