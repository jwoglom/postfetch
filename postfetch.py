import datetime, json, os, requests
from subprocess import Popen

def get_json(date):
    return requests.get("https://www.washingtonpost.com/wp-stat/tablet/v1.1/{date}/tablet_{date}.json".format(date=date)).json()

def get_pdf_url(info):
    return "https://www.washingtonpost.com/wp-stat/tablet/v1.1/{date}/{pdf}".format(date=info[0], pdf=info[2])

def get_pdf_save(info):
    return "out/{date}/{pdf}".format(date=info[0], pdf=info[2])

def parse_json(json):
    data = []

    date = json["sections"]["pubdate"]
    sections = json["sections"]["section"]
    for section in sections:
        sname = section["name"]
        pages = section["pages"]["page"]
        for page in pages:
            data.append((date, page["page_name"], page["hires_pdf"]))

    return data

def init_folder(date):
    if not os.path.exists('out'):
        os.mkdir('out')

    base = 'out/{}/'.format(int(date))
    if not os.path.exists(base):
        os.mkdir(base)

def download_pdf(info):
    url = get_pdf_url(info)
    save = get_pdf_save(info)
    open(save, 'wb').write(requests.get(url).content)
    print("=== saved", save)

def download_data(data):
    for info in data:
        download_pdf(info)


def run(date):
    print("== Processing", date)
    json = get_json(date)
    init_folder(date)
    data = parse_json(json)
    print("== Downloading", date)
    download_data(data)

def get_dates():
    cur_dates = set(filter((lambda x: x.isnumeric() and len(x) == 8), os.listdir('out')))
    start_date = datetime.date(2015, 5, 20) # first date where files exist
    end_date = datetime.datetime.now().date()
    dates = set()
    d = start_date
    while d <= end_date:
        if d not in cur_dates:
            fmt = '{}{}{}'.format(d.year, '%02d'%d.month, '%02d'%d.day)
            dates.add(fmt)
        d += datetime.timedelta(days=1)

    return sorted(dates)

def main():
    dates = get_dates()
    print("Dates to download...", len(dates))
    i = 0
    for d in dates:
        run(d)
        i += 1
        if i%10 == 0:
            print("=", len(dates)-i, "downloads remaining...")

    print("Completed", len(dates), "downloads.")

if __name__ == '__main__':
    main()

