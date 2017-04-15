# Lines of Code Grapher

Generates a graph of the lines of C++ and Java source code in WPILib's Git repository commits.

Running `graph.sh` will clone WPILib into /tmp, create a CSV file containing the data, and generate a graph in LaTeX from that data. Upon completion, there will be a `loc.pdf` file in the current directory. The repository is left in /tmp to avoid recloning during subsequent runs.

`./graph.sh skip-parse` regenerates the graph without reparsing the Git repository.
