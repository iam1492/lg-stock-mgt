from langgraph.graph.state import CompiledStateGraph
from dataclasses import dataclass

@dataclass
class NodeStyles:
    default: str = (
        "fill:#45C4B0, fill-opacity:0.3, color:#23260F, stroke:#45C4B0, stroke-width:1px, font-weight:bold, line-height:1.2"  # 기본 색상
    )
    first: str = (
        "fill:#45C4B0, fill-opacity:0.1, color:#23260F, stroke:#45C4B0, stroke-width:1px, font-weight:normal, font-style:italic, stroke-dasharray:2,2"  # 점선 테두리
    )
    last: str = (
        "fill:#45C4B0, fill-opacity:1, color:#000000, stroke:#45C4B0, stroke-width:1px, font-weight:normal, font-style:italic, stroke-dasharray:2,2"  # 점선 테두리
    )
    
def save_mermaid_as_png(graph: CompiledStateGraph):
    graph.get_graph(xray=True).draw_mermaid_png(
        background_color="white",
        node_colors=NodeStyles(),
        output_file_path="./stock_agent/graph/graph.png")
    
        