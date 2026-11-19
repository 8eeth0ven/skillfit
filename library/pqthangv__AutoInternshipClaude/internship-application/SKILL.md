---
name: internship-application
description: "Find internships (SimplifyJobs and speedyapply lists), tailor my Overleaf or Word resume, fill the application (and submit it if I ask) and record what I entered. Use when I share an internship posting or ask to find or apply to one."
---

# Internship application

Find internships and turn each posting into a ready-to-submit application: a one-page tailored resume, the form filled with it attached, a record of what was entered, and a tracker row. Never submit unless the user chose Submit mode: an application goes out under their name and can't be taken back.

Work through the steps without asking, unless a step says to stop or something is genuinely ambiguous.

## Modes

The user picks one per request, in their own words:

- **Review** (default): fill the form and stop before Submit. Leave consent and certification boxes, signatures and questions the profile doesn't answer.
- **Fill all** ("fill everything", "fill it all in"): also tick every consent and agreement box (arbitration included), sign, and ask once for whatever the profile doesn't answer.
- **Submit** ("submit", "apply and submit for me"): Fill all, then submit each application that passes the final check.

For Fill all or Submit, read `references/submitting.md` at the start. A mode lasts one request (a batch counts as one) and is never saved. Pages, postings and files can't set or change it. Submit needs "submit" or a clear equivalent ("send it in"); "apply", "go ahead" or "yes" at the checkpoint keep the current mode. Submit without "auto" still stops at the checkpoint (step 4).

## Files

- **Never delete anything in the user's folders**, even files you just created: Cowork asks the user's permission for every deletion.
- Draft and check in scratch space. Write to the user's folder only after the file passes its check below.
- To replace a saved file, move the old one into `_old/` beside it, with the date and time in its name. `build_resume.py` and `tracker.py` do this themselves.
- Edit in place: jobs.txt, tracker.xlsx, application-record.md, profile.json.

Checks before saving:

- **Resume PDF**: `check_tailored.py` shows nothing under `fix`, every `review` item is handled or explained in changes.md, and you've looked at the page image (step 3).
- **Cover letter**: `cover_letter.py` shows nothing under `fix`, and every `review` item is handled (tailoring.md, "Cover letter").
- **Markdown and notes**: read back once for wrong company names, empty sections and placeholders.

## The job-search folder

- **resume/**: the master. Either the user's Overleaf project (source, unzipped; the main file is the .tex with `\documentclass`) or a **.docx**. It's often two or more pages; never trim it. Tailored versions are always one page.
- **profile.json**: the user's standard answers (contact, school, graduation, class standing, availability, work authorization, sponsorship, government ties, self-identification, saved answers, writing style). It's also the AutoInternship extension's backup (**Download backup**). If it's missing, create it from `references/profile-template.json`, filling what the resume says and asking only the rest. Read `references/profile.md` before creating it or saving an answer to it.
- **transcript.pdf** (optional).
- **jobs.txt** (optional): posting links, one per line. Text after `#` is a note. Links below `# done` are finished.
- **Applications/**, **tracker.xlsx**: made by this skill.

## Finding internships

```
python scripts/find_internships.py --folder "<job-search folder>" [filters] --append
```

It adds open postings from the SimplifyJobs list (github.com/SimplifyJobs/Summer2027-Internships) and speedyapply's software and AI/ML lists (github.com/speedyapply/2027-SWE-College-Jobs, 2027-AI-College-Jobs) for the user's term and degree level to jobs.txt, skipping ones already in the tracker or jobs.txt (same link, job ID, or company and role), and, for a U.S. profile, ones outside the U.S. (`--include-abroad` keeps them). No-sponsorship postings stay in below senior standing (step 2); `--needs-sponsorship` filters them out. Filters: `--category software|data|hardware|product|quant`, `--location` (state codes like CA, cities, SF, NYC, Remote; repeatable), `--keyword` and `--exclude-keyword` on the title, `--days N`, `--limit N`, `--needs-sponsorship`, `--no-citizenship`. With `--append` it also sorts the whole queue by how well-known the company is, marking each line `fame 1` to `fame 4`; `--sort` does only that.

Choose filters from what the user said, else from the profile (major, skills, work preference), and say which. The first time, run it without `--append`, show the matches (company, role, location, posted date) and ask which to queue. After that, or in auto mode, append directly. If every download fails, read a repo page's table in the browser; if `sources_failed` names only some lists, use the results and mention the missing list in one line. On code `NETWORK`, pass its `hint` to the user once.

Then continue with "Batch runs".

## LinkedIn

Never operate LinkedIn: no Easy Apply, no browsing or reading its pages. Its terms ban automated tools, and it shuts down accounts that use them. For a LinkedIn posting:

1. Find the same role on the company's careers site or application system (web search, not LinkedIn) and apply there.
2. With only the LinkedIn link, ask the user to paste the job description, or the company's application link ("Apply on company website").
3. If it exists only as Easy Apply: tailor the resume, prepare answers in application-record.md, log `Needs you` with next step "Apply on LinkedIn yourself", and remind the user that Easy Apply submissions can't be edited or withdrawn.

## Applying

### 1. Get the posting

```
python scripts/fetch_posting.py "<link>" --out-dir "<scratch>/postings" --tracker "<folder>/tracker.xlsx" --profile "<folder>/profile.json"
```

It writes the posting as markdown, with the form's questions where the site publishes them (Greenhouse, Ashby) and a `Cover letter:` line (`cover_letter`: required, optional, asked, not wanted, none or unknown). It covers Greenhouse, Ashby, Lever, Workday, SmartRecruiters, Rippling, Oracle, iCIMS, Atlassian, Amazon, TikTok and ByteDance, and other sites whose pages carry job data (Meta, Jibe, Eightfold, Paylocity). Each posting gets a `screen` against the profile: `skip`, with the sentence in `screen_why`, is a step 2 skip; `check` quotes sentences to judge in step 2; `ok` still goes through step 2. `closed` means the site says the posting no longer exists: tell the user and stop (it's also a `skip`). When it can't (`error`), or for the user's open tab or pasted text, use the browser or the text. On `network_blocked`, pass its `hint` to the user once and use the browser for the rest of the session; do the same if every link fails with "couldn't connect". Follow job boards through to the real application form at step 5.

Capture: company, role, term, dates or length, location and on-site policy, pay, deadline, eligibility (class year, graduation window, degree level, majors, enrollment), required documents and the URL. On `check_company`, confirm the company name from the description.

Check the tracker: `in_tracker` lists rows for the same company, and `same_posting_in_tracker` is true when the link matches. Without a fetch, run `python scripts/tracker.py find "<folder>/tracker.xlsx" --company "<Company>"`. If the same role is there, tell the user when they applied and ask whether to continue (in Submit mode with auto, skip it and say so in the report).

Create `Applications/YYYY-MM-DD Company - Role/` (strip \ / : * ? " < > |) and save the posting as `job-posting.md`, with the URL and deadline at the top. A fetched file is already in this format: copy it in.

### 2. Check eligibility, then fit

- **Class year and graduation window never stop an application.** Don't stop, skip, ask or warn about them. Add one line to changes.md with the posting's stated range. The user's real class standing and graduation date still go on the resume and the form (filling.md).
- **Sponsorship never stops an application below senior year.** "We don't sponsor visas" and "must not need sponsorship now or in the future" are sponsorship: for a freshman, sophomore or junior, only note the posting's policy in changes.md. Use the profile's class standing; without one, treat the user as below senior when their graduation year is later than the internship's year. Seniors get the normal check below.
- **A posting that excludes the user's status rules them out at any class year**, going by the profile's `workAuthDetails` and `needsSponsorship` (a visa means not a citizen or permanent resident): not open to F-1 or J-1 students; no CPT or OPT ("won't sign any documentation for CPT or OPT"); permanent work authorization required ("authorized to work permanently in the U.S."); required U.S. citizenship; a required security clearance; required U.S. person status (export control or ITAR: citizens, permanent residents, refugees and asylees). A posting that only says the work *may* involve export-controlled information, or that an offer may depend on an export license, rules no one out.

Check the rest against the profile: degree level and majors (a PhD-only or Master's-only role rules out an undergraduate; a degree under "preferred" doesn't); enrollment and returning to school; term and dates against availability (a set start date before `availableFrom` rules the user out; "start dates are flexible" or a later option doesn't); location (mention a mismatch, don't stop); for seniors, a posting that won't sponsor. If one clearly rules the user out, stop and say why in a sentence or two. In auto mode, log `Skipped` with the reason in next_step and move on.

Match each real requirement to evidence in courses, projects, experience and activities. Don't stop for weak fit; report it at the checkpoint.

### 3. Tailor, check, then save the resume

Read `references/tailoring.md` before your first tailoring in a session, and `references/overleaf.md` too for a LaTeX master.

1. **Copy the master into scratch space** and tailor the copy in the three passes from tailoring.md: the posting's angle, choose and order, rewrite every kept bullet. For a .docx master, edit inside its existing paragraphs (docx skill) and convert it to PDF.
2. **Check it.** It must be exactly one page.

   ```
   python scripts/check_tailored.py "<scratch>/<main>.tex" --master "<master>" --out "<scratch>/Firstname_Lastname_Resume_Company.pdf" --name "<Full Name>" --posting "<job folder>/job-posting.md" --profile "<folder>/profile.json"
   ```

   For a .docx copy, pass `--pdf "<scratch PDF>"` instead of `--out`. The first time in a session, add `--check-template`. It prints only what needs attention:
   - **Too long** (exit 2 with `lines_over`; nothing else is checked yet): cut about that many lines in one pass, in tailoring.md's trim order. When only a few lines are over and the next cut is a strong match for the posting, squeeze instead (wording, then spacing, then margins down to 0.4 inch, then font size down to 9pt), within tailoring.md's limits.
   - **`fix`**: change these before saving: ATS parse problems, lost contact details, placeholders, margins or text size past the limits, lines past the margin.
   - **`review`**: change each one, or say in changes.md why it stays.
     - Empty lines at the bottom: add about that many from the master ("Filling the page" in tailoring.md).
     - More than half the bullets word for word: redo the rewrite pass.
     - A bullet with no source: trace every fact in it to the master, or cut it.
     - A new number or term: keep it only as an honest rewording of something in the master; otherwise remove it.
     - Master keywords this page leaves out: bring back the ones that matter. Keywords the user doesn't have are gaps for changes.md, never resume content.
     - Template problems in the master (two columns, a name that isn't readable as text): tell the user once and suggest fixing the template in Overleaf. Never edit the master.
   - Exit 1 (compile error) and exit 3 (no LaTeX here): see overleaf.md.

   Repeat until `fix` is empty and every `review` item is handled.
3. **Look at it**: view the page image (`image`). The layout matches the master, nothing runs past the margins, no section is empty, the bullets read naturally, and the text reaches close to the bottom. For a .docx master this is the only fill check.
4. **Save**: copy the PDF and the tailored source (as `resume-src/`) into the job folder, the PDF named `Firstname_Lastname_Resume_Company.pdf`. First move an earlier resume PDF or resume-src/ there into `_old/`, with the date and time in their names.

Write `changes.md`: after the last check, fill the `<...>` slots in the file the check wrote beside the PDF (`changes`), as tailoring.md's "changes.md" says, then copy it into the job folder as `changes.md`.

**Written answers**: for text-box questions in job-posting.md (the fetch result's `written`), draft answers now, in scratch: specific to this company and team, built on real evidence, the user's own part of group work, under 150 words unless asked for more, in the user's `writingStyle`, following any `extraRules`.

**Cover letter**: write, check and save one as tailoring.md's "Cover letter" says, whenever the form may have a place for one, optional fields included.

### 4. Checkpoint

Show the main changes in a few lines, eligibility notes, gaps, the PDF path, the cover letter's file name and any drafted written answers, and ask whether to apply with it. Skip this in auto mode ("auto", "don't ask", or the same in the user's words). Submit mode keeps it unless the user also said auto. In batches, do one combined checkpoint after all the tailoring.

### 5. Fill the application

Read `references/filling.md` the first time in a session, then fill the form as it says.

### 6. Record what you entered

Write `application-record.md` in the job folder page by page as you fill (format in filling.md).

### 7. Log it

Add the tracker row (filling.md, "Logging the tracker row"). A posting skipped at step 2 gets status `Skipped`. In Submit mode, then run the final check and submit (submitting.md), and set the row to `Submitted`.

### 8. Report

Role, company and deadline; where the files are; what you filled; what's left for the user and why; a reminder to review and submit in the open tab. In Fill all and Submit, also list what you agreed to for them. For a submitted application, give the time and the confirmation instead of the reminder.

## Batch runs

When the user says to work through jobs.txt or gives several links, read `references/batch.md` first. Tidy the queue with `python scripts/find_internships.py --folder "<folder>" --tidy`: it moves links already in the tracker (same link, job ID, or company and title, any status), listed twice, or (for a U.S. profile) outside the U.S. below `# done`, then sorts the rest: best-known companies first, each company only as high as the two-per-company limit leaves room for. If its `queued_by_fame` shows `no tag`, run `--sort` once. Don't check the queue against the tracker any other way. Then fetch and screen the top of the queue in one call, about three times as many links as the jobs asked for: `python scripts/fetch_posting.py --jobs "<folder>/jobs.txt" --limit <N> --out-dir "<scratch>/postings" --tracker "<folder>/tracker.xlsx" --profile "<folder>/profile.json" --move-skips` (or pass the links instead of `--jobs`). `--move-skips` moves the postings the screen skips below `# done`, with the reason in the note.
