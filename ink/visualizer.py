"""
Visualizer for .ink files.
Generates Mermaid diagrams for mind structures, interactions, and pressure fields.
"""

from __future__ import annotations

from ink.ast_nodes import InkFile


class InkVisualizer:
    """Generate diagrams from .ink AST."""

    def mind_graph(self, ast: InkFile) -> str:
        """Generate a Mermaid graph of all minds and their blocks."""
        lines = ["graph TD"]

        # System node
        system_name = ast.header.system or "INK System"
        lines.append(f'    SYS["{system_name}<br/>v{ast.header.version}"]')

        for name, mind in ast.minds.items():
            mind_id = f"M_{name}"
            lines.append(f"    {mind_id}[\"🧠 {name}\"]")
            lines.append(f"    SYS --> {mind_id}")

            # Sensations
            for s_name, s in mind.sensations.items():
                sid = f"S_{name}_{s_name}"
                label = s_name.replace("_", " ")
                lines.append(f'    {sid}(["💫 {label}<br/>\"{s.feels_like[:40]}...\"])')
                lines.append(f"    {mind_id} --> {sid}")

            # Triggers
            for t_name, t in mind.triggers.items():
                tid = f"T_{name}_{t_name}"
                label = t_name.replace("_", " ")
                lines.append(f'    {tid}(["⚡ {label}"])')
                lines.append(f"    {mind_id} --> {tid}")
                # Draw activation arrow
                if t.activates:
                    target = t.activates.replace("@", "").replace("::", "_").replace("SENSATION", "S")
                    lines.append(f"    {tid} -.->|activates| {target}")

            # Overrun
            if mind.overrun:
                oid = f"O_{name}"
                lines.append(f'    {oid}(["⚠️ Overrun<br/>{mind.overrun.correction_action}"])')
                lines.append(f"    {mind_id} --> {oid}")

            # Crystallization
            if mind.crystallization:
                cid = f"C_{name}"
                lines.append(f'    {cid}(["🔒 Crystallize<br/>{mind.crystallization.action}"])')
                lines.append(f"    {mind_id} --> {cid}")

            # Satisfaction
            if mind.satisfaction:
                satid = f"SAT_{name}"
                reqs = "<br/>".join(mind.satisfaction.requires[:3])
                lines.append(f'    {satid}(["✅ Satisfied when<br/>{reqs}"])')
                lines.append(f"    {mind_id} --> {satid}")

        # Interactions
        for name, mind in ast.minds.items():
            for inter in mind.interactions:
                src_id = f"M_{inter.source_mind}"
                tgt_id = f"M_{inter.target_mind}"
                lines.append(f"    {src_id} <-.->|{inter.relationship}| {tgt_id}")

        lines.append("")
        lines.append("    classDef mind fill:#1a1a2e,stroke:#e94560,color:#fff")
        lines.append("    classDef sensation fill:#16213e,stroke:#0f3460,color:#fff")
        lines.append("    classDef trigger fill:#1a1a2e,stroke:#e94560,color:#fff")
        lines.append("    classDef guard fill:#2d2d2d,stroke:#ffc107,color:#fff")

        return "\n".join(lines)

    def interaction_diagram(self, ast: InkFile) -> str:
        """Generate a Mermaid sequence diagram of mind interactions."""
        lines = ["sequenceDiagram"]

        # Participants
        for name in ast.minds:
            lines.append(f"    participant {name}")

        # Interactions
        for name, mind in ast.minds.items():
            for inter in mind.interactions:
                arrow = "->>" if inter.relationship == "lateral" else "-->>"
                query_label = inter.queries.split("::")[-1] if inter.queries else "query"
                lines.append(f"    {inter.source_mind} {arrow} {inter.target_mind}: {query_label}")

        # Pressure field collapse
        if ast.pressure_field and len(ast.minds) > 1:
            lines.append(f"    Note over {','.join(ast.minds.keys())}: Pressure Field Collapse")
            for axis in ast.pressure_field.axes:
                vec = ", ".join(f"{v:+.1f}" for v in axis.vector)
                lines.append(f"    Note right of {axis.mind_name}: [{vec}]")

        return "\n".join(lines)

    def pressure_field_diagram(self, ast: InkFile) -> str:
        """Generate a Mermaid diagram of the pressure field."""
        if not ast.pressure_field:
            return "# No pressure field defined in this file"

        pf = ast.pressure_field

        lines = ["graph LR"]

        lines.append(f'    CENTER["⚡ Pressure Field<br/>Dissent: {pf.dissent_threshold}<br/>Magnitude: {pf.magnitude_threshold}"]')

        axis_labels = ["concrete ←→ abstract", "speed ←→ depth", "safe ←→ risky"]

        for axis in pf.axes:
            aid = f"V_{axis.mind_name}"
            vec_desc = "<br/>".join(
                f"{axis_labels[i]}: {v:+.1f}"
                for i, v in enumerate(axis.vector)
            )
            lines.append(f'    {aid}["🧠 {axis.mind_name}<br/>{vec_desc}"]')
            lines.append(f"    {aid} --> CENTER")

        # Collapse result
        if ast.collapse:
            lines.append(f'    RESULT["🎯 Collapse<br/>Method: {ast.collapse.method}<br/>Format: {ast.collapse.output_format}"]')
            lines.append(f"    CENTER --> RESULT")

            for fb in ast.collapse.fallbacks:
                lines.append(f'    RESULT -.->|{fb.condition}| Fallback["🔧 {fb.action}"]')

        lines.append("")
        lines.append("    classDef center fill:#1a1a2e,stroke:#e94560,color:#fff")
        lines.append("    classDef vector fill:#16213e,stroke:#0f3460,color:#fff")
        lines.append("    classDef result fill:#2d2d2d,stroke:#ffc107,color:#fff")

        return "\n".join(lines)
