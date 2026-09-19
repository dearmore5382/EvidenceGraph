import { useEffect, useState, type FormEvent } from "react";
import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionHashVariant } from "genlayer-js/types";
import {
  ArrowRight,
  BadgeCheck,
  Check,
  ChevronRight,
  CircleAlert,
  FileCheck2,
  GitBranch,
  Menu,
  Network,
  Search,
  ShieldCheck,
  Swords,
  Wallet,
  X,
} from "lucide-react";
import deployment from "./deployment.json";

type Provider = NonNullable<Parameters<typeof createClient>[0]>["provider"];
type Evidence = {
  role: string;
  owner: string;
  repository: string;
  commit: string;
  path: string;
  sha256: string;
};
type CaseRecord = {
  id: number;
  title: string;
  claim: string;
  criteria: string;
  creator: string;
  status: string;
  verdict: string;
  evidence: Evidence[];
  observation: string;
  challenger: string;
  challenge_reason: string;
};
const address = deployment.contractAddress as `0x${string}`;
const configured =
  /^0x[a-fA-F0-9]{40}$/.test(address) && !/^0x0{40}$/.test(address);
const reader = createClient({ chain: studionet });
const demo: CaseRecord = {
  id: 42,
  title: "Milestone 2 delivery",
  claim:
    "Project Alpha completed all four deliverables required by the sealed milestone plan.",
  criteria:
    "Each deliverable must be explicitly identified as completed and accepted. Future intent, partial work, or ambiguous status is insufficient.",
  creator: "0x4a12…89ef",
  status: "ASSESSED",
  verdict: "SUPPORTED",
  challenger: "",
  challenge_reason: "",
  observation: "",
  evidence: [
    {
      role: "SUPPORT",
      owner: "acme-labs",
      repository: "grant-alpha",
      commit: "81f4a9d2c072d888e43cb16cfa2c8db95ee5e130",
      path: "reports/milestone-2.md",
      sha256: "b13d…a991",
    },
    {
      role: "SUPPORT",
      owner: "acme-labs",
      repository: "grant-alpha",
      commit: "81f4a9d2c072d888e43cb16cfa2c8db95ee5e130",
      path: "evidence/acceptance.md",
      sha256: "0c44…621e",
    },
  ],
};
const short = (v: string) =>
  v.length > 16 ? `${v.slice(0, 8)}…${v.slice(-6)}` : v;

export default function App() {
  const [page, setPage] = useState<"home" | "explore" | "build">("home");
  const [menu, setMenu] = useState(false);
  const [wallet, setWallet] = useState("");
  const [busy, setBusy] = useState(false);
  const [caseId, setCaseId] = useState("0");
  const [record, setRecord] = useState<CaseRecord>(demo);
  const [challenge, setChallenge] = useState(false);
  const [toast, setToast] = useState("");
  function go(next: "home" | "explore" | "build") {
    setPage(next);
    setMenu(false);
    setChallenge(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
    history.pushState({}, "", next === "home" ? "/" : `/${next}`);
  }
  function message(text: string) {
    setToast(text);
    window.setTimeout(() => setToast(""), 4200);
  }
  async function connect() {
    try {
      if (!configured)
        throw new Error(
          "Contract deployment is pending. Wallet writes unlock after the verified address is configured.",
        );
      const provider = (window as unknown as { ethereum?: Provider }).ethereum;
      if (!provider) throw new Error("Install an EIP-1193 wallet to connect.");
      await provider.request({
        method: "wallet_switchEthereumChain",
        params: [{ chainId: `0x${studionet.id.toString(16)}` }],
      });
      const accounts = (await provider.request({
        method: "eth_requestAccounts",
      })) as string[];
      setWallet(accounts[0] ?? "");
      message("Wallet connected to StudioNet.");
    } catch (error) {
      message(
        error instanceof Error ? error.message : "Wallet connection failed.",
      );
    }
  }
  async function loadCase(event?: FormEvent) {
    event?.preventDefault();
    if (!configured) {
      setRecord(demo);
      go("explore");
      message(
        "Showing the interactive demo. Live lookup unlocks after deployment.",
      );
      return;
    }
    setBusy(true);
    try {
      const raw = await reader.readContract({
        address,
        functionName: "get_case",
        args: [BigInt(caseId)],
        transactionHashVariant: TransactionHashVariant.LATEST_FINAL,
      });
      setRecord(JSON.parse(String(raw)) as CaseRecord);
      go("explore");
      message(`Loaded case ${caseId} from StudioNet.`);
    } catch (error) {
      message(error instanceof Error ? error.message : "Case lookup failed.");
    } finally {
      setBusy(false);
    }
  }
  async function write(method: string, args: (string | bigint)[]) {
    if (!configured) {
      message(
        "Live contract actions unlock after the reviewed deployment address is configured.",
      );
      return;
    }
    if (!wallet) {
      message("Connect your StudioNet wallet first.");
      return;
    }
    const provider = (window as unknown as { ethereum?: Provider }).ethereum;
    if (!provider) {
      message("Wallet provider is unavailable.");
      return;
    }
    setBusy(true);
    try {
      const client = createClient({
        chain: studionet,
        account: wallet as `0x${string}`,
        provider,
      });
      const hash = await client.writeContract({
        address,
        functionName: method,
        args,
        value: 0n,
        leaderOnly: false,
      });
      message(
        `Submitted once: ${String(hash)}. Wait for finality before another action.`,
      );
    } catch (error) {
      message(error instanceof Error ? error.message : "Transaction failed.");
    } finally {
      setBusy(false);
    }
  }
  function createCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    void write("create_case", [
      String(data.get("title")),
      String(data.get("claim")),
      String(data.get("criteria")),
    ]);
  }
  function addEvidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    void write("add_evidence", [
      BigInt(record.id),
      record.status === "CHALLENGED" ? "COUNTER" : String(data.get("role")),
      String(data.get("owner")),
      String(data.get("repository")),
      String(data.get("commit")),
      String(data.get("path")),
      String(data.get("sha256")),
    ]);
  }
  function sealCase() {
    void write("seal_case", [BigInt(record.id)]);
  }
  function assessCase() {
    void write("assess_case", [BigInt(record.id)]);
  }
  function openChallenge() {
    if (record.status !== "ASSESSED") {
      message("Only an assessed case can be challenged.");
      return;
    }
    setChallenge(true);
  }
  function submitChallenge(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    void write("open_challenge", [
      BigInt(record.id),
      String(data.get("reason")),
    ]);
    setChallenge(false);
  }
  useEffect(() => {
    const route = () =>
      setPage(
        location.pathname === "/build"
          ? "build"
          : location.pathname === "/explore"
            ? "explore"
            : "home",
      );
    route();
    addEventListener("popstate", route);
    return () => removeEventListener("popstate", route);
  }, []);

  return (
    <div className="site">
      <header className="topbar">
        <button className="brand" onClick={() => go("home")}>
          <img src="/evidence-graph-logo.png" />
          <span>EvidenceGraph</span>
        </button>
        <nav className={menu ? "open" : ""}>
          <button onClick={() => go("home")}>How it works</button>
          <button onClick={() => go("explore")}>Explore a case</button>
          <button onClick={() => go("build")}>Build a case</button>
          <button
            onClick={() =>
              message(
                "Repository link will be enabled after the first verified push.",
              )
            }
          >
            <GitBranch />
            GitHub
          </button>
        </nav>
        <div className="top-actions">
          <button
            className="connect"
            onClick={() => void connect()}
            disabled={busy}
          >
            <Wallet />
            {wallet ? short(wallet) : "Connect wallet"}
          </button>
          <button
            className="menu"
            aria-label="Toggle menu"
            onClick={() => setMenu(!menu)}
          >
            {menu ? <X /> : <Menu />}
          </button>
        </div>
      </header>
      {page === "home" && (
        <main>
          <section className="hero">
            <div className="hero-copy">
              <p className="eyebrow">
                <i /> ONCHAIN CLAIM VERIFICATION
              </p>
              <h1>
                Turn scattered evidence into a <em>verifiable decision.</em>
              </h1>
              <p className="lede">
                Seal a claim, bind it to immutable GitHub sources, and let
                independent validators build a transparent evidence graph.
              </p>
              <div className="hero-actions">
                <button className="primary" onClick={() => go("build")}>
                  Build an evidence case <ArrowRight />
                </button>
                <button className="secondary" onClick={() => void loadCase()}>
                  Explore the live flow <ChevronRight />
                </button>
              </div>
              <div className="trust">
                <span>
                  <ShieldCheck />
                  Digest verified
                </span>
                <span>
                  <Network />
                  Validator consensus
                </span>
                <span>
                  <GitBranch />
                  Commit pinned
                </span>
              </div>
            </div>
            <div className="hero-visual">
              <div className="orbit orbit-a" />
              <div className="orbit orbit-b" />
              <div className="claim-card">
                <span>SEALED CLAIM</span>
                <b>Milestone requirements were completed.</b>
                <small>Criteria locked · sources immutable</small>
              </div>
              <div className="proof proof-a">
                <FileCheck2 />
                <div>
                  <b>Delivery report</b>
                  <span>SUPPORTS</span>
                </div>
              </div>
              <div className="proof proof-b">
                <FileCheck2 />
                <div>
                  <b>Acceptance log</b>
                  <span>SUPPORTS</span>
                </div>
              </div>
              <div className="consensus">
                <BadgeCheck />
                <div>
                  <small>CONSENSUS</small>
                  <b>SUPPORTED</b>
                </div>
              </div>
            </div>
          </section>
          <section className="problem">
            <div>
              <p className="eyebrow">WHY EVIDENCEGRAPH</p>
              <h2>
                A digest proves the bytes.
                <br />
                It does not prove the claim.
              </h2>
            </div>
            <p>
              EvidenceGraph combines cryptographic integrity with bounded
              semantic judgment. Validators fetch the exact source
              independently, recompute its digest, then classify only its
              relationship to the sealed claim.
            </p>
          </section>
          <section className="steps">
            <article>
              <span>01</span>
              <GitBranch />
              <h3>Bind exact sources</h3>
              <p>
                Only commit-pinned Raw GitHub documents with expected SHA-256
                digests are accepted.
              </p>
            </article>
            <article>
              <span>02</span>
              <Network />
              <h3>Recompute and assess</h3>
              <p>
                Every validator fetches the bytes, checks integrity, and
                independently classifies each source.
              </p>
            </article>
            <article>
              <span>03</span>
              <Swords />
              <h3>Challenge transparently</h3>
              <p>
                An independent wallet can append one counter-source without
                rewriting the original evidence.
              </p>
            </article>
          </section>
          <section className="lookup">
            <div>
              <p className="eyebrow">PUBLIC CASE LOOKUP</p>
              <h2>
                Inspect the reasoning,
                <br />
                not just the verdict.
              </h2>
            </div>
            <form onSubmit={loadCase}>
              <label>
                Case ID
                <input
                  value={caseId}
                  onChange={(e) => setCaseId(e.target.value)}
                  inputMode="numeric"
                  aria-label="Case ID"
                />
              </label>
              <button disabled={busy}>
                <Search />
                Open case
              </button>
            </form>
          </section>
        </main>
      )}
      {page === "explore" && (
        <main className="case-page">
          <button className="back" onClick={() => go("home")}>
            ← Back to overview
          </button>
          <section className="case-heading">
            <div>
              <p className="eyebrow">
                CASE {String(record.id).padStart(4, "0")} · {record.status}
              </p>
              <h1>{record.title}</h1>
              <p>{record.claim}</p>
            </div>
            <div className="result">
              <BadgeCheck />
              <span>CONSENSUS OUTCOME</span>
              <b>{record.verdict.replaceAll("_", " ")}</b>
              <small>{record.evidence.length} immutable sources</small>
            </div>
          </section>
          <section className="evidence-story">
            <div className="sealed">
              <span>SEALED CLAIM</span>
              <h2>{record.claim}</h2>
              <p>{record.criteria}</p>
            </div>
            <div className="evidence-list">
              {record.evidence.map((item, index) => (
                <article key={`${item.commit}${item.path}`}>
                  <span>0{index + 1}</span>
                  <div>
                    <small>{item.role}</small>
                    <h3>{item.path}</h3>
                    <p>
                      {item.owner}/{item.repository}
                    </p>
                    <code>{short(item.commit)}</code>
                  </div>
                  <Check />
                </article>
              ))}
            </div>
          </section>
          <section className="case-actions">
            <div>
              <ShieldCheck />
              <p>
                Sources are fetched from their exact commits and SHA-256 digests
                are recomputed before semantic assessment.
              </p>
            </div>
            <button
              className="challenge-button"
              onClick={openChallenge}
              disabled={record.status !== "ASSESSED"}
            >
              <Swords />
              {record.status === "RESOLVED"
                ? "Challenge resolved"
                : "Open challenge"}
              {record.status === "ASSESSED" && <ArrowRight />}
            </button>
          </section>
          <section className="lifecycle-panel">
            <div>
              <p className="eyebrow">ONCHAIN ACTIONS</p>
              <h2>Advance this case</h2>
              <p>
                Available actions follow the authoritative lifecycle returned by
                the contract.
              </p>
            </div>
            {(record.status === "DRAFT" || record.status === "CHALLENGED") && (
              <form onSubmit={addEvidence}>
                <label>
                  Role
                  <select name="role" disabled={record.status === "CHALLENGED"}>
                    <option>SUPPORT</option>
                    <option>CONTEXT</option>
                    <option>COUNTER</option>
                  </select>
                </label>
                <label>
                  GitHub owner
                  <input name="owner" required />
                </label>
                <label>
                  Repository
                  <input name="repository" required />
                </label>
                <label>
                  Full commit SHA
                  <input name="commit" pattern="[a-fA-F0-9]{40}" required />
                </label>
                <label>
                  Path at commit
                  <input name="path" required />
                </label>
                <label>
                  Expected SHA-256
                  <input name="sha256" pattern="[a-fA-F0-9]{64}" required />
                </label>
                <button className="primary">Add immutable evidence</button>
              </form>
            )}
            {record.status === "DRAFT" && (
              <button className="primary" onClick={sealCase}>
                Seal case
              </button>
            )}
            {(record.status === "SEALED" || record.status === "CHALLENGED") && (
              <button className="primary" onClick={assessCase}>
                Run validator assessment
              </button>
            )}
            {record.status === "RESOLVED" && (
              <div className="resolved-note">
                <BadgeCheck />
                <div>
                  <b>This challenge is resolved.</b>
                  <span>No further writes are available for this case.</span>
                </div>
              </div>
            )}
          </section>
        </main>
      )}
      {page === "build" && (
        <main className="build-page">
          <section className="build-intro">
            <p className="eyebrow">CREATE A VERIFICATION CASE</p>
            <h1>Start with a claim that can be proven—or falsified.</h1>
            <p>
              The claim and criteria become immutable after sealing. Evidence is
              added as exact repository coordinates, never arbitrary URLs.
            </p>
            <ol>
              <li className="active">
                <span>1</span>
                <div>
                  <b>Frame the claim</b>
                  <small>Create a draft case</small>
                </div>
              </li>
              <li>
                <span>2</span>
                <div>
                  <b>Bind evidence</b>
                  <small>Add two or three sources</small>
                </div>
              </li>
              <li>
                <span>3</span>
                <div>
                  <b>Seal and assess</b>
                  <small>Trigger validator consensus</small>
                </div>
              </li>
            </ol>
          </section>
          <form className="builder" onSubmit={createCase}>
            <div className="form-head">
              <span>STEP 01</span>
              <h2>Claim and proof boundary</h2>
              <p>
                Be specific enough that contrary evidence could change the
                outcome.
              </p>
            </div>
            <label>
              Case title
              <input
                name="title"
                placeholder="Example: Milestone 2 delivery"
                maxLength={120}
                required
              />
            </label>
            <label>
              Sealed claim
              <textarea
                name="claim"
                placeholder="State the exact proposition validators should evaluate."
                maxLength={1600}
                required
              />
            </label>
            <label>
              Evaluation criteria
              <textarea
                name="criteria"
                placeholder="Define sufficient evidence and what would falsify the claim."
                maxLength={1600}
                required
              />
            </label>
            <div className="guardrail">
              <CircleAlert />
              <div>
                <b>Draft first, evidence second</b>
                <span>
                  After this transaction finalizes, use the returned case ID to
                  bind immutable sources.
                </span>
              </div>
            </div>
            <button className="primary" disabled={busy}>
              {wallet ? "Create draft case" : "Create draft — wallet required"}
              <ArrowRight />
            </button>
            <output>
              {configured
                ? "Connected to the configured StudioNet contract."
                : "Preview mode · deployment address pending"}
            </output>
          </form>
        </main>
      )}
      <footer>
        <div>
          <img src="/evidence-graph-logo.png" />
          <b>EvidenceGraph</b>
        </div>
        <p>Integrity before interpretation. Evidence before outcome.</p>
        <span>
          StudioNet · {deployment.liveAuditVerified ? "live verified · " : ""}
          {configured ? short(address) : "deployment pending"}
        </span>
      </footer>
      {challenge && (
        <div className="modal-backdrop" onClick={() => setChallenge(false)}>
          <form
            className="modal"
            onSubmit={submitChallenge}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="modal-close"
              aria-label="Close challenge form"
              onClick={() => setChallenge(false)}
            >
              <X />
            </button>
            <Swords />
            <p className="eyebrow">INDEPENDENT REVIEW</p>
            <h2>Challenge case {record.id}</h2>
            <p>
              Explain why a commit-pinned counter-source could change this
              outcome.
            </p>
            <label>
              Challenge reason
              <textarea
                name="reason"
                minLength={12}
                maxLength={900}
                required
                autoFocus
              />
            </label>
            <button className="primary" disabled={busy}>
              Open challenge <ArrowRight />
            </button>
          </form>
        </div>
      )}
      {toast && (
        <div className="toast" role="status">
          <CircleAlert />
          {toast}
          <button aria-label="Dismiss message" onClick={() => setToast("")}>
            <X />
          </button>
        </div>
      )}
    </div>
  );
}
