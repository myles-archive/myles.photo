#!/usr/bin/env python

import os
import glob

from livereload import Server, shell


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))

    source_dir = os.path.join(root_dir, 'source')
    template_dir = os.path.join(root_dir, 'theme/templates')
    static_dir = os.path.join(root_dir, 'theme/static')

    build_dir = os.path.join(root_dir, 'build')

    server = Server()

    server.watch(os.path.join(source_dir, '*.md'), 'sigal build')
    server.watch(os.path.join(template_dir, '*.html'), 'sigal build')

    # SCSS Setup
    include_path = os.path.join(root_dir, './bower_components/')
    scssc_py = 'sassc.py --include-path={0} {1}'
    scss_in = os.path.join(static_dir, 'scss/style.scss')
    scss_out = os.path.join(static_dir, 'css/style.css')

    for filepath in glob.glob(os.path.join(static_dir, 'scss/**/*.scss'),
                              recursive=True):
        cmd = shell(scssc_py.format(include_path, scss_in), output=scss_out)

        server.watch(filepath, cmd, delay='forever')

    server.watch(scss_out, 'sigal build')

    server.serve(root=build_dir)

if __name__ == '__main__':
    main()
