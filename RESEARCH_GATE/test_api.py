# import pandas as pd
# from sklearn.cluster import AgglomerativeClustering
# from sklearn.metrics.pairwise import pairwise_distances
# import numpy as np

# # Load the dataset
# df = pd.read_csv('after_node.csv')

# # Define the Jaro-Winkler distance function
# from jarowinkler import jarowinkler_similarity

# def jaro_winkler_distance(s1, s2):
#     return jarowinkler_similarity(s1, s2)
# print(jaro_winkler_distance('hello', 'halloZ'))
# # Perform hierarchical clustering with Jaro-Winkler distance
# X = df.loc[df['type'] == 2, 'name'].tolist()
# print(X)
# uniques = np.unique(X)

# distance_matrix = []
# for i, name1 in enumerate(X):
#     row = []
#     for j, name2 in enumerate(X):
#         row.append(jaro_winkler_distance(name1, name2))
#     distance_matrix.append(row)
# threshold = 0.2  # Set the custom distance threshold
# clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=threshold)
# labels = clustering.fit_predict(distance_matrix)
# for i, value in enumerate(labels):
#     print(f"\n{X[i]}: {value}")
# # Print the cluster labels
# print("Cluster labels:", labels)

# # Visualize the clustering results
# import matplotlib.pyplot as plt

# plt.figure(figsize=(8, 6))
# plt.scatter(range(len(X)), [0] * len(X), c=labels, cmap='viridis')
# plt.title(f'Hierarchical Clustering with Jaro-Winkler Distance (Threshold: {threshold:.2f})')
# plt.xlabel('Data Index')
# plt.ylabel('Arbitrary Y-axis')
# plt.show()

from opencage.geocoder import OpenCageGeocode
import requests
import json

api_key = "5bf38ed7c2484256b6b739055b532a37"
geocoder = OpenCageGeocode(api_key)
result = geocoder.geocode("University of Bari Aldo Moro Bari, Italy")
print(result[0]["formatted"])

# def find_place(query):    
#     # Define the API endpoint
#     url = 'https://places.googleapis.com/v1/places:searchText'

#     # Define the headers
#     headers = {
#         'Content-Type': 'application/json',
#         'X-Goog-Api-Key': 'AIzaSyA_0YrEuHRV1BwqKASWEleMR6QdcgovdkI',  # Replace 'API_KEY' with your actual Google Places API key
#         # 'X-Goog-FieldMask': 'places.id'
#     }

#     # Define the data payload for the POST request
#     data = {
#         'textQuery': query
#     }

#     # Make the POST request
#     response = requests.post(url, headers=headers, json=data)

#     # Check if the request was successful
#     if response.status_code == 200:
#         # Process the response
#         print(response.json())
#     else:
#         print(f"Error: {response.status_code}, {response.text}")
#     return json.loads(response.text)

# print(find_place('University of Calabria  Rende, Italy'))