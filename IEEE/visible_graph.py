import csv
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

df_links = pd.read_csv('after_link.csv')
df_queue = pd.read_csv('after_queue.csv')
df_nodes = pd.read_csv('after_node.csv')
df_author = pd.read_csv('after_author.csv')
df_paper = pd.read_csv('after_paper.csv')

G = nx.Graph()
for index,node in df_queue.iterrows():
  print(node['id'], '\n', node['type'])
  if node["type"] == 1:
    document = df_paper.loc[df_paper['ner_id'] == node["id"]]
    if len(document) > 0:
      document = document.iloc[0]  # Access the first row of the document DataFrame
      G.add_node(node["id"], link = node["link"], type = node["type"], title = document["title"], doi = document["doi"])
    else:
      G.add_node(node["id"], link = node["link"], type = node["type"])
    print("\ninsert node", id, "type ", node["type"])
  elif node["type"] == 2:
    author = df_author.loc[df_author['ner_id'] == node["id"]]
    if len(author) > 0:
      author = author.iloc[0]  # Access the first row of the document DataFrame
      G.add_node(node["id"], link = node["link"], type = node["type"], name = author["name"], orcid = author["orcid"])
    else:
      G.add_node(node["id"], link = node["link"], type = node["type"])
    print("\ninsert node", id, "type ", node["type"])

grouped = df_queue.groupby(['type']).count()
print(grouped)
for link in df_links.index:
  G.add_edge(int(df_links.iloc[link]['from'])+1,int(df_links.iloc[link]['to'])+1,weight=df_links.iloc[link]['count'])
  print('\n', df_links.iloc[link]['from'], df_links.iloc[link]['to'])

# connected_components = nx.connected_components(G)

# # # Find the largest connected component
# largest_component = max(connected_components, key=len)
# print(largest_component)
# # # Create a subgraph of the largest connected component
# largest_subgraph = G.subgraph(largest_component)

# degree_centrality = nx.degree_centrality(G)

# # Sort nodes by degree centrality in descending order
# sorted_nodes = sorted(degree_centrality, key=degree_centrality.get, reverse=True)

# # Get the top 30 nodes with the highest degree centrality
# top_30_nodes = sorted_nodes[:100]
# print(top_30_nodes)
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
