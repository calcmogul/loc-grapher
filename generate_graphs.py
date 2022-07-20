#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile


def clone_repo(url, branch):
    repo = os.path.basename(url)
    dest = os.path.join(os.getcwd(), repo).rstrip(".git")

    # Clone Git repository into current directory or update it
    if not os.path.exists(dest):
        subprocess.run(["git", "clone", url, dest])
        os.chdir(dest)
    else:
        os.chdir(dest)
        subprocess.run(["git", "pull"])

    # Quash rename limit warning
    subprocess.run(["git", "config", "diff.renameLimit", "999999"])

    # Check out branch before retrieving log info so branch exists
    subprocess.run(["git", "switch", branch])


def get_commit_count(branch, ref):
    return subprocess.check_output(
        ["git", "rev-list", "--count", f"--before={ref}", branch], encoding="ascii"
    ).rstrip()


def generate_latex_plot_cmd(xmin, xmax, title):
    # Generating this in Python was necessary because \input{} in a tikzpicture
    # hangs
    return (
        r"""\begin{center}
  \LARGE \sffamily
  \begin{tikzpicture} [trim axis left, trim axis right]
    \begin{axis} [
      title=#3,
      xlabel=Commits,
      ylabel=Lines of Code,
      width=0.95\textwidth, height=0.75\textheight,
      scale only axis,
      xmin=#1,
      xmax=#2,
      ymin=0,
      grid=both,
      max space between ticks=28pt,
      xticklabel style={
        rotate=45,
        anchor=east,
        /pgf/number format/1000 sep={},
      },
      restrict x to domain=#1:,
      yticklabel style={
        /pgf/number format/.cd,
          fixed,
          precision=3,
          1000 sep={},
        /tikz/.cd,
      },
      scaled y ticks={base 10:-3},
      ]
      \addplot[blue, line width=1pt] table [col sep=comma] {data.csv};
    \end{axis}
  \end{tikzpicture}
\end{center}
""".replace(
            "#1", xmin
        )
        .replace("#2", xmax)
        .replace("#3", title)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-latex-only",
        dest="latex_only",
        action="store_true",
        help="Don't run CSV generation before LaTeX compilation",
    )
    args = parser.parse_args()

    branch = "main"

    cwd = os.getcwd()
    os.chdir(tempfile.gettempdir())
    clone_repo("https://github.com/wpilibsuite/allwpilib", branch)

    if not args.latex_only:
        # Create list of commit hashes
        print("Collecting commit data...", end="")
        sys.stdout.flush()
        args = [
            "git",
            "--no-pager",
            "log",
            "--numstat",
            "--reverse",
            "--pretty=oneline",
            branch,
        ]
        output_list = subprocess.check_output(args, encoding="utf-8").splitlines()
        print(" done.")

        commit_hash_regex = re.compile("^[a-f0-9]{40}")

        # Fields are additions, subtractions, and filename
        line_regex = re.compile("^([0-9]+)\s+([0-9]+)\s+(.*?)$")

        ext_regex = re.compile("\.(c|cc|cpp|h|hpp|inc|inl|java|js|py)$")
        commit_count = 0
        line_count = 0
        with open("data.csv", "w") as data:
            for line in output_list:
                if commit_hash_regex.search(line):
                    # If line has a commit hash, write entry to file
                    data.write(str(commit_count))
                    data.write(",")
                    data.write(str(line_count))
                    data.write("\n")

                    commit_count += 1
                else:
                    m = line_regex.search(line)

                    # Lines with "- -" for counts are for binary files and are
                    # ignored by line_regex
                    if m and ext_regex.search(m.group(3)):
                        line_count += int(m.group(1))
                        line_count -= int(m.group(2))
            # Write rest of data
            data.write(str(commit_count))
            data.write(",")
            data.write(str(line_count))
            data.write("\n")
        shutil.move("data.csv", f"{cwd}/loc/data.csv")

    # Generate plot ranges of interest
    end_2014_season = get_commit_count(branch, "2014-simulation-alpha-rc3")
    end_2015_season = get_commit_count(branch, "jenkins-release-2015.337")
    end_2016_season = get_commit_count(branch, "v2016.5.1")
    end_2017_season = get_commit_count(branch, "v2017.3.1")
    end_2018_season = get_commit_count(branch, "v2018.4.1")
    end_2019_season = get_commit_count(branch, "v2019.4.1")
    end_2020_season = get_commit_count(branch, "v2020.3.2")
    end_2021_season = get_commit_count(branch, "v2021.3.1")
    end_2022_season = get_commit_count(branch, "v2022.4.1")
    end_all = get_commit_count(branch, branch)

    commit_ranges = [
        ("0", end_all, "\\title"),
        (end_2014_season, end_2015_season, "\\title\\ (2015 dev season)"),
        (end_2015_season, end_2016_season, "\\title\\ (2016 dev season)"),
        (end_2016_season, end_2017_season, "\\title\\ (2017 dev season)"),
        (end_2017_season, end_2018_season, "\\title\\ (2018 dev season)"),
        (end_2018_season, end_2019_season, "\\title\\ (2019 dev season)"),
        (end_2019_season, end_2020_season, "\\title\\ (2020 dev season)"),
        (end_2020_season, end_2021_season, "\\title\\ (2021 dev season)"),
        (end_2021_season, end_2022_season, "\\title\\ (2022 dev season)"),
        (end_2022_season, end_all, "\\title\\ (2023 dev season)"),
    ]

    # Generate plots.tex
    with open(f"{cwd}/loc/plots.tex", "w") as f:
        i = 0
        for start, end, title in commit_ranges:
            if i > 0:
                f.write("\\newpage\n")
            f.write(generate_latex_plot_cmd(start, end, title))
            f.write("\\trailer\n")

    # Generate plots
    os.chdir(f"{cwd}/loc")
    subprocess.run(["latexmk", "-pdf", "-silent", "loc"])
    shutil.copy("loc.pdf", "../loc.pdf")


if __name__ == "__main__":
    main()
