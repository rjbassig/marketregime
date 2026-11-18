from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors

ROOT = Path(__file__).resolve().parents[1]

def main():
    out = ROOT / "research" / "marketregime_research.pdf"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=9, leading=13, spaceAfter=8))
    doc = SimpleDocTemplate(str(out), pagesize=letter, rightMargin=.75*inch, leftMargin=.75*inch, topMargin=.7*inch, bottomMargin=.7*inch)
    story = [Paragraph("MarketRegime", styles["Title"]), Paragraph("Chronological Market-Regime and Strategy Evaluation", styles["Heading2"]), Paragraph("Research release 0.1 · Randall Bassig · 2026-11-18", styles["BodySmall"]), Spacer(1, 10)]
    sections = [
      ("Abstract", "This release evaluates whether simple market-state labels add information beyond trend and buy-and-hold baselines. It uses real daily SPY, QQQ, and IWM bars retrieved from Yahoo Finance, adjusted close returns, and a 70/30 chronological split. A trailing-feature rule classifier is compared with a three-state Gaussian mixture fit on training data only. Results are historical research, not investment advice."),
      ("Data and methods", "Each asset contains 4,245 validated observations from 2010-01-04 through 2026-11-17. Features are trailing log return, 20-session annualized volatility, a 20/100 moving-average ratio, momentum, and drawdown. The trend baseline holds above a moving-average ratio of one; the regime-aware rule additionally requires volatility below 35%. The displayed holdout uses next-bar close returns and explicitly zero fees/slippage."),
      ("Verified held-out results", "The QQQ regime-aware rule returned 58.07% with Sharpe 0.69 and maximum drawdown -14.56%, versus 55.43% for its cost-aware trend baseline. SPY regime-aware return was 36.03% with Sharpe 0.62; IWM was -16.01% with Sharpe -0.16. Buy-and-hold returns were 61.96%, 66.02%, and 27.78% respectively. The mixed result does not support a universal regime premium."),
      ("Limitations and reproducibility", "Daily bars do not provide intraday execution precision. Public provider revisions and adjustment conventions can change a rerun. Gaussian mixture labels are descriptive and are not treated as real-time causal signals. Reproduce with scripts/acquire_data.py, scripts/run_research.py, and pytest; exact URLs, retrieval timestamps, and raw hashes are in data/provenance.json and artifacts/summary.json."),
    ]
    for title, body in sections:
        story += [Paragraph(title, styles["Heading2"]), Paragraph(body, styles["BodySmall"]), Spacer(1, 4)]
    table = Table([["Asset","Buy/hold","Trend","Regime-aware","Regime Sharpe"],["SPY","61.96%","36.03%","36.03%","0.62"],["QQQ","66.02%","55.43%","58.07%","0.69"],["IWM","27.78%","-16.01%","-16.01%","-0.16"]], colWidths=[1.2*inch]*5)
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#171c24")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.HexColor("#9aa4b2")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),("PADDING",(0,0),(-1,-1),6)]))
    story += [Paragraph("Summary table", styles["Heading2"]), table]
    doc.build(story)
    print(out)

if __name__ == "__main__": main()

