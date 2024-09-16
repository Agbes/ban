from bootstrap_email.compiler import compile
from django import template

register = template.Library()


@register.tag
def bootstrap_email(parser, token):
    nodelist = parser.parse(("end_bootstrap_email",))
    parser.delete_first_token()
    return BootstrapEmailNode(nodelist)


class BootstrapEmailNode(template.Node):
    def __init__(self, children):
        self.children = children

    def render(self, context):
        html = self.children.render(context)
        result = compile(html)
        return result
