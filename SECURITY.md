# Security Policy

The EDA-Schema project is maintained by the Drexel University ICE Laboratory.
We appreciate responsible disclosure of security issues.

## Supported Versions

Only the latest release series receives security updates.

## Scope

Examples of security issues include:

* Arbitrary code execution through schema parsing or plugin execution.
* Unsafe deserialization or dynamic evaluation vulnerabilities.
* Denial-of-service attacks caused by malformed or adversarial schema inputs.
* Unauthorized file system access, path traversal, or sandbox escapes.
* Dependency-related vulnerabilities that expose users to remote compromise.
* Leakage of sensitive data through logs, error messages, or exported artifacts.
* Authentication or authorization bypasses in associated tooling or services.

General bugs, documentation issues, and malformed-input validation failures
should be reported through normal GitHub issues instead.

## How to Report

Send a private email to the following addresses:

* **[ps937@drexel.edu](mailto:ps937@drexel.edu)** — Pratik Shrestha (maintainer)
* **[aja367@drexel.edu](mailto:aja367@drexel.edu)** — Alec Aversa (maintainer)
* **[is338@drexel.edu](mailto:is338@drexel.edu)** — Ioannis Savidis (faculty advisor)

Use the subject line: `EDA-schema SECURITY: <short summary>`

Include in your report:

1. **Affected version(s)** — `eda-schema` version and Git commit SHA.
2. **Environment** — OS, Python version, install method (`pip`, source).
3. **Vulnerability class** — see categories above.
4. **Impact** — what an attacker can achieve and under what preconditions.
5. **Reproduction** — minimal proof-of-concept (code, dataset snippet,
   request payload). Encrypt PoCs that contain unsanitized exploits.
6. **Discoverer** — how you would like to be credited (or "anonymous").
7. **Disclosure timeline** — your preferred disclosure date.

We will make a best effort to acknowledge reports and address confirmed
issues in a timely manner.
