# Security Policy

The **EDA-Schema** project is maintained by the Drexel University Integrated
Circuits and Electronics (ICE) Laboratory. We take security and data-integrity
issues seriously and appreciate responsible disclosure from the research and
open-source community.

---

## Supported Versions

Only the latest **minor** release line receives security fixes. Older lines
must be upgraded.

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

`MAJOR.MINOR.PATCH` follows [Semantic Versioning](https://semver.org/).
Security patches are issued as a `PATCH` bump and recorded in
[`CHANGELOG.md`](CHANGELOG.md) under the `Security` heading.

---

## What Counts as a Security Issue

Report any of the following privately (do **not** open a public Issue):

- **Code execution** — input that allows arbitrary code execution when loading
  a dataset, parsing a Parquet file, deserializing a `dill`/`pickle` blob,
  reading a Protobuf message, or invoking the gRPC service.
- **Data tampering** — flaws that allow undetected modification of dataset
  contents (e.g., schema bypass, checksum bypass).
- **Privilege escalation or sandbox escape** in any shipped script or service.
- **Denial of service** — pathological inputs that cause unbounded memory
  consumption, infinite loops, or process crashes in library APIs.
- **Information disclosure** — accidental exposure of credentials,
  internal hostnames, private dataset paths, or PII inside the source
  distribution, dataset, or examples.
- **Supply-chain integrity** — typosquatting concerns, compromised
  dependencies, malicious build artifacts, or compromised release tags.

The following are **not** treated as security issues — file them as normal
bugs:

- Schema-validation errors on malformed user-supplied data.
- Performance degradation on legitimate large inputs.
- Documentation errors.
- License-classification questions.

---

## How to Report

Send a private email to **both** of the following addresses:

- **ps937@drexel.edu** — Pratik Shrestha (lead maintainer)
- **is338@drexel.edu** — Ioannis Savidis (faculty advisor)

Use the subject line: `SECURITY: <short summary>`

Include in your report:

1. **Affected version(s)** — `eda-schema` version and Git commit SHA.
2. **Environment** — OS, Python version, install method (`pip`, source).
3. **Vulnerability class** — see categories above.
4. **Impact** — what an attacker can achieve and under what preconditions.
5. **Reproduction** — minimal proof-of-concept (code, dataset snippet,
   request payload). Encrypt PoCs that contain unsanitized exploits.
6. **Discoverer** — how you would like to be credited (or "anonymous").
7. **Disclosure timeline** — your preferred disclosure date.

If you require encrypted communication, request a current PGP key in your
first email and we will respond with one.

GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
is enabled on the repository as an alternative channel:
<https://github.com/drexel-ice/eda-schema/security/advisories/new>.

---

## Our Process

| Stage | Target time |
|---|---|
| Acknowledge receipt of report | within **3 business days** |
| Initial triage and severity assessment (CVSS v3.1) | within **7 business days** |
| Status update to reporter | at least **every 14 days** until resolved |
| Coordinated fix and CVE request (if applicable) | typically within **90 days** |
| Public advisory and patched release | coordinated with reporter |

We will:

1. Confirm the vulnerability and determine affected versions.
2. Develop and test a fix in a private branch.
3. Request a CVE through GitHub Security Advisories when warranted.
4. Publish the fix in a `PATCH` release on PyPI and GitHub.
5. Disclose the advisory and credit the reporter (unless anonymity is
   requested).

We follow a **coordinated disclosure** model. Please do not publicly disclose
the issue, post proof-of-concept code, or share details with third parties
until a fix is released and the advisory is published, except as required by
law.

---

## Safe-Harbor Statement

We will not pursue legal action against, or initiate law-enforcement
investigation of, security researchers who:

1. Make a good-faith effort to comply with this policy.
2. Avoid privacy violations, destruction of data, and interruption or
   degradation of services.
3. Use only the minimum interaction with the system necessary to demonstrate
   the issue.
4. Give us a reasonable amount of time to respond before any public
   disclosure.

This safe harbor does not apply to actions that violate Drexel University
policy, U.S. federal or state law, or applicable international law.

---

## Hall of Fame

Researchers who responsibly disclose verified vulnerabilities will be
acknowledged in the [`CHANGELOG.md`](CHANGELOG.md) `Security` section and in
the corresponding GitHub Security Advisory, unless they request anonymity.

---

## Out-of-Scope: Dataset Content

The published EDA-Schema dataset is derived from open benchmarks (IWLS'05,
OpenCores, IBEX) and open-source PDKs. Concerns about the **content** of
those upstream sources should be reported to the respective upstream
maintainers. Concerns about how this project **packages, processes, or
distributes** that content are in scope for this policy.

---

## Contact Summary

| Channel | Use |
|---|---|
| ps937@drexel.edu, is338@drexel.edu | Private vulnerability reports |
| GitHub Security Advisories | Private vulnerability reports (alternative) |
| <https://github.com/drexel-ice/eda-schema/issues> | Non-security bugs |
| <https://github.com/drexel-ice/eda-schema/discussions> | Questions, feature requests |
