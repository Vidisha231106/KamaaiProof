/**
 * WorkPassport.jsx
 * ─────────────────
 * PDF document component for the KamaaiProof Work Passport.
 * Rendered 100 % client-side via @react-pdf/renderer.
 *
 * Sections:
 *  1. Header      — dark banner, title, generation date
 *  2. Summary     — consistency score (colour-coded), income, months covered
 *  3. Transactions — table of all parsed documents; WhatsApp rows tagged UNVERIFIED
 *  4. Flags        — rendered only when flags array is non-empty
 *  5. Footer       — disclaimer for MFI loan officers
 *
 * Props
 * ─────
 * result  {object}  — the normalised result object produced by transformResult.js
 *   estimatedMonthlyIncome  {number}
 *   consistencyScore        {number}  0-100
 *   monthsCovered           {number}
 *   documents               {Array<{id, source, category, date, amount, verified}>}
 *   flags                   {string[]}
 *   whatsappProvided        {boolean}
 */

import {
  Document,
  Page,
  View,
  Text,
  StyleSheet,
} from "@react-pdf/renderer";

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function toRupees(amount) {
  const n = Number(amount);
  if (!Number.isFinite(n)) return "—";
  // Manual INR formatting (Intl.NumberFormat is not available in PDF renderer)
  const abs = Math.round(Math.abs(n));
  const str = abs.toString();
  let result = "";
  let count = 0;
  for (let i = str.length - 1; i >= 0; i--) {
    if (count > 0 && count % (count === 3 ? 2 : 2) === 0 && count !== 3) {
      result = "," + result;
    }
    if (count === 3) {
      result = "," + result;
    }
    result = str[i] + result;
    count++;
  }
  // Simplified: just insert comma after every 2 digits past the last 3
  // Use a simpler approach for INR
  const formatted = formatINR(abs);
  return (n < 0 ? "-" : "") + "\u20B9" + formatted;
}

function formatINR(n) {
  const s = n.toString();
  if (s.length <= 3) return s;
  const last3 = s.slice(-3);
  const rest = s.slice(0, -3);
  const withCommas = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",");
  return withCommas + "," + last3;
}

function getGenerationDate() {
  const d = new Date();
  const day = String(d.getDate()).padStart(2, "0");
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${day} ${months[d.getMonth()]} ${d.getFullYear()}`;
}

function scoreColor(score) {
  if (score >= 80) return "#166546"; // success green
  if (score >= 50) return "#966103"; // amber/warn
  return "#a32424"; // danger red
}

function scoreLabel(score) {
  if (score >= 80) return "Strong";
  if (score >= 50) return "Moderate";
  return "Low";
}

// ─────────────────────────────────────────────────────────────────────────────
// Styles — all sizes in pt (react-pdf uses points)
// ─────────────────────────────────────────────────────────────────────────────

const S = StyleSheet.create({
  page: {
    fontFamily: "Helvetica",
    fontSize: 9,
    color: "#0a1729",
    backgroundColor: "#f4f7fb",
    paddingTop: 0,
    paddingBottom: 28,
    paddingHorizontal: 0,
  },

  // ── Header ──────────────────────────────────────────────────────────────────
  header: {
    backgroundColor: "#0d1b31",
    paddingHorizontal: 32,
    paddingTop: 28,
    paddingBottom: 22,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
  },
  headerLeft: {
    flexDirection: "column",
  },
  headerKicker: {
    fontSize: 7.5,
    color: "#7bb6ff",
    letterSpacing: 1.4,
    textTransform: "uppercase",
    fontFamily: "Helvetica-Bold",
    marginBottom: 5,
  },
  headerTitle: {
    fontFamily: "Helvetica-Bold",
    fontSize: 20,
    color: "#ecf3ff",
    letterSpacing: -0.4,
  },
  headerSubtitle: {
    fontSize: 8.5,
    color: "#b5c7e1",
    marginTop: 5,
  },
  headerRight: {
    flexDirection: "column",
    alignItems: "flex-end",
  },
  headerDateLabel: {
    fontSize: 7,
    color: "#7bb6ff",
    letterSpacing: 0.8,
    textTransform: "uppercase",
    marginBottom: 2,
  },
  headerDate: {
    fontSize: 9,
    color: "#ecf3ff",
    fontFamily: "Helvetica-Bold",
  },
  headerBadge: {
    marginTop: 6,
    backgroundColor: "#132643",
    borderRadius: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  headerBadgeText: {
    fontSize: 7.5,
    color: "#6ce3d5",
    fontFamily: "Helvetica-Bold",
    letterSpacing: 0.5,
  },

  // ── Body wrapper ────────────────────────────────────────────────────────────
  body: {
    paddingHorizontal: 32,
    paddingTop: 20,
    flexDirection: "column",
  },
  sectionSpacing: {
    marginBottom: 12,
  },

  // ── Section headings ────────────────────────────────────────────────────────
  sectionLabel: {
    fontSize: 7,
    color: "#415a82",
    fontFamily: "Helvetica-Bold",
    letterSpacing: 1.2,
    textTransform: "uppercase",
    marginBottom: 6,
  },

  // ── Summary cards ────────────────────────────────────────────────────────────
  summaryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  summaryCard: {
    flex: 1,
    backgroundColor: "#ffffff",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#c9d6ea",
    padding: 12,
    flexDirection: "column",
    marginRight: 10,
  },
  summaryCardLast: {
    marginRight: 0,
  },
  summaryCardLabel: {
    fontSize: 7.5,
    color: "#3f4f68",
  },
  summaryCardValue: {
    fontSize: 18,
    fontFamily: "Helvetica-Bold",
    letterSpacing: -0.4,
    color: "#0a1729",
    marginTop: 2,
  },
  summaryCardSub: {
    fontSize: 7.5,
    color: "#3f4f68",
    marginTop: 1,
  },
  summaryAccentBar: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: 3,
    backgroundColor: "#167684",
    borderTopLeftRadius: 8,
    borderTopRightRadius: 8,
  },

  // ── Transactions table ──────────────────────────────────────────────────────
  tableSection: {
    flexDirection: "column",
  },
  tableWrap: {
    backgroundColor: "#ffffff",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#c9d6ea",
    overflow: "hidden",
  },
  tableHeader: {
    flexDirection: "row",
    backgroundColor: "#f1f5fc",
    borderBottomWidth: 1,
    borderBottomColor: "#c9d6ea",
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  tableHeaderCell: {
    fontFamily: "Helvetica-Bold",
    fontSize: 6.5,
    color: "#3f4f68",
    letterSpacing: 0.9,
    textTransform: "uppercase",
  },
  tableRow: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: "#e8eef8",
    paddingVertical: 7,
    paddingHorizontal: 10,
  },
  tableRowAlt: {
    backgroundColor: "#f9fbff",
  },
  tableCell: {
    fontSize: 8,
    color: "#0a1729",
  },
  tableCellMuted: {
    fontSize: 8,
    color: "#3f4f68",
  },
  // Column widths (flex values)
  colSource: { flex: 2 },
  colCategory: { flex: 2 },
  colDate: { flex: 1.5 },
  colAmount: { flex: 1.2 },
  colStatus: { flex: 1 },

  // Status badges
  badgeVerified: {
    backgroundColor: "#d4f4e5",
    borderRadius: 20,
    paddingHorizontal: 6,
    paddingVertical: 2,
    alignSelf: "flex-start",
  },
  badgeVerifiedText: {
    fontSize: 6.5,
    color: "#166546",
    fontFamily: "Helvetica-Bold",
    letterSpacing: 0.3,
  },
  badgeUnverified: {
    backgroundColor: "#ffe5e5",
    borderRadius: 20,
    paddingHorizontal: 6,
    paddingVertical: 2,
    alignSelf: "flex-start",
  },
  badgeUnverifiedText: {
    fontSize: 6.5,
    color: "#a32424",
    fontFamily: "Helvetica-Bold",
    letterSpacing: 0.3,
  },
  emptyRow: {
    paddingVertical: 14,
    paddingHorizontal: 10,
  },
  emptyRowText: {
    fontSize: 8,
    color: "#3f4f68",
    textAlign: "center",
  },

  // ── Flags section ────────────────────────────────────────────────────────────
  flagSection: {
    flexDirection: "column",
  },
  flagCard: {
    backgroundColor: "#fff8ec",
    borderRadius: 7,
    borderWidth: 1,
    borderColor: "#f0c878",
    padding: 10,
    marginBottom: 5,
    flexDirection: "row",
    alignItems: "flex-start",
  },
  flagDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#966103",
    marginTop: 2,
    marginRight: 7,
  },
  flagText: {
    flex: 1,
    fontSize: 8.5,
    color: "#5c3b00",
    lineHeight: 1.5,
  },

  // ── Divider ──────────────────────────────────────────────────────────────────
  divider: {
    height: 1,
    backgroundColor: "#c9d6ea",
    marginVertical: 4,
  },

  // ── Footer / disclaimer ──────────────────────────────────────────────────────
  footer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "#0d1b31",
    paddingHorizontal: 32,
    paddingVertical: 12,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  footerText: {
    flex: 1,
    fontSize: 7,
    color: "#b5c7e1",
    lineHeight: 1.6,
    marginRight: 16,
  },
  footerBrand: {
    fontSize: 7.5,
    color: "#7bb6ff",
    fontFamily: "Helvetica-Bold",
    letterSpacing: 0.4,
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function Header({ generatedOn }) {
  return (
    <View style={S.header}>
      <View style={S.headerLeft}>
        <Text style={S.headerKicker}>Work Passport · Official Record</Text>
        <Text style={S.headerTitle}>KamaaiProof</Text>
        <Text style={S.headerSubtitle}>
          Work Passport for India's Informal Workforce
        </Text>
      </View>
      <View style={S.headerRight}>
        <Text style={S.headerDateLabel}>Generated on</Text>
        <Text style={S.headerDate}>{generatedOn}</Text>
        <View style={S.headerBadge}>
          <Text style={S.headerBadgeText}>Algorithmically Generated</Text>
        </View>
      </View>
    </View>
  );
}

function SummarySection({ result }) {
  const scoreCol = scoreColor(result.consistencyScore);
  const scoreTag = scoreLabel(result.consistencyScore);

  return (
    <View style={S.tableSection}>
      <Text style={S.sectionLabel}>Income Summary</Text>
      <View style={S.summaryRow}>
        {/* Estimated Monthly Income */}
        <View style={S.summaryCard}>
          <View style={[S.summaryAccentBar, { backgroundColor: "#0d4da8" }]} />
          <Text style={S.summaryCardLabel}>Estimated Monthly Income</Text>
          <Text style={[S.summaryCardValue, { fontSize: 16 }]}>
            {toRupees(result.estimatedMonthlyIncome)}
          </Text>
          <Text style={S.summaryCardSub}>Average across covered months</Text>
        </View>

        {/* Consistency Score */}
        <View style={S.summaryCard}>
          <View style={[S.summaryAccentBar, { backgroundColor: scoreCol }]} />
          <Text style={S.summaryCardLabel}>Consistency Score</Text>
          <Text style={[S.summaryCardValue, { color: scoreCol }]}>
            {result.consistencyScore}/100
          </Text>
          <Text style={[S.summaryCardSub, { color: scoreCol }]}>
            {scoreTag} — based on 6-month window
          </Text>
        </View>

        {/* Months Covered */}
        <View style={[S.summaryCard, S.summaryCardLast]}>
          <View style={[S.summaryAccentBar, { backgroundColor: "#167684" }]} />
          <Text style={S.summaryCardLabel}>Months of Evidence</Text>
          <Text style={S.summaryCardValue}>
            {result.monthsCovered || 0}/6
          </Text>
          <Text style={S.summaryCardSub}>Months with income records</Text>
        </View>
      </View>
    </View>
  );
}

function TransactionsSection({ documents }) {
  return (
    <View style={S.tableSection}>
      <Text style={S.sectionLabel}>Parsed Documents</Text>
      <View style={S.tableWrap}>
        {/* Table header */}
        <View style={S.tableHeader}>
          <Text style={[S.tableHeaderCell, S.colSource]}>Source</Text>
          <Text style={[S.tableHeaderCell, S.colCategory]}>Category</Text>
          <Text style={[S.tableHeaderCell, S.colDate]}>Date</Text>
          <Text style={[S.tableHeaderCell, S.colAmount]}>Amount</Text>
          <Text style={[S.tableHeaderCell, S.colStatus]}>Status</Text>
        </View>

        {/* Rows */}
        {documents && documents.length > 0 ? (
          documents.map((doc, i) => (
            <View
              key={doc.id || i}
              style={[S.tableRow, i % 2 === 1 ? S.tableRowAlt : null]}
              wrap={false}
            >
              <Text style={[S.tableCell, S.colSource]} numberOfLines={1}>
                {doc.source || "—"}
              </Text>
              <Text style={[S.tableCellMuted, S.colCategory]} numberOfLines={1}>
                {doc.category || "—"}
              </Text>
              <Text style={[S.tableCellMuted, S.colDate]}>
                {doc.date || "—"}
              </Text>
              <Text style={[S.tableCell, S.colAmount]}>
                {toRupees(doc.amount)}
              </Text>
              <View style={S.colStatus}>
                {doc.verified ? (
                  <View style={S.badgeVerified}>
                    <Text style={S.badgeVerifiedText}>Verified</Text>
                  </View>
                ) : (
                  <View style={S.badgeUnverified}>
                    <Text style={S.badgeUnverifiedText}>UNVERIFIED</Text>
                  </View>
                )}
              </View>
            </View>
          ))
        ) : (
          <View style={S.emptyRow}>
            <Text style={S.emptyRowText}>No parsed documents available.</Text>
          </View>
        )}
      </View>
    </View>
  );
}

function FlagsSection({ flags }) {
  if (!flags || flags.length === 0) return null;

  return (
    <View style={S.flagSection}>
      <Text style={S.sectionLabel}>Manual Review Warnings</Text>
      {flags.map((flag, i) => (
        <View key={i} style={S.flagCard} wrap={false}>
          <View style={S.flagDot} />
          <Text style={S.flagText}>{flag}</Text>
        </View>
      ))}
    </View>
  );
}

function Footer() {
  return (
    <View style={S.footer} fixed>
      <Text style={S.footerText}>
        This document is algorithmically generated supporting evidence for MFI
        loan officers. It does not constitute a credit decision. The loan
        officer retains full verification responsibility. KamaaiProof does not
        store raw personally identifiable information.
      </Text>
      <Text style={S.footerBrand}>KamaaiProof · kamaaiproof.in</Text>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main PDF Document export
// ─────────────────────────────────────────────────────────────────────────────

export function WorkPassport({ result }) {
  const generatedOn = getGenerationDate();

  return (
    <Document
      title="KamaaiProof Work Passport"
      author="KamaaiProof"
      subject="Income consistency evidence for informal workers"
      creator="KamaaiProof AI Engine"
      producer="@react-pdf/renderer"
    >
      <Page size="A4" style={S.page}>
        <Header generatedOn={generatedOn} />

        <View style={S.body}>
          <View style={S.sectionSpacing}>
            <SummarySection result={result} />
          </View>
          <View style={S.divider} />
          <View style={S.sectionSpacing}>
            <TransactionsSection documents={result.documents} />
          </View>
          {result.flags && result.flags.length > 0 && (
            <>
              <View style={S.divider} />
              <View style={S.sectionSpacing}>
                <FlagsSection flags={result.flags} />
              </View>
            </>
          )}
        </View>

        <Footer />
      </Page>
    </Document>
  );
}

export default WorkPassport;
