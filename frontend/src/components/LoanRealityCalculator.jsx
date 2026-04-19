import { useMemo, useState } from "react";

function toRupees(amount) {
  if (!Number.isFinite(amount)) return "-";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(Math.round(amount));
}

function LoanRealityCalculator() {
  const [loanInput, setLoanInput] = useState("10000");

  const results = useMemo(() => {
    const principal = Number(loanInput) || 0;
    const moneylenderRepayment = principal * 1.6;
    const mfiRepayment = principal * 1.12;
    const savings = moneylenderRepayment - mfiRepayment;

    return {
      principal,
      moneylenderRepayment,
      mfiRepayment,
      savings
    };
  }, [loanInput]);

  return (
    <section className="loan-card" aria-labelledby="loan-calc-heading">
      <div className="card-heading-row">
        <h3 id="loan-calc-heading">Loan Reality Check</h3>
        <p>Rupee comparison only</p>
      </div>

      <label className="field-label" htmlFor="loan-input">
        Loan Amount Needed (Rs)
      </label>
      <input
        id="loan-input"
        className="text-input"
        inputMode="numeric"
        min="0"
        type="number"
        value={loanInput}
        onChange={(event) => setLoanInput(event.target.value)}
      />

      <div className="loan-grid">
        <article className="loan-item">
          <p className="loan-label">Moneylender repayment</p>
          <p className="loan-value danger">{toRupees(results.moneylenderRepayment)}</p>
        </article>
        <article className="loan-item">
          <p className="loan-label">MFI repayment</p>
          <p className="loan-value safe">{toRupees(results.mfiRepayment)}</p>
        </article>
        <article className="loan-item span-two">
          <p className="loan-label">Worker savings</p>
          <p className="loan-value strong">{toRupees(results.savings)}</p>
        </article>
      </div>
    </section>
  );
}

export default LoanRealityCalculator;
