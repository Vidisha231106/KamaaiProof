function normalizeAmount(value) {
  const amount = Number(value);
  return Number.isFinite(amount) ? amount : 0;
}

function toArray(value) {
  return Array.isArray(value) ? value : [];
}

export function normalizeParseResponse(payload, uploadedDocs = [], whatsappText = "") {
  const root = payload?.result && typeof payload.result === "object" ? payload.result : payload || {};

  const rawTransactions =
    toArray(root.transactions).length > 0
      ? toArray(root.transactions)
      : toArray(root.records).length > 0
        ? toArray(root.records)
        : toArray(root.documents);

  const transactions =
    rawTransactions.length > 0
      ? rawTransactions.map((item, index) => {
          const category = item.category || item.type || item.documentType || "Unknown";
          const source = item.source || item.sourceType || category;
          const date =
            item.date ||
            item.transactionDate ||
            item.paymentDate ||
            item.monthYear ||
            item.timestamp ||
            "Not provided";

          return {
            id: item.id || `doc-${index + 1}`,
            source,
            category,
            date,
            amount: normalizeAmount(item.amount ?? item.amountDue ?? item.value),
            verified:
              item.unverified === true
                ? false
                : String(item.verificationStatus || "").toLowerCase() !== "unverified" &&
                  !String(category).toLowerCase().includes("whatsapp")
          };
        })
      : uploadedDocs.map((doc, index) => ({
          id: doc.id || `uploaded-${index + 1}`,
          source: doc.file?.name || `Uploaded document ${index + 1}`,
          category: doc.tag || "Unknown",
          date: "Pending extraction",
          amount: 0,
          verified: !String(doc.tag).toLowerCase().includes("whatsapp")
        }));

  const flags = toArray(root.flags).length > 0 ? toArray(root.flags) : toArray(root.warnings);
  const score = Number(root.consistencyScore ?? root.score ?? 0);
  const estimatedMonthlyIncome = normalizeAmount(root.totalIncome ?? root.estimatedMonthlyIncome ?? 0);

  const inferredMonthsCovered = Array.isArray(root.months)
    ? root.months.length
    : Number.isFinite(Number(root.monthsCovered))
      ? Number(root.monthsCovered)
      : Number.isFinite(Number(root.months))
        ? Number(root.months)
        : 0;

  return {
    estimatedMonthlyIncome,
    consistencyScore: Number.isFinite(score) ? Math.max(0, Math.min(100, Math.round(score))) : 0,
    monthsCovered: inferredMonthsCovered,
    documents: transactions,
    flags,
    whatsappProvided: whatsappText.trim().length > 0
  };
}

export function createDemoResult(uploadedDocs = [], whatsappText = "") {
  const today = new Date();
  const fallbackDocs = uploadedDocs.map((doc, index) => ({
    id: doc.id || `demo-${index + 1}`,
    source: doc.file?.name || `Document ${index + 1}`,
    category: doc.tag || "Unknown",
    date: today.toISOString().slice(0, 10),
    amount: 2500 + index * 1500,
    verified: !String(doc.tag).toLowerCase().includes("whatsapp")
  }));

  return {
    estimatedMonthlyIncome: 12000,
    consistencyScore: 78,
    monthsCovered: 5,
    documents: fallbackDocs,
    flags: whatsappText.trim().length
      ? ["WhatsApp payment references are unverified and should be cross-checked."]
      : ["One or more documents need manual verification by a loan officer."],
    whatsappProvided: whatsappText.trim().length > 0
  };
}
