import argparse
import codecs
import os
import re
from collections import defaultdict
from graphviz import Digraph

include_regex = re.compile(r'#include\s+["<"](.*)[">]')
valid_headers = [['.h', '.hpp', '.cuh'], 'red']
valid_sources = [['.c', '.cc', '.cpp', '.cu'], 'blue']
valid_extensions = valid_headers[0] + valid_sources[0]


def normalize(path):
    """ Return the name of the node that will represent the file at path. """
    filename = os.path.basename(path)
    end = filename.rfind('.')
    end = end if end != -1 else len(filename)
    return filename[:end]


def get_extension(path):
    """ Return the extension of the file targeted by path. """
    return path[path.rfind('.'):]


def find_all_files(path, ignore_tests, recursive=True):
    """
    Return a list of all the files in the folder.
    If recursive is True, the function will search recursively.
    """
    files = []
    for entry in os.scandir(path):
        if entry.is_dir() and recursive:
            files += find_all_files(entry.path, ignore_tests)
        elif get_extension(entry.path) in valid_extensions:
            # print('!', entry.path)
            if ignore_tests:
                norm_path = normalize(entry)
                # print(norm_path)
                if len(norm_path) >= 4:
                    if 'test' in norm_path:
                        continue
            files.append(entry.path)
    return files


def find_neighbors(path):
    """ Find all the other nodes included by the file targeted by path. """
    f = codecs.open(path, 'r', "utf-8", "ignore")
    code = f.read()
    f.close()
    return [include for include in include_regex.findall(code) if not code.strip().startswith('//')]


def count_lines(filename, chunk_size=1 << 13):
    with open(filename) as file:
        return len(file.readlines())


def get_absolute_path(path, include, include_directories):
    include_directories = list(include_directories.split(','))
    include_directories.append(os.path.dirname(path))
    for id in include_directories:
        maybe = os.path.join(id, include)
        if os.path.exists(maybe):
            return os.path.normpath(maybe)
    return None


def consume(magic, graph, label_cluster, stack, fire):
    empty = tuple()
    if empty in magic:
        print(f"use {magic[empty]}")
        fire(magic.pop(empty), '/'.join(stack), graph)
    while magic:
        # noinspection PyUnresolvedReferences
        key = min(magic, key=len)[0]
        stack.append(key)
        cluster_name = '/'.join(stack)
        print(f'==> {stack}')
        with graph.subgraph(name=f"cluster_{cluster_name}", graph_attr=dict(penwidth='0.05', color='gray')) as cluster:
            if label_cluster:
                cluster.attr(label=cluster_name)

            magic1 = {k[1:]: magic.pop(k) for k in [k for k in magic if k[0] == key]}
            consume(magic1, cluster, label_cluster, stack, fire)
        stack.pop()
        print(f'<== {stack}')


def create_graph(folder, include_directories, create_cluster, label_cluster, strict, gv, text, lines, ignore_tests,
                 show_path, flip):
    """ Create a graph from a folder. """
    # Find nodes and clusters
    if ',' in folder:
        n_folder = '__'.join(normalize(ff) for ff in folder.split(','))
        files = []
        for ff in folder.split(","):
            files.extend(find_all_files(ff, ignore_tests))
    else:
        files = find_all_files(folder, ignore_tests)
        n_folder = normalize(folder)

    nodes = set(files)
    # Create graph
    splines = 'polyline'
    splines = 'ortho'
    splines = 'true'
    ga = dict(splines=splines, ranksep='1.0', newrank='true', concentrate='true')
    # ga = {'concentrate': 'true', 'penwidth': '.31'}
    g0 = Digraph(strict=strict, graph_attr=ga, node_attr=dict(shape='rectangle', penwidth='.3'), edge_attr=dict(penwidth='.3'))
    # Find edges and create clusters

    files_to_numbers = {f: i + 1 for i, f in enumerate(files)}
    str_lines = []
    gv_lines = []
    if text:
        str_lines.extend(['', 'Nodes:\n'])
        for i in range(len(files)):
            if show_path:
                normalized_name = files[i]
            else:
                normalized_name = normalize(files[i]) + get_extension(files[i])
            if lines:
                str_lines.append(f'{i + 1} {normalized_name} {count_lines(files[i])}\n')
            else:
                str_lines.append(f'{i + 1} {normalized_name}\n')
        str_lines.append('Edges:\n')
    if gv:
        gv_lines.append('digraph ' + str(n_folder) + ' {\n')
        for i in range(len(files)):
            if show_path:
                normalized_name = files[i]
            else:
                normalized_name = normalize(files[i]) + get_extension(files[i])
            gv_lines.append(f'\t{i + 1} [label="{normalized_name}"];\n')

    unresolved = defaultdict(set)

    common_prefix = os.path.commonprefix(files)
    magic = {}
    for path in files:
        folder1 = os.path.dirname(path)
        folder2 = tuple(os.path.normpath(folder1 if not (common_prefix and folder1.startswith(common_prefix)) else (folder1[len(common_prefix):])).split(os.path.sep))
        if folder2 not in magic:
            magic[folder2] = []
        magic[folder2].append(path)

    def fire(files_in_folder, folder1_name, graph):
        add_stuff(create_cluster, files_in_folder, files_to_numbers, flip, folder1_name, g0, graph, gv, gv_lines,
                  include_directories, label_cluster, nodes, show_path, str_lines, 0, text, unresolved)

    consume(magic, g0, label_cluster, [], fire)

    for k, v in unresolved.items():
        print(f'cannot resolve within {k}: {",".join(v)}')

    return g0


def add_stuff(create_cluster, files_in_folder, files_to_numbers, flip, folder1_name, g0, cluster, gv, gv_lines,
              include_directories, label_cluster, nodes, show_path, str_lines, subgraph_counter, text, unresolved):
    subgraph_nodes = []
    for path in files_in_folder:
        color = 'black'
        if show_path:
            label = path
        else:
            label = normalize(path) + get_extension(path)

        ext = get_extension(path)
        if ext in valid_headers[0]:
            color = valid_headers[1]
        if ext in valid_sources[0]:
            color = valid_sources[1]
        if create_cluster:
            cluster.node(path, label)
            subgraph_nodes.append(files_to_numbers[path])
        else:
            g0.node(path, label)
        neighbors = find_neighbors(path)
        for neighbor in neighbors:
            abs_path = get_absolute_path(path, neighbor, include_directories)
            if abs_path is None:
                unresolved[os.path.dirname(path)].add(neighbor)
            if abs_path != path and abs_path in nodes:
                g0.edge(abs_path if flip else path, path if flip else abs_path, color=color)
                if text:
                    str_lines.append(f'{files_to_numbers[path]} {files_to_numbers[abs_path]}\n')
                if gv:
                    gv_lines.append(
                        f'\t{files_to_numbers[path]} -> {files_to_numbers[abs_path]} [color = {color}];\n')
    if create_cluster:
        if gv:
            gv_lines.append(f'\tsubgraph cluster_{subgraph_counter} ' + '{\n')
            subgraph_counter += 1
        if label_cluster:
            # cluster.attr(label=folder1_name)
            if gv:
                gv_lines.append(f'\t\tlabel = "{folder1_name}";\n')
        if gv:
            for node in subgraph_nodes:
                gv_lines.append(f'\t\t{node};\n')
            gv_lines.append('\t}\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', help='Path to the folder to scan')
    parser.add_argument('include_directories', help='include directories')
    parser.add_argument('output', help='Path of the output file without the extension')
    parser.add_argument('-f', '--format', help='Format of the output', default='pdf', choices=['bmp', 'gif', 'jpg', 'png', 'pdf', 'svg'])
    parser.add_argument('-v', '--view', action='store_true', help='View the graph')
    parser.add_argument('-c', '--cluster', action='store_true', help='Create a cluster for each subfolder')
    parser.add_argument('--cluster-labels', dest='cluster_labels', action='store_true', help='Label subfolder clusters')
    parser.add_argument('--flip_edges', dest='flip_edges', action='store_false', help='Label subfolder clusters')
    parser.add_argument('-s', '--strict', action='store_true', help='Rendering should merge multi-edges', default=False)
    parser.add_argument('--gv', action='store_true', help='Create graph.gv', default=False)
    parser.add_argument('--text', action='store_true', help='Create graph.txt with filenames and edges', default=False)
    parser.add_argument('--lines', action='store_true', help='Add to graph.txt number of lines in files', default=False)
    parser.add_argument('--ignore-tests', action='store_true',
                        help='Files with names that includes "test" will be ignored in graph', default=False)
    parser.add_argument('--show-path', action='store_true', help='Files will be labeled with path', default=False)

    args = parser.parse_args()
    graph = create_graph(args.folder, args.include_directories, args.cluster, args.cluster_labels, args.strict, args.gv,
                         args.text, args.lines,
                         args.ignore_tests, args.show_path, args.flip_edges)
    graph.format = args.format
    graph.render(args.output, cleanup=True, view=args.view)


if __name__ == '__main__':
    main()
