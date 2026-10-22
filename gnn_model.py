import networkx as nx
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class FraudGNN:
    """
    Graph Neural Network simulation for fraud detection.
    Uses NetworkX to build transaction graphs and analyze patterns.
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.transactions = []
        
    def add_transaction(self, tx_data: Dict):
        """
        Add a transaction to the graph.
        tx_data: dict with amount, merchant, city, country, device, channel, etc.
        """
        # Create nodes
        user_id = tx_data.get('user', 'default_user')
        merchant_id = tx_data.get('merchant', 'unknown_merchant')
        device_id = tx_data.get('device', 'unknown_device')
        location_id = f"{tx_data.get('city', 'unknown')}, {tx_data.get('country', 'unknown')}"
        
        # Add nodes with attributes
        self.graph.add_node(user_id, type='user', label='User')
        self.graph.add_node(merchant_id, type='merchant', label='Merchant')
        self.graph.add_node(device_id, type='device', label='Device')
        self.graph.add_node(location_id, type='location', label='Location')
        
        # Add edges (transactions)
        tx_id = f"tx_{len(self.transactions)}"
        self.graph.add_edge(user_id, merchant_id, 
                           transaction_id=tx_id,
                           amount=tx_data.get('amount', 0),
                           timestamp=tx_data.get('timestamp', 'unknown'),
                           fraud_risk=tx_data.get('risk', 0))
        
        self.graph.add_edge(user_id, device_id,
                           transaction_id=tx_id,
                           used_device=True)
        
        self.graph.add_edge(user_id, location_id,
                           transaction_id=tx_id,
                           used_location=True)
        
        self.transactions.append(tx_data)
        
    def analyze_graph(self) -> Dict:
        """
        Analyze the transaction graph for fraud patterns.
        Returns analysis results.
        """
        analysis = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'high_risk_transactions': 0,
            'suspicious_merchants': [],
            'suspicious_devices': [],
            'suspicious_locations': [],
            'graph_density': nx.density(self.graph),
            'connected_components': nx.number_connected_components(self.graph.to_undirected())
        }
        
        # Count high risk transactions
        for u, v, data in self.graph.edges(data=True):
            if 'fraud_risk' in data and data['fraud_risk'] >= 70:
                analysis['high_risk_transactions'] += 1
                
        # Find suspicious nodes (high degree nodes)
        degrees = dict(self.graph.degree())
        high_degree_threshold = np.percentile(list(degrees.values()), 75) if degrees else 0
        
        for node, degree in degrees.items():
            if degree > high_degree_threshold:
                node_type = self.graph.nodes[node].get('type', 'unknown')
                if node_type == 'merchant':
                    analysis['suspicious_merchants'].append(node)
                elif node_type == 'device':
                    analysis['suspicious_devices'].append(node)
                elif node_type == 'location':
                    analysis['suspicious_locations'].append(node)
                    
        return analysis
    
    def get_risk_score(self, tx_data: Dict) -> float:
        """
        Calculate risk score based on graph patterns.
        """
        # Simulate GNN-based risk calculation
        risk = 0
        
        # Check if merchant is frequently used
        merchant = tx_data.get('merchant', '')
        merchant_degree = self.graph.degree(merchant) if merchant in self.graph else 0
        if merchant_degree > 5:
            risk += 15
            
        # Check if device is new or frequently used
        device = tx_data.get('device', '')
        if device == 'New Device':
            risk += 20
        elif device in self.graph and self.graph.degree(device) > 3:
            risk += 10
            
        # Check if location is new
        location = f"{tx_data.get('city', '')}, {tx_data.get('country', '')}"
        if location not in self.graph:
            risk += 15
            
        # Check amount
        amount = tx_data.get('amount', 0)
        if amount > 1000:
            risk += 20
        elif amount > 500:
            risk += 10
            
        return min(risk, 99)
    
    def visualize_graph(self, highlighted_nodes=None):
        """
        Create an interactive plotly visualization of the transaction graph.
        """
        if not PLOTLY_AVAILABLE:
            return None
            
        if self.graph.number_of_nodes() == 0:
            return None
            
        # Create layout
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        # Extract node positions
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_type = self.graph.nodes[node].get('type', 'unknown')
            node_text.append(f"{node}\n({node_type})")
            
            # Color based on node type
            if node_type == 'user':
                node_colors.append('#667eea')  # Blue
                node_sizes.append(30)
            elif node_type == 'merchant':
                node_colors.append('#f56565')  # Red
                node_sizes.append(25)
            elif node_type == 'device':
                node_colors.append('#48bb78')  # Green
                node_sizes.append(20)
            elif node_type == 'location':
                node_colors.append('#ed8936')  # Orange
                node_sizes.append(20)
            else:
                node_colors.append('#718096')  # Gray
                node_sizes.append(15)
        
        # Extract edges
        edge_x = []
        edge_y = []
        
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create figure
        if not PLOTLY_AVAILABLE:
            return None
            
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            line=dict(width=1, color='#cbd5e0'),
            hoverinfo='none',
            showlegend=False
        ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            ),
            text=node_text,
            textposition='top center',
            textfont=dict(size=10),
            hoverinfo='text',
            showlegend=False
        ))
        
        fig.update_layout(
            title='Transaction Network Graph (GNN Visualization)',
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="Blue: User | Red: Merchant | Green: Device | Orange: Location",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    xanchor='left', yanchor='bottom',
                    font=dict(size=12)
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        return fig


def create_sample_transactions() -> List[Dict]:
    """Create sample transactions for demonstration."""
    merchants = ["Amazon", "Flipkart", "Walmart", "Electronics Store", "Grocery"]
    devices = ["Mobile", "Desktop", "Known Device", "New Device"]
    cities = ["Hyderabad", "Bengaluru", "Chennai", "Mumbai", "Delhi"]
    
    transactions = []
    for i in range(10):
        tx = {
            'user': 'user_1',
            'amount': np.random.randint(100, 2000),
            'merchant': np.random.choice(merchants),
            'device': np.random.choice(devices),
            'city': np.random.choice(cities),
            'country': 'India',
            'timestamp': f'2024-01-{i+1}',
            'risk': np.random.randint(0, 100)
        }
        transactions.append(tx)
    
    return transactions
