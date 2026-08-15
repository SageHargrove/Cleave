# 0001. ReportLab over WeasyPrint

**Status:** decided, shipped
**Area:** `report/`, supply chain

## The question

Cleave's headline deliverable is a client-ready PDF. Something has to render it.
WeasyPrint is the obvious pick: you write HTML and CSS, which is a far more
pleasant authoring model than a document-object API, and it produces genuinely
attractive output.

The spec left this open on purpose, and the open question was recorded as "which
PDF engine" rather than resolved during planning.

## What decided it

Not ergonomics. The reason usually given for avoiding WeasyPrint is that its
GTK/Pango dependency is annoying to install on Windows. That is true and it is
not the real problem.

The real problem is that WeasyPrint renders through a **native** stack (Pango,
Cairo, HarfBuzz) that sits entirely outside `uv.lock`. That means it is:

- not hash-pinned, so builds are not reproducible
- not visible to `pip-audit`, so a CVE in it never appears in the gate
- absent from the CycloneDX SBOM

Cleave's whole security posture rests on a hashed, audited, inventoried
dependency set. Taking WeasyPrint would have opened a hole in that posture
exactly the size of the component rendering the deliverable, which is the worst
possible place for one.

ReportLab is pure Python. It hash-pins, it audits, and it appears in the SBOM.

## The check

Choosing on this basis is only honest if you then confirm the converse actually
holds, so that was verified rather than assumed: after the switch, `pip-audit` is
clean and both `reportlab` and `pillow` appear in the generated SBOM.

## What it cost

Real ergonomic pain. Platypus flowables are a much slower authoring model than
CSS, and the layout work took noticeably longer.

It also introduced a security issue that the HTML model would not have had in
the same form. ReportLab's paragraph markup accepts an `<img>` tag, so an
unescaped string interpolated into the cover page can **embed an arbitrary local
file into the generated PDF**. This was found in security review, measured to
confirm it was real rather than theoretical, and fixed with a regression test
that fails without the fix.

Two further bugs surfaced only by rendering rather than reading: a corrupt logo
crashed the render because ReportLab decodes images lazily, well past the
constructor where you would expect the error, and the footer template was never
activated so no page ever carried a page number. The tests had asserted only
that the output bytes began with `%PDF-`, which is the kind of assertion that
looks like coverage and is not.

## In hindsight

The decision holds. The lesson worth keeping is narrower than "prefer pure
Python": a dependency's *audit surface* is a first-class selection criterion, and
it deserves to be weighed before ergonomics rather than after.
