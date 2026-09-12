# Install

After this page Cleave is installed and running on your machine, and you know where it keeps things.

## What you need

- **Python 3.12 or newer.** This is the only prerequisite, and on a managed
  corporate laptop it is the one most likely to be blocked. Check with
  `python --version` (on some systems `python3 --version`). If you cannot
  install Python, stop here and ask your IT team; nothing below works without
  it.
- **Windows, macOS or Linux.** All three are tested. The paths below differ per
  system and are listed where they matter.
- **A few hundred megabytes of disk** for Python packages (the scientific
  stack Cleave is built on is most of it), plus room for your project files.
- **An internet connection for the install itself.** After that, none. Cleave
  makes no network calls in use.

## Install the package

Cleave is delivered as a Python wheel, a single `.whl` file. Install it into
its own virtual environment so it does not interfere with anything else on the
machine:

```
python -m venv cleave-env
cleave-env\Scripts\activate          # Windows
source cleave-env/bin/activate       # macOS, Linux
pip install cleave-0.0.0-py3-none-any.whl
```

Use the file name of the wheel you were sent. `pip` fetches Cleave's
dependencies from PyPI; that download is most of the install time. Measured on
2026-08-17 on Windows 11 with Python 3.12, `pip install` took 73 to 79 seconds
depending on the cache, and the whole path from creating the environment to a
first report was about 96 seconds.

Three commands are now on your path while the environment is active:

| Command | What it does |
| --- | --- |
| `cleave` | Starts the product and opens it in your browser |
| `cleave-sample` | Creates a synthetic sample project you can analyse without a licence ([Your first run](first-run.md)) |
| `cleave-synth` | The generator behind the sample, for developers; you do not need it |

## Start Cleave

```
cleave
```

Cleave starts a local server, prints the address it is listening on, and opens
your browser there after a second. The address is `http://127.0.0.1:<port>/#token=<token>`:
it is bound to your own machine only (nothing else on the network can reach it),
and the part after `#` is a session token minted fresh for this launch. Keep the
tab open; the token is what lets it talk to the server. Every launch gets a new
one, so a bookmark will not work: start `cleave` and use the tab it opens.

Two options:

- `cleave --port 8787` listens on a fixed port instead of a free one the system
  picks. Useful when you want a predictable address.
- `cleave --no-browser` starts the server and prints the address without opening
  a tab. Copy the address, token included, into the browser yourself.

`cleave --help` lists both. Stop the server with `Ctrl+C` in the terminal; the
tab then shows a "session ended" screen and nothing is lost.

## Where things live

Cleave keeps two kinds of files, in two places, and it is worth knowing which
is which before you have a client's data in one of them.

**Project files.** One project holds one client's dataset: every import, every
analysis run, every finding and annotation. It is a single SQLite file at a
path *you* choose when you create the project. Copy it, back it up, move it,
put it on the encrypted drive your engagement requires: it is self-contained
and works wherever it is opened. There is one exception to "you choose the
path": `cleave-sample` puts the sample project in the folder it writes,
`northwind-sample.sqlite`.

**The app directory.** A per-user folder for things that are about *this
machine*, not about any client:

| System | App directory |
| --- | --- |
| Windows | `%LOCALAPPDATA%\Cleave` (usually `C:\Users\<you>\AppData\Local\Cleave`) |
| macOS | `~/Library/Application Support/Cleave` |
| Linux | `$XDG_DATA_HOME/Cleave`, or `~/.local/share/Cleave` if that is unset |

Inside it:

- `workspace.json`: the list of project files Cleave knows about (name and
  path). It holds no project data. Removing a project from the workspace in the
  interface only forgets the entry; the file is never touched.
- `license.txt`: your licence, once you have one ([The licence](licence.md)).
- `uploads/`, `jobs/`, `exports/`: files you upload to the import wizard,
  the working state of long-running jobs, and the reports and exports Cleave
  has produced, each under the project they belong to.
- `ai.json` and `ai-logs/`: only if you have configured the optional AI
  layer, which has no interface yet ([Limits](limits.md#ai-assistance)).

## What leaves your machine

Nothing. Cleave binds to `127.0.0.1` only, has no telemetry, no update check,
no account, and no crash reporting. The licence is verified locally against a
public key; installing or checking it makes no network call in any state. The
one opt-in exception is the AI layer, which can send redacted prompts to a
model endpoint you configure, is off by default, and has no interface yet, so
today it stays off unless you edit a configuration file by hand.

For a client's security questionnaire, the in-app **Security** page (at
`/legal/security`, linked from the bottom of the interface) states the same in more
detail.

## Upgrade

Activate the environment and install the new wheel over the old one:

```
pip install --upgrade cleave-<new-version>-py3-none-any.whl
```

Project files upgrade themselves the first time the new version opens them
(the schema is versioned inside the file). Older versions cannot open a file
a newer version has upgraded, so keep a copy if you need to go back. Your
workspace, licence and exports are untouched by an upgrade.

## Remove

```
pip uninstall cleave
```

removes the package. It does not remove the app directory (delete it yourself
if you want the workspace, licence and past exports gone) and it never touches
project files, because those are yours and live where you put them. Delete each
project file deliberately, the way you would delete any client data.
