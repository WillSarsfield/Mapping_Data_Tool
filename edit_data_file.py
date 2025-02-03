import pandas as pd

dta = pd.read_csv('examples/ITL3_scorecards_data_file.csv', index_col=0)

skip = ['itlname','par','year','Taxonomy relative to the UK','Taxonomy relative to ITL1']
dta = dta.ffill()
dta = dta.loc[dta['year'] == 2022]

dta = dta.drop(columns=skip)

dta.to_csv('examples/ITL3_scorecards_data_file_modified.csv')