#!/usr/bin/env python
# encoding: utf-8
"""
dir-stats.py

Run analysis on directory
Can walk the directory or parse a file with the format as printed by find with
the following options:
find <dir> -printf "%Y %s %p\n"

Created by Aske Olsson 2011-09-05.
Copyright (c) 2011 Aske Olsson. All rights reserved.
"""

import os
from subprocess import Popen, PIPE
import operator
import sys

def extract_file_types(files, dirs):
    dict = {}
    for file in files.keys():
        # get file extension
        extension = os.path.splitext(file)[1]
        if extension == '':
            # which file is it then, makefiles should be detectable
            if os.path.split(file)[1].lower().startswith('make'):
                extension = 'makefile'
            elif os.path.split(file)[1].lower() == 'readme':
                extension = 'readme'
            elif os.path.split(file)[1].lower() == 'doxyfile':
                extension = 'doxyfile'
            else:
                extension = "NO-EXT"
        else:
            # Remove the . from the extension
            extension = extension.lstrip('.')
        if dict.has_key(extension):
            dict[extension].append(file)
        else:
            dict[extension] = [file]

    dict['directories'] = dirs.keys()
    return dict


def extract_size_info(files, file_types, dirs):
    total_size = sum(files.values()) + sum(dirs.values())

    type_size = {}
    for type in file_types.keys():
        if not type == 'directories':
            type_size[type] = sum([files[file] for file in file_types[type]])

    type_size['directories'] = sum(dirs.values())
    return type_size, total_size

def largest_files(content, num_of_files):
    """ Get the largest files in the dir """
    sorted_size = sorted(content.iteritems(), key=operator.itemgetter(1))
    sorted_size.reverse()
    return sorted_size[:num_of_files]


def analyze_dir(files, dirs):
    file_types = extract_file_types(files, dirs)
    total_files = 0
    for type in sorted(file_types.keys()):
        total_files += len(file_types[type])

    size_info, total_size = extract_size_info(files, file_types, dirs)
    return file_types, size_info, total_size


def format_content(file):
    """ Read content of directory from a file.
    Use find <dir> -printf "%Y %s %p\n" to generate
    """
    f = open(file, 'rb')
    content = f.read()
    f.close()

    files = {}
    dirs = {}
    for line in content.splitlines():
        type, size, path = line.split(' ', 2)
        if type == 'd':
            dirs[path] = float(size)
        else:
            files[path] = float(size)

    return files, dirs

def get_content(dir):
    files_dict = {}
    directories = {}
    for root, dirs, files in os.walk(dir):
        for fn in files:
            path = os.path.join(root, fn)
            size = os.stat(path).st_size # in bytes
            files_dict[path] = float(size)
        for dir in dirs:
            path = os.path.join(root, dir)
            size = os.stat(path).st_size # in bytes
            directories[path] = float(size)
    return files_dict, directories

def find_empty_dirs(files, dirs):
    # Used dirs:
    used_dirs = [os.path.split(d)[0] for d in files.keys()]
    # Find leaf dirs
    leaf = []
    last = sorted(dirs.keys())[0]
    for dir in sorted(dirs.keys())[1:]:
        if not dir.startswith(last):
            leaf.append(last)
        else:
            # Check if current dir just starts with same name as last dir
            if os.path.split(last)[0] == os.path.split(dir)[0]:
                if os.path.split(last)[1] != os.path.split(dir)[1]:
                    leaf.append(last)
        last = dir
    leaf.append(last)

    for dir in set(used_dirs):
        if dir in leaf:
            leaf.remove(dir)
    return leaf

def run_command(command):
    """Execute a command"""
    p = Popen(command, stdout=PIPE, stderr=PIPE)

    # Store the result as a single string.
    stdout, stderr = p.communicate()

    if stderr:
        return stderr
    return stdout

def pretty_print_size(size):
    """Convert a file size to human-readable form."""
    SUFFIXES = ['KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    if size < 0:
        raise ValueError('number must be non-negative')

    multiple = 1024
    for suffix in SUFFIXES:
        size /= multiple
        if size < multiple:
            return '{0:.1f} {1}'.format(size, suffix)

def longest_path( paths ):
    key = lambda path:path.count('/')
    return max(paths, key=key)

def subdir_size(files, dirs):
    """ Calculate size, members and depth of subdirs """
    subdirs = {}
    for file, size in files.iteritems():
        path, fn = os.path.split(file)
        # add size and count to all dirs under path
        splitted = path.split('/')
        for i, p in enumerate(splitted):
            dir = '/'.join(splitted[0:i+1])
            if subdirs.has_key(dir):
                subdirs[dir]['size'] += size
                subdirs[dir]['members'].append(file)
            else:
                subdirs[dir] = {'size': size, 'depth': dir.count('/'), 'members': [file]}
    for path, size in dirs.iteritems():
        # add size and count to all dirs under path
        splitted = path.split('/')
        for i, p in enumerate(splitted):
            dir = '/'.join(splitted[0:i+1])
            if subdirs.has_key(dir):
                subdirs[dir]['size'] += size
                subdirs[dir]['members'].append(dir)
            else:
                subdirs[dir] = {'size': size, 'depth': dir.count('/'), 'members': [dir]}

#    for dir in sorted(subdirs.keys()):
#        print dir, 'members', len(subdirs[dir]['members']), 'size', pretty_print_size(subdirs[dir]['size']), 'depth', subdirs[dir]['depth']
    return subdirs

def get_dir_stats(dir, num_of_largest=50):
    # Determine is input is a file (find <dir> .printf  "%Y %s %p\n"
    if os.path.isfile(dir):
        files, dirs = format_content(dir)
    else:
        files, dirs = get_content(dir)
    file_types, size_info,total_size = analyze_dir(files, dirs)
    empty = find_empty_dirs(files, dirs)
    largest = largest_files(files, num_of_largest)
    path = longest_path(dirs.keys())
    subdirs = subdir_size(files, dirs)
    return files, dirs, file_types, size_info, total_size, empty, largest, path, subdirs

def main():
    num_of_largest = 50
    dir = sys.argv[1]
    if len(sys.argv) > 2:
        num_of_largest = sys.argv[2]

    dir = dir.strip('/')
    files, dirs, file_types, size_info,total_size, empty, largest, longest_path = get_dir_stats(dir, num_of_largest=num_of_largest)
    print '{0:<15} {1:>6s} {2:>12s}'.format('File types', 'count', 'size')
    for type in sorted(file_types.keys()):
        print '{0:.<15}.{1:.>6s}.{2:.>12s}'.format(type, str(len(file_types[type])), pretty_print_size(size_info[type]))
    for file, size in largest:
        print pretty_print_size(size), file

    print "Total number of files %d" %len(files.keys())
    print "Total number of directories %d" % len(dirs.keys())
    print "Total entries in %s: %d" % (dir, len(files.keys())+len(dirs.keys()))
    print "Total size %s" % pretty_print_size(total_size)
    print "Longest path: ", longest_path
    print 'Empty directories: %d' %len(empty)

if __name__ == '__main__':
    main()
