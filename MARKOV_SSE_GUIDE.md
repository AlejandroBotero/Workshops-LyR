# Markov Chain in SSE Stream

## Overview

The Markov Chain service analyzes article category transitions and sends graph data to the frontend via the SSE (Server-Sent Events) stream in real-time.

---

## How It Works

### 1. **Article Submission**
When a new article is submitted:
```
POST /api/submit/
```

### 2. **Markov Chain Calculation**
The system:
- Analyzes all articles ordered by publication date
- Counts transitions between consecutive categories
- Calculates transition probabilities
- Generates graph data (nodes + edges)

### 3. **SSE Broadcast**
The Markov chain graph is included in the SSE event:
```
GET /api/stream/
```

---

## SSE Event Structure

### Complete Event Payload

```json
{
  "new_article": {
    "_id": "123",
    "headline": "AI Breakthrough...",
    "category": "technology",
    ...
  },
  "related_article": {...},
  "related_similarity_distance": 5,
  "statistics": {
    "total_articles": 100,
    "category_counts": {...},
    "full_trend_analysis": {...},
    "recent_trend_analysis": {...},
    "top_tendencies": [...]
  },
  "markov_graph": {
    "nodes": [
      {
        "id": "technology",
        "label": "Technology",
        "count": 25
      },
      {
        "id": "sports",
        "label": "Sports",
        "count": 20
      },
      {
        "id": "world",
        "label": "World",
        "count": 30
      },
      {
        "id": "entertainment",
        "label": "Entertainment",
        "count": 25
      }
    ],
    "edges": [
      {
        "from": "technology",
        "to": "sports",
        "probability": 0.35
      },
      {
        "from": "technology",
        "to": "world",
        "probability": 0.25
      },
      {
        "from": "technology",
        "to": "entertainment",
        "probability": 0.4
      },
      {
        "from": "sports",
        "to": "technology",
        "probability": 0.3
      },
      {
        "from": "sports",
        "to": "world",
        "probability": 0.5
      },
      {
        "from": "sports",
        "to": "entertainment",
        "probability": 0.2
      }
    ]
  }
}
```

---

## Frontend Integration

### JavaScript Example

```javascript
// Connect to SSE stream
const eventSource = new EventSource('http://127.0.0.1:8000/api/stream/');

eventSource.onmessage = function(event) {
  if (event.data === ':heartbeat') return;
  
  const data = JSON.parse(event.data);
  
  // Extract Markov graph data
  const markovGraph = data.markov_graph;
  
  console.log('Nodes:', markovGraph.nodes);
  console.log('Edges:', markovGraph.edges);
  
  // Update visualization
  updateMarkovGraph(markovGraph);
};

function updateMarkovGraph(graphData) {
  // Use D3.js, Cytoscape.js, or other graph library
  // to visualize the Markov chain
}
```

### React Example

```jsx
import { useEffect, useState } from 'react';

function MarkovChainVisualization() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  
  useEffect(() => {
    const eventSource = new EventSource('http://127.0.0.1:8000/api/stream/');
    
    eventSource.onmessage = (event) => {
      if (event.data === ':heartbeat') return;
      
      const data = JSON.parse(event.data);
      setGraphData(data.markov_graph);
    };
    
    return () => eventSource.close();
  }, []);
  
  return (
    <div>
      <h2>Category Transition Graph</h2>
      <p>Nodes: {graphData.nodes.length}</p>
      <p>Edges: {graphData.edges.length}</p>
      {/* Render graph visualization */}
    </div>
  );
}
```

---

## Graph Data Format

### Nodes

Each node represents a category:

```json
{
  "id": "technology",        // Category identifier
  "label": "Technology",     // Display name
  "count": 25                // Number of articles in this category
}
```

### Edges

Each edge represents a transition probability:

```json
{
  "from": "technology",      // Source category
  "to": "sports",            // Target category
  "probability": 0.35        // Probability of transition (0-1)
}
```

---

## Visualization Examples

### Example 1: D3.js Force-Directed Graph

```javascript
function renderMarkovGraph(graphData) {
  const width = 800;
  const height = 600;
  
  const svg = d3.select('#graph')
    .attr('width', width)
    .attr('height', height);
  
  // Create force simulation
  const simulation = d3.forceSimulation(graphData.nodes)
    .force('link', d3.forceLink(graphData.edges)
      .id(d => d.id)
      .distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2));
  
  // Draw edges
  const link = svg.selectAll('.link')
    .data(graphData.edges)
    .enter().append('line')
    .attr('class', 'link')
    .attr('stroke', '#999')
    .attr('stroke-width', d => d.probability * 5);
  
  // Draw nodes
  const node = svg.selectAll('.node')
    .data(graphData.nodes)
    .enter().append('circle')
    .attr('class', 'node')
    .attr('r', d => Math.sqrt(d.count) * 3)
    .attr('fill', '#69b3a2');
  
  // Add labels
  const label = svg.selectAll('.label')
    .data(graphData.nodes)
    .enter().append('text')
    .attr('class', 'label')
    .text(d => d.label);
  
  // Update positions on tick
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);
    
    node
      .attr('cx', d => d.x)
      .attr('cy', d => d.y);
    
    label
      .attr('x', d => d.x + 10)
      .attr('y', d => d.y + 5);
  });
}
```

### Example 2: Cytoscape.js

```javascript
function renderCytoscapeGraph(graphData) {
  const cy = cytoscape({
    container: document.getElementById('cy'),
    
    elements: {
      nodes: graphData.nodes.map(node => ({
        data: {
          id: node.id,
          label: node.label,
          count: node.count
        }
      })),
      edges: graphData.edges.map(edge => ({
        data: {
          source: edge.from,
          target: edge.to,
          probability: edge.probability
        }
      }))
    },
    
    style: [
      {
        selector: 'node',
        style: {
          'background-color': '#666',
          'label': 'data(label)',
          'width': 'data(count)',
          'height': 'data(count)'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 'data(probability)',
          'line-color': '#ccc',
          'target-arrow-color': '#ccc',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier'
        }
      }
    ],
    
    layout: {
      name: 'circle'
    }
  });
}
```

---

## Understanding the Data

### Transition Probabilities

The probability on each edge represents:
```
P(next category = B | current category = A) = edge.probability
```

**Example**:
```json
{
  "from": "technology",
  "to": "sports",
  "probability": 0.35
}
```

**Interpretation**: If the last article was "technology", there's a 35% chance the next article will be "sports".

### Node Sizes

Node `count` represents the total number of articles in that category. Use this to size nodes proportionally in your visualization.

---

## Real-Time Updates

The Markov graph updates automatically when new articles are submitted:

1. **New article submitted** → Database updated
2. **Markov chain recalculated** → Transition probabilities updated
3. **SSE event sent** → Frontend receives new graph data
4. **Visualization updates** → Graph reflects new transitions

---

## Testing

### Test the SSE Stream

```bash
# Terminal 1: Start server
python manage.py runserver

# Terminal 2: Listen to stream
curl -N http://127.0.0.1:8000/api/stream/

# Terminal 3: Submit articles
python ollama_submitter.py 1
```

### Verify Graph Data

```javascript
// In browser console
const eventSource = new EventSource('http://127.0.0.1:8000/api/stream/');

eventSource.onmessage = function(event) {
  if (event.data === ':heartbeat') return;
  
  const data = JSON.parse(event.data);
  console.log('Markov Graph:', data.markov_graph);
  
  // Check structure
  console.log('Nodes:', data.markov_graph.nodes.length);
  console.log('Edges:', data.markov_graph.edges.length);
  
  // Verify probabilities sum to ~1.0 for each source
  const bySource = {};
  data.markov_graph.edges.forEach(edge => {
    if (!bySource[edge.from]) bySource[edge.from] = 0;
    bySource[edge.from] += edge.probability;
  });
  console.log('Probability sums:', bySource);
};
```

---

## Performance Considerations

### Calculation Overhead

The Markov chain is recalculated on every SSE event. For large datasets:
- **< 1000 articles**: Negligible overhead
- **1000-10000 articles**: ~10-50ms
- **> 10000 articles**: Consider caching

### Optimization

If needed, add caching to `MarkovChainService`:

```python
from django.core.cache import cache

@staticmethod
def get_markov_graph_data():
    cache_key = 'markov_graph'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    # Calculate graph data
    graph_data = ...
    
    # Cache for 60 seconds
    cache.set(cache_key, graph_data, 60)
    
    return graph_data
```

---

## Summary

The Markov Chain service:

✅ **Analyzes** category transitions from article sequence  
✅ **Calculates** transition probabilities  
✅ **Generates** graph data (nodes + edges)  
✅ **Streams** to frontend via SSE in real-time  
✅ **Updates** automatically on new articles  

**Frontend receives**:
- `nodes`: Categories with article counts
- `edges`: Transitions with probabilities

**Perfect for**:
- Real-time graph visualizations
- Understanding content flow patterns
- Predicting next article categories
- Editorial insights

🎨 Ready to visualize with D3.js, Cytoscape.js, or any graph library!
