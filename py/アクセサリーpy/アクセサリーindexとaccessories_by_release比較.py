import json

# ファイルを読み込み
with open('/storage/emulated/0/html/pkpk/data/accessories_by_release_new.json', 'r') as f:
    release_data = json.load(f)

with open('/storage/emulated/0/html/pkpk/images/accessories/index.json', 'r') as f:
    index_data = json.load(f)

# カテゴリとプレフィックスの定義
categories = {
    'icons': 'icons/',
    'backdrops': 'backdrops/',
    'covers': 'covers/',
    'card_sleeves': 'card_sleeves/',
    'playmats': 'playmats/',
    'coins': 'coins/'
}

# index側をカテゴリごとに分類
index_by_category = {cat: set() for cat in categories}
for item in index_data:
    for cat, prefix in categories.items():
        if item.startswith(prefix):
            index_by_category[cat].add(item)
            break

# カテゴリごとに比較
print('=== カテゴリ別 不足アイテム一覧 ===\n')

total_missing = 0
for cat, prefix in categories.items():
    release_items = set(release_data[cat])
    index_items = index_by_category[cat]
    
    missing = sorted(list(release_items - index_items))
    extra = sorted(list(index_items - release_items))
    
    if missing:
        print(f'📁 {cat} ({len(missing)}個 不足)')
        for item in missing:
            print(f'  - {item}')
        print()
        total_missing += len(missing)
    
    if extra:
        print(f'⚠️ {cat} (index側にだけある: {len(extra)}個)')
        for item in extra:
            print(f'  - {item}')
        print()

# 統計サマリー
print('=== 統計サマリー ===\n')
for cat, prefix in categories.items():
    release_count = len(release_data[cat])
    index_count = len(index_by_category[cat])
    missing_count = len(set(release_data[cat]) - index_by_category[cat])
    print(f'{cat:12} : release={release_count:3}, index={index_count:3}, 不足={missing_count:3}')

print(f'\n合計不足数: {total_missing}個')