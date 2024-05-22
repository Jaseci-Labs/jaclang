import streamlit as st
import os

def get_nodes_edges(dot_file: str) -> tuple[dict, list]:
    import pydot
    from streamlit_agraph import Node, Edge

    graphs = pydot.graph_from_dot_file("example1.dot")
    graph: pydot.Graph = graphs[0]
    nodes: list[pydot.Node] = graph.get_node_list()
    _nodes = {}
    for node in nodes:
        _nodes[node.get_name()] = (Node(id=node.get_name(), label=node.get_label(), color="#DBEBC2"))

    edges = graph.get_edge_list()
    _edges = []
    for edge in edges:
        _edges.append(Edge(source=edge.get_source(), target=edge.get_destination(), label=edge.get_label()))
    return _nodes, _edges

st.title("Visualize DOT file")

selected_dot_file = st.selectbox("Select a DOT file", [x for x in os.listdir() if x.endswith(".dot")])
vis_opt = st.radio("Visualization options", ["Use pygraphviz (Static)", "Use streamlit-agraph (Interactive)"])

if selected_dot_file:
    if vis_opt == "Use pygraphviz (Static)":
        dot_graph_str = open(selected_dot_file).read()
        st.graphviz_chart(dot_graph_str)
    elif vis_opt == "Use streamlit-agraph (Interactive)":
        from streamlit_agraph import agraph, ConfigBuilder

        nodes, edges = get_nodes_edges(selected_dot_file)
        config_builder = ConfigBuilder(nodes)
        config = config_builder.build()

        return_value = agraph(list(nodes.values()), edges, config)
        if return_value:
            with st.expander("Selected Node Information", expanded=True):
                selected_node = nodes[return_value]
                st.write(f"Node Id: {selected_node.id}")
                st.write(f"Node Label: {selected_node.label}")
                st.write(f"Node Color: {selected_node.color}")

