import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
import pandas as pd
from namematcher import NameMatcher

df_author = pd.read_csv('new_author.csv')

name_matcher = NameMatcher()
# score = name_matcher.match_names('C. I. Ezeife', 'Christiana Ijeoma Ezeife')
# print(score) 

# Danh sách các tác giả (ví dụ)
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

# Tính ma trận khoảng cách tùy chỉnh
distance_matrix = custom_distance(df_author)
print(distance_matrix)
Z = linkage(distance_matrix, method='ward')
print()
# Chọn ngưỡng và phân cụm
threshold = 0.1
cluster_ids = fcluster(Z, threshold, criterion='distance')

print("Phân cụm các tác giả:")
for i, author in df_author.iterrows():
    print(f"{author['name']} - Cụm {cluster_ids[i]}")