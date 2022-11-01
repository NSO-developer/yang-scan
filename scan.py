"""YANG issues scanning plugin

"""

import optparse
import typing as t

from pyang import plugin, statements as st, error, xpath, context


def pyang_plugin_init() -> None:
    plugin.register_plugin(ScanPlugin())


class ScanPlugin(plugin.PyangPlugin):
    def __init__(self) -> None:
        super().__init__(name='yang-scan')
        self.multiple_modules = True
        self.prefixes: t.Dict[str, st.Statement] = {}
        error.add_error_code('SCAN_DUPLICATE_PREFIXES', 4,
                             'Modules %s and %s have the same prefix')
        error.add_error_code('SCAN_HIDDEN', 4,
                             '"tailf:hidden %s" will cause NSO interoperability issues')

    def setup_fmt(self, ctx: context.Context) -> None:
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

    def check_config_references(self, ctx: context.Context, statement: st.Statement) -> None:
        xpath.v_xpath(ctx, statement, statement.parent)

    def check_prefix(self, ctx: context.Context, statement: st.Statement) -> None:
        if statement.parent.keyword != 'module':
            return
        if statement.arg in self.prefixes and self.prefixes[statement.arg] != statement.parent:
            error.err_add(ctx.errors, statement.pos, 'SCAN_DUPLICATE_PREFIXES',
                          (self.prefixes[statement.arg], statement.parent.arg))
        self.prefixes[statement.arg] = statement.parent

    def check_hidden(self, ctx: context.Context, statement: st.Statement) -> None:
        if statement.arg != 'full':
            error.err_add(ctx.errors, statement.pos, 'SCAN_HIDDEN', (statement.arg,))
