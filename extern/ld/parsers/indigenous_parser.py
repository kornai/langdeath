from utils import get_html
from base_parsers import OnlineParser


tweets_url = "http://indigenoustweets.com/"
blogs_url = "http://indigenoustweets.com/blogs/"


class IndigenousParser(OnlineParser):
    def __init__(self):
        self.needed_keys = {
            "Language": "name",
            "code": "code",
            "Blogs": "indi_blogs",
            "Posts": "indi_posts",
            "Words": "indi_words",
            "Users": "indi_users",
            "Tweets": "indi_tweets"
        }
        pass

    def get_header(self, html):
        h = html.split("<thead>")[1].split("</thead>")[0]
        header = []
        for s in h.split("</th>")[:-1]:
            h_part = s.split(">")[-1]
            if h_part in header:
                # hack to avoid same header "Tweets" twice
                h_part = h_part + "_2"
            header.append(h_part)
        return header

    def get_rows(self, html):
        body = html.split("<tbody>")[1].split("</tbody>")[0]
        for s in body.split("</tr>")[:-1]:
            data = []
            for d in s.split("</td>")[:-1]:
                data.append(d.split("<td>")[1])
            link = data[0]
            data.append(link.split("\"")[1].rstrip("/"))
            data[0] = link.split(">")[1].split("<")[0]
            yield data

    def html_to_dict(self, html):
        h = self.get_header(html)
        d = {}
        for row in self.get_rows(html):
            # add row data based on header into a dict
            data = dict([(self.needed_keys[h[i]], row[i]) for i in
                         xrange(len(row) - 1) if h[i] in self.needed_keys])
            data['code'] = row[-1]
            d[row[-1]] = data
        return d

    def merge_data(self, data1, data2):
        for l2 in data2:
            if l2 in data1:
                data1[l2].update(data2[l2])

    def parse(self):
        tweets_html = get_html(tweets_url)
        blogs_html = get_html(blogs_url)
        tweets_data = self.html_to_dict(tweets_html)
        blogs_data = self.html_to_dict(blogs_html)
        self.merge_data(tweets_data, blogs_data)
        for l in tweets_data:
            yield tweets_data[l]


def main():
    i = IndigenousParser()
    for d in i.parse():
        print d


if __name__ == "__main__":
    main()
