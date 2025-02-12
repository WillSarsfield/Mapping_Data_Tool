import pandas as pd

goodsitl1 = pd.read_excel('subnationaltradeingoods2022.xlsx', sheet_name='Table 2 ITL1 Country', skiprows=[0,1,2,3,4])[['ITL code', 'Direction of trade', 'Partner Country', 'All industries']]

itlmapping = pd.read_csv('src/itlmapping.csv')

itl1 = list(itlmapping['itl1'].drop_duplicates())

goodsitl1 = goodsitl1.loc[goodsitl1['ITL code'].isin(itl1)]
goodsitl1 = goodsitl1.loc[goodsitl1['Direction of trade'] == 'Balance']
goodsitl1 = goodsitl1.loc[goodsitl1['Partner Country'].isin(['EU', 'Non-EU', 'United States inc Puerto Rico'])]
goodsitl1 = goodsitl1.drop(columns='Direction of trade')

goodsitl1 = goodsitl1.pivot_table(
    index=['ITL code'],  # Keep these as row identifiers
    columns='Partner Country',                 # Make these into columns
    values='All industries',                   # Fill values from this column
    aggfunc='sum'                              # In case of duplicates, sum the values
).reset_index()
goodsitl1.columns.name = None

goodsitl1.columns = ['itl', 'EU trade balance in goods (£ millions)', 'Non-EU trade balance in goods (£ millions)', 'US trade balance in goods (£ millions)']

# Services

servicesitl1 = pd.read_excel('subnationaltradeinservices2022.xlsx', sheet_name='Table 2 ITL1 Industry Country', skiprows=[0,1,2,3,4])[['ITL code', 'Direction of trade', 'Partner Country', 'All industries']]

servicesitl1 = servicesitl1.loc[servicesitl1['ITL code'].isin(itl1)]
servicesitl1 = servicesitl1.loc[servicesitl1['Direction of trade'] == 'Balance']
servicesitl1 = servicesitl1.loc[servicesitl1['Partner Country'].isin(['EU', 'Non-EU', 'United States inc Puerto Rico'])]
servicesitl1 = servicesitl1.drop(columns='Direction of trade')

servicesitl1 = servicesitl1.pivot_table(
    index=['ITL code'],  # Keep these as row identifiers
    columns='Partner Country',                 # Make these into columns
    values='All industries',                   # Fill values from this column
    aggfunc='sum'                              # In case of duplicates, sum the values
).reset_index()
servicesitl1.columns.name = None

servicesitl1.columns = ['itl', 'EU trade balance in services (£ millions)', 'Non-EU trade balance in services (£ millions)', 'US trade balance in services (£ millions)']

trade_itl1 = pd.concat([goodsitl1.set_index('itl'), servicesitl1.set_index('itl')], axis=1)

trade_itl1.to_csv('examples/ITL1_tradebalance.csv')
print(trade_itl1)