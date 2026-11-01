# GitHub Submission Guide (Windows, beginner friendly)

Repository: https://github.com/divyapr-27/A3-PS015-TC032

Install Git first: https://git-scm.com/download/win (default options are fine). Open **PowerShell** and check:

```powershell
git --version
```

Tell Git who you are (once per computer):

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

The repository belongs to `divyapr-27`. The person pushing must be the owner or must be added under
GitHub > repository > **Settings > Collaborators**. Git will ask you to sign in through the browser the first time.

## Step 1: Clone the existing repository

```powershell
cd $HOME\Desktop
git clone https://github.com/divyapr-27/A3-PS015-TC032.git
cd A3-PS015-TC032
```

## Step 2: Look at what is already there (do this before copying anything)

```powershell
dir
git log --oneline -5
git branch
```

Note which files already exist (for example `README.md`). **Do not overwrite them blindly.**
If the repository already has a `README.md` or other files, keep a copy of them elsewhere, open both versions and
merge anything you want to keep into the new `README.md`.

## Step 3: Add the project files

Unzip `A3-PS015-TC032.zip` somewhere else (for example `C:\temp\project`). Copy **the contents** of the unzipped
`A3-PS015-TC032` folder into the cloned repository folder (so `app.py` sits directly next to the `.git` folder).
Windows will ask about files with the same name: choose **Compare** or **Skip** and check each one.
Make sure the hidden `.gitignore` and `.streamlit` folder are copied too.

## Step 4: Check the status

```powershell
git status
```

You should see the new files in red under "Untracked files". Nothing from `.venv` or `__pycache__` should appear.

## Step 5: Add and commit

```powershell
git add .
git status
git commit -m "Add explainable connectivity diagnosis app, tests and documentation"
```

## Step 6: Push to the main branch

First check the branch name with `git branch`. If it is `main`:

```powershell
git push origin main
```

(If your branch is called `master`, use `git push origin master`, or rename it with `git branch -M main` first.)
If Git says the remote has changes you do not have, run `git pull origin main`, solve any conflicts, then push again.

## Step 7: Verify the upload

```powershell
git status
git log --oneline -3
git ls-files
```

* `git status` should say "nothing to commit, working tree clean".
* Open https://github.com/divyapr-27/A3-PS015-TC032 in the browser and check that you can see `app.py`, `src/`, `tests/`, `docs/`, `README.md`,
  and that the diagrams in `docs/architecture.md` and `docs/data_flow.md` are drawn.
* Open `docs/proposal/Proposed-structure-hackathon.pdf` to confirm the proposal uploaded.

## Before the final submission checklist

- [ ] Run `python -m pytest -v` on your Windows computer. All tests should pass.
- [ ] Run `python scripts/generate_test_results.py` so `docs/test_results.md` shows your own environment, then commit it.
- [ ] Run the app, take the real screenshots listed in `screenshots/README.md`, save them in `screenshots/`, commit them.
- [ ] Do a real **Live measurement** run on your own network and keep the report.
- [ ] (Planned) Perform the lab fault-injection tests and fill in `docs/test_plan.md` section 5 honestly.
- [ ] Deploy to Streamlit Community Cloud and replace the live demo placeholder in `README.md`.

```powershell
git add .
git commit -m "Add screenshots, test results and live demo link"
git push origin main
```
