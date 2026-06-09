"""
Enterprise Memory Execution Agent — Streamlit Dashboard

Run with:
    streamlit run dashboard/app.py
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Any

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Enterprise Memory Execution Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
.metric-card {
    background: #1e1e2e;
    border-radius: 10px;
    padding: 1rem 1.5rem;
    border-left: 4px solid #7c3aed;
    margin-bottom: 0.5rem;
}
.status-success { color: #22c55e; font-weight: 600; }
.status-simulated { color: #3b82f6; font-weight: 600; }
.status-error { color: #ef4444; font-weight: 600; }
.status-running { color: #f59e0b; font-weight: 600; }
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-success { background: #166534; color: #86efac; }
.badge-sim { background: #1e3a5f; color: #93c5fd; }
.badge-error { background: #7f1d1d; color: #fca5a5; }
.badge-running { background: #78350f; color: #fcd34d; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def api(path: str, method: str = "GET", **kwargs: Any) -> Any:
    try:
        resp = requests.request(method, f"{API_BASE}{path}", timeout=60, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE}. Is the server running?")
        return None
    except Exception as exc:
        st.error(f"API error: {exc}")
        return None


def status_badge(status: str) -> str:
    cls_map = {
        "completed": "badge-success",
        "success": "badge-success",
        "simulated": "badge-sim",
        "running": "badge-running",
        "failed": "badge-error",
        "error": "badge-error",
    }
    cls = cls_map.get(status, "badge-sim")
    return f'<span class="badge {cls}">{status}</span>'


def fmt_duration(ms: int) -> str:
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.1f}s"


def fmt_ts(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%b %d %H:%M:%S")
    except Exception:
        return ts


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🤖 Enterprise MEA")
    st.markdown("*Memory Execution Agent*")
    st.divider()
    page = st.radio(
        "Navigation",
        ["Dashboard", "New Run", "Run Details", "Memory Explorer"],
        index=0,
    )
    st.divider()
    health = api("/health")
    if health:
        cfg = health.get("config", {})
        st.markdown("**System Status**")
        st.success("API Online")
        st.markdown(f"LLM: `{cfg.get('llm_model','—')}`")
        st.markdown(f"Composio: {'🟢 real' if cfg.get('composio_configured') else '🟡 mock'}")
        st.markdown(f"Dry Run: {'✅' if cfg.get('dry_run_default') else '🔴 off'}")
        apps = health.get("apps", [])
        st.markdown(f"Apps: {' · '.join(apps)}")


# ── Page: Dashboard ───────────────────────────────────────────────────────────

if page == "Dashboard":
    st.title("🤖 Enterprise Memory Execution Agent")
    st.markdown("*Autonomous research, persistent memory, and cross-app execution*")

    # Stats row
    stats = api("/stats")
    if stats:
        r = stats.get("runs", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Runs", r.get("total", 0))
        c2.metric("Success Rate", f"{r.get('success_rate', 0)}%")
        c3.metric("Total Actions", stats.get("total_traced_actions", 0))
        c4.metric("Memory Records", stats.get("memory_records", 0))

    st.divider()

    # Recent runs
    st.subheader("Recent Runs")
    runs = api("/runs?limit=20")
    if runs:
        rows = []
        for r in runs:
            trace = r.get("trace_entries") or []
            rows.append({
                "Run ID": r["id"][:16] + "…",
                "Prompt": r["prompt"][:60] + ("…" if len(r["prompt"]) > 60 else ""),
                "Status": r["status"],
                "Dry Run": "✅" if r.get("dry_run") else "🔴",
                "Actions": len(trace) if isinstance(trace, list) else "—",
                "Started": fmt_ts(r.get("created_at", "")),
            })

        import pandas as pd
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No runs yet. Go to **New Run** to trigger your first workflow.")

    # Agent architecture diagram
    st.divider()
    st.subheader("Agent Architecture")
    cols = st.columns(5)
    agents = [
        ("🗺️", "Planner", "Decomposes prompt into steps"),
        ("🔬", "Research", "Synthesises topic with LLM"),
        ("⚖️", "Critic", "Validates quality & scores confidence"),
        ("🧠", "Memory", "Stores/retrieves vector + SQL context"),
        ("⚡", "Executor", "Fires Composio actions across 5 apps"),
    ]
    for col, (icon, name, desc) in zip(cols, agents):
        with col:
            st.markdown(f"**{icon} {name}**")
            st.caption(desc)

    st.divider()
    apps_row = st.columns(5)
    app_info = [
        ("📄", "Notion", "Research report page"),
        ("📋", "Linear", "4 engineering tasks"),
        ("🐙", "GitHub", "Issue tracking"),
        ("💬", "Slack", "Block Kit summary"),
        ("📧", "Gmail", "Stakeholder email"),
    ]
    for col, (icon, name, desc) in zip(apps_row, app_info):
        with col:
            st.markdown(f"**{icon} {name}**")
            st.caption(desc)


# ── Page: New Run ─────────────────────────────────────────────────────────────

elif page == "New Run":
    st.title("▶️ Trigger New Workflow")
    st.markdown("Submit a research prompt to run the full multi-agent pipeline.")

    with st.form("run_form"):
        prompt = st.text_area(
            "Research Prompt",
            value="Research MCP frameworks for enterprise adoption and create an execution plan.",
            height=100,
        )
        dry_run = st.checkbox("Dry Run (simulate Composio actions)", value=True)
        submitted = st.form_submit_button("🚀 Run Workflow", type="primary")

    if submitted:
        with st.spinner("Running multi-agent workflow…"):
            result = api(
                "/run-research-workflow",
                method="POST",
                json={"prompt": prompt, "dry_run": dry_run},
            )

        if result:
            status = result.get("status", "unknown")
            if status == "completed":
                st.success(f"✅ Workflow completed — Run ID: `{result['run_id'][:16]}…`")
            else:
                st.error(f"Workflow {status}")

            # Critique summary
            critique = result.get("critique", {})
            if critique:
                score = critique.get("confidence_score", 0)
                bar_color = "green" if score >= 80 else "orange" if score >= 60 else "red"
                st.markdown(f"**Research Confidence Score:** {score}/100  ({critique.get('quality_rating','?')})")
                st.progress(score / 100)

            # Key insights
            research = result.get("research", {})
            if research.get("key_insights"):
                st.subheader("Key Insights")
                for insight in research["key_insights"]:
                    st.markdown(f"- {insight}")

            # Execution results
            exec_res = result.get("execution_results", {})
            if exec_res:
                st.subheader("Execution Results")
                app_cols = st.columns(5)
                apps_order = ["notion", "linear", "github", "slack", "gmail"]
                icons = {"notion": "📄", "linear": "📋", "github": "🐙", "slack": "💬", "gmail": "📧"}
                for col, app in zip(app_cols, apps_order):
                    r = exec_res.get(app)
                    if isinstance(r, list):
                        r = r[0] if r else {}
                    with col:
                        if r and r.get("success"):
                            st.markdown(f"**{icons[app]} {app.capitalize()}**")
                            st.markdown("✅ Success" if not r.get("simulated") else "🔵 Simulated")
                        else:
                            st.markdown(f"**{icons[app]} {app.capitalize()}**")
                            st.markdown("❌ Failed")

            # Trace summary
            ts = result.get("trace_summary", {})
            if ts:
                st.caption(
                    f"Trace: {ts.get('total_actions')} actions · "
                    f"{ts.get('success')} success · "
                    f"{ts.get('simulated')} simulated · "
                    f"{fmt_duration(ts.get('total_duration_ms', 0))} total"
                )

            with st.expander("Raw JSON Response"):
                st.json(result)


# ── Page: Run Details ─────────────────────────────────────────────────────────

elif page == "Run Details":
    st.title("🔍 Run Details")

    runs = api("/runs?limit=50") or []
    if not runs:
        st.info("No runs yet.")
        st.stop()

    options = {f"{r['id'][:16]}… — {r['prompt'][:40]}": r["id"] for r in runs}
    selected_label = st.selectbox("Select Run", list(options.keys()))
    run_id = options[selected_label]

    run = api(f"/runs/{run_id}")
    if not run:
        st.stop()

    # Header
    col_a, col_b, col_c = st.columns(3)
    col_a.markdown(f"**Status:** {run.get('status','—')}")
    col_b.markdown(f"**Dry Run:** {'Yes' if run.get('dry_run') else 'No'}")
    col_c.markdown(f"**Started:** {fmt_ts(run.get('created_at',''))}")

    st.markdown(f"**Prompt:** {run.get('prompt','')}")
    st.divider()

    # Critique card
    exec_results = run.get("execution_results") or {}

    # Agent trace timeline
    st.subheader("🕐 Agent Execution Timeline")
    trace = run.get("trace_entries") or []
    if isinstance(trace, list) and trace:
        for entry in trace:
            icon_map = {
                "PlannerAgent": "🗺️", "ResearchAgent": "🔬", "CriticAgent": "⚖️",
                "MemoryAgent": "🧠", "ExecutionAgent": "⚡", "Orchestrator": "🔧",
            }
            icon = icon_map.get(entry.get("agent_name", ""), "•")
            status_color = {
                "success": "🟢", "simulated": "🔵", "error": "🔴",
            }.get(entry.get("status", ""), "⚪")

            with st.expander(
                f"{icon} {entry.get('agent_name','?')} — "
                f"{entry.get('action_type','?')} → {entry.get('target_app','?')} "
                f"{status_color} {fmt_duration(entry.get('duration_ms', 0))}"
            ):
                cols = st.columns(2)
                with cols[0]:
                    st.markdown("**Input**")
                    st.json(entry.get("input") or {})
                with cols[1]:
                    st.markdown("**Output**")
                    st.json(entry.get("output") or {})
                st.caption(f"Timestamp: {fmt_ts(entry.get('timestamp',''))}")
    else:
        st.info("No trace entries available for this run.")

    # Execution results
    st.divider()
    st.subheader("⚡ Execution Results")
    if exec_results:
        apps_order = ["notion", "linear", "github", "slack", "gmail"]
        icons_map = {"notion": "📄", "linear": "📋", "github": "🐙", "slack": "💬", "gmail": "📧"}
        for app in apps_order:
            res = exec_results.get(app)
            if not res:
                continue
            items = res if isinstance(res, list) else [res]
            for item in items:
                if not item:
                    continue
                status_icon = "✅" if item.get("success") and not item.get("simulated") else "🔵" if item.get("simulated") else "❌"
                data = item.get("data") or {}
                label = f"{icons_map[app]} **{app.capitalize()}** — {status_icon}"
                with st.expander(label, expanded=False):
                    st.json(data)


# ── Page: Memory Explorer ─────────────────────────────────────────────────────

elif page == "Memory Explorer":
    st.title("🧠 Memory Explorer")
    st.markdown("Browse and search the persistent knowledge base.")

    # Search
    query = st.text_input("Search memory", placeholder="e.g. MCP enterprise security")
    mode = st.radio("Search mode", ["hybrid", "vector", "keyword"], horizontal=True)

    if query:
        results = api(f"/memory/search?q={query}&mode={mode}&limit=10")
        if results:
            st.markdown(f"**Vector results:** {len(results.get('vector_results', []))}")
            for doc in results.get("vector_results", []):
                with st.expander(doc.get("content", "")[:80] + "…"):
                    st.write(doc.get("content"))
                    st.caption(f"Metadata: {doc.get('metadata')}")

            st.markdown(f"**Knowledge records:** {len(results.get('knowledge_records', []))}")
            import pandas as pd
            krs = results.get("knowledge_records", [])
            if krs:
                df = pd.DataFrame([{
                    "Topic": r.get("topic", "")[:50],
                    "Confidence": f"{int(float(r.get('confidence', 0)) * 100)}%",
                    "Version": r.get("version", 1),
                    "Updated": fmt_ts(r.get("updated_at", "")),
                } for r in krs])
                st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        # Show all
        mem = api("/memory?limit=50")
        if mem:
            col1, col2 = st.columns(2)
            col1.metric("Knowledge Records", mem.get("total_knowledge_records", 0))
            col2.metric("Vector Documents", mem.get("total_vector_docs", 0))

            records = mem.get("records", [])
            if records:
                st.subheader("Knowledge Records (latest version per topic)")
                import pandas as pd
                df = pd.DataFrame([{
                    "Topic": r.get("topic", "")[:60],
                    "Confidence": f"{int(float(r.get('confidence', 0)) * 100)}%",
                    "Version": r.get("version", 1),
                    "Run ID": (r.get("run_id") or "")[:12] + "…",
                    "Updated": fmt_ts(r.get("updated_at", "")),
                } for r in records])
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Show full details on expand
                for record in records[:5]:
                    with st.expander(f"📚 {record.get('topic', '')}"):
                        st.markdown(f"**Confidence:** {int(float(record.get('confidence', 0)) * 100)}%  |  Version {record.get('version', 1)}")
                        st.markdown("**Summary excerpt:**")
                        st.write(record.get("summary", "")[:500] + "…")
                        st.markdown("**Recommendations:**")
                        st.write(record.get("recommendation", "—"))
            else:
                st.info("No knowledge records yet. Run a workflow first.")
