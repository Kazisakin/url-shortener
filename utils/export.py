# utils/export.py
from flask import Response

def export_urls_to_csv(urls):
    output = ['Short URL,Original URL,Clicks']
    for url in urls:
        short_url = f'http://yourdomain.com/{url.short_alias}'
        output.append(f"{short_url},{url.original_url},{len(url.clicks)}")
    return Response(
        '\n'.join(output),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=urls.csv'}
    )