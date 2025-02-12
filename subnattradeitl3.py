import pandas as pd

goodsitl3 = pd.read_excel('subnationaltradeingoods2022.xlsx', sheet_name='Table 5 ITL3 Country', skiprows=[0,1,2,3,4])[['ITL code', 'Direction of trade', 'EU', 'Non-EU']]

itlmapping = pd.read_csv('src/itlmapping.csv')

itl3 = list(itlmapping['itl3'].drop_duplicates())

goodsitl3 = goodsitl3.loc[goodsitl3['ITL code'].isin(itl3)]
goodsitl3 = goodsitl3.loc[goodsitl3['Direction of trade'] == 'Balance']
goodsitl3 = goodsitl3.drop(columns='Direction of trade')

goodsitl3.columns = ['itl', 'EU trade balance in goods (£ millions)', 'Non-EU trade balance in goods (£ millions)']

# Services

servicesitl3 = pd.read_excel('subnationaltradeinservices2022.xlsx', sheet_name='Table 5 ITL3 Country', skiprows=[0,1,2,3,4])[['ITL code', 'Direction of trade', 'EU', 'Non-EU']]

servicesitl3 = servicesitl3.loc[servicesitl3['ITL code'].isin(itl3)]
servicesitl3 = servicesitl3.loc[servicesitl3['Direction of trade'] == 'Balance']
servicesitl3 = servicesitl3.drop(columns='Direction of trade')

servicesitl3.columns = ['itl', 'EU trade balance in services (£ millions)', 'Non-EU trade balance in services (£ millions)']

trade_itl3 = pd.concat([goodsitl3.set_index('itl'), servicesitl3.set_index('itl')], axis=1)

trade_itl3.to_csv('examples/ITL3_tradebalance.csv')
print(trade_itl3)