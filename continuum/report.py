"""A portable, accessible methods-first report with no remote resources.

Design contract: technical readers need exact per-trial evidence, raw-ledger
links and explicit missingness. Tables are intentional: two policies and
deterministic candidate repeats do not justify an inferential chart. Sections
map the build-report technical specification to this fixed offline runtime.
"""

from html import escape


CSS = """
:root{color-scheme:light;--ink:#192c35;--muted:#465a63;--paper:#f7f8f5;--line:#c3cdd0;--accent:#15516a}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.65 system-ui,sans-serif}
a{color:var(--accent);text-underline-offset:.18em}a:focus-visible,summary:focus-visible,[tabindex]:focus-visible{outline:3px solid #ad6400;outline-offset:4px}
.skip{position:absolute;top:-100px;left:1rem;padding:.7rem;background:white;z-index:2}.skip:focus{top:1rem}
header,main,footer{max-width:1100px;margin:auto;padding:2rem clamp(1rem,4vw,3rem)}
header{padding-top:3rem;padding-bottom:1rem}.eyebrow{font-size:.78rem;font-weight:750;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
h1{font-size:clamp(2rem,5vw,3.7rem);line-height:1.12;letter-spacing:-.035em;max-width:20ch;margin:.6rem 0 1.25rem}
h2{font-size:1.5rem;line-height:1.3;margin:0 0 1rem}h3{font-size:1.1rem}p{max-width:80ch;margin:.65rem 0 1rem}
nav{display:flex;gap:.55rem 1.1rem;flex-wrap:wrap;margin:1.5rem 0}nav a{padding:.35rem 0}
section{padding:2rem 0;border-top:1px solid var(--line);scroll-margin-top:1rem}.answer{padding:1.4rem;background:white;border-left:5px solid var(--accent);margin:1rem 0}
.status{font-size:.78rem;letter-spacing:.06em;font-weight:750;text-transform:uppercase}.muted,figcaption,caption{color:var(--muted)}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1.3rem;margin:1.5rem 0}.fact strong{display:block;font-size:1.8rem;line-height:1.3}
dl{display:grid;grid-template-columns:minmax(8rem,1fr) 3fr;gap:.5rem 1rem}dt{font-weight:700}dd{margin:0;overflow-wrap:anywhere}
table{border-collapse:collapse;width:100%;background:white;text-align:left;font-size:.92rem}caption{text-align:left;padding:0 0 .7rem;font-weight:600}
th,td{border-bottom:1px solid var(--line);padding:.7rem .8rem;vertical-align:top}th{font-weight:700}thead th{background:#eaf0f1}tbody th{max-width:22rem;overflow-wrap:anywhere}
.scroll{overflow-x:auto;margin:1.2rem 0;padding-bottom:.3rem}.scroll:focus{outline-offset:-3px}.number{font-variant-numeric:tabular-nums;white-space:nowrap}
code{font: .87em ui-monospace,monospace;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eaf0f1;padding:1rem;font-size:.88rem}
details{background:white;border:1px solid var(--line);padding:.8rem 1rem;margin:1rem 0}summary{cursor:pointer;font-weight:700}ul,ol{padding-left:1.4rem}li{margin:.5rem 0}
.tag{display:inline-block;padding:.12rem .45rem;border:1px solid var(--line);border-radius:.2rem;font-size:.75rem;font-weight:700}footer{font-size:.9rem;color:var(--muted);padding-bottom:3rem}
@media(max-width:550px){body{font-size:16px}header,main,footer{padding-left:1rem;padding-right:1rem}dl{grid-template-columns:1fr;gap:.1rem}dd{margin-bottom:.7rem}th,td{padding:.6rem}.facts{grid-template-columns:1fr 1fr}}
@media print{body{background:white;font-size:11pt}header,main,footer{max-width:none;padding:1rem 0}nav,.skip{display:none}.scroll{overflow:visible}table{font-size:9pt}tr,details{break-inside:avoid}a{color:inherit}section{break-before:auto}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
"""


def _e(value):
    return escape(str(value), quote=True)


def _n(value):
    return "Not available" if value is None else format(value, ".10g")


def _table(caption, headings, rows, label):
    head = "".join(f'<th scope="col">{_e(h)}</th>' for h in headings)
    body = "".join("<tr>" + "".join(
        f'<th scope="row">{value}</th>' if index == 0 else f"<td>{value}</td>"
        for index, value in enumerate(row)) + "</tr>" for row in rows)
    return (f'<div class="scroll" tabindex="0" role="region" aria-label="{_e(label)}">'
            f"<table><caption>{_e(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")


def render(snapshot, summary):
    """Render only prevalidated evidence and derived data; escape all input text."""
    from .numerical import OBJECTIVE_INFO
    study = snapshot["study"]
    formula = OBJECTIVE_INFO[study["evaluator"]]["formula"]
    titles = {"CANDIDATE_LOWER": f"{study['candidate']} has the lower confirmation median.",
              "BASELINE_LOWER": f"{study['baseline']} has the lower confirmation median.",
              "TIE": "The confirmation medians are tied.",
              "INCONCLUSIVE": "The comparison is inconclusive."}
    answer = titles[summary["verdict"]]
    reasons = "".join(f"<li>{_e(reason)}</li>" for reason in summary["inconclusive_reasons"])
    reason_html = f"<ul>{reasons}</ul>" if reasons else (
        "<p>All original trials completed, each original phase has equal charged evaluation costs across policies, "
        "and the reserved reproduction sequences match. This permits a descriptive comparison under the frozen rules.</p>")
    group_rows = []
    for row in summary["groups"]:
        group_rows.append([_e(row["phase"].title()) + " · " + _e(row["policy"]),
                           f'{row["completed_trials"]} / {row["scheduled_trials"]}',
                           _n(row["median_best"]), str(row["quality_met_trials"]),
                           str(row["charged_evaluations"]), str(row["recorded_evaluations"]), str(row["failed_attempts"])])
    groups = _table("All phases and policies. Lower best objective is better; partial-group medians are descriptive only.",
                    ["Phase / policy", "Complete / scheduled", "Median best", "Quality met", "Charged units", "Recorded calls", "Failed attempts"],
                    group_rows, "Phase comparison; scroll horizontally for all columns")
    confirmation = _table("Every frozen confirmation seed, including missing or exhausted trials.",
        ["Trial", "State", "Best objective", "Quality threshold met", "Charged units"],
        [[f'<a href="#trial-{_e(row["trial_id"])}">{_e(row["trial_id"])}</a>', _e(row["status"]), _n(row["best"]),
          "Not available" if row["quality_met"] is None else "Yes" if row["quality_met"] else "No", str(row["charged_evaluations"])]
         for row in summary["trials"] if row["phase"] == "confirmation"], "Individual confirmation outcomes")
    attempt_rows = []
    for spec in snapshot["trial_specs"]:
        attempts = [a for a in snapshot["attempts"] if a["trial_id"] == spec["id"]]
        if not attempts:
            attempt_rows.append([f'<span id="trial-{_e(spec["id"])}">{_e(spec["id"])}</span>',
                                 "Not admitted", "PENDING", "0", "0", "Not available", "Not available", "Not available"])
        for i, attempt in enumerate(attempts):
            terminal = attempt["terminal"]
            label = f'<span id="trial-{_e(spec["id"])}">{_e(spec["id"])}</span>' if i == 0 else _e(spec["id"])
            status = terminal["status"] if terminal else "STAGED" if attempt["staged"] else "RUNNING"
            partial = " (partial; ineligible)" if terminal and terminal["status"] != "COMPLETED" else ""
            attempt_rows.append([label, f'<code>{_e(attempt["id"])}</code><br>Attempt {attempt["number"]}',
                f'<strong>{_e(status)}</strong><br>{_e(terminal["reason"] if terminal else "No terminal result yet")}',
                str(attempt["charged_evaluations"]), str(len(attempt["observations"])),
                _n(terminal["best"] if terminal else None) + partial,
                _n(terminal["elapsed_seconds"] if terminal else None), _n(terminal["cpu_seconds"] if terminal else None)])
    ledger = _table("Complete attempt ledger. Failed partial best values are retained and excluded from comparison.",
        ["Trial", "Attempt identity", "Terminal / reason", "Charged units", "Recorded calls", "Best objective", "Elapsed seconds", "CPU seconds"],
        attempt_rows, "Complete attempt ledger; scroll horizontally for accounting and timing")
    reproduction = _table("Reserved reproduction checks every original policy/phase/seed sequence within tolerance 1e-12.",
        ["Source trial", "Fresh reserved trial", "Sequence result"],
        [[_e(row["source_trial_id"]), _e(row["trial_id"]), _e(row["status"])] for row in summary["reproductions"]],
        "Reserved reproduction outcomes")
    control_table = _table("Known-answer and rejection controls are additional to search calls.",
        ["Control", "Expected", "Observed", "Verdict", "Objective calls"],
        [[_e(row["name"]), _e(row["expected"]), _e(row["observed"]), "PASS" if row["passed"] else "FAIL", str(row["objectiveCalls"])]
         for row in snapshot["controls"]], "Evaluator controls")
    limitations = "".join(f"<li>{_e(text)}</li>" for text in summary["limitations"])
    environment = "".join(f"<dt>{_e(key.replace('_', ' ').title())}</dt><dd><code>{_e(value)}</code></dd>"
                          for key, value in snapshot["environment"].items())
    sources = "".join(f'<li><strong>{_e(row["id"])}</strong>: {_e(row["description"])} '
                      f'({_e(row["license"])}). Source locator: <code>{_e(row["locator"])}</code>.</li>'
                      for row in snapshot["source_records"])
    uncertainty_html = ""
    if "uncertainty" in summary:
        uncertainty = summary["uncertainty"]
        interval = "Not estimated" if uncertainty["interval"] is None else " to ".join(_n(x) for x in uncertainty["interval"])
        uncertainty_html = (f'<h3>Paired seed uncertainty</h3><p>{_e(uncertainty["status"])} · '
                            f'{uncertainty["n_pairs"]} original confirmation pairs. Median candidate minus baseline paired best: '
                            f'{_n(uncertainty["median_difference"])}. Descriptive interval: {interval}.</p>'
                            f'<p>{_e(uncertainty["interpretation"])}</p>')
    state = "Terminal evidence complete" if summary["campaign_complete"] else "Campaign in progress"
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<meta name="color-scheme" content="light"><title>Research Continuum — {_e(study['study_id'])}</title><style>{CSS}</style></head>
<body><a class="skip" href="#main">Skip to evidence</a>
<header><div class="eyebrow">Research Continuum · bounded numerical study</div>
<h1>A question, with its evidence intact.</h1>
<p>{_e(study['question'])}</p>
<nav aria-label="Report sections"><a href="#finding">Finding</a><a href="#design">Frozen study</a><a href="#comparison">Comparison</a>
<a href="#ledger">All attempts</a><a href="#reproduction">Reproduction</a><a href="#limits">Limits &amp; next steps</a></nav></header>
<main id="main" tabindex="-1">
<section id="finding" aria-labelledby="finding-title"><div class="status">{_e(state)} · Unreviewed</div>
<div class="answer"><h2 id="finding-title">{_e(answer)}</h2>
<p>Hypothesis relation: <strong>{_e(summary['hypothesis_relation'])}</strong> under this descriptive protocol.
Independent human and qualified domain review: <strong>PENDING</strong>.</p>{reason_html}</div>
<p>The metric is each completed run’s lowest recorded objective, then the median across the frozen confirmation seeds.
Lower is better; the analytic minimum is zero. Deterministic coordinate repeats are implementation checks, not independent stochastic samples.</p>
<div class="facts"><div class="fact"><strong>{summary['recorded_evaluations']:,}</strong>recorded search objective evaluations</div>
<div class="fact"><strong>{summary['charged_evaluations']:,}</strong>charged evaluation units</div>
<div class="fact"><strong>{summary['reserved_evaluations']:,}</strong>reserved evaluation units</div>
<div class="fact"><strong>{summary['failed_attempts']:,}</strong>retained failed attempts</div></div></section>
<section id="design" aria-labelledby="design-title"><h2 id="design-title">The contract was frozen before execution</h2>
<dl><dt>Study revision</dt><dd>{_e(study['study_id'])} · {_e(study['revision'])}</dd>
<dt>Hypothesis</dt><dd>{_e(study['hypothesis'])}</dd><dt>Falsifier</dt><dd>{_e(study['falsifier'])}</dd>
<dt>Objective</dt><dd><code>{_e(formula)}</code>, dimensionless, minimized</dd>
<dt>Closed domain</dt><dd>{_e(study['domain'])}</dd><dt>Candidate start / step</dt><dd>{_e(study['start'])} / {_e(study['initial_step'])}</dd>
<dt>Run allowance</dt><dd>{study['evaluations_per_policy']} evaluations, including boundary duplicates and the candidate initial point</dd>
<dt>Development seeds</dt><dd>{_e(study['development_seeds'])}</dd><dt>Confirmation seeds</dt><dd>{_e(study['confirmation_seeds'])}</dd>
<dt>Quality diagnostic</dt><dd>Best objective ≤ {_e(study['quality_threshold'])}; this is not a significance threshold</dd>
<dt>Attempt limit / timeout</dt><dd>{study['max_attempts_per_trial']} attempts per trial / {study['attempt_timeout_seconds']} seconds per attempt</dd></dl>
<p>Uniform random search draws each coordinate independently from the frozen bounds using the seed. Coordinate refinement tests
+x, −x, +y, −y in order, clips to bounds, accepts strict improvements immediately, and halves the step after a sweep with no improvement.
Fixed-step coordinate search omits the step halving. Grid search visits cell centres in row order on a ceil(sqrt(allowance)) square lattice, stopping at the allowance; an incomplete last row is not area-uniform.
Each policy receives only its own scalar feedback and starts fresh for every run.</p></section>
<section id="comparison" aria-labelledby="comparison-title"><h2 id="comparison-title">Every phase and confirmation outcome is visible</h2>
<p>Confirmation medians answer the frozen question only when every original trial completes, charged costs match within each original phase,
and reserved reproduction succeeds. Development and reproduction summaries provide context. Missing or ineligible trials never receive a zero score.</p>
{groups}{confirmation}{uncertainty_html}<p>Failed attempts can increase costs even when a retry succeeds. Equal admitted allowances and equal consumed costs are different conditions.
Elapsed and CPU time remain separate measurements; these tables do not establish statistical significance.</p></section>
<section id="ledger" aria-labelledby="ledger-title"><h2 id="ledger-title">Failures and retries remain in the ledger</h2>
<p>Admission charges the full allowance. A crash cannot refund it. Recorded calls count only durable observations, so a call interrupted before persistence
may be missing while its allowance stays charged. A retry has a new identity and preserves the previous attempt.</p>{ledger}
<p>Raw points, objective values, full retry references and event transitions are retained in <a href="evidence.json">evidence.json</a>.
The <a href="records.json">versioned records</a> link the question, hypothesis, study, trials, evaluations, reproduction and unreviewed claim.</p></section>
<section id="reproduction" aria-labelledby="reproduction-title"><h2 id="reproduction-title">Fresh reserved runs check the recorded sequences</h2>
<p>Each source trial has a reserved fresh run. Both point and objective sequences must agree at absolute and relative tolerance 1e-12.
These are checks in the same coordinator. A separate freshly installed execution and real independent review remain separate evidence.</p>{reproduction}
<h3>Controls challenge the evaluator</h3>{control_table}<p>{summary['control_objective_calls']} control objective calls are additional to recorded search calls.
Import verification also recomputes objective values and replays each seeded built-in policy; bundled text is never executed.
Operator-invoked validation and report audits perform additional objective calculations outside admitted search; these are audit overhead,
not campaign search calls, and do not debit policy reserves or provide adaptive policy feedback.</p></section>
<section id="limits" aria-labelledby="limits-title"><h2 id="limits-title">Interpret the result within these limits</h2><ul>{limitations}</ul>
<h3>Next steps and open questions</h3><p>Inspect the raw evidence and frozen study, then use the matching release’s documented reproduction workflow in a fresh environment.
Record the actual operator, runtime and unsuccessful outcomes. A qualified reviewer must assess the protocol before treating the result as reviewed research.</p>
<p>Would a separately frozen domain, start or allowance change the descriptive outcome? That requires a new study revision; this report does not tune the present protocol.</p>
<details><summary>Evidence identity, runtime and provenance</summary><dl><dt>Campaign</dt><dd><code>{_e(snapshot['campaign_id'])}</code></dd>
<dt>Created (UTC)</dt><dd>{_e(snapshot['created_at'])}</dd><dt>Study SHA-256</dt><dd><code>{_e(snapshot['study_digest'])}</code></dd>
<dt>Evaluator SHA-256</dt><dd><code>{_e(snapshot['evaluator_digest'])}</code></dd>{environment}</dl><ul>{sources}</ul>
<p><a href="manifest.json">Bundle manifest</a> · <a href="summary.json">Machine-readable summary</a>. Digests detect changes, not authorship or scientific validity.</p></details></section>
</main><footer>Research Continuum · Trusted built-ins, finite budgets, retained evidence. This offline report uses system fonts and no scripts or remote resources.</footer>
</body></html>'''
