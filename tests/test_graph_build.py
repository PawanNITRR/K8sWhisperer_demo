def test_build_graph_compiles():
    from agent.graph import build_graph

    g = build_graph()
    assert g is not None
