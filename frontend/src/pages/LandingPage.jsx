import { useNavigate } from "react-router-dom";

const STEPS = [
  {
    title: "Collect your proof",
    detail: "Gather UPI screenshots, utility bills, and payment receipts you already have."
  },
  {
    title: "Upload and tag",
    detail: "Upload each file and mark what type of document it is."
  },
  {
    title: "Add WhatsApp notes",
    detail: "Paste payment messages if needed. They are labeled as unverified."
  },
  {
    title: "Generate your passport",
    detail: "The app summarizes your consistency and estimated monthly earning."
  },
  {
    title: "Show it to lenders",
    detail: "Download and carry the result as supporting evidence for loan review."
  }
];

function LandingPage() {
  const navigate = useNavigate();

  return (
    <section className="landing-page">
      <div className="hero-panel">
        <p className="hero-kicker">Built for informal workers across India</p>
        <h1>Turn everyday earnings into bank-ready proof.</h1>
        <p className="hero-copy">
          KamaaiProof helps domestic workers, auto drivers, street vendors, and daily wage earners create a
          portable work passport from documents they already own.
        </p>
        <button className="btn btn-primary" type="button" onClick={() => navigate("/upload")}>
          Start Building Passport
        </button>
      </div>

      <div className="steps-panel" aria-labelledby="how-it-works-heading">
        <div className="panel-heading-row">
          <h2 id="how-it-works-heading">How It Works</h2>
          <p>Simple 5-step flow in clear language</p>
        </div>

        <ol className="steps-grid">
          {STEPS.map((step, index) => (
            <li key={step.title} className="step-item">
              <span className="step-index">0{index + 1}</span>
              <h3>{step.title}</h3>
              <p>{step.detail}</p>
            </li>
          ))}
        </ol>
      </div>

      <div className="sdg-row" aria-label="Sustainable Development Goals supported">
        <article className="sdg-badge">
          <p className="sdg-number">SDG 1</p>
          <p className="sdg-title">No Poverty</p>
        </article>
        <article className="sdg-badge">
          <p className="sdg-number">SDG 8</p>
          <p className="sdg-title">Decent Work & Economic Growth</p>
        </article>
      </div>
    </section>
  );
}

export default LandingPage;
