#!/usr/bin/env bash
# Render a Mermaid or PlantUML source file to an image.
# Usage: render.sh <mermaid|plantuml> <input-file> <output-path>
# Why a script: the render+format+move+dependency-check glue is identical on
# every call and the PlantUML rename-after-render quirk is easy to get wrong.
set -euo pipefail

engine=${1:?engine required: mermaid|plantuml}
infile=${2:?input file required}
outpath=${3:?output path required}

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

[[ -f "$infile" ]] || { echo "render.sh: input file not found: $infile" >&2; exit 1; }

# Format is driven by the output extension; default svg.
ext=${outpath##*.}
[[ "$ext" == "$outpath" ]] && ext=svg

case "$engine" in
  mermaid)
    command -v mmdc >/dev/null 2>&1 || {
      echo "render.sh: 'mmdc' not found. Install: npm install -g @mermaid-js/mermaid-cli" >&2
      exit 1
    }
    # --no-sandbox via bundled puppeteer config: Ubuntu AppArmor blocks the
    # unprivileged-userns sandbox, and mermaid's headless-shell build ships no
    # chrome-sandbox to SUID. Safe here — Chromium only loads diagram syntax we
    # generate, never untrusted web/HTML input.
    mmdc -p "$script_dir/puppeteer-config.json" -i "$infile" -o "$outpath"
    # Emit the editable source beside the image (opens in mermaid.live, Miro, VS Code).
    src="${outpath%.*}.mmd"; cp -f "$infile" "$src"; echo "source:   $src"
    ;;

  plantuml)
    # Prefer a distro 'plantuml' wrapper; fall back to $PLANTUML_JAR + java.
    if command -v plantuml >/dev/null 2>&1; then
      runner=(plantuml)
    elif [[ -n "${PLANTUML_JAR:-}" && -f "$PLANTUML_JAR" ]]; then
      command -v java >/dev/null 2>&1 || {
        echo "render.sh: java not found; PlantUML needs a JVM on PATH." >&2
        exit 1
      }
      runner=(java -jar "$PLANTUML_JAR")
    else
      echo "render.sh: no 'plantuml' command and \$PLANTUML_JAR unset/missing." >&2
      echo "  Install the 'plantuml' package, or set PLANTUML_JAR=/path/to/plantuml.jar" >&2
      exit 1
    fi

    outdir=$(dirname "$outpath")
    # PlantUML writes <basename>.<ext> into the output dir; rename to requested path.
    "${runner[@]}" "-t${ext}" "$infile" -o "$outdir"
    produced="$outdir/$(basename "${infile%.*}").${ext}"
    [[ "$produced" != "$outpath" ]] && mv -f "$produced" "$outpath"
    # Emit the editable source beside the image (opens in any PlantUML editor / server).
    src="${outpath%.*}.puml"; cp -f "$infile" "$src"; echo "source:   $src"
    ;;

  *)
    echo "render.sh: unknown engine '$engine' (want: mermaid|plantuml)" >&2
    exit 1
    ;;
esac

echo "rendered: $outpath"
