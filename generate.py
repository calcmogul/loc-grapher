#!/usr/bin/env python3

import argparse
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MultipleLocator
import numpy as np
import os
import re
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


class Language:
    def __init__(self, name, extensions):
        self.name = name
        self.ext_regex = re.compile(r"\.(" + "|".join(extensions) + ")$")
        self.line_count = 0


def generate_plot(pdf, dates, counts, labels, years=None):
    plt.figure(figsize=(11, 8.5))
    plt.stackplot(dates, counts, labels=labels)

    if years:
        if years[0] + 1 == years[1]:
            plt.title(f"WPILib Lines of Code ({years[0]})")
        else:
            plt.title(f"WPILib Lines of Code ({years[0]}-{years[1]})")
    else:
        plt.title("WPILib Lines of Code")

    plt.ylabel("Lines of Code")

    ax = plt.gca()
    ax.yaxis.set_minor_locator(MultipleLocator(50e3))
    ax.ticklabel_format(axis="y", style="scientific", scilimits=(3, 3), useOffset=False)

    if years:
        plt.xlim([datetime.date(years[0], 1, 1), datetime.date(years[1], 1, 1)])
    else:
        plt.xlim(
            [
                datetime.date(dates[0].year, 1, 1),
                datetime.date(dates[-1].year + 1, 1, 1),
            ]
        )

    plt.grid()

    plt.legend(labels, loc="upper left")

    pdf.savefig()
    plt.close()


def main():
    branch = "main"

    cwd = os.getcwd()
    os.chdir(tempfile.gettempdir())
    clone_repo("https://github.com/wpilibsuite/allwpilib", branch)

    languages = []
    languages.append(Language("C++", ["cc", "cpp", "h", "hpp", "inc", "inl"]))
    languages.append(Language("Java", ["java"]))
    languages.append(Language("Python", ["py"]))

    # Collect commit data
    print("Collecting commit data...", end="")
    sys.stdout.flush()
    args = [
        "git",
        "--no-pager",
        "log",
        "--numstat",
        "--no-renames",
        "--reverse",
        "--format=date %ci",
        branch,
    ]
    output_list = subprocess.check_output(args, encoding="utf-8").splitlines()
    print(" done.")

    # Fields are additions, subtractions, and filename
    line_regex = re.compile("^([0-9]+)\s+([0-9]+)\s+(.*?)$")

    dates = []
    counts = []
    for i in range(len(languages)):
        counts.append([])

    for line in output_list:
        if line.startswith("date "):
            # If line designates a new commit, record the previous one's line
            # counts
            dates.append(datetime.datetime.strptime(line[5:], "%Y-%m-%d %H:%M:%S %z"))

            if len(dates) == 1:
                continue

            for i, lang in enumerate(languages):
                counts[i].append(lang.line_count)
        elif m := line_regex.search(line):
            # Lines with "- -" for counts are for binary files and are
            # ignored by line_regex
            for lang in languages:
                if lang.ext_regex.search(m.group(3)):
                    lang.line_count += int(m.group(1))
                    lang.line_count -= int(m.group(2))

                    # Each file belongs to only one language
                    break

    # Write rest of data
    for i, lang in enumerate(languages):
        counts[i].append(lang.line_count)

    # Generate plots
    os.chdir(cwd)
    print("Generating plots...", end="")
    sys.stdout.flush()
    with PdfPages("loc.pdf") as pdf:
        labels = tuple(lang.name for lang in languages)
        generate_plot(pdf, dates, counts, labels)
        for year in range(2014, 2023):
            generate_plot(pdf, dates, counts, labels, (year, year + 1))
    print(" done.")


if __name__ == "__main__":
    main()