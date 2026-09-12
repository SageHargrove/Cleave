# Troubleshooting

After this page the common first-week problems have a cause and a fix.

Each item is a symptom, what is going on, and what to do. If yours is not here,
[report it](#reporting-a-problem).

## The browser did not open

**Symptom.** `cleave` prints `Cleave running at http://127.0.0.1:<port>/#token=...`
and nothing else happens.

**Cause.** No default browser is registered, the terminal is remote or
headless, or you started it with `cleave --no-browser`.

**Fix.** Copy the whole printed address, fragment included, into a browser on
the same machine. The `#token=` part is the session; without it you get a
screen asking for it, and pasting the printed address into that box also
works. Cleave only listens on `127.0.0.1`, so a browser on another machine
cannot reach it, by design.

## The tab says the session ended

**Symptom.** A page saying "Session ended: the local server was stopped or
restarted".

**Cause.** Every launch of `cleave` mints a new session token; the tab you have
belongs to a server that is no longer running (you pressed `Ctrl+C`, the
terminal closed, the machine slept long enough for the process to be killed).
Nothing is lost: everything is in the project file.

**Fix.** Run `cleave` again and use the tab it opens. Old tabs and bookmarks
will not work.

## The port is in use

**Symptom.** `cleave --port 8787` fails to start with an address-in-use error.

**Cause.** Something else, often a previous `cleave`, is listening on that port.

**Fix.** Stop the other process, pick another port, or run `cleave` with no
`--port` and let the system choose a free one.

## The wizard refuses a file

**Symptom.** A file is rejected at the first step, or every row of it is
quarantined.

**Causes and fixes**, most common first:

- **Wrong profile.** The file's name does not match any pattern in the chosen
  profile (`*users*`, `*groups*` and so on), or matches the wrong one. Check
  which input type the wizard assigned each file and correct it, or rename the
  file. [Profiles](import.md#profiles) lists what each expects.
- **Wrong delimiter or encoding.** Cleave detects commas, semicolons, tabs and
  pipes, and UTF-8 or Windows-1252. A file in another encoding, or a
  tab-delimited AD dump fed to a profile expecting commas, reads as one column.
  Re-export as UTF-8 CSV, or customise the profile's delimiter.
- **The header is not where the profile expects, or the columns are named
  differently.** The mapping editor on the first step shows what the wizard
  found; map the columns it could not.
- **Everything is quarantined for a blank key.** The key column the profile
  names is empty in your export (or is named differently). Change the profile's
  key column, or add the column to the export.
- **The sample project refuses it.** "The sample project accepts only the files
  cleave-sample writes." You are importing your own data into the sample
  project. Create a regular project for it ([The sample project](import.md#the-sample-project)).
- **The Quarantine CSV.** Whatever the reason, download it from the Preview
  step: every quarantined row with its reason, source file and row number, which
  is what you take back to whoever produced the export.

## No outliers appear

**Symptom.** The analysis finishes and the Outliers view is empty, or nearly.

**Cause.** Everything scored at or below the threshold. On a very small or
very uniform estate (a few dozen identities, or one where department and title
are missing so peer groups are weak) nothing may clear 0.80. The run's warnings
will say if peer grouping fell back or attributes were sparse.

**Fix.** Lower `outlier_min_score` on the analysis panel and run again
([Parameters](analysis.md#parameters)); check the peer groups tab on the Role
mining view to see what "peers" meant in this run; consider the
`agglomerative` method if department and title are sparse. Do not lower the
threshold on a large estate without a reason: the list grows quickly.

## No dormancy findings

**Symptom.** The Findings view has no dormant accounts, and the run's warnings
include `dormancy_not_checked`.

**Cause.** No imported source supplied last-login data, so the check did not
run. This is not a clean result.

**Fix.** Import a source that carries last login (Entra sign-in activity, AD
`lastLogonTimestamp`, an application's own last-login export) with a profile
that maps it, and run again. Or state in the report that dormancy was not
assessed. Never report "no dormant accounts" from a run that says
`dormancy_not_checked` ([Warnings](analysis.md#warnings)).

## Analyse or export is disabled

**Symptom.** The **Run analysis** button, the export buttons or the CSV
download are disabled with a message about a licence, or a banner across the
top says the product is read-only.

**Cause.** No licence is installed, or it has expired or does not verify, and
this is a regular project. Everything else keeps working; producing new
analysis or exports does not.

**Fix.** [Install a licence](licence.md#installing-a-licence). To evaluate
first, use the sample project, which is never refused ([Your first run](first-run.md)).
If you have a licence and the Licence page says `invalid`, the reason is shown
next to it: usually a paste that lost characters, or a token for a different
product build; paste it again from the original message.

## Reporting a problem

Write to `hello@cleavehq.com` with:

- The version: `pip show cleave`.
- Your operating system and Python version (`python --version`).
- What you did, what you expected, what happened, in that order.
- For an analysis problem: the methodology block from any export of the run
  (the PDF's last page, the Excel Methodology sheet, or the top of a CSV). It
  holds the parameters and warnings and no client data.
- For an import problem: the quarantine CSV if there is one, and the header row
  of the file that misbehaved. Do not send the file itself unless it is
  synthetic; we do not want your client's data and we will not ask for it.

There are no logs to send because there is no telemetry and no log file:
Cleave writes nothing about your session anywhere but the project file and the
terminal you started it from. If the terminal showed an error, copy that.
