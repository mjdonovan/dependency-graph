# dependency-graph

A python script to show the "include" dependency of C++ classes.

It is useful to check the presence of circular dependencies.

## Differences from original version

The original version does not work correctly when the source and header files have the same names. This has been fixed in this version.

The --gv argument has been added, which generates a graph.gv file with a graph for use in third-party applications.

The --text argument has been added, which generates a graph.txt file with a text file containing graph data.

Added the --line argument, which adds information about the number of lines in files in graph.txt (Requires the --text argument)

## Installation

The script depends on [Graphviz](https://www.graphviz.org/) to draw the graph. 

On Ubuntu, you can install the dependencies with these two commands:

```
sudo apt install graphviz
pip3 install -r requirements.txt
```

## Manual

```
usage: dependency_graph.py [-h] [-f {bmp,gif,jpg,png,pdf,svg}] [-v] [-c] [--cluster-labels] [-s] [--gv] [--text] [--lines] folder output

positional arguments:
  folder                Path to the folder to scan
  output                Path of the output file without the extension

options:
  -h, --help            show this help message and exit
  -f {bmp,gif,jpg,png,pdf,svg}, --format {bmp,gif,jpg,png,pdf,svg}
                        Format of the output
  -v, --view            View the graph
  -c, --cluster         Create a cluster for each subfolder
  --cluster-labels      Label subfolder clusters
  -s, --strict          Rendering should merge multi-edges
  --gv                  Create graph.gv
  --text                Create graph.txt with filenames and edges
  --lines               Add to graph.txt number of lines in files
```

## Examples

Example of a graph produced by the script:

![Example 1](https://github.com/pvigier/dependency-graph/raw/master/examples/example1.png)

Graph produced for the same project with clusters (`-c`):

![Example 2](https://github.com/pvigier/dependency-graph/raw/master/examples/example2.png)
