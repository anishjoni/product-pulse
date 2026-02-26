"""
Wealthsimple Community Intelligence Platform
Streamlit dashboard — human review of AI-generated insight cards.

Run:
    uv run streamlit run ui/app.py
"""

import json
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WS Community Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Color palette (fintech-grade, accessible) ─────────────────────────────────
# Inspired by Coolors "Professional Tech" and "Trust & Growth" palettes
COLORS = {
    "roadmap": "#2563EB",   # deep blue — opportunity, forward-looking
    "friction": "#EF4444",  # clear red — pain points
    "win": "#059669",       # teal-green — success, positive
    "other": "#6B7280",     # cool gray — neutral
    "bg": "#F9FAFB",        # off-white background
    "surface": "#FFFFFF",
    "border": "#E5E7EB",
    "text": "#111827",
    "muted": "#6B7280",
}

CATEGORY_META = {
    "roadmap": {"icon": "🗺️", "color": COLORS["roadmap"], "label": "Roadmap Opportunity"},
    "friction": {"icon": "🔥", "color": COLORS["friction"], "label": "Friction / Pain Point"},
    "win":      {"icon": "🏆", "color": COLORS["win"],     "label": "Win"},
    "other":    {"icon": "📌", "color": COLORS["other"],   "label": "Other"},
}

STATUS_OPTIONS = [
    "pending",
    "escalate to product",
    "under investigation",
    "known issue",
    "out of scope",
    "dismissed",
]

# ── Paths ─────────────────────────────────────────────────────────────────────
INSIGHTS_PATH = Path("data/insights/insights.json")
REVIEW_LOG_PATH = Path("data/insights/review_log.json")


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_insights() -> list[dict]:
    if INSIGHTS_PATH.exists():
        with open(INSIGHTS_PATH) as f:
            data = json.load(f)
        if data:
            return data
    return _demo_insights()


@st.cache_data(ttl=10)
def load_review_log() -> dict:
    if REVIEW_LOG_PATH.exists():
        with open(REVIEW_LOG_PATH) as f:
            return json.load(f)
    return {}


def save_review(topic_id: str, action: str, note: str = "") -> None:
    log = load_review_log()
    log[topic_id] = {"action": action, "note": note, "reviewed_at": datetime.now().isoformat()}
    REVIEW_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)
    st.cache_data.clear()


# ── Charts ────────────────────────────────────────────────────────────────────
def render_overview(insights: list[dict], review_log: dict) -> None:
    """Clean overview: 4 KPI tiles + 1 focused chart. No clutter."""
    total_posts = sum(i.get("n_posts", 1) for i in insights)
    reviewed = sum(1 for i in insights if str(i.get("topic_id", "")) in review_log)
    flagged = sum(1 for i in insights if i.get("needs_human_review"))
    pending = len(insights) - reviewed

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Posts analyzed", f"{total_posts:,}")
    k2.metric("Insight cards", len(insights))
    k3.metric("Pending review", pending)
    k4.metric("Flagged", flagged, help="Insights Claude flagged as needing human judgment")

    st.divider()

    # Single focused chart: top topics by post volume, colored by category
    sorted_insights = sorted(insights, key=lambda x: x.get("n_posts", 0), reverse=True)[:8]

    labels = []
    for ins in sorted_insights:
        h = ins.get("headline", "")
        labels.append((h[:42] + "…") if len(h) > 42 else h)

    fig = go.Figure(
        go.Bar(
            x=[i.get("n_posts", 0) for i in sorted_insights],
            y=labels,
            orientation="h",
            marker_color=[CATEGORY_META.get(i.get("category", "other"), {}).get("color", COLORS["other"]) for i in sorted_insights],
            hovertemplate="%{y}<br>%{x} posts<extra></extra>",
        )
    )
    fig.update_layout(
        title="Top topics by post volume",
        title_font_size=15,
        xaxis_title="Posts",
        yaxis=dict(autorange="reversed", tickfont_size=12),
        height=320,
        margin=dict(t=48, b=32, l=8, r=16),
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor=COLORS["surface"],
        font=dict(color=COLORS["text"]),
        showlegend=False,
    )
    fig.update_xaxes(gridcolor=COLORS["border"], zeroline=False)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")

    st.plotly_chart(fig, use_container_width=True)


# ── Insight card ──────────────────────────────────────────────────────────────
def render_card(insight: dict, review_log: dict, idx: int) -> None:
    topic_id = str(insight.get("topic_id", idx))
    review = review_log.get(topic_id, {})
    current_status = review.get("action", insight.get("status", "pending"))
    current_note = review.get("note", "")

    cat = insight.get("category", "other")
    meta = CATEGORY_META.get(cat, CATEGORY_META["other"])
    conf = insight.get("confidence", "medium")
    conf_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf, "🟡")
    n_posts = insight.get("n_posts", "?")

    # Header
    col_title, col_status = st.columns([5, 1.5])
    with col_title:
        st.markdown(
            f"**{meta['icon']} {insight.get('headline', 'Untitled')}**  "
            f"<span style='color:{meta['color']};font-size:0.8em'>{meta['label']}</span>  "
            f"&nbsp;{conf_icon} {conf.title()} confidence &nbsp;·&nbsp; {n_posts} posts",
            unsafe_allow_html=True,
        )
    with col_status:
        if insight.get("needs_human_review"):
            st.warning("⚠️ Needs review", icon=None)
        if current_status not in ("pending", ""):
            st.info(current_status.title())

    # Body: 60/40 split
    col_body, col_action = st.columns([3, 2])

    with col_body:
        st.write(insight.get("summary", ""))
        if evidence := insight.get("evidence"):
            st.markdown(f"> {evidence}")

    with col_action:
        if action := insight.get("product_action"):
            st.info(f"💡 {action}")
        if ctx := insight.get("canadian_context"):
            st.caption(f"🍁 {ctx}")
        if flag := insight.get("review_reason"):
            st.caption(f"⚠️ {flag}")

    # Review controls — compact single row
    s_col, n_col, b_col = st.columns([2, 4, 1.5])
    with s_col:
        new_status = st.selectbox(
            "Status",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(current_status) if current_status in STATUS_OPTIONS else 0,
            key=f"status_{topic_id}",
            label_visibility="collapsed",
        )
    with n_col:
        note = st.text_input(
            "Note",
            value=current_note,
            placeholder="Add context, ticket link, or reasoning…",
            key=f"note_{topic_id}",
            label_visibility="collapsed",
        )
    with b_col:
        if st.button("Save", key=f"save_{topic_id}", use_container_width=True):
            save_review(topic_id, new_status, note)
            st.toast("Saved ✓", icon="✅")
            st.rerun()

    st.divider()


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar(insights: list[dict], review_log: dict) -> dict:
    """Returns current filter config."""
    with st.sidebar:
        st.markdown("## 📊 WS Community Intel")
        st.caption("AI finds the signal. You decide what to build.")
        st.divider()

        st.markdown("**Category**")
        selected_cats = {
            cat
            for cat, meta in CATEGORY_META.items()
            if st.checkbox(f"{meta['icon']} {meta['label']}", value=True, key=f"cat_{cat}")
        }

        st.divider()
        st.markdown("**Review status**")
        show_pending = st.checkbox("⏳ Pending", value=True)
        show_actioned = st.checkbox("✅ Actioned", value=False)
        show_dismissed = st.checkbox("🗑️ Dismissed", value=False)

        st.divider()
        st.markdown("**Confidence**")
        conf_filter = set()
        if st.checkbox("🟢 High", value=True):
            conf_filter.add("high")
        if st.checkbox("🟡 Medium", value=True):
            conf_filter.add("medium")
        if st.checkbox("🔴 Low", value=False):
            conf_filter.add("low")

        st.divider()
        flagged_only = st.checkbox("⚠️ Flagged for review only", value=False)

        st.divider()
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        # Reviewed progress
        n_reviewed = sum(1 for i in insights if str(i.get("topic_id", "")) in review_log)
        pct = int(n_reviewed / len(insights) * 100) if insights else 0
        st.divider()
        st.caption(f"Review progress: {n_reviewed}/{len(insights)} ({pct}%)")
        st.progress(pct / 100)

    return {
        "selected_cats": selected_cats,
        "show_pending": show_pending,
        "show_actioned": show_actioned,
        "show_dismissed": show_dismissed,
        "conf_filter": conf_filter,
        "flagged_only": flagged_only,
    }


def apply_filters(insights: list[dict], review_log: dict, filters: dict) -> list[dict]:
    result = []
    for ins in insights:
        cat = ins.get("category", "other")
        conf = ins.get("confidence", "medium")
        tid = str(ins.get("topic_id", ""))
        review = review_log.get(tid, {})
        status = review.get("action", ins.get("status", "pending"))

        if cat not in filters["selected_cats"]:
            continue
        if conf not in filters["conf_filter"]:
            continue
        if filters["flagged_only"] and not ins.get("needs_human_review"):
            continue

        is_pending = status in ("pending", "")
        is_actioned = status not in ("pending", "dismissed", "")
        is_dismissed = status == "dismissed"

        if is_pending and not filters["show_pending"]:
            continue
        if is_actioned and not filters["show_actioned"]:
            continue
        if is_dismissed and not filters["show_dismissed"]:
            continue

        result.append(ins)
    return result


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    insights = load_insights()
    review_log = load_review_log()
    filters = render_sidebar(insights, review_log)

    st.title("Wealthsimple Community Intelligence")
    st.caption(
        "Aggregates Reddit + App Store feedback → AI classifies & synthesizes → "
        "**You decide what to build.**"
    )

    render_overview(insights, review_log)

    filtered = apply_filters(insights, review_log, filters)
    st.markdown(f"### {len(filtered)} insight{'s' if len(filtered) != 1 else ''}")

    if not filtered:
        st.info("No insights match the current filters.")
        return

    for idx, ins in enumerate(filtered):
        render_card(ins, review_log, idx)

    st.caption(
        "**Human-AI split:** AI handles ingestion, topic discovery, sentiment, and insight drafting. "
        "You decide what to act on — because only you have the full strategic, legal, and business context."
    )


def _demo_insights() -> list[dict]:
    """Built-in demo data — dashboard works immediately without running the pipeline."""
    return [
        {
            "topic_id": 1,
            "headline": "Users confused by TFSA over-contribution limits",
            "category": "friction",
            "confidence": "high",
            "summary": (
                "47 posts describe confusion or accidental over-contributions on TFSA accounts. "
                "Users manually track contribution room in spreadsheets because Wealthsimple "
                "doesn't update room in real-time from CRA data. Several report receiving CRA penalty letters."
            ),
            "evidence": (
                "\"I had no idea I was over-contributing — WS showed my balance but not my actual room. "
                "Got an $800 penalty.\" | \"Why can't WS just show my available TFSA room like my bank does?\""
            ),
            "product_action": (
                "Add a TFSA contribution room tracker in account overview. "
                "Let users enter their CRA-confirmed room and show a warning before any deposit that would exceed it."
            ),
            "volume_signal": "47 posts across Reddit + App Store, recurring over 14 months",
            "needs_human_review": True,
            "review_reason": "CRA API integration may have compliance/data-sharing implications",
            "canadian_context": "TFSA over-contribution penalty is 1%/month on excess — real financial harm",
            "n_posts": 47,
            "top_words": "tfsa, contribution, room, limit, cra, over, penalty",
            "status": "pending",
        },
        {
            "topic_id": 2,
            "headline": "Instant deposit limits feel arbitrary and too low",
            "category": "friction",
            "confidence": "high",
            "summary": (
                "Users frequently hit deposit limits ($250-$1,500) and find the process "
                "for increasing them opaque. Many compare unfavorably to competitors offering "
                "higher limits or instant bank verification via Plaid."
            ),
            "evidence": (
                "\"Transferred $5k to buy during the dip, only $250 was instant. Missed the window.\" | "
                "\"Questrade increased my limit after one call. WS support said 'review in 30 days'.\""
            ),
            "product_action": (
                "Build a self-serve instant deposit limit increase flow. "
                "Show users exactly what criteria are checked and let them act on them directly."
            ),
            "volume_signal": "62 posts over 18 months, spikes during market volatility",
            "needs_human_review": False,
            "review_reason": None,
            "canadian_context": "Instant deposit is a key differentiator vs Questrade for active traders",
            "n_posts": 62,
            "top_words": "instant, deposit, limit, increase, transfer, bank",
            "status": "pending",
        },
        {
            "topic_id": 3,
            "headline": "Round-up and auto-invest features driving strong loyalty",
            "category": "win",
            "confidence": "high",
            "summary": (
                "Strong positive sentiment around passive saving features — round-ups, recurring deposits, "
                "and auto-rebalancing. Users credit these for building their first investment portfolio. "
                "High retention signal."
            ),
            "evidence": (
                "\"The round-up feature made me an investor without realizing it.\" | "
                "\"Auto-invest into my TFSA every payday — completely hands off. Love it.\""
            ),
            "product_action": (
                "Extend round-ups to RRSP and FHSA accounts. "
                "Add a savings milestone screen to reinforce positive behavior and boost sharing."
            ),
            "volume_signal": "89 positive mentions, consistent over 2 years",
            "needs_human_review": False,
            "review_reason": None,
            "canadian_context": "FHSA extension would be uniquely relevant for first-time home buyers",
            "n_posts": 89,
            "top_words": "round up, auto invest, recurring, passive, easy, love",
            "status": "pending",
        },
        {
            "topic_id": 4,
            "headline": "Demand for fractional shares on Canadian stocks",
            "category": "roadmap",
            "confidence": "medium",
            "summary": (
                "Significant demand to extend fractional share purchasing to TSX-listed stocks, "
                "not just US equities. Users want to invest exact dollar amounts into high-priced "
                "Canadian stocks like Shopify."
            ),
            "evidence": (
                "\"WS has fractional for US stocks but not Canadian? Shopify is $90 — I want to buy $50 worth.\" | "
                "\"Fractional CAD stocks would make Wealthsimple perfect for small investors.\""
            ),
            "product_action": (
                "Explore extending fractional share infrastructure to TSX-listed securities. "
                "No Canadian broker currently offers this — would be a meaningful differentiator."
            ),
            "volume_signal": "33 posts, growing frequency over last 6 months",
            "needs_human_review": True,
            "review_reason": "TSX fractional shares may have regulatory/settlement complexity under IIROC",
            "canadian_context": "TSX settlement is T+2; fractional mechanics may differ from US markets",
            "n_posts": 33,
            "top_words": "fractional, canadian, shares, tsx, shopify, dollar",
            "status": "pending",
        },
        {
            "topic_id": 5,
            "headline": "App crashes at market open frustrate active traders",
            "category": "friction",
            "confidence": "high",
            "summary": (
                "Multiple reports of instability specifically during market open (9:30 AM ET) "
                "and high-volatility events. Users lose confidence and miss trades — this directly costs money."
            ),
            "evidence": (
                "\"App froze for 20 minutes at open on a volatile day. Couldn't execute my stop-loss.\" | "
                "\"1-star because the app crashes every time there's big news.\""
            ),
            "product_action": (
                "Prioritize load testing at market open. Add a public status page and in-app incident banner. "
                "Consider an order queue that auto-executes on reconnect."
            ),
            "volume_signal": "28 crash reports, concentrated at market open",
            "needs_human_review": False,
            "review_reason": None,
            "canadian_context": None,
            "n_posts": 28,
            "top_words": "crash, freeze, app, open, market, slow, error",
            "status": "pending",
        },
        {
            "topic_id": 6,
            "headline": "FHSA launch praised — driving new account openings",
            "category": "win",
            "confidence": "high",
            "summary": (
                "Wealthsimple's FHSA launch received very positive reception. Users praise WS for "
                "being first to market, and many opened accounts specifically for this feature."
            ),
            "evidence": (
                "\"Opened my WS account just for the FHSA. Finally a broker that moves fast.\" | "
                "\"FHSA on WS is seamless — my bank took 3 months and buried it in a phone call.\""
            ),
            "product_action": (
                "Use FHSA as an acquisition funnel. Build FHSA education content and "
                "a combined FHSA+RRSP tax optimization calculator."
            ),
            "volume_signal": "54 positive mentions in 8 months since launch",
            "needs_human_review": False,
            "review_reason": None,
            "canadian_context": "FHSA is uniquely Canadian (2023 launch). Max $8k/year, $40k lifetime.",
            "n_posts": 54,
            "top_words": "fhsa, home savings, first home, account, easy, great",
            "status": "pending",
        },
    ]


if __name__ == "__main__":
    main()
