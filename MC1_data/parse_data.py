import json
import pandas as pd
import networkx as nx

# STEP 1: Load the graph
# ─────────────────────────────────────────────
with open("MC1_graph.json", "r") as f:
    data = json.load(f)

# Load as a real NetworkX multigraph (as intended by the data source)
G = nx.node_link_graph(data)

print(f"Nodes: {G.number_of_nodes()}")   # expect 17,412
print(f"Edges: {G.number_of_edges()}")   # expect 37,857

# STEP 2: Extract and split nodes by type
# ─────────────────────────────────────────────
nodes = []
for node_id, attrs in G.nodes(data=True):
    row = {"id": node_id}
    row.update(attrs)
    nodes.append(row)

nodes_df = pd.DataFrame(nodes)
print(nodes_df["Node Type"].value_counts())

# Split into one table per node type
persons       = nodes_df[nodes_df["Node Type"] == "Person"].copy()
songs         = nodes_df[nodes_df["Node Type"] == "Song"].copy()
albums        = nodes_df[nodes_df["Node Type"] == "Album"].copy()
musical_groups= nodes_df[nodes_df["Node Type"] == "MusicalGroup"].copy()
record_labels = nodes_df[nodes_df["Node Type"] == "RecordLabel"].copy()

# STEP 3: Extract edges
# ─────────────────────────────────────────────
edges = []
for source, target, attrs in G.edges(data=True):
    row = {"source": source, "target": target}
    row.update(attrs)
    edges.append(row)

edges_df = pd.DataFrame(edges)
print(edges_df["Edge Type"].value_counts())

# Split into one table per edge type
performer_of       = edges_df[edges_df["Edge Type"] == "PerformerOf"]
composer_of        = edges_df[edges_df["Edge Type"] == "ComposerOf"]
producer_of        = edges_df[edges_df["Edge Type"] == "ProducerOf"]
lyricist_of        = edges_df[edges_df["Edge Type"] == "LyricistOf"]
recorded_by        = edges_df[edges_df["Edge Type"] == "RecordedBy"]
distributed_by     = edges_df[edges_df["Edge Type"] == "DistributedBy"]
member_of          = edges_df[edges_df["Edge Type"] == "MemberOf"]

# Influence-type edges (most important for your research questions)
in_style_of        = edges_df[edges_df["Edge Type"] == "InStyleOf"]
interpolates_from  = edges_df[edges_df["Edge Type"] == "InterpolatesFrom"]
cover_of           = edges_df[edges_df["Edge Type"] == "CoverOf"]
lyrical_ref        = edges_df[edges_df["Edge Type"] == "LyricalReferenceTo"]
directly_samples   = edges_df[edges_df["Edge Type"] == "DirectlySamples"]

# STEP 4: Build a unified "influence" edge table
# (combines all 5 musical influence edge types)
# ─────────────────────────────────────────────
influence_edges = edges_df[edges_df["Edge Type"].isin([
    "InStyleOf", "InterpolatesFrom", "CoverOf",
    "LyricalReferenceTo", "DirectlySamples"
])].copy()

# ─────────────────────────────────────────────
# STEP 5: Enrich edges with node attributes
# (so Tableau rows are self-contained)
# ─────────────────────────────────────────────

# Build lookup dictionaries from the node tables
song_lookup = songs.set_index("id")[["genre", "release_date", "notable", "notoriety_date"]].to_dict("index")
person_lookup = persons.set_index("id")[["name", "stage_name"]].to_dict("index")

def get_node_attr(node_id, attr, lookup):
    return lookup.get(node_id, {}).get(attr)

# Enrich influence edges: label source and target with genre and release year
influence_edges["source_genre"]   = influence_edges["source"].map(lambda x: get_node_attr(x, "genre", song_lookup))
influence_edges["source_year"]    = influence_edges["source"].map(lambda x: get_node_attr(x, "release_date", song_lookup))
influence_edges["target_genre"]   = influence_edges["target"].map(lambda x: get_node_attr(x, "genre", song_lookup))
influence_edges["target_year"]    = influence_edges["target"].map(lambda x: get_node_attr(x, "release_date", song_lookup))

# ─────────────────────────────────────────────
# STEP 6: Compute graph metrics on persons
# (for the "rising star" dashboard)
# ─────────────────────────────────────────────

# Build a subgraph of just PerformerOf edges to compute artist-level stats
performer_graph = nx.from_pandas_edgelist(
    performer_of, source="source", target="target", create_using=nx.DiGraph()
)

# For influence spread: who influences whom (via songs they performed)
# We'll compute in/out degree on the full graph as a proxy
in_deg  = dict(G.in_degree())
out_deg = dict(G.out_degree())

persons["in_degree"]  = persons["id"].map(in_deg).fillna(0).astype(int)
persons["out_degree"] = persons["id"].map(out_deg).fillna(0).astype(int)

# ─────────────────────────────────────────────
# STEP 7: Export all CSVs
# ─────────────────────────────────────────────
persons.to_csv("persons.csv", index=False)
songs.to_csv("songs.csv", index=False)
albums.to_csv("albums.csv", index=False)
musical_groups.to_csv("musical_groups.csv", index=False)
record_labels.to_csv("record_labels.csv", index=False)

influence_edges.to_csv("influence_edges.csv", index=False)
performer_of.to_csv("performer_of.csv", index=False)
composer_of.to_csv("composer_of.csv", index=False)
producer_of.to_csv("producer_of.csv", index=False)
member_of.to_csv("member_of.csv", index=False)

print("All CSVs exported.")