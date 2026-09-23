from pathlib import Path
from bs4 import BeautifulSoup
import hashlib

base = Path('baseline.html').read_text()

# Comparator A: move the whole verified desktop section ahead of the failed showcase.
soup = BeautifulSoup(base, 'html.parser')
main = soup.find('main', id='main')
hero = main.find('section', class_='hero')
desktop = main.find('section', class_=lambda x: x and 'desktop' in x.split())
desktop.extract()
hero.insert_after(desktop)
Path('candidate_reorder.html').write_text(str(soup))

# Comparator B: swap only the two media figures; section copy/order remains fixed.
soup = BeautifulSoup(base, 'html.parser')
main = soup.find('main', id='main')
doom = main.find('figure', class_=lambda x: x and 'hero-media' in x.split())
desktop = main.find('section', class_=lambda x: x and 'desktop' in x.split())
deskfig = desktop.find('figure')
doom_clone = BeautifulSoup(str(doom), 'html.parser').find('figure')
desk_clone = BeautifulSoup(str(deskfig), 'html.parser').find('figure')
desk_clone['class'] = ['hero-media', 'wrap']
doom_clone.attrs.pop('class', None)
doom.replace_with(desk_clone)
deskfig.replace_with(doom_clone)
Path('candidate_swapmedia.html').write_text(str(soup))

for name in ('baseline.html', 'candidate_reorder.html', 'candidate_swapmedia.html'):
    data = Path(name).read_bytes()
    print(name, len(data), hashlib.sha256(data).hexdigest())
