import csv
import pandas as pd
from opencage.geocoder import OpenCageGeocode

api_key = "5c39d7a78a4b48e0ababc3d0cfb1d3f3"
geocoder = OpenCageGeocode(api_key)

df_affiliation = pd.read_csv('affiliation.csv')
print(df_affiliation)
df_affiliation = df_affiliation.drop_duplicates(subset='affiliation')
df_affiliation.set_index('affiliation', inplace=True)
print(df_affiliation)
# df_affiliation = pd.DataFrame(columns=['affiliation', 'result'])
# df_affiliation.set_index('affiliation')
df_acm_author = pd.read_csv('../IEEE/after_author1.csv', index_col=0)

def getAffiliation(affiliation):
	global df_affiliation
	result = ''
	formatted_affiliation = affiliation.strip()
	formatted_affiliation = ' '.join(formatted_affiliation.strip().split())
	try:
		result = df_affiliation.loc[formatted_affiliation,'result']
		print('\nda co')
	except KeyError:
		print('\nchua co', formatted_affiliation)
		getGeocode = geocoder.geocode(formatted_affiliation)
		if(len(getGeocode) == 0):
			result = formatted_affiliation
			print('\n============== tim dươc: ', result)
		else:
			result = getGeocode[0]['formatted']
			print('\n============== giu nguyen: ', result)
		df_affiliation.loc[formatted_affiliation] = result
	return result

try: 
	for index, author in df_acm_author.iterrows():
		print(author)
		if isinstance(author['affiliation'], str):
			results = []
			for affiliation in author['affiliation'].split('; '):
				results.append(getAffiliation(affiliation))
			print(results)
			author['affiliation'] = ';'.join(results)
			print(author['affiliation'])
	print('\nFinish all')
except Exception as e:
	df_affiliation.to_csv('affiliation.csv')
	print('\nerrror api')
	print(str(e))
finally:
	df_affiliation.to_csv('affiliation.csv')
	print('\ndone')
	print(df_affiliation)
	
df_affiliation.to_csv('affiliation.csv')
print(df_affiliation)