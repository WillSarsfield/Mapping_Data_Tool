import pandas as pd

lamapping = pd.read_csv('lamapping.csv')

lamappingcodes = pd.concat([lamapping['laold'], lamapping['la']]).drop_duplicates()
lamappingnames = pd.concat([lamapping['laoldname'], lamapping['laname']]).drop_duplicates()
lamapping = pd.concat([lamappingcodes, lamappingnames], axis = 1)
lamapping.columns = ['la', 'laname']
lamapping = lamapping.set_index('la')

mcamapping = pd.read_csv('Local_Authority_District_to_Combined_Authority_(May_2024)_Lookup_in_EN.csv').rename(columns={'LAD24CD': 'la'})
result = pd.merge(
    lamapping,  # All local authorities
    mcamapping,  # Mapping data
    on="la",  # Join on region_code
    how="left"  # Keep all local authorities
)[['la', 'laname', 'CAUTH24CD', 'CAUTH24NM']]
result.columns = ['la', 'laname', 'mca', 'mcaname']

result.set_index('la').to_csv('mcamapping.csv')