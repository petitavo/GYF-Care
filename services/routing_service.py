from graph.graph_builder import GraphBuilder

class RoutingService:
    
    def __init__(self):
        self.graph_builder = GraphBuilder()
        self.graph_builder.load_nodes_from_db()
        self.graph = self.graph_builder.build_knn_graph()

    def get_graph(self):
        return self.graph
