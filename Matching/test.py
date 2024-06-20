import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
import pandas as pd
from namematcher import NameMatcher
import time
from collections import defaultdict
from scipy.spatial.distance import pdist
import numpy as np
from sklearn.cluster import AgglomerativeClustering
import re

df_author = pd.read_csv('new_author_test.csv', index_col=0)
df_author.set_index('ner_id', inplace = True)
df_nodes = pd.read_csv('new_node_test.csv', index_col=0)
df_nodes.set_index('id', inplace = True)
df_paper = pd.read_csv('new_paper_test.csv', index_col=0)
df_paper.set_index('ner_id', inplace = True)
df_links = pd.read_csv('new_link_test.csv', index_col=0)

df_affiliation = pd.read_csv('affiliation.csv', index_col='affiliation')

name_matcher = NameMatcher()
score = name_matcher.match_names('C. I. Ezeife', 'Christiana Ijeoma Ezeife')
print(score) 

# Danh sách các tác giả (ví dụ)

def get_neighbor(node_id):
    neighbor_rows = df_links[(df_links['from'] == node_id) | (df_links['to'] == node_id)]
    neighbor_nodes = pd.unique(neighbor_rows[['from', 'to']].values.ravel())
    neighbor_nodes = [node for node in neighbor_nodes if node != node_id]
    return neighbor_nodes

def caculate_neighbor_sim(id1, id2):
    neighbor_1 = get_neighbor(id1)
    neighbor_2 = get_neighbor(id2)
    intersection = len(set(neighbor_1).intersection(set(neighbor_2)))
    result = intersection / len(neighbor_1) if intersection / len(neighbor_1) > intersection / len(neighbor_2) else intersection / len(neighbor_2)
    return result

def simple_string(string):
    return re.sub(r"[!\"#$%&()*+,\-/:;<=>?@\[\\\]^_`{|}~]", " ", string

def caculate_ahc_distance(id1, id2):
    node1 = df_author.loc[id1]
    node2 = df_author.loc[id2]
    name_sim = name_matcher.match_names(simple_string(node1['name']), simple_string(node2['name'])
    # print(node1['name'], node2['name'], name_sim)
    neighbor_sim = caculate_neighbor_sim(id1, id2)
    if(1 - 0.85 * name_sim - 0.15 * neighbor_sim < 0.1):
        print('\n*************', id1, id2, node1['name'], node2['name'], name_sim, neighbor_sim)
    return 1 - 0.85 * name_sim - 0.15 * neighbor_sim

# def match_paper():
#     for index1, node1 in df_paper.iterrows():
#         print(index)

def author_ahc_distance():
    # distance_matrix = [[caculate_ahc_distance(point1, point2) for point2 in df_author.index] for point1 in df_author.index]
    # distance_matrix = pd.DataFrame(index=df_author.index, columns=df_author.index)
    # distance_matrix = distance_matrix.astype('float64')
    n = len(df_author.index)
    distance_matrix = np.zeros((n, n))
    for i, id1 in enumerate(df_author.index):
        for j, id2 in enumerate(df_author.index):
            if(i > j):
                continue;
            if(i == j):
                distance_matrix[i, i] = 1
                continue;
            distance = caculate_ahc_distance(id1, id2)
            print(id1, id2, distance)
            distance_matrix[i, j] = distance
            distance_matrix[j, i] = distance
    print(distance_matrix)
    return distance_matrix
    # distances = pdist(distance_matrix, metric=caculate_ahc_distance)
    # print(distances)
    # return distances

def match_author_from_paper(paper_id):
    neighbors = get_neighbor(paper_id)
    neighbors_name = df_author.iloc[df_author.index.isin(neighbors), df_author.columns.get_loc('name')]
    print(neighbors, neighbors_name)
    matched_list = []
    for id1, name1 in neighbors_name.items():
        if id1 in matched_list:
            continue; 
        for id2, name2 in neighbors_name.items():
            if id2 in matched_list or id1 >= id2:
                continue;
            if name_matcher.match_names(simple_string(name1), simple_string(name2) > 0.85:
                matched_list.append(id1)
                matched_list.append(id2)
                match_author(id1, id2);
                continue;

def match_paper(id1, id2):
    global df_nodes, df_paper, df_links
    print('\nmatch paper', id1, id2)
    node1 = df_nodes.loc[id1]
    node2 = df_nodes.loc[id2]
    df_nodes.loc[id1, 'link'] = node1['link'] + '; ' + node2['link']
    df_nodes = df_nodes.drop(id2)

    paper1 = df_paper.loc[id1]
    paper2 = df_paper.loc[id2]
    df_paper.loc[id1, 'link'] = paper1['link'] + '; ' + paper2['link']
    df_paper = df_paper.drop(id2)

    df_links.loc[df_links['from'] == id2, 'from'] = id1
    df_links.loc[df_links['to'] == id2, 'to'] = id1

    match_author_from_paper(id1)

def match_author(id1, id2):
    global df_nodes, df_author, df_links
    print('\nmatch author', id1, id2, '\n')
    node1 = df_nodes.loc[id1]
    node2 = df_nodes.loc[id2]
    df_nodes.loc[id1, 'link'] = node1['link'] + '; ' + node2['link']
    df_nodes = df_nodes.drop(id2)

    author1 = df_author.loc[id1]
    author2 = df_author.loc[id2]
    if(author2['orcid']):
        df_author.loc[id1, 'orcid'] = author2['orcid']
    if(author2['email']):
        df_author.loc[id1, 'email'] = author2['email']
    affiliations = set(str(author1['affiliation']).split(';')).intersection(set(str(author2['affiliation']).split(';')))
    df_author.loc[id1, 'affiliation'] = '; '.join(affiliations)
    df_author.loc[id1, 'link'] = author1['link'] + '; ' + author2['link']
    df_author = df_author.drop(id2)
    df_links.loc[df_links['from'] == id2, 'from'] = id1
    df_links.loc[df_links['to'] == id2, 'to'] = id1

def paper_match_process():
    paper_block = defaultdict()
    for id, doi in zip(df_paper.index, df_paper['doi']):
        if(doi in paper_block):
            match_paper(paper_block[doi], id)
        else:
            paper_block[doi] = id

def get_author_block(id, name, author_block):
    for index, authors in author_block.items():
        for author_name in authors.values():
            if(name_matcher.match_names(simple_string(name), simple_string(author_name) > 0.85):
                return index
    return -1

def author_match_blocking(author_block):
    for id, name in zip(df_author.index, df_author['name']):
        block_id = get_author_block(id, name, author_block)
        if(block_id == -1):
            new_block = len(author_block)
            author_block.update({new_block: {}})
            author_block[new_block].update({id: name})
        else:
            author_block[block_id].update({id:name})
    return author_block

def getAffiliation(affiliation):
    global df_affiliation
    result = ''
    formatted_affiliation = affiliation.strip()
    formatted_affiliation = ' '.join(formatted_affiliation.strip().split())
    try:
        result = df_affiliation.loc[formatted_affiliation,'result']
        print('\nda co')
    except KeyError:
        print('\nchua co')
        getGeocode = geocoder.geocode(formatted_affiliation)
        if(len(getGeocode) == 0):
            result = formatted_affiliation
        else:
            result = getGeocode[0]['formatted']
        df_affiliation.loc[formatted_affiliation] = result
    return result

def caculate_affiliation_sim(author1, author2):
    if(not isinstance(author1['affiliation'], str) or not isinstance(author2['affiliation'], str)):
        print('\n==========================fuck', str(author1['affiliation']))
        return 0
    for author1_affiliation in str(author1['affiliation']).split(';'):
        for author2_affiliation in str(author2['affiliation']).split(';'):
            if(getAffiliation(author1_affiliation) == getAffiliation(author2_affiliation)):
                return 1

def caculate_author_matching_distance(id1, id2):
    print(id1, id2)
    author1 = df_author.loc[id1]
    author2 = df_author.loc[id2]
    if(isinstance(author1['email'], str) and author1['email'] == author2['email']):
        return 1
    if(isinstance(author1['orcid'], str) and author1['orcid'] == author2['orcid']):
        return 1
    affiliation_sim = caculate_affiliation_sim(author1, author2)
    if(affiliation_sim):
        return 1
    # if(not isinstance(author1['affiliation'], str) or not isinstance(author2['affiliation'], str)):
    #     print('\n==========================fuck', str(author1['affiliation']))
    #     return 0
    # for author1_affiliation in str(author1['affiliation']).split(';'):
    #     for author2_affiliation in str(author2['affiliation']).split(';'):
    #         if(author1_affiliation == author2_affiliation):
    #             return 1
    return 0

def author_match_matching(author_block):
    for authors in author_block.values():
        print(authors)
        matched_list = []
        for count1, id1 in enumerate(authors.keys()):
            if(id1 in matched_list):
                continue;
            for count2, id2 in enumerate(authors.keys()):
                if(count2 <= count1 or id2 in matched_list):
                    continue;
                if(caculate_author_matching_distance(id1, id2)):
                    matched_list.append(id1)
                    matched_list.append(id2)
                    match_author(id1, id2)
                    continue;   

def author_match_cluster():
    distance_matrix = author_ahc_distance()
    clustering = AgglomerativeClustering(n_clusters=None, affinity='precomputed', linkage='single', distance_threshold=0.1)
    cluster_ids = clustering.fit_predict(distance_matrix)

    # Z = linkage(distance_matrix, method='average')
    # threshold = 0.8
    # print(Z)
    # cluster_ids = fcluster(Z, t = threshold, criterion='distance')
    cluster_dict = dict(zip(df_author.index, cluster_ids))
    print(cluster_ids)
    print(cluster_dict)
    cluster_node = {}
    for id in df_author.index:
        cluster_id = cluster_dict[id]
        if(cluster_id in cluster_node):
            match_author(cluster_node[cluster_id], id)
        else:
            cluster_node.update({cluster_id : id})
    print(len(cluster_node), len(cluster_dict))

def author_match_process():
    author_block = defaultdict()
    author_block = author_match_blocking(author_block)
    author_match_matching(author_block)
    author_match_cluster()

# # Tính ma trận khoảng cách tùy chỉnh
# print(distance_matrix)
# Z = linkage(distance_matrix, method='ward')
# print()
# # Chọn ngưỡng và phân cụm


# print("Phân cụm các tác giả:")
# for i, author in df_author.iterrows():
#     print(f"{author['name']} - Cụm {cluster_ids[i]}")
# print(df_author.index)
# print(df_author.loc[df_author['ner_id'] == 2])
# print(caculate_neighbor_sim(df_author.iloc[4], df_author.iloc[6]))
# print(name_matcher.match_names('Theodoros media Kouzelis','T m. Kouzelis'))
# match_paper()
print(df_author)
paper_match_process()
author_match_process()
