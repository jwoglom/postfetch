import datetime, json, os, requests, argparse
from subprocess import Popen

DEFAULT_START_DATE = "20150520" # first date where files exist

parser = argparse.ArgumentParser(description="Download Washington Post archives.")
parser.add_argument('--all', dest='all', action='store_const', const=True, default=False,
    help='download all available pages')
parser.add_argument('--date', dest='date', type=str, metavar='YYYYMMDD',
    help='download for this specific date (format YYYYMMDD)')
parser.add_argument('--date-range', dest='date_range', action='store_const', const=True, default=False,
    help='download for a specific range of dates.')

parser.add_argument('--start-date', dest='start_date', type=str, default=DEFAULT_START_DATE, metavar='YYYYMMDD',
    help='the initial date to download from (format YYYYMMDD)')
parser.add_argument('--start-auto', dest='start_auto', action='store_const', const=True,
    help='auto-determine start date if applicable (using last date stored previously)')
parser.add_argument('--recheck-recent', dest='recheck_recent', action='store_const', const=True,
    help='recheck for new editions from yesterday')
parser.add_argument('--end-date', dest='end_date', type=str, default=None, metavar='YYYYMMDD',
    help='the date to download until (format YYYYMMDD)')
parser.add_argument('--thumbnails', dest='thumbnails', action='store_const', const=True, default=False,
    help='download thumbnails')
parser.add_argument('--no-thumbnails', dest='thumbnails', action='store_const', const=False,
    help='do not download thumbnails (default)')
parser.add_argument('--pdfs', dest='pdfs', action='store_const', const=True, default=True,
    help='download pdfs (default)')
parser.add_argument('--no-pdfs', dest='pdfs', action='store_const', const=False,
    help='do not download pdfs')

parser.add_argument('--only-front', dest='only_front', action='store_const', const=True,
    help='download only front page')


args = vars(parser.parse_args())

def main():
    if args["date"]:
        run_date(args["date"], dw_pdf=args["pdfs"], dw_thumb=args["thumbnails"], only_front=args["only_front"])
    elif args["date_range"] or args["all"]:
        dates = get_dates(args["start_date"], args["end_date"], start_auto=args["start_auto"], recheck_recent=args["recheck_recent"])
        print('Got dates:', dates)
        for date in dates:
            run_date(date, dw_pdf=args["pdfs"], dw_thumb=args["thumbnails"], only_front=args["only_front"])
    else:
        exit("Specify either --date, --date-range, or --all")

def parse_date(datestr):
    return datetime.datetime.strptime(datestr, "%Y%m%d").date()

def get_json(date):
    r = requests.get("https://www.washingtonpost.com/wp-stat/tablet/v1.1/{date}/tablet_{date}.json".format(date=date))
    if r:
        return r.json()

def get_pdf_url(info):
    return "https://www.washingtonpost.com/wp-stat/tablet/v1.1/{date}/{pdf}".format(date=info[0], pdf=info[2])

def get_thumb_url(info):
    return "https://www.washingtonpost.com/wp-stat/tablet/v1.1/{date}/{thumb}".format(date=info[0], thumb=info[3])

def get_pdf_save(info):
    return "out/{date}/{pdf}".format(date=info[0], pdf=info[2])

def get_thumb_save(info):
    return "out/{date}/thumb/{thumb}".format(date=info[0], thumb=info[3])

def parse_json(jsond, only_front):
    data = []

    date = jsond["sections"]["pubdate"]
    sections = jsond["sections"]["section"]
    for section in sections:
        sname = section["name"]
        pages = section["pages"]["page"]
        for page in pages:
            if (only_front and page["page_name"] == 'A01') or not only_front:
                data.append((date, page["page_name"], page["hires_pdf"], page["thumb_300"]))

    return data

def save_json(date, jsond):
    open('out/{}/tablet.json'.format(date), 'w').write(json.dumps(jsond))

def init_folder(date, dw_thumb=False):
    if not os.path.exists('out'):
        os.mkdir('out')

    base = 'out/{}/'.format(int(date))
    if not os.path.exists(base):
        os.mkdir(base)
    
    if not os.path.exists(base+'thumb'):
        os.mkdir(base+'thumb')

def download_pdf(info):
    url = get_pdf_url(info)
    save = get_pdf_save(info)
    if not os.path.exists(save):
        content = requests.get(url).content
        print('=== downloaded', url)
        open(save, 'wb').write(content)
        print('=== saved', save)

def download_thumb(info):
    url = get_thumb_url(info)
    save = get_thumb_save(info)
    if not os.path.exists(save):
        content = requests.get(url).content
        print('=== downloaded thumb', url)
        open(save, 'wb').write(content)
        print('=== saved thumb', save)

        
def run_date(date, dw_pdf, dw_thumb, only_front):
    print("=== Processing", date)
    jsond = get_json(date)
    if not jsond:
        print("=== SKIP", date)
        return
    print('=== got JSON, init folder')
    init_folder(date, dw_thumb)
    save_json(date, jsond)
    data = parse_json(jsond, only_front)
    print("=== Downloading", date)
    
    for info in data:
        if dw_pdf:
            download_pdf(info)
        if dw_thumb:
            download_thumb(info)

def get_dates(start_date, end_date, start_auto=False, recheck_recent=False):
    if not os.path.exists('out'):
        os.mkdir('out')
    if start_auto:
        cur_dates = set(filter((lambda x: x.isnumeric() and len(x) == 8), os.listdir('out')))
    else:
        cur_dates = set()
    if not start_date:
        start_date = DEFAULT_START_DATE
    else:
        start_date = parse_date(start_date)
    if not end_date:
        end_date = datetime.datetime.now().date()
    else:
        end_date = parse_date(end_date)
    dates = set()
    d = start_date
    while d <= end_date:
        f = '{}{}{}'.format(d.year, '%02d'%d.month, '%02d'%d.day)
        if f not in cur_dates:
            dates.add(f)
        if recheck_recent and d >= end_date+datetime.timedelta(days=-1):
            dates.add(f)
        d += datetime.timedelta(days=1)
    return sorted(dates)

if __name__ == '__main__':
    main()

