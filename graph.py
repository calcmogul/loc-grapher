#!/usr/bin/env python3

import os
import re
import shutil
import subprocess
import sys


def main():
    repo = "allwpilib"
    branch = "master"
    url = "git://github.com/wpilibsuite/" + repo

    cwd = os.getcwd()

    # Clone Git repository into /tmp or update it
    os.chdir("/tmp")
    if not os.path.exists(repo):
        subprocess.run(["git", "clone", url])
        os.chdir(repo)
    else:
        os.chdir(repo)
        subprocess.run(["git", "pull"])

    # Quash rename limit warning
    subprocess.run(["git", "config", "diff.renameLimit", "999999"])

    # Check out branch before retrieving log info so branch exists
    subprocess.run(["git", "checkout", branch])

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
    output_list = (
        subprocess.run(args, stdout=subprocess.PIPE).stdout.decode().split("\n")
    )
    print(" done.")

    line_regex = re.compile("([0-9]+)\s+([0-9]+)\s+(\S+)")
    ext_regex = re.compile(".*\.(c|cpp|h|hpp|inc|inl|java)$")
    commit_count = 0
    line_count = 0
    with open("data.csv", "w") as data:
        for line in output_list:
            if "\t" not in line[0:40]:
                # Write entry to file
                data.write(str(commit_count))
                data.write(",")
                data.write(str(line_count))
                data.write("\n")

                commit_count += 1
            else:
                match = line_regex.search(line)
                if match and ext_regex.search(match.group(3)):
                    line_count += int(match.group(1))
                    line_count -= int(match.group(2))
        # Write rest of data
        data.write(str(commit_count))
        data.write(",")
        data.write(str(line_count))
        data.write("\n")

    # Generate graph
    shutil.move("data.csv", cwd + "/graph/data.csv")
    os.chdir(cwd + "/graph")
    subprocess.run(["latexmk", "-pdf", "-silent", "graph"])
    os.rename("graph.pdf", "../loc.pdf")


if __name__ == "__main__":
    main()
