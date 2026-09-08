    answer = processor.get_answer()
    if not answer:
        answer = "I'm sorry, I'm taking too long to think. Please try asking again."
        
    return jsonify({"answer": answer})
# ── 7. Admin Dashboard ──
@app.route("/admin")
@admin_required
def admin():
    stats = get_dashboard_stats()
    return render_template("admin.html", stats=stats)
def _fig_to_base64(fig) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor(), transparent=True)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
# ──────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────
import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "="*55)
    print("  Smart Awareness System for Financial Literacy")
    print("="*55 + "\n")
    app.run(host="0.0.0.0", port=port)
