import pandas as pd

goodsitl2 = pd.read_excel('subnationaltradeingoods2022.xlsx', sheet_name='Table 4 ITL2 Country', skiprows=[0,1,2,3,4])[['ITL code', 'Direction of trade', 'Partner Country', 'All industries']]

itlmapping = pd.read_csv('src/itlmapping.csv')

itl2 = list(itlmapping['itl2'].drop_duplicates())

goodsitl2 = goodsitl2.loc[goodsitl2['ITL code'].isin(itl2)]
goodsitl2 = goodsitl2.loc[goodsitl2['Direction of trade'] == 'Balance']
goodsitl2 = goodsitl2.loc[goodsitl2['Partner Country'].isin(['EU', 'Non-EU', 'United States inc Puerto Rico'])]
goodsitl2 = goodsitl2.drop(columns='Direction of trade')

goodsitl2 = goodsitl2.pivot_table(
    index=['ITL code'],  # Keep these as row identifiers
    columns='Partner Country',                 # Make these into columns
    values='All industries',                   # Fill values from this column
    aggfunc='sum'                              # In case of duplicates, sum the values
).reset_index()
goodsitl2.columns.name = None

goodsitl2.columns = ['itl', 'EU trade balance in goods (£ millions)', 'Non-EU trade balance in goods (£ millions)', 'US trade balance in goods (£ millions)']

# Services

servicesitl2 = pd.read_excel('subnationaltradeinservices2022.xlsx', sheet_name='Table 4 ITL2 Industry Country', skiprows=[0,1,2,3,4])[['ITL code', 'Direction of trade', 'Partner Country', 'All industries (Exc. Travel)']]

servicesitl2 = servicesitl2.loc[servicesitl2['ITL code'].isin(itl2)]
servicesitl2 = servicesitl2.loc[servicesitl2['Direction of trade'] == 'Balance']
servicesitl2 = servicesitl2.loc[servicesitl2['Partner Country'].isin(['EU', 'Non-EU', 'United States inc Puerto Rico'])]
servicesitl2 = servicesitl2.drop(columns='Direction of trade')

servicesitl2 = servicesitl2.pivot_table(
    index=['ITL code'],  # Keep these as row identifiers
    columns='Partner Country',                 # Make these into columns
    values='All industries (Exc. Travel)',                   # Fill values from this column
    aggfunc='sum'                              # In case of duplicates, sum the values
).reset_index()
servicesitl2.columns.name = None

servicesitl2.columns = ['itl', 'EU trade balance in services (£ millions)', 'Non-EU trade balance in services (£ millions)', 'US trade balance in services (£ millions)']

trade_itl2 = pd.concat([goodsitl2.set_index('itl'), servicesitl2.set_index('itl')], axis=1)

trade_itl2.to_csv('examples/ITL2_tradebalance.csv')
print(trade_itl2)