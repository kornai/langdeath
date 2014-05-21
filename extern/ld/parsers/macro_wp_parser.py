import re


from base_parsers import OnlineParser
from utils import get_html


url = "http://en.wikipedia.org/wiki/ISO_639_macrolanguage"

a_tag_pat = re.compile("<a [^>]+>(.+?)</a>")


def remove_href(s):
    mo = a_tag_pat.search(s)
    if mo:
        return mo.group(1)
    else:
        return s


def get_macrolang_table(html):
    maybe = html.split("<table class=\"wikitable sortable\">")[1].split(
        "</table>")[0]
    if "th>Name of macrolanguage</th>" in maybe:
        return maybe


def parse_macrolang_table(table):
    header_s = table.split("<th>")
    header = []
    for h_element in header_s[1:]:
        h_element = h_element.split("</th>")[0]
        header.append(h_element)

    rows = table.split("<tr>")

    # remove header
    del rows[0:2]

    langs = []
    for row in rows:
        data = {}
        i = 0
        for td in row.split("<td>")[1:]:
            td = td.split("</td>")[0]
            td = remove_href(td)
            data[header[i]] = td
            i += 1
        langs.append(data)
    return langs


def get_detailed_list(html):
    return html.split('<h2><span class="mw-headline" id="List_of_macrolanguages_and_the_individual_languages">')[1].split('<h2><span class="mw-headline" id="See_also_3">')[0]  # nopep8


def parse_detailed_list(html):
    for h4 in html.split("<h4>")[1:]:
        code = h4.split('<span class="mw-headline"')[1].split(
            "</span>")[0].split(">")[1]
        print repr(code)
        children_list = h4.split("<ol>")[1].split("</ol>")[0]
        children = []
        for child in children_list.split("<li>")[1:]:
            try:
                child_code = remove_href(
                    child.split("<tt>")[1].split("</tt>")[0])
                children.append(child_code)
            except IndexError:
                continue
        yield code, children

class MacroWPParser(OnlineParser):
    def parse():
        html = get_html(url)
        detailed_list = get_detailed_list(html)
        for res in parse_detailed_list(detailed_list):
            champion, children = res
            for child in children:
                yield {'sil': child,
                       'champion': champion
                      }


def main():
    html = get_html(url)
    table = get_macrolang_table(html)
    langs = parse_macrolang_table(table)
    detailed_list = get_detailed_list(html)
    parse_detailed_list(detailed_list)


if __name__ == "__main__":
    main()
