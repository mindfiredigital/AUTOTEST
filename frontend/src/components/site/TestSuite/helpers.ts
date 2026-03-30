import { MarkerType, type Node, type Edge } from '@xyflow/react'

export const START_NODE: Node = {
  id: 'node-start',
  type: 'start',
  position: { x: 300, y: 0 },
  data: { label: 'START', node_type: 'start' },
}

export function buildAutoLayout(stepNodes: Node[]): Node[] {
  const X_CENTER = 300
  const Y_STEP = 160
  return stepNodes.map((n, i) => ({ ...n, position: { x: X_CENTER, y: (i + 1) * Y_STEP } }))
}

export function buildSequentialEdges(nodes: Node[]): Edge[] {
  const edges: Edge[] = []
  for (let i = 0; i < nodes.length - 1; i++) {
    edges.push({
      id: `edge-${nodes[i].id}-${nodes[i + 1].id}`,
      source: nodes[i].id,
      target: nodes[i + 1].id,
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#E4D7D7', strokeWidth: 2 },
    })
  }
  return edges
}
