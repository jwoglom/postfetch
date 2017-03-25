import datetime, json, os, requests
from subprocess import Popen

def get_json(date):
    r = requests.get("https://www.washingtonpost.com/wp-stat/tablet/v1.1/{date}/tablet_{date}.json".format(date=date))
    if r:
        return r.json()

def get_pdf_url(info):
    return "https://www.washingtonpost.com/wp-stat/tablet/v1.1/{date}/{pdf}".format(date=info[0], pdf=info[2])

def get_pdf_save(info):
    return "out/{date}/{pdf}".format(date=info[0], pdf=info[2])

def parse_json(jsond):
    data = []

    date = jsond["sections"]["pubdate"]
    sections = jsond["sections"]["section"]
    for section in sections:
        sname = section["name"]
        pages = section["pages"]["page"]
        for page in pages:
            data.append((date, page["page_name"], page["hires_pdf"]))

    return data

def save_json(date, jsond):
    open('out/{}/tablet.json'.format(date), 'w').write(json.dumps(jsond))

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
    print("== saved", save)

def download_data(data):
    for info in data:
        print("== download", info)
        download_pdf(info)


def run(date):
    print("=== Processing", date)
    jsond = get_json(date)
    if not jsond:
        print("=== SKIP", date)
        return
    init_folder(date)
    save_json(date, jsond)
    data = parse_json(jsond)
    print("=== Downloading", date)
    download_data(data)

def get_dates():
    if not os.path.exists('out'):
        os.mkdir('out')
    cur_dates = set(filter((lambda x: x.isnumeric() and len(x) == 8), os.listdir('out')))
    start_date = datetime.date(2015, 5, 20) # first date where files exist
    end_date = datetime.datetime.now().date()
    dates = set()
    d = start_date
    while d <= end_date:
        f = '{}{}{}'.format(d.year, '%02d'%d.month, '%02d'%d.day)
        if f not in cur_dates:
            dates.add(f)
        d += datetime.timedelta(days=1)

    return sorted(dates)

def main():
    dates = get_dates()
    print("Dates to download...", len(dates))
    print(dates)
    i = 0
    for d in dates:
        run(int(d))
        i += 1
        if i%10 == 0:
            print("=", len(dates)-i, "downloads remaining...")

    print("Completed", len(dates), "downloads.")

if __name__ == '__main__':
    main()

