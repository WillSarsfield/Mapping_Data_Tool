import pandas as pd

itlmapping = pd.read_csv('src/itlmapping.csv')

excluded_itl1 = ["TLN", "TLM", "TLL"]
remaining_itl1 = itlmapping[~itlmapping['itl1'].isin(excluded_itl1)]['itl1'].unique().tolist()
print(remaining_itl1)