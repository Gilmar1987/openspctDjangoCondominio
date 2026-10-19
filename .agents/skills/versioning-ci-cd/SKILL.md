---
name: versioning-ci-cd
description: "Use when designing, implementing, or reviewing software versioning, release processes, changelogs, Git tags, CI pipelines, continuous delivery, deployment automation, build workflows, or rollback strategies. Detect the project's existing stack and CI/CD provider; do not assume one."
---

# Versioning, CI, and CD

Provide repository-grounded guidance and changes for versioning and delivery workflows. This skill is intentionally technology-neutral: discover the project's existing conventions and tools before recommending or editing anything.

## Operating principles

- Determine the target repository from the user's request and active workspace. Apply implementation changes only to that target. When the skill is installed from this store for a consumer project, do not edit the store/template; edit the store itself only when the user explicitly asks to change the template. If the target is unclear, ask before editing.
- Inspect before proposing: read repository instructions, project metadata, lockfiles, existing workflow definitions, release scripts, tests, and deployment configuration relevant to the request.
- Preserve the existing CI/CD provider and conventions unless the user explicitly asks to migrate them.
- Prefer the smallest change that meets the stated requirement. Do not add a new provider, dependency, registry, environment, or release process without a clear need.
- Keep credentials out of source, logs, examples, and generated files. Use the provider's protected secret store and least-privilege permissions.
- Treat CI as validation and CD as controlled delivery. Never assume a successful build authorizes a production deployment.
- If the project uses OpenSpec, follow its configured rules and change artifacts. When a behavior or release policy needs planning, capture it through the project's OpenSpec workflow before implementation.
- Report assumptions and distinguish observed repository configuration from recommendations.

## 1. Discover the repository

Before editing:

1. Identify the project root and read applicable `AGENTS.md`, `copilot-instructions.md`, and other repository instructions.
2. Detect languages, frameworks, package managers, build/test commands, and the source of the current version from files already present. Examples include `package.json`, lockfiles, `pyproject.toml`, `.csproj`, `Cargo.toml`, `go.mod`, and project-specific version files; do not assume these examples apply.
3. Identify the CI/CD provider and current workflow conventions from existing configuration, such as GitHub Actions, GitLab CI, Azure Pipelines, Jenkins, CircleCI, Buildkite, or another system.
4. Inspect the current branch/release process, tags, changelog, artifact publishing, environments, deployment gates, and rollback mechanism only as relevant to the request.
5. Run read-only status and inspection commands first. Do not overwrite existing user changes.

If critical facts cannot be determined and different choices would change release behavior, ask a focused question before editing. Otherwise, state a reasonable, reversible assumption and keep the solution minimal.

## 2. Git version control and collaboration

- Detect the repository's branch and review model. Preserve the established model (for example, trunk-based development, short-lived feature branches, or GitFlow); do not impose one without agreement.
- Follow existing rules for pull/merge requests, required reviews, protected branches, and CI status checks. Do not weaken protections to make a pipeline pass.
- Follow existing commit message conventions. Use Conventional Commits only when the project already uses them or the user requests them.
- Inspect working-tree and branch state before edits. Preserve unrelated staged, unstaged, and untracked changes.
- Do not rewrite shared history, amend another person's commit, resolve conflicts by discarding content, switch branches, commit, or push unless explicitly requested and authorized.

## 3. Versioning and release policy

- Determine whether the project versions an application, library, API, container image, or multiple deliverables.
- Find the authoritative version source and avoid introducing competing version numbers. Keep manifests, package metadata, tags, release notes, and image tags consistent where applicable.
- Do not impose Semantic Versioning on every project. If the project has a public compatibility contract or the user requests SemVer, use `MAJOR.MINOR.PATCH`:
  - MAJOR for incompatible public changes;
  - MINOR for backward-compatible functionality;
  - PATCH for backward-compatible fixes.
- Follow the existing prerelease, build-metadata, tag-prefix, and release-branch conventions. If none exist, recommend a policy and obtain agreement before automating externally visible releases.
- Generate changelog or release notes from the repository's actual commit/PR conventions. Never claim a change is breaking, compatible, or user-visible without evidence.
- Avoid changing version files automatically on every build unless that is the agreed source-of-truth policy.

## 4. Continuous Integration

Design or update the project's current CI pipeline to give fast, trustworthy feedback. Choose checks based on the actual project and its existing scripts, normally considering:

1. Checkout and runtime/toolchain setup using the versions declared by the project.
2. Dependency installation with the repository's lockfile and reproducible/frozen mode when supported.
3. Formatting/lint and static analysis where configured.
4. Unit and integration tests, with required services provisioned only when necessary.
5. Build/package validation and artifact retention when needed.
6. Security checks appropriate to existing dependencies and permissions.

Pipeline requirements:

- Use least-privilege token permissions, pin third-party actions/plugins according to repository policy, and avoid exposing secrets to untrusted fork code.
- Use caching only when it is safe and keyed by relevant lockfiles/toolchain inputs.
- Add concurrency/cancellation only where it will not interrupt a release or deployment incorrectly.
- Keep required checks deterministic and avoid silently making validation optional.
- Reuse existing scripts rather than duplicating build logic inside YAML when practical.
- Do not invent commands: verify each command against project metadata or existing documentation.

## 5. Continuous Delivery and deployment

When delivery/deployment is in scope:

- Separate validation from deployment and model the project's actual environments (for example, development, staging, production) without requiring these exact names.
- Prefer building an immutable artifact once and promoting the same artifact through environments, rather than rebuilding different bytes for each environment.
- Define explicit triggers, approvals, environment protections, and rollback behavior. Treat production as protected by default.
- Keep deployment credentials in protected environment/secret stores, scope them narrowly, and do not print secrets.
- Consider database/schema migration compatibility and ordering; do not assume application rollback can safely reverse a destructive data migration.
- Include health checks, smoke tests, deployment status, and a documented recovery path when appropriate.
- Do not run a real deployment, publish a release, push tags, or modify remote environments without explicit user authorization for that action. Describe what would happen first and wait for approval if needed.

## 6. Implementation workflow

1. Summarize the current versioning/CI/CD setup with evidence from the repository.
2. Restate the requested outcome and identify unresolved release-impacting decisions.
3. Propose the smallest file-level plan. If the user requested implementation and the choices are clear, make the scoped changes; otherwise ask before selecting a provider or release policy.
4. Edit only the relevant existing workflow and project metadata files. Preserve unrelated configuration and local changes.
5. Validate syntax and configuration with available tooling; run the relevant local checks without publishing, pushing, tagging, or deploying.
6. Review the resulting workflow for secret exposure, excessive permissions, trigger behavior, branch protection assumptions, artifact consistency, and accidental production paths.
7. Report changed files, behavior, validation performed, remaining setup requirements, and any action requiring user authorization.

## Safety boundaries

Never perform these actions without explicit user approval in the current request:

- Deploy to a real environment, especially production.
- Publish packages, container images, or public releases.
- Push commits or tags, create/delete remote branches, or trigger a remote release workflow.
- Replace the CI/CD provider or alter protected branch/environment policies.
- Expose, copy, rotate, or delete credentials.

Do not use destructive Git commands (for example, force-push, hard reset, or deleting tags) as a shortcut. If the user requests such an operation, explain the exact target and consequence and obtain confirmation before proceeding.
