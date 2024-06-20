import csv
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

# df_links = pd.read_csv('new_link.csv')
# df_queue = pd.read_csv('new_queue.csv', index_col='id')
# df_nodes = pd.read_csv('new_node.csv', index_col='id')
# df_author = pd.read_csv('new_author.csv', index_col='ner_id')
# # df_author = df_author.astype({'orcid': 'str', 'email': 'str', 'affiliation': 'str'})
# df_paper = pd.read_csv('new_paper.csv', index_col='ner_id')

df_links = pd.read_csv('after_link3.csv')
df_queue = pd.read_csv('after_queue3.csv', index_col='id')
df_nodes = pd.read_csv('after_node3.csv', index_col='id')
df_author = pd.read_csv('after_author3.csv', index_col='ner_id')
# df_author = df_author.astype({'orcid': 'str', 'email': 'str', 'affiliation': 'str'})
df_paper = pd.read_csv('after_paper3.csv', index_col='ner_id')

G = nx.Graph()
for index,node in df_nodes.iterrows():
  if node["type"] == 1:
    
    try:
      document = df_paper.loc[index]
      if(not document['doi']):
        print('==================fuck================\n')
      G.add_node(index, link = node["link"], type = node["type"], title = document["title"], doi = document["doi"])
    except KeyError:
      G.add_node(index, link = node["link"], type = node["type"])
    print("\ninsert node", index, "type ", node["type"])
  elif node["type"] == 2:
    try:
      author = df_author.loc[index]
      G.add_node(index, link = node["link"], type = node["type"], name = author["name"], orcid = author["orcid"] if isinstance(author["orcid"], str)  else '', affiliation = author['affiliation'] if isinstance(author['affiliation'], str) else '', email = author['email'] if isinstance(author['email'], str) else '')
    except KeyError:
      G.add_node(index, link = node["link"], type = node["type"])
    print("\ninsert node", index, "type ", node["type"])

grouped = df_queue.groupby(['type']).count()
# print(grouped)
for link in df_links.index:
  G.add_edge(int(df_links.iloc[link]['from']),int(df_links.iloc[link]['to']),weight=df_links.iloc[link]['count'])
  # print('\n', df_links.iloc[link]['from'], df_links.iloc[link]['to'])

# get modularity
communities = nx.community.louvain_communities(G)
modularity = nx.algorithms.community.modularity(G, communities)
print('\n====================modularity======================\n', modularity)

avg_clustering = nx.average_clustering(G)
print('\n====================Clustering Coefficient======================\n', nx.clustering(G),avg_clustering)

# # # Find the largest connected component
# connected_components = nx.connected_components(G)
# largest_component = max(connected_components, key=len)
# largest_subgraph = G.subgraph(largest_component)
# nx.write_gexf(largest_subgraph, 'subgraph.gexf')


# print(largest_component)
# # Create a subgraph of the largest connected component
degree_centrality = nx.degree_centrality(G)
sorted_nodes = sorted(degree_centrality, key=degree_centrality.get, reverse=True)
top_30_nodes = sorted_nodes[:30]
# for node in top_30_nodes:
#     print(f"\nNode {node} with degree {G.degree[node]}: {dict(G.nodes[node])}")

# # Get the top 30 nodes with the highest degree centrality
# # Print the top 30 nodes and their degree centrality values
# new_graph = nx.Graph()

# # Add edges and nodes to the new graph
# for edge in G.edges():
#     node1, node2 = edge

#     # Add the edge if either node is in the top 20 nodes
#     if node1 in top_30_nodes or node2 in top_30_nodes:
#         new_graph.add_edge(node1, node2)

# # Add the top 20 nodes to the new graph
# new_graph.add_nodes_from(top_30_nodes)
# pos = nx.spring_layout(G)
# nx.draw(G, pos, node_size = 50,label=True, node_color='lightcoral', edgecolors='lavender',width=0.5) 
nx.write_gexf(G, "new_test.gexf")
# plt.show()
