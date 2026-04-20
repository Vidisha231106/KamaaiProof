import { useNavigate } from "react-router-dom";

const STEPS = [
  {
    cue: "Collect",
    title: "Collect your proof",
    detail: "Gather UPI screenshots, utility bills, and payment receipts you already have."
  },
  {
    cue: "Tag",
    title: "Upload and tag",
    detail: "Upload each file and mark what type of document it is."
  },
  {
    cue: "Add",
    title: "Add WhatsApp notes",
    detail: "Paste payment messages if needed. They are labeled as unverified."
  },
  {
    cue: "Generate",
    title: "Generate your passport",
    detail: "The app summarizes your consistency and estimated monthly earning."
  },
  {
    cue: "Share",
    title: "Show it to lenders",
    detail: "Download and carry the result as supporting evidence for loan review."
  }
];

function LandingPage() {
  const navigate = useNavigate();

  return (
    <section className="landing-page" aria-labelledby="landing-hero-heading">
      <header className="hero-panel">
        <div className="hero-content">
          <p className="hero-kicker">Built for informal workers across India</p>
          <h1 id="landing-hero-heading">Turn everyday earnings into bank-ready proof.</h1>
          <p className="hero-copy">
            KamaaiProof helps domestic workers, auto drivers, street vendors, and daily wage earners create
            a portable work passport from documents they already own.
          </p>

          <div className="hero-actions">
            <button className="btn btn-primary btn-large" type="button" onClick={() => navigate("/upload")}>
              Start Building Passport
            </button>
            <a className="btn btn-secondary" href="#how-it-works-heading">
              See how it works
            </a>
          </div>

          <p className="hero-footnote">No jargon. No complicated forms. Just evidence you already have.</p>
        </div>

        <aside className="hero-proof-card" aria-label="What your work passport includes">
          <p className="proof-title">What your work passport shows</p>

          <ul className="proof-list">
            <li>Estimated monthly income in INR</li>
            <li>Consistency score linked to submitted records</li>
            <li>Clear verified and unverified evidence labels</li>
          </ul>

          <div className="hero-metric-grid" aria-label="Quick metrics">
            <article className="hero-metric">
              <p className="hero-metric-value">3+</p>
              <p>Tagged files needed</p>
            </article>
            <article className="hero-metric">
              <p className="hero-metric-value">5 min</p>
              <p>Typical setup time</p>
            </article>
          </div>
        </aside>
      </header>

      <section className="steps-panel" aria-labelledby="how-it-works-heading">
        <div className="panel-heading-row">
          <div>
            <h2 id="how-it-works-heading">How It Works</h2>
            <p>Simple 5-step flow in clear language</p>
          </div>
          <p className="progress-pill">No account setup needed</p>
        </div>

        <ol className="steps-grid">
          {STEPS.map((step, index) => (
            <li key={step.title} className="step-item">
              <div className="step-head">
                <span className="step-index">0{index + 1}</span>
                <span className="step-cue">{step.cue}</span>
              </div>
              <h3>{step.title}</h3>
              <p>{step.detail}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="sdg-row" aria-label="Sustainable Development Goals supported">
        <article className="sdg-badge">
          <p className="sdg-number">SDG 1</p>
          <p className="sdg-title">No Poverty</p>
        </article>
        <article className="sdg-badge">
          <p className="sdg-number">SDG 8</p>
          <p className="sdg-title">Decent Work & Economic Growth</p>
        </article>
      </section>
    </section>
  );
}

export default LandingPage;
