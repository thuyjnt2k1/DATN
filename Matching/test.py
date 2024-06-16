import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
import pandas as pd
from namematcher import NameMatcher

df_author = pd.read_csv('new_author.csv', index_col=0)
df_author.set_index('ner_id')
df_nodes = pd.read_csv('new_node.csv', index_col=0)
df_nodes.set_index('id')
df_paper = pd.read_csv('new_paper.csv', index_col=0)
print(df_paper.index)
df_paper.set_index('doi')
df_links = pd.read_csv('new_link.csv', index_col=0)

name_matcher = NameMatcher()
# score = name_matcher.match_names('C. I. Ezeife', 'Christiana Ijeoma Ezeife')
# print(score) 

# Danh sách các tác giả (ví dụ)

def get_neighbor(node_id):
    neighbor_rows = df_links[(df_links['from'] == node_id) | (df_links['to'] == node_id)]
    neighbor_nodes = pd.unique(neighbor_rows[['from', 'to']].values.ravel())
    neighbor_nodes = [node for node in neighbor_nodes if node != node_id]
    return neighbor_nodes

def caculate_neighbor_sim(node1, node2):
    neighbor_1 = get_neighbor(node1['ner_id'])
    neighbor_2 = get_neighbor(node2['ner_id'])
    intersection = len(set(neighbor_1).intersection(set(neighbor_2)))
    result = intersection / len(neighbor_1) if intersection / len(neighbor_1) > intersection / len(neighbor_2) else intersection / len(neighbor_2)
    return result

def caculate_distance(node1, node2):
    name_sim = name_matcher.match_names(node1['name'], node2['name'])
    affiliation_sim = 0
    for node1_affiliation in node1['affiliation'].split(';'):
        for node2_affiliation in node2['affiliation'].split(';'):
            if(node1_affiliation == node2_affiliation):
                affiliation_sim = 1
    return 0.8 * name_sim + 0.2 * affiliation_sim

def match_paper():
    for index, node in df_paper.iterrows():
        print(index)

def custom_distance(df):
    # Tạo một ma trận khoảng cách tùy chỉnh
    distance_matrix = pd.DataFrame(index=df['ner_id'], columns=df['ner_id'])
    print(distance_matrix)

    for i in df['ner_id']:
        for j in df['ner_id']:
            # Tính khoảng cách dựa trên các đặc trưng mong muốn, ví dụ: tên, ORCID, email, liên kết
            distance = 1 - name_matcher.match_names(df.loc[df['ner_id'] == i, 'name'].values[0], df.loc[df['ner_id'] == j, 'name'].values[0])
            distance_matrix.loc[i, j] = distance
    
    return distance_matrix

# # Tính ma trận khoảng cách tùy chỉnh
# distance_matrix = custom_distance(df_author)
# print(distance_matrix)
# Z = linkage(distance_matrix, method='ward')
# print()
# # Chọn ngưỡng và phân cụm
# threshold = 0.1
# cluster_ids = fcluster(Z, threshold, criterion='distance')

# print("Phân cụm các tác giả:")
# for i, author in df_author.iterrows():
#     print(f"{author['name']} - Cụm {cluster_ids[i]}")
# print(df_author.index)
# print(df_author.loc[df_author['ner_id'] == 2])
# print(caculate_neighbor_sim(df_author.iloc[4], df_author.iloc[6]))

match_paper()