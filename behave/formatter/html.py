# -*- coding: utf-8 -*-
"""
Creates a very basic one-page html file for reporting a test run.
"""

from __future__ import absolute_import
from behave.formatter.base import Formatter
from behave.formatter.css import BasicTheme
from behave.compat.collections import Counter
import xml.etree.ElementTree as ET
import base64


def _valid_XML_char_ordinal(i):
    return (  # conditions ordered by presumed frequency
        0x20 <= i <= 0xD7FF
        or i in (0x9, 0xA, 0xD)
        or 0xE000 <= i <= 0xFFFD
        or 0x10000 <= i <= 0x10FFFF
    )


def ET_tostring(elem, pretty_print=False):
    text = ET.tostring(elem, "utf-8")
    if pretty_print:
        pass
    return text


class JavaScriptLibrary(object):
    collapsible = """
function collapsible_toggle(id)
{
    var elem = document.getElementById(id);
    elem.style.display = (elem.style.display == 'none' ? 'block' : 'none');
    return false;
}

function collapsible_expandAll(className)
{
    var elems = document.getElementsByClassName(className);
    var i = 0;
    while (i != elems.length)
    {
        elems[i].style.display = 'block';
        i++
    }
}

function collapsible_collapseAll(className)
{
    var elems = document.getElementsByClassName(className);
    var i = 0;
    while (i != elems.length)
    {
        elems[i].style.display = 'none';
        i++
    }
}
"""


class Page(object):
    """
    Provides a HTML page construct (as technological layer).
    XXX
    """
    theme = BasicTheme

    def __init__(self, title=None):
        pass


# -----------------------------------------------------------------------------
# CLASS: HTMLFormatter
# -----------------------------------------------------------------------------
class HTMLFormatter(Formatter):
    """
    Provides a single-page HTML formatter that writes the result of a  test run.
    """
    name = 'html'
    description = 'Basic HTML formatter'
    title = u"Behave Test Report"

    def __init__(self, stream_opener, config):
        super(HTMLFormatter, self).__init__(stream_opener, config)

        # -- XXX-JE-PREPARED-BUT-DISABLED:
        # XXX Seldom changed value.
        # XXX Should only be in configuration-file in own section "behave.formatter.html" ?!?
        # XXX Config support must be provided.
        # XXX REASON: Don't clutter behave config-space w/ formatter/plugin related config data.
        # self.css = self.default_css
        # if config.css is not None:
        #    self.css = config.css
        self.html = ET.Element('html')
        head = ET.SubElement(self.html, 'head')
        ET.SubElement(head, 'title').text = self.title
        ET.SubElement(head, 'meta', {'content': 'text/html;charset=utf-8'})
        style = ET.SubElement(head, 'style', type=u"text/css")
        style.text = Page.theme.stylesheet_text
        # style.append(ET.Comment(Page.theme.stylesheet_text))
        script = ET.SubElement(head, 'script', type=u"text/javascript")
        script.text = JavaScriptLibrary.collapsible
        # script_text = ET.Comment(JavaScriptLibrary.collapsible)
        # script.append(script_text)

        self.stream = self.open()
        body = ET.SubElement(self.html, 'body')
        self.suite = ET.SubElement(body, 'div', {'class': 'behave'})

        #Summary
        self.header = ET.SubElement(self.suite, 'div', id='behave-header')
        label = ET.SubElement(self.header, 'div', id='label')
        ET.SubElement(label, 'h1').text = self.title

        summary = ET.SubElement(self.header, 'div', id='summary')

        totals = ET.SubElement(summary, 'p', id='totals')

        self.current_feature_totals = ET.SubElement(totals, 'p', id='feature_totals')
        self.scenario_totals = ET.SubElement(totals, 'p', id='scenario_totals')
        self.step_totals = ET.SubElement(totals, 'p', id='step_totals')
        self.duration = ET.SubElement(summary, 'p', id='duration')

        # -- PART: Expand/Collapse All
        expand_collapse = ET.SubElement(summary, 'div', id='expand-collapse')
        expander = ET.SubElement(expand_collapse, 'a', id='expander', href="#")
        expander.set('onclick', "collapsible_expandAll('scenario_steps')")
        expander.text = u'Expand All'
        cea_spacer = ET.SubElement(expand_collapse, 'span')
        cea_spacer.text = u" | "
        collapser = ET.SubElement(expand_collapse, 'a', id='collapser', href="#")
        collapser.set('onclick', "collapsible_collapseAll('scenario_steps')")
        collapser.text = u'Collapse All'

        self.embed_id = 0
        self.embed_in_this_step = None
        self.embed_data = None
        self.embed_mime_type = None
        self.scenario_id = 0

    def feature(self, feature):
        if not hasattr(self, "all_features"):
            self.all_features = []
        self.all_features.append(feature)

        self.current_feature = ET.SubElement(self.suite, 'div', {'class': 'feature'})
        if feature.tags:
            tags_element = ET.SubElement(self.current_feature, 'span', {'class': 'tag'})
            tags_element.text = u'@' + reduce(lambda d, x: "%s, @%s" % (d, x), feature.tags)
        h2 = ET.SubElement(self.current_feature, 'h2')
        feature_element = ET.SubElement(h2, 'span', {'class': 'val'})
        feature_element.text = u'%s: %s' % (feature.keyword, feature.name)
        if feature.description:
            description_element = ET.SubElement(self.current_feature, 'pre', {'class': 'message'})
            description_element.text = reduce(lambda d, x: "%s\n%s" % (d, x), feature.description)

    def background(self, background):
        self.current_background = ET.SubElement(self.current_feature, 'div', {'class': 'background'})

        h3 = ET.SubElement(self.current_background, 'h3')
        ET.SubElement(h3, 'span', {'class': 'val'}).text = \
            u'%s: %s' % (background.keyword, background.name)

        self.steps = ET.SubElement(self.current_background, 'ol')

    def scenario(self, scenario):
        if scenario.feature not in self.all_features:
            self.all_features.append(scenario.feature)
        self.scenario_el = ET.SubElement(self.current_feature, 'div', {'class': 'scenario'})

        scenario_file = ET.SubElement(self.scenario_el, 'span', {'class': 'scenario_file'})
        scenario_file.text = "%s:%s" % (scenario.location.filename, scenario.location.line)

        if scenario.tags:
            tags = ET.SubElement(self.scenario_el, 'span', {'class': 'tag'})
            tags.text = u'@' + reduce(lambda d, x: "%s, @%s" % (d, x), scenario.tags)

        self.scenario_name = ET.SubElement(self.scenario_el, 'h3')
        span = ET.SubElement(self.scenario_name, 'span', {'class': 'val'})
        span.text = u'%s: %s' % (scenario.keyword, scenario.name)

        if scenario.description:
            description_element = ET.SubElement(self.scenario_el, 'pre', {'class': 'message'})
            description_element.text = reduce(lambda d, x: "%s\n%s" % (d, x), scenario.description)

        self.steps = ET.SubElement(self.scenario_el, 'ol',
                                   {'class': 'scenario_steps',
                                    'id': 'scenario_%s' % self.scenario_id})

        self.scenario_name.set("onclick",
                               "collapsible_toggle('scenario_%s')" % self.scenario_id)
        self.scenario_id += 1

    def scenario_outline(self, outline):
        self.scenario(self, outline)
        self.scenario_el.set('class', 'scenario outline')

    def match(self, match):
        self.arguments = match.arguments
        if match.location:
            self.location = "%s:%s" % (match.location.filename, match.location.line)
        else:
            self.location = "<unknown>"

    def step(self, step):
        self.arguments = None
        self.embed_in_this_step = None
        self.last_step = step

    def result(self, result):
        self.last_step = result

        # update feature class according to result status
        current_feature_class=self.current_feature.attrib["class"]
        if "failed" == result.status:
            if current_feature_class in ["feature", "feature passed", "feature failed"]:
                self.current_feature.attrib["class"] = "feature failed"
            else:
                raise
        elif "passed" == result.status:
            if current_feature_class in ["feature", "feature passed"]:
                self.current_feature.attrib["class"] = "feature passed"
            elif current_feature_class in ["feature failed"]:
                pass
            else:
                raise
            pass
        else:
            raise

        step = ET.SubElement(self.steps, 'li', {'class': 'step %s' % result.status})
        step_name = ET.SubElement(step, 'div', {'class': 'step_name'})

        keyword = ET.SubElement(step_name, 'span', {'class': 'keyword'})
        keyword.text = result.keyword + u' '

        if self.arguments:
            text_start = 0
            for argument in self.arguments:
                step_text = ET.SubElement(step_name, 'span', {'class': 'step val'})
                step_text.text = result.name[text_start:argument.start]
                ET.SubElement(step_text, 'b').text = str(argument.value)
                text_start = argument.end
            step_text = ET.SubElement(step_name, 'span', {'class': 'step val'})
            step_text.text = result.name[self.arguments[-1].end:]
        else:
            step_text = ET.SubElement(step_name, 'span', {'class': 'step val'})
            step_text.text = result.name

        step_file = ET.SubElement(step, 'div', {'class': 'step_file'})
        ET.SubElement(step_file, 'span').text = self.location

        self.last_step_embed_span = ET.SubElement(step, 'span')
        self.last_step_embed_span.set('class', 'embed')

        if result.text:
            message = ET.SubElement(step, 'div', {'class': 'message'})
            pre = ET.SubElement(message, 'pre', {'style': 'white-space: pre-wrap;'})
            pre.text = result.text

        if result.table:
            table = ET.SubElement(step, 'table')
            tr = ET.SubElement(table, 'tr')
            for heading in result.table.headings:
                ET.SubElement(tr, 'th').text = heading

            for row in result.table.rows:
                tr = ET.SubElement(table, 'tr')
                for cell in row.cells:
                    ET.SubElement(tr, 'td').text = cell

        if result.error_message:
            self.embed_id += 1
            link = ET.SubElement(step, 'a', {'class': 'message'})
            link.set("onclick",
                     "collapsible_toggle('embed_%s')" % self.embed_id)
            link.text = u'Error message'

            embed = ET.SubElement(step, 'pre',
                                  {'id': "embed_%s" % self.embed_id,
                                  'style': 'display: none; white-space: pre-wrap;'})
            cleaned_error_message = ''.join(
                c for c in result.error_message if _valid_XML_char_ordinal(ord(c))
            )
            embed.text = cleaned_error_message
            embed.tail = u'    '

        if result.status == 'failed':
            style = 'background: #C40D0D; color: #FFFFFF'
            self.scenario_name.set('style', style)
            self.header.set('style', style)

        if result.status == 'undefined':
            style = 'background: #FAF834; color: #000000'
            self.scenario_name.set('style', style)
            self.header.set('style', style)

        if hasattr(self, 'embed_in_this_step') and self.embed_in_this_step:
            self._doEmbed(self.last_step_embed_span,
                          self.embed_mime_type,
                          self.embed_data,
                          self.embed_caption)
            self.embed_in_this_step = None

    def _doEmbed(self, span, mime_type, data, caption):
        self.embed_id += 1

        link = ET.SubElement(span, 'a')
        link.set("onclick", "collapsible_toggle('embed_%s')" % self.embed_id)

        if 'video/' in mime_type:
            if not caption:
                caption = u'Video'
            link.text = unicode(caption)

            embed = ET.SubElement(span, 'video',
                                  {'id': 'embed_%s' % self.embed_id,
                                   'style': 'display: none',
                                   'width': '320',
                                   'controls': ''})
            embed.tail = u'    '
            ET.SubElement(embed, 'source', {
                          'src': u'data:%s;base64,%s' % (mime_type, base64.b64encode(data)),
                          'type': '%s; codecs="vp8 vorbis"' % mime_type})

        if 'image/' in mime_type:
            if not caption:
                caption = u'Screenshot'
            link.text = unicode(caption)

            embed = ET.SubElement(span, 'img', {
                                  'id': 'embed_%s' % self.embed_id,
                                  'style': 'display: none',
                                  'src': u'data:%s;base64,%s' % (
                                      mime_type, base64.b64encode(data))})
            embed.tail = u'    '

        if 'text/' in mime_type:
            if not caption:
                caption = u'Data'
            link.text = unicode(caption)

            cleaned_data = ''.join(
                c for c in data if _valid_XML_char_ordinal(ord(c))
            )

            embed = ET.SubElement(span, 'pre',
                                  {'id': "embed_%s" % self.embed_id,
                                   'style': 'display: none'})
            embed.text = cleaned_data
            embed.tail = u'    '

    def embedding(self, mime_type, data, caption=None):
        if self.last_step.status == 'untested':
            # Embed called during step execution
            self.embed_in_this_step = True
            self.embed_mime_type = mime_type
            self.embed_data = data
            self.embed_caption = caption
        else:
            # Embed called in after_*
            self._doEmbed(self.last_step_embed_span, mime_type, data, caption)

    def close(self):
        if not hasattr(self, "all_features"):
            self.all_features = []
        self.duration.text =\
            u"Finished in %0.1f seconds" %\
            sum(map(lambda x: x.duration, self.all_features))

        # Filling in summary details
        result = []
        statuses = map(lambda x: x.status, self.all_features)
        status_counter = Counter(statuses)
        for k in status_counter:
            result.append('%s: %s' % (k, status_counter[k]))
        self.current_feature_totals.text = u'Features: %s' % ', '.join(result)

        result = []
        scenarios_list = map(lambda x: x.scenarios, self.all_features)
        scenarios = []
        if len(scenarios_list) > 0:
            scenarios = reduce(lambda a, b: a + b, scenarios_list)
        statuses = map(lambda x: x.status, scenarios)
        status_counter = Counter(statuses)
        for k in status_counter:
            result.append('%s: %s' % (k, status_counter[k]))
        self.scenario_totals.text = u'Scenarios: %s' % ', '.join(result)

        result = []
        step_list = map(lambda x: x.steps, scenarios)
        steps = []
        if step_list:
            steps = reduce(lambda a, b: a + b, step_list)
        statuses = map(lambda x: x.status, steps)
        status_counter = Counter(statuses)
        for k in status_counter:
            result.append('%s: %s' % (k, status_counter[k]))
        self.step_totals.text = u'Steps: %s' % ', '.join(result)

        # Sending the report to stream
        if len(self.all_features) > 0:
            self.stream.write(u"<!DOCTYPE HTML>\n")
            self.stream.write(ET_tostring(self.html, pretty_print=True))
