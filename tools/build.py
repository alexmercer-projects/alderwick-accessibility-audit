"""Builds index.html for the Alderwick Family Clinic accessibility audit concept demo.
Findings live in one list so the summary counts, charts and table always agree.
Every contrast ratio quoted on the page is computed here with the WCAG 2.x formula."""
import html, re, sys, os

OUT = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
# --standalone: links for the GitHub Pages copy (PDF next to index.html, portfolio link absolute)
STANDALONE = '--standalone' in sys.argv
E = html.escape

def lum(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def cr(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)
def ratio(a, b):
    # WCAG says don't round up to pass; truncate to 2 decimals
    r = int(cr(a, b) * 100) / 100
    return f'{r:.2f}:1'

C = dict(gray=('#9a9a9a', '#ffffff'), gray_fix=('#5c6670', '#ffffff'),
         btn=('#ffffff', '#3fb8af'), btn_fix=('#ffffff', '#1f6f69'),
         border=('#cfd4d9', '#ffffff'), border_fix=('#7d8791', '#ffffff'))
R = {k: ratio(*v) for k, v in C.items()}

SC = {  # number: (name, level, new in 2.2?)
 '1.1.1': ('Non-text Content', 'A', 0), '1.2.2': ('Captions (Prerecorded)', 'A', 0),
 '1.3.1': ('Info and Relationships', 'A', 0), '1.3.2': ('Meaningful Sequence', 'A', 0),
 '1.4.1': ('Use of Color', 'A', 0), '1.4.3': ('Contrast (Minimum)', 'AA', 0),
 '1.4.10': ('Reflow', 'AA', 0), '1.4.11': ('Non-text Contrast', 'AA', 0),
 '2.1.2': ('No Keyboard Trap', 'A', 0), '2.4.2': ('Page Titled', 'A', 0),
 '2.4.4': ('Link Purpose (In Context)', 'A', 0), '2.4.6': ('Headings and Labels', 'AA', 0),
 '2.4.7': ('Focus Visible', 'AA', 0), '2.4.11': ('Focus Not Obscured (Minimum)', 'AA', 1),
 '2.5.8': ('Target Size (Minimum)', 'AA', 1), '3.1.1': ('Language of Page', 'A', 0),
 '3.1.2': ('Language of Parts', 'AA', 0),
 '3.2.6': ('Consistent Help', 'A', 1), '3.3.1': ('Error Identification', 'A', 0),
 '3.3.2': ('Labels or Instructions', 'A', 0), '3.3.8': ('Accessible Authentication (Minimum)', 'AA', 1),
 '4.1.2': ('Name, Role, Value', 'A', 0),
}
PRINC = {'1': 'Perceivable', '2': 'Operable', '3': 'Understandable', '4': 'Robust'}

# id, severity, title, [sc], where, who, problem, fix, fixref
F = [
 ('01', 'Critical', 'The “Book online” window can’t be closed or left with a keyboard', ['2.1.2', '4.1.2'], 'Book an appointment; every “Book online” button',
  'Keyboard-only, switch and screen reader users',
  'Tab cycles inside the booking window forever. The close “×” is a <div> with a click handler, so it can’t be reached, and Esc does nothing. The only way out is to reload the page.',
  'Use a real <button> to close, let Esc close it, and send focus back to the button that opened it. A native <dialog> opened with showModal() does most of this for free.', 'fix-trap'),
 ('02', 'Critical', 'Appointment form fields have no labels, only placeholder text', ['1.3.1', '3.3.2', '4.1.2'], 'Book an appointment: request form (7 fields)',
  'Screen reader and voice-control users; anyone who loses track once the hint disappears',
  'Fields are announced as “edit text, blank”. Date of birth is three unlabeled selects. The hint text vanishes as soon as someone starts typing.',
  'Give every field a visible <label for>, group date of birth in a <fieldset> with a <legend>, and add autocomplete tokens (given-name, bday-day and so on).', 'fix-labels'),
 ('03', 'Critical', 'Patient portal login blocks paste and password managers', ['3.3.8'], 'Patient portal login',
  'People with memory or cognitive disabilities, dyslexia, and anyone who relies on a password manager',
  'The password field cancels paste (onpaste="return false") and sets autocomplete="off", so the only way in is to recall and retype the password from memory.',
  'Remove the paste block. Use autocomplete="username" and autocomplete="current-password" so browsers and password managers can fill the form.', None),
 ('04', 'High', 'Provider photos and the insurance logo strip have no text alternative', ['1.1.1'], 'Find a provider (12 photos); Home (insurance strip)',
  'Screen reader users',
  'Headshots have no alt attribute, so screen readers read the file name (“dr_okafor_final2.jpg”). The accepted-insurance strip is one image holding nine plan names, with no text version.',
  'Mark headshots as decorative (alt="") because the name is right next to them. Replace the logo strip with a real list of plan names.', 'fix-alt'),
 ('05', 'High', f'Gray body text is too light ({R["gray"]})', ['1.4.3'], 'All pages: hours, addresses, form hints',
  'People with low vision or color-vision deficiency, older patients, anyone on a phone in daylight',
  f'Text in #9a9a9a on white measures {R["gray"]}. Normal-size text needs at least 4.5:1.',
  f'Darken it to #5c6670, which measures {R["gray_fix"]} and keeps the same quiet look.', 'fix-contrast'),
 ('06', 'High', f'White text on the teal “Book now” button is hard to read ({R["btn"]})', ['1.4.3'], 'Header and Home hero: “Book now” and “Pay a bill” buttons',
  'People with low vision or color-vision deficiency',
  f'White 16px text on #3fb8af measures {R["btn"]}. The label isn’t large text, so it needs 4.5:1.',
  f'Use a deeper teal, #1f6f69, which measures {R["btn_fix"]} with white text. Keep #3fb8af for decoration only.', 'fix-contrast'),
 ('07', 'High', 'Focus outline removed site-wide', ['2.4.7'], 'All pages (theme stylesheet)',
  'Keyboard-only users, switch users, people using screen magnifiers',
  'The theme sets *:focus { outline: none } with nothing to replace it, so there is no way to see which link, button or field is active.',
  'Delete the rule and add a clear :focus-visible style: a 3px outline with an offset, in a color that has at least 3:1 contrast against the page.', 'fix-focus'),
 ('08', 'High', 'Welcome video has no captions', ['1.2.2'], 'Home: 90-second “Welcome to Alderwick” video',
  'Deaf and hard-of-hearing patients; anyone watching with the sound off',
  'The embedded video has no caption track, and the auto-generated captions are switched off.',
  'Add an edited WebVTT caption file (check names and medical terms by hand) and link a text transcript under the video.', None),
 ('09', 'High', 'Form errors are shown by a red border only', ['3.3.1', '1.4.1'], 'Book an appointment; Pay a bill',
  'Screen reader users; people who can’t tell red from gray',
  'A missing or invalid field just turns its border red. There is no message, and screen readers announce nothing.',
  'Write the error as text next to the field, link it with aria-describedby, set aria-invalid="true", and on submit move focus to an error summary at the top of the form.', None),
 ('10', 'High', 'New-patient intake PDF is untagged', ['1.3.1', '1.3.2', '4.1.2'], 'New-patient intake form (4-page PDF)',
  'Screen reader users; people filling the form on a phone or with assistive tech',
  'The PDF has no tags, so it reads as one block of text. Reading order jumps between the two columns, and the 38 form fields have no names.',
  'Retag the PDF and fix the reading order, name every field, and set the title and language. The steps are in the PDF note below.', 'pdf'),
 ('11', 'Medium', 'Cookie banner and sticky header cover the focused element', ['2.4.11'], 'All pages until the cookie banner is dismissed',
  'Keyboard users, especially when zoomed in',
  'The 140px cookie banner fixed to the bottom of the screen hides links as you tab down the page. When tabbing back up, the sticky header hides them too.',
  'Put the banner’s buttons first in the tab order and don’t let it cover content (or make it a non-modal bar that pushes the page up). Add scroll-padding-top equal to the header height.', None),
 ('12', 'Medium', 'Headings are styled divs, and the real ones skip levels', ['1.3.1', '2.4.6'], 'Home, Find a provider',
  'Screen reader users who move around the page by heading',
  '“Our services” and “Locations” look like headings but are <div class="title">. The headings that do exist go from h1 straight to h4 because h4 had the right font size.',
  'Mark up every visual heading as a heading, in order (h1, then h2, then h3), and size them with CSS instead of picking a level for its looks.', 'fix-headings'),
 ('13', 'Medium', '“Read more” and “Click here” links don’t say where they go', ['2.4.4'], 'Home (6 links), Services (3 links), footer',
  'Screen reader users who list links on the page; voice-control users',
  'A links list reads “Read more, Read more, Read more…”. The card titles sit in a separate element, so the surrounding text doesn’t give the link its meaning.',
  'Make the link text say where it goes (“Pediatric care”), or make the card title the link itself.', 'fix-links'),
 ('14', 'Medium', 'Calendar days and social icons are tiny targets', ['2.5.8'], 'Booking calendar; footer social icons',
  'People with tremors or limited dexterity; most people on a phone',
  'Calendar days are 20×20 CSS px with a 2px gap. The footer social icons are 16×16 and sit right next to each other.',
  'Make targets at least 24×24 CSS px, or space them so a 24px circle around each one doesn’t overlap a neighbor. 44px is better for the calendar.', None),
 ('15', 'Medium', f'Form field borders are nearly invisible ({R["border"]})', ['1.4.11'], 'All forms',
  'People with low vision; anyone who has to find the fields',
  f'Input borders in #cfd4d9 on white measure {R["border"]}. Borders that show where a field is need 3:1.',
  f'Use #7d8791 for field borders ({R["border_fix"]}), or add a filled background that meets 3:1.', None),
 ('16', 'Medium', 'Pay a bill page needs sideways scrolling when zoomed', ['1.4.10'], 'Pay a bill',
  'People who zoom to 400% or use large text on small screens',
  'The page sits in a fixed 960px container. At 320 CSS px wide, every line has to be scrolled sideways to read.',
  'Change width: 960px to max-width: 960px with fluid padding, and let the two-column layout stack on narrow screens.', None),
 ('17', 'Low', 'Pages don’t declare their language', ['3.1.1', '3.1.2'], 'All pages; Spanish patient-information page',
  'Screen reader users (wrong voice and pronunciation)',
  'The <html> element has no lang attribute. The Spanish page gets read with English pronunciation.',
  'Add lang="en" site-wide and lang="es" on the Spanish page. Use lang on any Spanish phrases inside English pages too.', None),
 ('18', 'Low', 'Four pages share the same title', ['2.4.2'], 'Find a provider, Book an appointment, Pay a bill, Spanish page',
  'Screen reader users; anyone with several tabs open',
  'Four of the six pages are titled “Alderwick Family Clinic | Home”.',
  'Give each page a unique title that leads with the page: “Book an appointment | Alderwick Family Clinic”.', None),
 ('19', 'Low', 'The phone number moves between pages', ['3.2.6'], 'Book an appointment, Pay a bill',
  'People with cognitive disabilities who look for help in a familiar spot',
  'The call link sits in the header on four pages, but only in the footer on the two pages where people most often need help.',
  'Keep the phone and contact links in the same place, in the same order, on every page.', None),
]
SEVS = ['Critical', 'High', 'Medium', 'Low']
SEVDEF = {
 'Critical': 'Stops some people from finishing a key task (booking, logging in) at all.',
 'High': 'A key task is possible but hard, or content is missing for some users.',
 'Medium': 'Causes real friction or confusion, usually with a workaround.',
 'Low': 'Minor, but quick to fix and worth doing.',
}
counts = {s: sum(1 for f in F if f[1] == s) for s in SEVS}
total = len(F)
uniq_sc = sorted({s for f in F for s in f[3]}, key=lambda x: [int(p) for p in x.split('.')])
new22 = [s for s in uniq_sc if SC[s][2]]
by_pr = {p: sum(1 for f in F if any(x[0] == p for x in f[3])) for p in PRINC}
lvlA = sum(1 for f in F if SC[f[3][0]][1] == 'A'); lvlAA = total - lvlA
assert sum(counts.values()) == total

def code(s):
    s = E(s.strip('\n'))
    s = re.sub(r'(&lt;!--.*?--&gt;|/\*.*?\*/|//[^\n]*)', r'<span class="cm">\1</span>', s)
    return s

FIX = [
 ('fix-alt', 'Text alternatives', ['04'], '1.1.1',
  'Decide what each image is for. A photo next to the doctor’s name adds nothing for a screen reader, so it gets an empty alt. An image that holds information needs that information as text.',
  '''<img src="dr_okafor_final2.jpg">
<span class="name">Dr. Ama Okafor</span>

<!-- nine plan names, all inside one picture -->
<img src="insurance-logos.png">''',
  '''<img src="dr-okafor.jpg" alt="">
<span class="name">Dr. Ama Okafor</span>

<h3>Insurance we accept</h3>
<ul class="plans">
  <li>Example Health Plan</li>
  <li>Sample Mutual</li>
  <!-- … one item per plan -->
</ul>''', None),
 ('fix-contrast', 'Color contrast', ['05', '06'], '1.4.3',
  'Both pairs keep the clinic’s look but get dark enough to read. These ratios are computed with the WCAG relative-luminance formula and truncated, not rounded up.',
  '''.meta    { color: #9a9a9a; }  /* on #fff */
.btn-book { background: #3fb8af;
            color: #fff; }''',
  '''.meta    { color: #5c6670; }  /* on #fff */
.btn-book { background: #1f6f69;
            color: #fff; }''', 'swatches'),
 ('fix-labels', 'Form labels', ['02'], '3.3.2',
  'Placeholders aren’t labels. A visible label stays put, is read by screen readers, and gives voice-control users a name to say (“click First name”).',
  '''<input type="text" placeholder="First name">

<select name="dob_m">…</select>
<select name="dob_d">…</select>
<select name="dob_y">…</select>''',
  '''<label for="fname">First name</label>
<input id="fname" type="text"
       autocomplete="given-name">

<fieldset>
  <legend>Date of birth</legend>
  <label for="dob-m">Month</label>
  <select id="dob-m"
          autocomplete="bday-month">…</select>
  <!-- same for Day and Year -->
</fieldset>''', None),
 ('fix-focus', 'Visible focus', ['07'], '2.4.7',
  'Don’t remove the outline. Replace it with one that’s easier to see than the browser default, and only show it for keyboard focus.',
  '''/* theme.css */
*:focus { outline: none; }''',
  '''/* #1f6f69 is 5.93:1 on #fff */
:focus-visible {
  outline: 3px solid #1f6f69;
  outline-offset: 2px;
  border-radius: 4px;
}''', None),
 ('fix-trap', 'Keyboard trap in the booking window', ['01'], '2.1.2',
  'A modal should hold focus while it’s open, but there always has to be a way out. The native <dialog> element gives you Esc to close and a proper modal state.',
  '''<div class="modal" id="book">
  <div class="x" onclick="hide()">×</div>
  …
</div>
<script>
  // sends Tab back to the first field, forever
  last.onblur = () => first.focus();
</script>''',
  '''<dialog id="book" aria-labelledby="book-h">
  <h2 id="book-h">Book online</h2>
  <button type="button" class="x"
          aria-label="Close">×</button>
  …
</dialog>
<script>
  const d = document.querySelector('#book');
  let opener;
  function openBook(btn) {
    opener = btn;
    d.showModal();  // Esc now closes it
  }
  d.querySelector('.x').onclick =
    () => d.close();
  d.addEventListener('close',
    () => opener.focus());
</script>''', None),
 ('fix-headings', 'Heading structure', ['12'], '1.3.1',
  'Screen reader users jump between headings to scan a page, the way sighted people scan bold text. The levels should describe the outline, and CSS should handle the size.',
  '''<h1>Alderwick Family Clinic</h1>
<div class="title">Our services</div>
<h4>Pediatric care</h4>
<h4>Women’s health</h4>''',
  '''<h1>Family care in the valley</h1>
<h2>Our services</h2>
<h3 class="card-title">Pediatric care</h3>
<h3 class="card-title">Women’s health</h3>''', None),
 ('fix-links', 'Link purpose', ['13'], '2.4.4',
  'Every link should make sense on its own, because that’s how screen readers list them. Usually the best fix is to make the card title the link.',
  '''<div class="card">
  <div class="title">Pediatric care</div>
  <p>Checkups and shots from birth to 18.</p>
  <a href="/pediatrics">Read more</a>
</div>''',
  '''<div class="card">
  <h3>
    <a href="/pediatrics">Pediatric care</a>
  </h3>
  <p>Checkups and shots from birth to 18.</p>
</div>''', None),
]

PAGES = [
 ('Home', '/', 'Hero, services, insurance strip, welcome video, footer'),
 ('Find a provider', '/providers', '12 provider cards with photos, filters'),
 ('Book an appointment', '/book', 'Request form, “Book online” window, calendar'),
 ('Patient portal login', '/portal/login', 'Username and password form'),
 ('Pay a bill', '/billing/pay', 'Payment form, statement lookup'),
 ('Información para pacientes', '/es', 'Spanish patient-information page'),
 ('New-patient intake form', 'intake-form.pdf', '4-page fillable PDF'),
]
METHOD = [
 ('Automated scan', 'Run axe-core and Lighthouse on every page at desktop and phone widths. A scan catches roughly a third of issues, so it’s where the audit starts, not where it ends.'),
 ('Keyboard pass', 'Use every page with only Tab, Shift+Tab, Enter, Space, Esc and the arrow keys. Can you reach everything, see where you are, and get out of every popup?'),
 ('Screen reader pass', 'Book an appointment and log in with NVDA and Firefox on Windows and VoiceOver and Safari on iPhone. Check names, roles, headings, links and error messages.'),
 ('Zoom and reflow', 'Zoom to 200% and 400%, and check the layout at 320 CSS px wide. Turn on the text-spacing overrides and look for clipped or overlapping text.'),
 ('Color and contrast', 'Measure text and control colors with a contrast checker, and check that no information depends on color alone.'),
 ('Documents and media', 'Check PDFs with a PDF accessibility checker and the reading-order tools in a PDF editor. Check videos for captions and transcripts.'),
]
PLAN = [
 ('Week 1', 'Unblock booking and login', ['01', '02', '03', '07'], '6–9 hours of dev time',
  'These four stop people from booking or logging in. Most are small markup and CSS changes in shared templates, so one fix covers every page.'),
 ('Weeks 2–3', 'Fix what’s missing or hard to read', ['04', '05', '06', '08', '09', '10'], '10–14 hours, plus captioning and PDF time',
  'Color changes are one stylesheet edit. Alt text and captions need someone who knows the content. The intake PDF can be retagged, or rebuilt as an accessible web form.'),
 ('Within 45 days', 'Clean up structure and friction', ['11', '12', '13', '14', '15', '16', '17', '18', '19'], '8–12 hours',
  'Template-level fixes for headings, link text, target sizes, page titles and language, plus the cookie banner and the Pay a bill layout.'),
 ('Ongoing', 'Keep it fixed', [], 'About an hour a month',
  'Add an automated accessibility check to the build so new pages can’t ship with the basics broken. Give content editors a one-page checklist (alt text, link text, headings, captions). Retest the key tasks after each release, and publish an accessibility statement with a phone number and email for reporting problems.'),
]

fid = {f[0]: f for f in F}
def sev_chip(s): return f'<span class="sev sev--{s.lower()}">{s}</span>'
def sc_tag(s, full=True):
    n, l, new = SC[s]
    nn = ' <span class="new">New in 2.2</span>' if new else ''
    return f'<span class="sc"><a href="https://www.w3.org/TR/WCAG22/#{n.lower().replace(" ", "-").replace("(", "").replace(")", "").replace(",", "")}" class="sc__n">{s}</a> {E(n)} <span class="sc__l">({l})</span>{nn}</span>'

def esc_t(s):  # escape and turn <tag> mentions into code
    return re.sub(r'(&lt;[^&]*?&gt;|\*:focus \{ outline: none \}|onpaste=&quot;return false&quot;|autocomplete=&quot;[a-z-]+&quot;|aria-[a-z]+(?:=&quot;true&quot;)?|alt=&quot;&quot;|lang=&quot;[a-z]+&quot;|showModal\(\)|#[0-9a-f]{6}|width: 960px|max-width: 960px|scroll-padding-top|:focus-visible|given-name|bday-day)', r'<code>\1</code>', E(s))

# ---------- page ----------
h = []
A = h.append
A(f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Alderwick Family Clinic — WCAG 2.2 AA accessibility audit (concept demo)</title>
  <meta name="description" content="Concept demo of a WCAG 2.2 Level AA accessibility audit report for Alderwick Family Clinic, a fictional clinic website: severity summary, scope and method, {total} example findings mapped to success criteria, before-and-after code fixes, a remediation plan and a PDF note. Built by Alex Mercer.">
  <meta name="robots" content="noindex">
  <meta name="theme-color" content="#f3f1ea">
  <meta property="og:title" content="Alderwick Family Clinic accessibility audit — concept demo">
  <meta property="og:description" content="A sample WCAG 2.2 AA audit report for a made-up clinic website. The site doesn’t exist; every finding is an example.">
  <meta property="og:type" content="website">
  <link rel="preload" href="fonts/Geist.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="fonts/GeistMono.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="css/styles.css">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%2323407a'/%3E%3Cpath d='M16 7v18M7 16h18' stroke='%23f3f1ea' stroke-width='4' stroke-linecap='round'/%3E%3C/svg%3E">
  <script>if(!/[?&]static\\b/.test(location.search)&&!matchMedia('(prefers-reduced-motion: reduce)').matches)document.documentElement.classList.add('anim');</script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <aside class="demo-bar" aria-label="About this demo">
    <p><b>Concept demo by Alex Mercer.</b> Alderwick Family Clinic and its website are made up. Nothing was actually tested; every finding is an example.</p>
    <a href="../../index.html">Back to the portfolio</a>
  </aside>

  <header class="top">
    <div class="wrap top__inner">
      <a class="logo" href="#main">
        <svg class="logo__mark" viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="9" fill="currentColor"/><path d="M20 9.5v21M9.5 20h21" stroke="#f3f1ea" stroke-width="4.6" stroke-linecap="round"/></svg>
        <span class="logo__word"><span>Alderwick Family Clinic</span><small>Accessibility audit</small></span>
      </a>
      <nav class="top__nav" aria-label="Report sections">
        <a href="#summary">Summary</a>
        <a href="#scope">Scope</a>
        <a href="#findings">Findings</a>
        <a href="#fixes">Fixes</a>
        <a href="#plan">Plan</a>
        <a href="#pdf">PDFs</a>
      </nav>
      <a class="btn btn--dl top__dl" href="../../samples/Alderwick-accessibility-audit-DEMO.pdf"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11m0 0l-4.5-4.5M12 15l4.5-4.5M5 19.5h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg><span>PDF<span class="sr"> of this report</span></span></a>
    </div>
  </header>

  <main id="main">
    <section class="hero" aria-labelledby="hero-h">
      <div class="wrap">
        <div class="hero__head">
          <div>
            <p class="eyebrow">WCAG 2.2 Level AA audit report</p>
            <h1 id="hero-h">{total} barriers on the clinic site. <em>{counts["Critical"]} stop patients cold.</em></h1>
            <p class="hero__lede">A keyboard user can’t get out of the booking window, the appointment form has no labels, and the patient portal won’t accept a pasted password. Here’s each issue, who it affects, the success criterion it fails, and the fix.</p>
          </div>
          <div class="proj">
          <dl>
            <div><dt>Site</dt><dd>alderwickclinic.example</dd></div>
            <div><dt>Standard</dt><dd>WCAG 2.2, Level A + AA</dd></div>
            <div><dt>Scope</dt><dd>6 pages + 1 PDF</dd></div>
            <div><dt>Report date</dt><dd>Nov 18, 2026</dd></div>
          </dl>
          <p class="proj__stamp"><span class="stamp">Example findings</span></p>
          </div>
        </div>
      </div>
    </section>

    <section class="sec" id="summary" aria-labelledby="sum-h">
      <div class="wrap">
        <div class="sec__head rv">
          <p class="eyebrow">Executive summary</p>
          <h2 id="sum-h">Where the site stands</h2>
        </div>
        <div class="kpis">
          <div class="kpi kpi--lead rv">
            <p class="kpi__k">Issues found</p>
            <p class="kpi__v">{total}</p>
            <p class="kpi__s">{len(uniq_sc)} success criteria failed: {lvlA} issues at Level A, {lvlAA} at Level AA</p>
          </div>''')
for s in SEVS:
    A(f'''
          <div class="kpi kpi--{s.lower()} rv">
            <p class="kpi__k">{sev_chip(s)}</p>
            <p class="kpi__v">{counts[s]}</p>
            <p class="kpi__s">{SEVDEF[s]}</p>
          </div>''')
A('''
        </div>
        <div class="sumrow">
          <figure class="card bars rv">
            <figcaption class="card__h">Issues by severity</figcaption>
            <div class="stack" aria-hidden="true">''')
for s in SEVS:
    A(f'<span class="stack__s stack__s--{s.lower()}" style="flex:{counts[s]}"></span>')
A('''</div>
            <ul class="legend">''')
for s in SEVS:
    A(f'<li><span class="dot dot--{s.lower()}" aria-hidden="true"></span>{s} <b>{counts[s]}</b></li>')
A('''</ul>
            <p class="card__h card__h--2">Findings by WCAG principle (some touch two)</p>
            <ul class="pbars">''')
mx = max(by_pr.values())
for p, name in PRINC.items():
    A(f'<li><span class="pbars__k">{name}</span><span class="pbars__t" aria-hidden="true"><span style="width:{by_pr[p]/mx*100:.1f}%"></span></span><b>{by_pr[p]}</b></li>')
A(f'''</ul>
            <p class="bars__new"><span class="new">New in 2.2</span> {len([f for f in F if any(SC[s][2] for s in f[3])])} findings fall under criteria added in WCAG 2.2 ({", ".join(new22)}). Older audits and many scanners don’t check these.</p>
          </figure>
          <div class="card verdict rv">
            <p class="card__h">Bottom line</p>
            <p class="verdict__t">The site doesn’t meet WCAG 2.2 AA today. The good news is that most fixes live in shared templates and one stylesheet, so roughly 16–23 hours of development, plus captioning and PDF work, clears every Critical and High issue across the whole site.</p>
            <p class="card__h card__h--2">Fix these first</p>
            <ol class="first">''')
for i in ['01', '02', '03']:
    f = fid[i]
    A(f'<li><a href="#f-{i}"><span class="first__n">{i}</span><span>{E(f[2])}</span></a></li>')
A(f'''</ol>
            
          </div>
        </div>
      </div>
    </section>

    <section class="sec" id="scope" aria-labelledby="scope-h">
      <div class="wrap">
        <div class="sec__head rv">
          <p class="eyebrow">Scope and method</p>
          <h2 id="scope-h">What was checked, and how</h2>
          <p class="sec__lede">The pages were picked around the tasks patients come to do: find a doctor, book, log in, pay, and fill in the intake form. Each one goes through the same six checks. For this demo the site is fictional, so this describes the method, not results from real testing.</p>
        </div>
        <div class="scope">
          <div class="card rv">
            <table class="pages">
              <caption class="card__h">Pages in scope</caption>
              <thead><tr><th scope="col">Page</th><th scope="col">Path</th><th scope="col">What’s on it</th></tr></thead>
              <tbody>''')
for n, p, w in PAGES:
    A(f'<tr><th scope="row">{E(n)}</th><td><code>{E(p)}</code></td><td>{E(w)}</td></tr>')
A('''</tbody>
            </table>
          </div>
          <ol class="method">''')
for i, (t, d) in enumerate(METHOD, 1):
    A(f'<li class="rv"><span class="method__n" aria-hidden="true">{i:02d}</span><div><h3>{E(t)}</h3><p>{E(d)}</p></div></li>')
A('''</ol>
        </div>
        <div class="sevdefs rv">
          <h3 class="card__h">How severity is rated</h3>
          <dl>''')
for s in SEVS:
    A(f'<div><dt>{sev_chip(s)}</dt><dd>{SEVDEF[s]}</dd></div>')
A(f'''</dl>
        </div>
      </div>
    </section>

    <section class="sec" id="findings" aria-labelledby="find-h">
      <div class="wrap">
        <div class="sec__head sec__head--row rv">
          <div>
            <p class="eyebrow">Findings</p>
            <h2 id="find-h">All {total} issues</h2>
            <p class="sec__lede">Each one is mapped to the WCAG 2.2 success criterion it fails, with a link to the criterion.</p>
          </div>
          <div class="filter" role="group" aria-label="Show findings by severity" hidden>
            <button type="button" aria-pressed="true" data-sev="all">All <span>{total}</span></button>''')
for s in SEVS:
    A(f'<button type="button" aria-pressed="false" data-sev="{s.lower()}">{s} <span>{counts[s]}</span></button>')
A('''
          </div>
        </div>
        <p class="sr" id="find-status" aria-live="polite"></p>
        <div class="card tblcard">
          <table class="ft" role="table">
            <caption class="sr">Accessibility findings, with WCAG success criterion, severity, location, who is affected and the fix</caption>
            <thead role="rowgroup"><tr role="row"><th scope="col" role="columnheader">#</th><th scope="col" role="columnheader">Issue</th><th scope="col" role="columnheader">WCAG 2.2</th><th scope="col" role="columnheader">Severity</th><th scope="col" role="columnheader">Where and who</th><th scope="col" role="columnheader">Fix</th></tr></thead>
            <tbody role="rowgroup">''')
for f in F:
    i, sev, title, scs, where, who, prob, fix, ref = f
    more = ''
    if ref == 'pdf': more = ' <a class="ft__more" href="#pdf">PDF steps</a>'
    elif ref: more = f' <a class="ft__more" href="#{ref}">Before and after code</a>'
    A(f'''
              <tr role="row" id="f-{i}" data-sev="{sev.lower()}" class="ft__r ft__r--{sev.lower()}">
                <td role="cell" class="ft__id">{i}</td>
                <th scope="row" role="rowheader" class="ft__issue"><span class="ft__title">{E(title)}</span><span class="ft__prob">{esc_t(prob)}</span></th>
                <td role="cell" class="ft__sc"><span class="ft__lab" aria-hidden="true">WCAG</span>{"".join(sc_tag(s) for s in scs)}</td>
                <td role="cell" class="ft__sev">{sev_chip(sev)}</td>
                <td role="cell" class="ft__where"><span class="ft__lab">Where</span>{E(where)}<span class="ft__lab">Affects</span><span class="ft__who">{E(who)}</span></td>
                <td role="cell" class="ft__fix"><span class="ft__lab">Fix</span>{esc_t(fix)}{more}</td>
              </tr>''')
A('''
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="sec" id="fixes" aria-labelledby="fix-h">
      <div class="wrap">
        <div class="sec__head rv">
          <p class="eyebrow">Fixes</p>
          <h2 id="fix-h">Before and after, in code</h2>
          <p class="sec__lede">The fixes most teams ask about, written against the clinic’s example markup. The same patterns work in WordPress, Squarespace code blocks or any hand-built site.</p>
        </div>
        <div class="fixes">''')
for fx_id, t, refs, sc, why, before, after, extra in FIX:
    reflinks = ', '.join(f'<a href="#f-{r}">#{r}</a>' for r in refs)
    sw = ''
    if extra == 'swatches':
        def swatch(lbl, fg, bg, txt, k, ok):
            demo = (f'<svg class="sw__demo" viewBox="0 0 200 58" role="img" aria-label="{"Passing" if ok else "Failing"} example: {txt} in {fg} on {bg}">'
                    f'<rect width="200" height="58" fill="{bg}"/><text x="100" y="34" text-anchor="middle" fill="{fg}" font-family="Geist, sans-serif" font-size="15" font-weight="600">{txt}</text></svg>')
            return (f'<div class="sw {"sw--ok" if ok else "sw--bad"}">{demo}'
                    f'<p><b>{lbl}</b> <code>{fg}</code> on <code>{bg}</code></p><p class="sw__r">{R[k]} <span>{"passes" if ok else "fails"} 4.5:1</span></p></div>')
        sw = ('<div class="sws">' +
              swatch('Before', *C['gray'], 'Open 8–6 weekdays', 'gray', False) +
              swatch('After', *C['gray_fix'], 'Open 8–6 weekdays', 'gray_fix', True) +
              swatch('Before', *C['btn'], 'Book now', 'btn', False) +
              swatch('After', *C['btn_fix'], 'Book now', 'btn_fix', True) + '</div>')
    A(f'''
          <article class="fix rv" id="{fx_id}" aria-labelledby="{fx_id}-h">
            <div class="fix__text">
              <p class="fix__meta">{sc_tag(sc)} <span class="fix__refs">Findings {reflinks}</span></p>
              <h3 id="{fx_id}-h">{E(t)}</h3>
              <p>{esc_t(why)}</p>
            </div>
            {sw}
            <div class="fix__code">
              <figure class="code code--before"><figcaption><span class="tag tag--before">Before</span></figcaption><pre><code>{code(before)}</code></pre></figure>
              <figure class="code code--after"><figcaption><span class="tag tag--after">After</span></figcaption><pre><code>{code(after)}</code></pre></figure>
            </div>
          </article>''')
A('''
        </div>
      </div>
    </section>

    <section class="sec" id="plan" aria-labelledby="plan-h">
      <div class="wrap">
        <div class="sec__head rv">
          <p class="eyebrow">Remediation plan</p>
          <h2 id="plan-h">What to fix, in what order</h2>
          <p class="sec__lede">Ordered by harm first, then by effort. Hours are rough estimates for a developer who already knows the site’s templates.</p>
        </div>
        <ol class="plan">''')
for when, t, ids, eff, d in PLAN:
    chips = ''.join(f'<li><a href="#f-{i}" class="pchip pchip--{fid[i][1].lower()}"><span class="sr">Finding </span>{i}<span class="sr">, {fid[i][1]}</span></a></li>' for i in ids)
    chips = f'<ul class="plan__ids" aria-label="Findings in this phase">{chips}</ul>' if ids else ''
    A(f'''
          <li class="plan__i rv">
            <p class="plan__when">{when}</p>
            <div class="plan__body">
              <h3>{E(t)}</h3>
              <p>{E(d)}</p>
              {chips}
            </div>
            <p class="plan__eff">{E(eff)}</p>
          </li>''')
A(f'''
        </ol>
      </div>
    </section>

    <section class="sec" id="pdf" aria-labelledby="pdf-h">
      <div class="wrap pdf">
        <div class="pdf__intro rv">
          <p class="eyebrow">PDF remediation</p>
          <h2 id="pdf-h">The intake form, step by step</h2>
          <p class="sec__lede">PDFs on a website fall under the same WCAG criteria as the pages. For a form patients have to fill in, the questions to ask are whether a screen reader can read it in the right order and whether every field says what it wants.</p>
          <div class="card pdf__aside">
            <p class="card__h">Retag or rebuild?</p>
            <p>A 4-page form that changes once a year is worth retagging. If it changes often, rebuild it as an accessible web form that emails the clinic, and the PDF problem goes away.</p>
          </div>
        </div>
        <ol class="steps">''')
STEPS = [
 ('Fix the source first', 'If the Word or InDesign file exists, use real headings, lists and table headers there and export with tags turned on. That beats tagging by hand after the fact.'),
 ('Tag the structure', 'Every block gets the right tag: H1 to H3 for headings, P for text, L and LI for lists, Table with TH header cells. Page numbers, rules and other decoration are marked as artifacts so they’re skipped.'),
 ('Set the reading order', 'Order the tags so the left column is read fully before the right one, and every label comes right before its field. Check it with the reading-order tool and by listening with a screen reader.'),
 ('Name every form field', 'Give each of the 38 fields a tooltip (the TU entry) that a screen reader reads aloud, like “Date of birth, MM/DD/YYYY”. Set the tab order to follow the structure, and group radio buttons under one name.'),
 ('Describe images, set properties', 'Add alt text to the logo and the body diagram. Set the document title, show it in the title bar instead of the file name, and set the language to English.'),
 ('Check, then check by hand', 'Run a PDF/UA checker and the built-in accessibility check in a PDF editor, then fill in the whole form with NVDA and with the keyboard only. Automated checks pass plenty of PDFs that are still unusable.'),
]
for i, (t, d) in enumerate(STEPS, 1):
    A(f'<li class="rv"><span class="steps__n" aria-hidden="true">{i}</span><div><h3>{E(t)}</h3><p>{E(d)}</p></div></li>')
A(f'''</ol>
      </div>
    </section>

    <section class="sec sec--note" aria-labelledby="note-h">
      <div class="wrap">
        <div class="note rv">
          <h2 id="note-h">About this report</h2>
          <p>This is a concept demo of the audit reports I write. Alderwick Family Clinic, its website and its intake form are made up. Nothing was scanned or tested, and every finding, count and estimate is an example. The WCAG 2.2 success criteria, levels and contrast math are real.</p>
          <p>An audit is a snapshot of how a site works against WCAG on the day it’s checked. It isn’t a legal opinion or a certification.</p>
          <p class="note__self">This page was built to the same standard: real headings in order, a skip link, visible focus, text contrast of at least 4.5:1 (the two “before” swatches above are pictures of the failing colors, on purpose), and a findings table that works without JavaScript. It was checked with axe-core and a keyboard pass.</p>
        </div>
      </div>
    </section>
  </main>

  <footer class="foot">
    <div class="wrap foot__inner">
      <p><span class="foot__mark">Alderwick Family Clinic</span> · accessibility audit · concept demo, example findings only</p>
      <p>Built by Alex Mercer · <a href="mailto:alexmercer.projects@gmail.com">alexmercer.projects@gmail.com</a> · <a href="../../index.html">Portfolio</a></p>
    </div>
  </footer>
  <script src="js/app.js" defer></script>
</body>
</html>
''')
page = ''.join(h)
if STANDALONE:
    page = page.replace('../../samples/Alderwick-accessibility-audit-DEMO.pdf', 'Alderwick-accessibility-audit-DEMO.pdf')
    page = page.replace('../../index.html', 'https://alexmercer-studio.netlify.app/')
open(OUT, 'w').write(page)
print('wrote', OUT, 'findings', total, counts, 'criteria', len(uniq_sc), 'new22', new22, 'byP', by_pr, 'A/AA', lvlA, lvlAA)
print('ratios', R)
