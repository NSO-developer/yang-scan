"""YANG issues scanning plugin

"""

import optparse
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
        optlist: t.List[optparse.Option] = []
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
