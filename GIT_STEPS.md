# GitHub workflow (Windows / VS Code)

1. Download/extract the official challenge repository and preserve its `dataset/`.
2. Copy this project's `code/`, `tests/`, `prompts/`, and docs into that repository.
3. Open the official repository folder in VS Code → Terminal → New Terminal.
4. Check current Git setup:

```powershell
git status
git remote -v
```

If already cloned, do not run `git init` again.

5. Create a branch:

```powershell
git switch -c feature/ghost-data-audit
```

6. Review and commit source (never add `.env` or credentials):

```powershell
git add code tests prompts README.md GIT_STEPS.md .gitignore .env.example requirements-optional.txt
git status
git commit -m "Build evidence-grounded deletion audit agent"
```

7. Push to your own fork/repository:

```powershell
git push -u origin feature/ghost-data-audit
```

If `origin` does not exist, create an empty repository on GitHub and run:

```powershell
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin feature/ghost-data-audit
```

Replace the placeholders. Do not push directly to `interviewstreet` unless you have write access.
`output.csv` is ignored by default; if the challenge requires committing it, validate first and
deliberately force-add it with `git add -f output.csv`.
