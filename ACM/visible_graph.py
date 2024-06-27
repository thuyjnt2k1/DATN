import csv
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from community import community_louvain
import community

# df_links = pd.read_csv('new_link.csv')
# df_queue = pd.read_csv('new_queue.csv', index_col='id')
# df_nodes = pd.read_csv('new_node.csv', index_col='id')
# df_author = pd.read_csv('new_author.csv', index_col='ner_id')
# # df_author = df_author.astype({'orcid': 'str', 'email': 'str', 'affiliation': 'str'})
# df_paper = pd.read_csv('new_paper.csv', index_col='ner_id')

df_links = pd.read_csv('after_link3.csv')
df_queue = pd.read_csv('after_queue3.csv', index_col='id')
df_nodes = pd.read_csv('after_node3.csv', index_col='id')
print(df_nodes)
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
for id, link in df_links.iterrows():
  G.add_edge(int(link['from']),int(link['to']),weight=df_links.iloc[link]['count'])
  # print('\n', df_links.iloc[link]['from'], df_links.iloc[link]['to'])

# print('\n====================Number of publish link======================\n', publish_link_count)

# # get modularity
# print('\n====================community======================\n')
# communities = community.best_partition(G)
# giant_communites = []
# for i, community in enumerate(communities):
#   if(len(community) > 50):
#     giant_communites.append(community)
#   else:
#     for node in community:
#       giant_communites.append({node})

# modularity = nx.algorithms.community.modularity(G, communities)
# print('\n====================modularity======================\n', modularity, nx.algorithms.community.modularity(G, giant_communites))

# avg_clustering = nx.average_clustering(G)
# print('\n====================Clustering Coefficient======================\n',avg_clustering)

# density = nx.density(G)
# print('\n====================Density======================\n', density)

# # # # Find the largest connected component
# connected_components = nx.connected_components(G)
# largest_component = max(connected_components, key=len)
# print('\n====================Largest graph======================\n', len(largest_component))

# largest_subgraph = G.subgraph(largest_component)
# nx.write_gexf(largest_subgraph, 'subgraph.gexf')


betweenness = nx.betweenness_centrality(G)
sorted_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)

top_10_betweenness = sorted_betweenness[:10]

print("================Top 10 nodes by betweenness centrality:========================")
for node, value in top_10_betweenness:
    print(f"Node {node}: {value:.3f}")
    
coauthor_dict = {}
publicaction_dict = {}
def getLinkCount(x):
  print(x)
  neighbors = list(G.neighbors(x))
  publication = sum(1 for n in neighbors if G.nodes[n]['type'] == 1)
  coauthor = sum(1 for n in neighbors if  G.nodes[n]['type'] == 2)
  # print('\n', publication, coauthor, betweenness[x])

for node in G.nodes:
  print(node)
  neighbors = list(G.neighbors(node))
  publication = sum(1 for n in neighbors if G.nodes[n]['type'] == 1)
  coauthor = sum(1 for n in neighbors if  G.nodes[n]['type'] == 2)
  coauthor_dict[node] = coauthor
  publicaction_dict[node] = publication

coauthor_dict = dict(sorted(coauthor_dict.items(), key=lambda x: x[1], reverse=True)[:10])
print(coauthor_dict)
print('\n====================coauthor graph======================\n')
for id, value in coauthor_dict.items():
    print(f"\n{G.nodes[id]['name']}: {value}")
print('\n====================publication graph======================\n')
publicaction_dict = dict(sorted(publicaction_dict.items(), key=lambda x: x[1], reverse=True)[:10])
for id, value in publicaction_dict.items():
    print(f"\n{G.nodes[id]['name']}: {value}")

# print(largest_component)
# # Create a subgraph of the largest connected component
degree_centrality = nx.degree_centrality(G)
sorted_nodes = sorted(degree_centrality, key=degree_centrality.get, reverse=True)
top_30_nodes = sorted_nodes[:10]
print('\n====================top degree graph======================\n')
for node in top_30_nodes:
    print(f"\nNode {node} with degree {G.degree[node]}: {dict(G.nodes[node])}")
    # getLinkCount(node)

# print(G.nodes[3371], G.degree[3371], publicaction_dict[3371], coauthor_dict[3371])
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
