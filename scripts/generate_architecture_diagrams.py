import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch

def generate_domain_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Define domain boxes
    domains = {
        'API Layer': (2, 7, 8, 1),
        'Authentication': (1, 4, 3, 2),
        'Onboarding': (6, 4, 3, 2),
        'Shared': (3.5, 2, 3, 1),
        'Infrastructure': (2, 0, 8, 1)
    }
    
    # Draw domain boxes
    for name, (x, y, w, h) in domains.items():
        if name == 'Shared':
            color = 'lightgreen'
        elif name in ['API Layer', 'Infrastructure']:
            color = 'lightgray'
        else:
            color = 'lightblue'
        
        box = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2, name, ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Draw arrows for event flow
    arrow1 = ConnectionPatch((4, 5), (6, 5), "data", "data",
                            arrowstyle="->", shrinkA=5, shrinkB=5,
                            mutation_scale=20, fc="red")
    ax.add_artist(arrow1)
    ax.text(5, 5.2, "UserRegisteredEvent", ha='center', fontsize=8)
    
    ax.set_xlim(0, 12)
    ax.set_ylim(-1, 9)
    ax.axis('off')
    ax.set_title('Domain Architecture with Event Flow', fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('docs/architecture/diagrams/domain_architecture.png', dpi=300, bbox_inches='tight')

if __name__ == "__main__":
    generate_domain_diagram()
    print("\u2705 Architecture diagrams generated")