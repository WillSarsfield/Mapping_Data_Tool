from bs4 import BeautifulSoup
import pathlib
import shutil
import argparse
import streamlit as st

'''
Adds a Google Analytics tracking tag to the base Streamlit html page header.

Taken from:
https://medium.com/@calebdame/google-analytics-for-streamlit-in-3-easy-steps-06e4cd2fd02e
'''

GA_ID = "google_analytics"
GA_SCRIPT = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=XXX"></script>
<script id='google_analytics'>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'XXX');
</script>
"""

def inject_ga(google_analytics_id):
    index_path = pathlib.Path(st.__file__).parent / "static" / "index.html"
    soup = BeautifulSoup(index_path.read_text(), features="html.parser")
    if not soup.find(id=GA_ID): 
        bck_index = index_path.with_suffix('.bck')
        if bck_index.exists():
            shutil.copy(bck_index, index_path)  
        else:
            shutil.copy(index_path, bck_index)  
        html = str(soup)
        new_html = html.replace('<head>', '<head>\n' + GA_SCRIPT.replace('XXX', google_analytics_id))
        index_path.write_text(new_html)

# Look for a gtag ID passed as a command line argument.
# If present, inject the gtag code into the Streamlit html page header.

parser = argparse.ArgumentParser()
parser.add_argument('-i', "--id",)  
args = parser.parse_args()
google_analytics_id = args.id

if google_analytics_id:
    inject_ga(google_analytics_id)
