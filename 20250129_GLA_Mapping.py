import pandas as pd

# Load MCA mapping
MCA_mapping = pd.read_csv('src/mcamapping.csv')
MCA_mapping.loc[MCA_mapping['la'].str.startswith('E09', na=False), ['mca', 'mcaname']] = ['E61000001', 'Greater London']
MCA_mapping.to_csv('src/mcamapping.csv', index=False)
