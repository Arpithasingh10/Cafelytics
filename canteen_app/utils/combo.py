from itertools import combinations

def _is_nonveg(type_str):
    t = type_str.lower().replace('-', '').replace(' ', '')
    return t in ['nonveg', 'nonvegetarian']

def generate_smart_combos(df, budget, prefer_type='All', meal_type=None,
                          max_items=4, candidate_top=25, diversify=True):
    df2 = df.copy()
    df2['Type'] = df2['Type'].astype(str).fillna('')
    df2['Availability'] = df2.get('Availability', '').astype(str).fillna('')
    # Accept meal_type as Breakfast, Lunch, Dinner, or None
    if meal_type and str(meal_type).strip().lower() not in ['none', '', 'all']:
        df2 = df2[df2['Availability'].str.contains(str(meal_type), case=False, na=False)]
        if df2.empty:
            return []

    df2 = df2[df2['Price'].astype(float) <= float(budget)]
    if df2.empty:
        return []

    if 'utility' not in df2.columns:
        df2 = compute_utilities(df2)

    df2 = df2.sort_values('utility', ascending=False).head(candidate_top)
    rows = df2.to_dict('records')

    combos = []
    for r in range(1, max_items+1):
        for comb in combinations(rows, r):
            total_price = sum(float(c['Price']) for c in comb)
            if total_price <= budget:
                n_nonveg = sum(1 for c in comb if _is_nonveg(c.get('Type')))
                n_veg = r - n_nonveg
                items_list = [{'ItemID': c['ItemID'], 'ItemName': c['ItemName'],
                               'Price': float(c['Price']), 'Type': c.get('Type')}
                              for c in comb]
                combos.append({
                    'items': items_list,
                    'total_price': round(total_price, 2),
                    'total_utility': round(sum(float(c.get('utility', 0.0)) for c in comb), 4),
                    'n_items': r, 'n_nonveg': n_nonveg, 'n_veg': n_veg
                })

    if not combos:
        return []

    pref_raw = str(prefer_type or 'All').strip().lower().replace('-', '').replace(' ', '')
    if pref_raw in ('veg', 'vegetarian'):
        pref = 'veg'
    elif pref_raw in ('nonveg', 'nonvegetarian', 'nonveget'):
        pref = 'nonveg'
    else:
        pref = 'all'

    if pref == 'veg':
        combos = [c for c in combos if c['n_nonveg'] == 0]
    elif pref == 'nonveg':
        combos = [c for c in combos if c['n_veg'] == 0]
    else:
        pass

    if not combos:
        return []

    combos = sorted(combos, key=lambda x: (-x['total_utility'], x['total_price']))

    if diversify and pref == 'all':
        pure_veg = [c for c in combos if c['n_nonveg'] == 0]
        pure_nonveg = [c for c in combos if c['n_nonveg'] >= 1 and c['n_veg'] == 0]
        mixed = [c for c in combos if c['n_nonveg'] >= 1 and c['n_veg'] >= 1]

        out = []
        out.extend(pure_veg[:3])
        out.extend(pure_nonveg[:3])
        out.extend(mixed[:4])

        seen = set()
        final = []
        for c in out:
            key = tuple(sorted([it['ItemID'] for it in c['items']]))
            if key not in seen:
                seen.add(key)
                final.append(c)

        for c in combos:
            key = tuple(sorted([it['ItemID'] for it in c['items']]))
            if key not in seen:
                final.append(c)
                seen.add(key)
            if len(final) >= 10:
                break
        return final[:10]

    return combos[:10]
## Removed redundant import
## Removed unused imports

def compute_utilities(df):
    df = df.copy()
    # normalize preference
    minp, maxp = df['PreferenceScore'].min(), df['PreferenceScore'].max()
    df['pref_norm'] = (df['PreferenceScore'] - minp) / (maxp - minp + 1e-9)
    # price inverse
    min_pr, max_pr = df['Price'].min(), df['Price'].max()
    df['price_inv'] = 1 - (df['Price'] - min_pr) / (max_pr - min_pr + 1e-9)
    df['utility'] = 0.6 * df['pref_norm'] + 0.4 * df['price_inv']
    return df

def generate_combos_from_df(df, budget, prefer_type=None, max_items=4, candidate_top=15):
    df2 = df.copy()
    if prefer_type:
        df2 = df2[df2['Type'].str.contains(prefer_type, case=False, na=False)]
    df2 = df2[df2['Price'] <= budget]
    if df2.empty:
        return []
    df2 = df2.sort_values('utility', ascending=False).head(candidate_top)
    rows = df2.to_dict('records')
    combos=[]
    for r in range(1, max_items+1):
        for comb in combinations(rows, r):
            total = sum([c['Price'] for c in comb])
            if total <= budget:
                combos.append({
                    'items': [
                        {
                            'ItemID': c['ItemID'],
                            'ItemName': c['ItemName'],
                            'Price': c['Price'],
                            'utility': round(c.get('utility', 0), 4)
                        }
                        for c in comb
                    ],
                    'total_price': round(total,2),
                    'total_utility': round(sum([c['utility'] for c in comb]),4)
                })
    combos = sorted(combos, key=lambda x:(-x['total_utility'], x['total_price']))
    return combos
