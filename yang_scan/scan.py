"""YANG issues scanning plugin

"""

import optparse
import os
import re
import sys
import typing as t

from pyang import plugin, statements as st, error, xpath

old_pyang = False

try:
    from pyang.context import Context
except ImportError:
    # looks like we are using old pyang
    from pyang import Context
    old_pyang = True


def pyang_plugin_init() -> None:
    plugin.register_plugin(ScanPlugin())


class ScanPlugin(plugin.PyangPlugin):
    def __init__(self) -> None:
        if old_pyang:
            super().__init__()
        else:
            super().__init__(name='yang-scan')
        self.multiple_modules = True
        self.prefixes: t.Dict[str, st.Statement] = {}
        error.add_error_code('SCAN_DUPLICATE_PREFIXES', 4,
                             'Modules %s and %s have the same prefix')
        error.add_error_code('SCAN_HIDDEN', 4,
                             '"tailf:hidden %s" will cause NSO interoperability issues')

    def setup_fmt(self, ctx: Context) -> None:
        if not old_pyang:
            # xpath reference checking does not work in old pyang
            st.add_validation_fun('strict', [('tailf-common', 'display-when')],
                                  self.check_config_references)
        st.add_validation_fun('strict', ['prefix'], self.check_prefix)
        st.add_validation_fun('strict', [(('tailf-common', 'hidden'))],
                              self.check_hidden)

    def add_opts(self, optparser: optparse.OptionParser) -> None:
        optlist: t.List[optparse.Option] = [
            optparse.make_option('--scan-help',
                                 action='store_true',
                                 help='''Print help on YANG scanner and exit''')]
        g = optparser.add_option_group("YANG scan specific options")
        g.add_options(optlist)

    def add_output_format(self, fmts: t.Dict[str, plugin.PyangPlugin]) -> None:
        self.multiple_modules = True
        fmts['yang-scan'] = self

    def check_config_references(self, ctx: Context, statement: st.Statement) -> None:
        if old_pyang:
            st.v_xpath(ctx, statement)
        else:
            xpath.v_xpath(ctx, statement, statement.parent)

    def check_prefix(self, ctx: Context, statement: st.Statement) -> None:
        if statement.parent.keyword != 'module':
            return
        if statement.arg in self.prefixes and self.prefixes[statement.arg] != statement.parent:
            error.err_add(ctx.errors, statement.pos, 'SCAN_DUPLICATE_PREFIXES',
                          (self.prefixes[statement.arg].arg, statement.parent.arg))
        self.prefixes[statement.arg] = statement.parent

    def check_hidden(self, ctx: Context, statement: st.Statement) -> None:
        if statement.arg != 'full':
            error.err_add(ctx.errors, statement.pos, 'SCAN_HIDDEN', (statement.arg,))

    def setup_ctx(self, ctx: Context) -> None:
        if ctx.opts.scan_help:
            print_scan_help()


def process_readme(readme: t.TextIO) -> str:
    data = readme.read()
    chapters = re.split('[a-zA-Z ]+\n~+', data, flags=re.MULTILINE)
    paragraphs = chapters[1].split('\n\n')
    subrx = re.compile('(``)|(_)', flags=re.MULTILINE ^ re.DOTALL)
    return '\n\n'.join(
        subrx.sub(replacer, para)
        for para in paragraphs
        if len(para) > 5 and ' tag: ' not in para)


def replacer(match: re.Match) -> str:
    seq = match.group(0)
    mm = {'``': '`',
          '_': '',
          '\n ': ' ',
          '\n\n': '\n\n'}.get(match.group(0), seq[1:])
    return mm


README_NOT_FOUND_TEXT = '''
Cannot find the README.rst file.  Incorrect installation?

See https://pypi.org/project/yang-scan/ or https://gitlab.com/nso-developer/yang-scan/
for more information.
'''


def print_scan_help() -> None:
    readme_paths = [
        # standard install path
        os.path.join(sys.prefix, 'etc/yang-scan'),
        # if the plugin is run from a repository clone
        os.path.dirname(os.path.dirname(__file__))]
    for path in readme_paths:
        try:
            with open(os.path.join(path, 'README.rst')) as readme:
                print(process_readme(readme))
                break
        except FileNotFoundError:
            continue
    else:
        print(README_NOT_FOUND_TEXT)

    sys.exit(0)
