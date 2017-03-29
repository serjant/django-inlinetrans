# Copyright (c) 2010-2013 by Yaco Sistemas <ant30tx@gmail.com> or <goinnn@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this programe.  If not, see <http://www.gnu.org/licenses/>.

import copy
import sys

from django import template
from django.conf import settings
try:
    from django.urls import reverse
except ImportError:  # Django < 1.10 fallback
    from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
try:
    from django.template import TemplateSyntaxError, Node, Variable
except ImportError:
    from django.template.base import TemplateSyntaxError, Node, Variable
try:
    from django.template.base import render_value_in_context as _render_value_in_context
except ImportError:   # Django < 1.7 fallback
    try:
        from django.template.base import _render_value_in_context
    except ImportError:   # Django 1.1 fallback
        from django.template import _render_value_in_context

from django.utils.translation import get_language
from django.utils.translation.trans_real import catalog

from ..settings import get_user_can_translate


if sys.version_info[0] == 2:
    string = basestring
else:
    string = str


register = template.Library()


def get_static_url(subfix='inlinetrans'):
    static_prefix = getattr(settings, 'INLINETRANS_STATIC_URL', None)
    if static_prefix:
        return static_prefix
    static_prefix = getattr(settings, 'INLINETRANS_MEDIA_URL', None)
    if static_prefix:
        return static_prefix
    static_url = getattr(settings, 'STATIC_URL', getattr(settings, 'MEDIA_URL'))
    return '%s%s/' % (static_url, subfix)


def get_language_name(lang):
    for lang_code, lang_name in settings.LANGUAGES:
        if lang == lang_code:
            return lang_name


class NotTranslated(object):

    @staticmethod
    def ugettext(cadena):
        raise ValueError("not translated")

    @staticmethod
    def add_fallback(func):
        return


class InlineTranslateNode(Node):

    def __init__(self, filter_expression, noop):
        self.noop = noop
        self.filter_expression = filter_expression
        if isinstance(self.filter_expression.var, string):
            self.filter_expression.var = Variable(u"'%s'" % self.filter_expression.var)

    def render(self, context):
        if 'user' in context:
            user = context['user']
        elif 'request' in context:
            user = getattr(context.get('request'), 'user', None)
        else:
            user = None
        if not (user and get_user_can_translate(user)):
            self.filter_expression.var.translate = not self.noop
            output = self.filter_expression.resolve(context)
            return _render_value_in_context(output, context)

        if getattr(self.filter_expression.var, 'literal'):
            msgid = self.filter_expression.var.literal
        else:
            msgid = self.filter_expression.resolve(context)
        cat = copy.copy(catalog())
        cat.add_fallback(NotTranslated)
        styles = ['translatable']
        try:
            if sys.version_info[0] == 2:
                msgstr = cat.ugettext(msgid)
            else:
                msgstr = cat.gettext(msgid)
        except (ValueError, AttributeError):
            styles.append("untranslated")
            msgstr = msgid
        return render_to_string('inlinetrans/inline_trans.html',
                                {'msgid': msgid,
                                 'styles': ' '.join(styles),
                                 'value': msgstr})

class TokenParser(object):		
    """		
    Subclass this and implement the top() method to parse a template line.		
    When instantiating the parser, pass in the line from the Django template		
    parser.		
		
    The parser's "tagname" instance-variable stores the name of the tag that		
    the filter was called with.		
    """		
    def __init__(self, subject):		
        self.subject = subject		
        self.pointer = 0		
        self.backout = []		
        self.tagname = self.tag()		
		
    def top(self):		
        """		
        Overload this method to do the actual parsing and return the result.		
        """		
        raise NotImplementedError('subclasses of Tokenparser must provide a top() method')		
		
    def more(self):		
        """		
        Returns True if there is more stuff in the tag.		
        """		
        return self.pointer < len(self.subject)		
		
    def back(self):		
        """		
        Undoes the last microparser. Use this for lookahead and backtracking.		
        """		
        if not len(self.backout):		
            raise TemplateSyntaxError("back called without some previous "		
                                      "parsing")		
        self.pointer = self.backout.pop()		
		
    def tag(self):		
        """		
        A microparser that just returns the next tag from the line.		
        """		
        subject = self.subject		
        i = self.pointer		
        if i >= len(subject):		
            raise TemplateSyntaxError("expected another tag, found "		
                                      "end of string: %s" % subject)		
        p = i		
        while i < len(subject) and subject[i] not in (' ', '\t'):		
            i += 1		
        s = subject[p:i]		
        while i < len(subject) and subject[i] in (' ', '\t'):		
            i += 1		
        self.backout.append(self.pointer)		
        self.pointer = i		
        return s		
		
    def value(self):		
        """		
        A microparser that parses for a value: some string constant or		
        variable name.		
        """		
        subject = self.subject		
        i = self.pointer		
		
        def next_space_index(subject, i):		
            """		
            Increment pointer until a real space (i.e. a space not within		
            quotes) is encountered		
            """		
            while i < len(subject) and subject[i] not in (' ', '\t'):		
                if subject[i] in ('"', "'"):		
                    c = subject[i]		
                    i += 1		
                    while i < len(subject) and subject[i] != c:		
                        i += 1		
                    if i >= len(subject):		
                        raise TemplateSyntaxError("Searching for value. "		
                            "Unexpected end of string in column %d: %s" %		
                            (i, subject))		
                i += 1		
            return i		
		
        if i >= len(subject):		
            raise TemplateSyntaxError("Searching for value. Expected another "		
                                      "value but found end of string: %s" %		
                                      subject)		
        if subject[i] in ('"', "'"):		
            p = i		
            i += 1		
            while i < len(subject) and subject[i] != subject[p]:		
                i += 1		
            if i >= len(subject):		
                raise TemplateSyntaxError("Searching for value. Unexpected "		
                                          "end of string in column %d: %s" %		
                                          (i, subject))		
            i += 1		
		
            # Continue parsing until next "real" space,		
            # so that filters are also included		
            i = next_space_index(subject, i)		
		
            res = subject[p:i]		
            while i < len(subject) and subject[i] in (' ', '\t'):		
                i += 1		
            self.backout.append(self.pointer)		
            self.pointer = i		
            return res		
        else:		
            p = i		
            i = next_space_index(subject, i)		
            s = subject[p:i]		
            while i < len(subject) and subject[i] in (' ', '\t'):		
                i += 1		
            self.backout.append(self.pointer)		
            self.pointer = i		
            return s		

def inline_trans(parser, token):

    class TranslateParser(TokenParser):

        def top(self):
            value = self.value()
            if self.more():
                if self.tag() == 'noop':
                    noop = True
                else:
                    raise TemplateSyntaxError("only option for 'trans' is 'noop'")
            else:
                noop = False
            return (value, noop)
    value, noop = TranslateParser(token.contents).top()

    return InlineTranslateNode(parser.compile_filter(value), noop)

register.tag('inline_trans', inline_trans)
register.tag('itrans', inline_trans)


@register.inclusion_tag('inlinetrans/inline_header.html', takes_context=True)
def inlinetrans_static(context):
    tag_context = {
        'can_translate': False,
        'is_staff': False,  # backward compatible
        'INLINETRANS_STATIC_URL': get_static_url(),
        'INLINETRANS_MEDIA_URL': get_static_url(),  # backward compatible
        'request': context['request'],
    }
    user = context.get('user', None)
    if user and get_user_can_translate(user):
        tag_context.update({
            'can_translate': True,
            'is_staff': True,  # backward compatible
            'language': get_language_name(get_language()),
        })
    return tag_context


@register.inclusion_tag('inlinetrans/inline_header.html', takes_context=True)
def inlinetrans_media(context):  # backward compatible
    return inlinetrans_static(context)


@register.inclusion_tag('inlinetrans/inline_toolbar.html', takes_context=True)
def inlinetrans_toolbar(context, node_id):
    tag_context = {
        'INLINETRANS_STATIC_URL': get_static_url(),
        'INLINETRANS_MEDIA_URL': get_static_url(),  # backward compatible
        'request': context['request'],
        'set_new_translation_url': reverse('set_new_translation'),
        'do_restart_url': reverse('apply_changes'),
    }
    user = context.get('user', None)
    if user and get_user_can_translate(user):
        tag_context.update({
            'can_translate': True,
            'is_staff': True,  # backward compatible
            'language': get_language_name(get_language()),
            'node_id': node_id,
        })
    else:
        tag_context.update({
            'can_translate': False,
            'is_staff': False,  # backward compatible
            'INLINETRANS_STATIC_URL': get_static_url(),
            'INLINETRANS_MEDIA_URL': get_static_url(),  # backward compatible
            'request': context['request'],
        })
    return tag_context
