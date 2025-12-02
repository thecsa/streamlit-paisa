import modules.market_data as md

print("Testing TEFAS Data (TCD)...")
price = md.get_tefas_data("TCD")
print(f"TCD Price: {price}")

print("\nTesting Yahoo Finance (BTC-USD)...")
btc = md.get_market_price("BTC-USD")
print(f"BTC Price: {btc}")

print("\nTesting USD/TRY Rate...")
usd = md.get_usd_try_rate()
print(f"USD/TRY: {usd}")

if price and btc and usd:
    print("\nSUCCESS: All data sources are working.")
else:
    print("\nFAILURE: Some data sources failed.")
