#!/bin/bash

url=git://github.com/wpilibsuite/allwpilib
branch=master

repo=$(basename $url)

pushd $PWD
cd /tmp

if [ ! -d "$repo" ]; then
  # Clone Git repository to /tmp
  git clone $url
  cd $repo
  git checkout -q -f $branch
else
  # Update Git repository in /tmp
  cd $repo
  git checkout -q -f $branch
  git pull
fi

if [ $# != 1 ] || [ "$1" != "skip-parse" ]; then
  # Create list of commit hashes
  declare -i x=0
  rm -f data.csv

  # Write header to CSV
  echo commits$','loc >> data.csv

  declare -i total=$(git rev-list --count $branch)

  # Get lines of code (LOC) for all commits in branch and write it to CSV
  for elem in `git log --reverse --pretty=oneline | cut -d ' ' -f 1`; do
    # Get LOC for current commit
    git checkout -q -f $elem
    x=$((x + 1))
    y=$(find $PWD -type f -regextype posix-extended -regex '.*\.(cpp|hpp|inl|h|c|java)$' -exec cat {} + | wc -l)
    percent=$((x * 100 / total))

    # Print progress data and write LOC count to CSV
    echo -n $'\r'Parsing commits for data.csv: $percent% \($x$'/'$total\)
    echo $x$','$y >> data.csv
  done

  echo -n $',' done.

  # Print newline so prompt appears on next line
  echo
fi

echo Generating graph...
popd  # pop back to original directory

if [ $# != 1 ] || [ "$1" != "skip-parse" ]; then
  mv /tmp/$repo/data.csv graph/data.csv
fi

cd graph
latexmk -pdf -silent graph
mv graph.pdf ../loc.pdf
