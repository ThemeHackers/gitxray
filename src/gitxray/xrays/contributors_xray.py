from gitxray.include import gh_time, gh_public_events, gx_definitions
from gitxray.include import gx_ugly_openpgp_parser, gx_ugly_ssh_parser
from datetime import datetime, timezone
from collections import defaultdict
import sys, re, base64

def infer_timezone_from_location(location_str):
    """Try to infer timezone from location field (best effort)"""
    if not location_str:
        return None

    location_lower = location_str.lower()

    # Direct timezone mentions
    if 'utc' in location_lower or 'gmt' in location_lower:
        match = re.search(r'utc([+-]\d+)|gmt([+-]\d+)', location_lower)
        if match:
            offset = match.group(1) or match.group(2)
            return f"UTC{offset}"

    # Countries and major cities with their timezones
    location_timezones = {
        # North America
        'usa': 'UTC-5', 'united states': 'UTC-5', 'america': 'UTC-5',
        'california': 'UTC-8', 'san francisco': 'UTC-8', 'sf': 'UTC-8', 'los angeles': 'UTC-8', 'seattle': 'UTC-8', 'portland': 'UTC-8', 'san diego': 'UTC-8',
        'new york': 'UTC-5', 'nyc': 'UTC-5', 'boston': 'UTC-5', 'washington': 'UTC-5', 'miami': 'UTC-5', 'atlanta': 'UTC-5', 'philadelphia': 'UTC-5',
        'chicago': 'UTC-6', 'austin': 'UTC-6', 'dallas': 'UTC-6', 'houston': 'UTC-6',
        'denver': 'UTC-7', 'phoenix': 'UTC-7', 'salt lake city': 'UTC-7',
        'canada': 'UTC-5', 'toronto': 'UTC-5', 'montreal': 'UTC-5', 'vancouver': 'UTC-8', 'ottawa': 'UTC-5', 'calgary': 'UTC-7',
        'mexico': 'UTC-6', 'mexico city': 'UTC-6', 'guadalajara': 'UTC-6', 'monterrey': 'UTC-6',

        # Central America & Caribbean
        'guatemala': 'UTC-6', 'honduras': 'UTC-6', 'el salvador': 'UTC-6', 'nicaragua': 'UTC-6',
        'costa rica': 'UTC-6', 'panama': 'UTC-5', 'belize': 'UTC-6',
        'cuba': 'UTC-5', 'havana': 'UTC-5', 'jamaica': 'UTC-5', 'haiti': 'UTC-5',
        'dominican republic': 'UTC-4', 'puerto rico': 'UTC-4', 'trinidad': 'UTC-4',

        # South America
        'colombia': 'UTC-5', 'bogotá': 'UTC-5', 'bogota': 'UTC-5', 'medellín': 'UTC-5', 'medellin': 'UTC-5', 'cali': 'UTC-5',
        'venezuela': 'UTC-4', 'caracas': 'UTC-4',
        'ecuador': 'UTC-5', 'quito': 'UTC-5', 'guayaquil': 'UTC-5',
        'peru': 'UTC-5', 'lima': 'UTC-5',
        'bolivia': 'UTC-4', 'la paz': 'UTC-4',
        'chile': 'UTC-4', 'santiago': 'UTC-4',
        'argentina': 'UTC-3', 'buenos aires': 'UTC-3', 'córdoba': 'UTC-3', 'cordoba': 'UTC-3',
        'uruguay': 'UTC-3', 'montevideo': 'UTC-3',
        'paraguay': 'UTC-4', 'asunción': 'UTC-4', 'asuncion': 'UTC-4',
        'brazil': 'UTC-3', 'brasil': 'UTC-3', 'são paulo': 'UTC-3', 'sao paulo': 'UTC-3', 'rio': 'UTC-3', 'rio de janeiro': 'UTC-3', 'brasília': 'UTC-3', 'brasilia': 'UTC-3',
        'guyana': 'UTC-4', 'suriname': 'UTC-3',

        # Western Europe
        'uk': 'UTC+0', 'united kingdom': 'UTC+0', 'england': 'UTC+0', 'london': 'UTC+0', 'manchester': 'UTC+0', 'edinburgh': 'UTC+0', 'scotland': 'UTC+0', 'wales': 'UTC+0',
        'ireland': 'UTC+0', 'dublin': 'UTC+0',
        'portugal': 'UTC+0', 'lisbon': 'UTC+0', 'porto': 'UTC+0',
        'spain': 'UTC+1', 'madrid': 'UTC+1', 'barcelona': 'UTC+1', 'valencia': 'UTC+1', 'seville': 'UTC+1',
        'france': 'UTC+1', 'paris': 'UTC+1', 'lyon': 'UTC+1', 'marseille': 'UTC+1',
        'belgium': 'UTC+1', 'brussels': 'UTC+1', 'antwerp': 'UTC+1',
        'netherlands': 'UTC+1', 'holland': 'UTC+1', 'amsterdam': 'UTC+1', 'rotterdam': 'UTC+1', 'the hague': 'UTC+1',
        'luxembourg': 'UTC+1',
        'switzerland': 'UTC+1', 'zurich': 'UTC+1', 'geneva': 'UTC+1', 'bern': 'UTC+1',

        # Central Europe
        'germany': 'UTC+1', 'deutschland': 'UTC+1', 'berlin': 'UTC+1', 'munich': 'UTC+1', 'frankfurt': 'UTC+1', 'hamburg': 'UTC+1', 'cologne': 'UTC+1',
        'austria': 'UTC+1', 'vienna': 'UTC+1', 'wien': 'UTC+1',
        'italy': 'UTC+1', 'rome': 'UTC+1', 'milan': 'UTC+1', 'naples': 'UTC+1', 'turin': 'UTC+1',
        'poland': 'UTC+1', 'warsaw': 'UTC+1', 'krakow': 'UTC+1', 'wroclaw': 'UTC+1',
        'czech republic': 'UTC+1', 'czechia': 'UTC+1', 'prague': 'UTC+1',
        'slovakia': 'UTC+1', 'bratislava': 'UTC+1',
        'hungary': 'UTC+1', 'budapest': 'UTC+1',
        'slovenia': 'UTC+1', 'ljubljana': 'UTC+1',
        'croatia': 'UTC+1', 'zagreb': 'UTC+1',

        # Nordic Countries
        'norway': 'UTC+1', 'oslo': 'UTC+1',
        'sweden': 'UTC+1', 'stockholm': 'UTC+1', 'göteborg': 'UTC+1', 'goteborg': 'UTC+1',
        'finland': 'UTC+2', 'helsinki': 'UTC+2',
        'denmark': 'UTC+1', 'copenhagen': 'UTC+1',
        'iceland': 'UTC+0', 'reykjavik': 'UTC+0',

        # Eastern Europe
        'greece': 'UTC+2', 'athens': 'UTC+2',
        'romania': 'UTC+2', 'bucharest': 'UTC+2',
        'bulgaria': 'UTC+2', 'sofia': 'UTC+2',
        'ukraine': 'UTC+2', 'kyiv': 'UTC+2', 'kiev': 'UTC+2', 'kharkiv': 'UTC+2', 'odesa': 'UTC+2',
        'belarus': 'UTC+3', 'minsk': 'UTC+3',
        'estonia': 'UTC+2', 'tallinn': 'UTC+2',
        'latvia': 'UTC+2', 'riga': 'UTC+2',
        'lithuania': 'UTC+2', 'vilnius': 'UTC+2',
        'serbia': 'UTC+1', 'belgrade': 'UTC+1',
        'bosnia': 'UTC+1', 'sarajevo': 'UTC+1',
        'albania': 'UTC+1', 'tirana': 'UTC+1',

        # Russia & Central Asia
        'russia': 'UTC+3', 'moscow': 'UTC+3', 'st petersburg': 'UTC+3', 'saint petersburg': 'UTC+3',
        'kazakhstan': 'UTC+6', 'almaty': 'UTC+6',
        'uzbekistan': 'UTC+5', 'tashkent': 'UTC+5',
        'turkmenistan': 'UTC+5', 'kyrgyzstan': 'UTC+6', 'tajikistan': 'UTC+5',

        # Middle East
        'turkey': 'UTC+3', 'türkiye': 'UTC+3', 'istanbul': 'UTC+3', 'ankara': 'UTC+3',
        'israel': 'UTC+2', 'tel aviv': 'UTC+2', 'jerusalem': 'UTC+2',
        'saudi arabia': 'UTC+3', 'riyadh': 'UTC+3', 'jeddah': 'UTC+3',
        'uae': 'UTC+4', 'dubai': 'UTC+4', 'abu dhabi': 'UTC+4',
        'qatar': 'UTC+3', 'doha': 'UTC+3',
        'kuwait': 'UTC+3',
        'bahrain': 'UTC+3',
        'oman': 'UTC+4',
        'iran': 'UTC+3.5', 'tehran': 'UTC+3.5',
        'iraq': 'UTC+3', 'baghdad': 'UTC+3',
        'jordan': 'UTC+2', 'amman': 'UTC+2',
        'lebanon': 'UTC+2', 'beirut': 'UTC+2',
        'syria': 'UTC+2', 'damascus': 'UTC+2',

        # South Asia
        'india': 'UTC+5.5', 'bharat': 'UTC+5.5', 'mumbai': 'UTC+5.5', 'delhi': 'UTC+5.5', 'bangalore': 'UTC+5.5', 'bengaluru': 'UTC+5.5', 'hyderabad': 'UTC+5.5', 'chennai': 'UTC+5.5', 'kolkata': 'UTC+5.5', 'pune': 'UTC+5.5',
        'pakistan': 'UTC+5', 'karachi': 'UTC+5', 'lahore': 'UTC+5', 'islamabad': 'UTC+5',
        'bangladesh': 'UTC+6', 'dhaka': 'UTC+6',
        'sri lanka': 'UTC+5.5', 'colombo': 'UTC+5.5',
        'nepal': 'UTC+5.75', 'kathmandu': 'UTC+5.75',
        'afghanistan': 'UTC+4.5', 'kabul': 'UTC+4.5',

        # Southeast Asia
        'thailand': 'UTC+7', 'bangkok': 'UTC+7',
        'vietnam': 'UTC+7', 'hanoi': 'UTC+7', 'ho chi minh': 'UTC+7',
        'philippines': 'UTC+8', 'manila': 'UTC+8',
        'indonesia': 'UTC+7', 'jakarta': 'UTC+7', 'bali': 'UTC+8',
        'malaysia': 'UTC+8', 'kuala lumpur': 'UTC+8',
        'singapore': 'UTC+8',
        'myanmar': 'UTC+6.5', 'burma': 'UTC+6.5', 'yangon': 'UTC+6.5',
        'cambodia': 'UTC+7', 'phnom penh': 'UTC+7',
        'laos': 'UTC+7', 'vientiane': 'UTC+7',

        # East Asia
        'china': 'UTC+8', 'beijing': 'UTC+8', 'shanghai': 'UTC+8', 'guangzhou': 'UTC+8', 'shenzhen': 'UTC+8', 'chengdu': 'UTC+8',
        'japan': 'UTC+9', 'tokyo': 'UTC+9', 'osaka': 'UTC+9', 'kyoto': 'UTC+9', 'yokohama': 'UTC+9',
        'korea': 'UTC+9', 'south korea': 'UTC+9', 'seoul': 'UTC+9', 'busan': 'UTC+9',
        'north korea': 'UTC+9', 'pyongyang': 'UTC+9',
        'taiwan': 'UTC+8', 'taipei': 'UTC+8',
        'hong kong': 'UTC+8', 'hk': 'UTC+8',
        'macau': 'UTC+8', 'macao': 'UTC+8',
        'mongolia': 'UTC+8', 'ulaanbaatar': 'UTC+8',

        # Africa - North
        'egypt': 'UTC+2', 'cairo': 'UTC+2', 'alexandria': 'UTC+2',
        'morocco': 'UTC+0', 'casablanca': 'UTC+0', 'rabat': 'UTC+0',
        'algeria': 'UTC+1', 'algiers': 'UTC+1',
        'tunisia': 'UTC+1', 'tunis': 'UTC+1',
        'libya': 'UTC+2', 'tripoli': 'UTC+2',

        # Africa - West
        'nigeria': 'UTC+1', 'lagos': 'UTC+1', 'abuja': 'UTC+1',
        'ghana': 'UTC+0', 'accra': 'UTC+0',
        'senegal': 'UTC+0', 'dakar': 'UTC+0',
        'ivory coast': 'UTC+0', 'côte d\'ivoire': 'UTC+0', 'abidjan': 'UTC+0',
        'cameroon': 'UTC+1', 'yaoundé': 'UTC+1', 'yaounde': 'UTC+1',
        'mali': 'UTC+0', 'bamako': 'UTC+0',
        'burkina faso': 'UTC+0',
        'niger': 'UTC+1',
        'benin': 'UTC+1',
        'togo': 'UTC+0',

        # Africa - East
        'kenya': 'UTC+3', 'nairobi': 'UTC+3',
        'ethiopia': 'UTC+3', 'addis ababa': 'UTC+3',
        'tanzania': 'UTC+3', 'dar es salaam': 'UTC+3',
        'uganda': 'UTC+3', 'kampala': 'UTC+3',
        'somalia': 'UTC+3', 'mogadishu': 'UTC+3',
        'rwanda': 'UTC+2', 'kigali': 'UTC+2',
        'burundi': 'UTC+2',

        # Africa - Southern
        'south africa': 'UTC+2', 'johannesburg': 'UTC+2', 'cape town': 'UTC+2', 'pretoria': 'UTC+2', 'durban': 'UTC+2',
        'zimbabwe': 'UTC+2', 'harare': 'UTC+2',
        'botswana': 'UTC+2', 'gaborone': 'UTC+2',
        'namibia': 'UTC+2', 'windhoek': 'UTC+2',
        'mozambique': 'UTC+2', 'maputo': 'UTC+2',
        'zambia': 'UTC+2', 'lusaka': 'UTC+2',
        'malawi': 'UTC+2',

        # Africa - Central
        'congo': 'UTC+1', 'drc': 'UTC+1', 'kinshasa': 'UTC+1',
        'angola': 'UTC+1', 'luanda': 'UTC+1',
        'chad': 'UTC+1',
        'gabon': 'UTC+1',

        # Oceania
        'australia': 'UTC+10', 'sydney': 'UTC+10', 'melbourne': 'UTC+10', 'brisbane': 'UTC+10', 'perth': 'UTC+8', 'adelaide': 'UTC+9.5',
        'new zealand': 'UTC+12', 'nz': 'UTC+12', 'auckland': 'UTC+12', 'wellington': 'UTC+12',
        'fiji': 'UTC+12',
        'papua new guinea': 'UTC+10',
    }

    for location, tz in location_timezones.items():
        if location in location_lower:
            return tz

    return None

def run(gx_context, gx_output, gh_api):

    repository = gx_context.getRepository()
    contributor_scope = gx_context.getContributorScope()

    if contributor_scope != None:
        gx_output.notify(f"YOU HAVE SCOPED THIS GITXRAY TO CONTRIBUTORS: {contributor_scope} - OTHER USERS WON'T BE ANALYZED.")

    gx_output.stdout(f"Querying GitHub for repository contributors.. Please wait.", shushable=True, end='', flush=True)

    # Let's store the whole set of contributors in the context
    gx_context.setContributors(gh_api.fetch_repository_contributors(repository))

    c_users = []
    c_anon = []

    c_len = len(gx_context.getContributors())
    gx_output.stdout(f"\rIdentified {c_len} contributors.." + ' '*70, shushable=True, flush=True)

    # If focused on a contributor, let's first make sure the contributor exists in the repository
    if contributor_scope != None:
        if not gx_context.areContributors(contributor_scope): 
            gx_output.warn(f"One of the collaborators you specified {contributor_scope} were not found as a contributor in the repo.")
            gx_output.warn(f"If you intend to filter results for a non-contributor, using the filter function instead (eg. -f johnDoe03). Quitting..")
            return False

    # Were were invoked to just list contributors and quit?
    if gx_context.listAndQuit():
        gx_output.notify(f"LISTING CONTRIBUTORS (INCLUDING THOSE WITHOUT A GITHUB USER ACCOUNT) AND EXITING..", shushable=False)
        gx_output.stdout(", ".join([c.get('login', c.get('email')) for c in gx_context.getContributors()]), shushable=False)
        return False

    if c_len > 500:
        gx_output.stdout(f"IMPORTANT: The repository has 500+ contributors. GitHub states > 500 contributors will appear as Anonymous")
        gx_output.stdout(f"More information at: https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#list-repository-contributors")

    # We will use this created_at_time for the repository in one or two loops before.
    repository_created_at_time = gh_time.parse_date(repository.get('created_at'))

    for i, c in enumerate(gx_context.getContributors()):
        if contributor_scope != None and c.get('login') not in contributor_scope: continue
        gx_output.stdout('\rFetching repository contributor details [{}/{}]'.format(i+1, c_len), end='', flush=True)
        ctype = c.get('type')
        if ctype in ["User", "Bot"]:
            c_users.append(gh_api.fetch_contributor(c))
        elif ctype == "Anonymous":
            c_anon.append(c)
        else:
            print(c)
            raise Exception("Contributor of Type !== User/Anonymous found. Failing almost gracefully")

    if contributor_scope == None and len(gx_context.getContributors()) != 0:
        gx_output.stdout(f"\r\nDiscovered {len(c_users)} contributors with GitHub User accounts, and {len(c_anon)} Anonymous contributors", end='', flush=True)
        gx_output.r_log(f"Repository has {len(c_anon)} Anonymous contributors.", rtype="contributors")
        gx_output.r_log(f"Repository has {len(c_users)} contributors with GitHub User accounts.", rtype="contributors")

    gx_output.stdout(f"\r\nPlease wait, beginning to collect keys and commits for User contributors..", end='', flush=True)

    c_users_index = 1
    for contributor in c_users:
        if contributor is None: continue
        unique_pgp_keyids = []
        contributor_emails = []
        contributor_login = contributor.get('login')
        c_started_at = datetime.now()
        gx_output.c_log(f"X-Ray on contributor started at {c_started_at}", contributor=contributor_login, rtype="metrics")

        gx_output.stdout(f"\r[{c_users_index}/{len(c_users)}] Analyzing Profile data for {contributor.get('login')}"+' '*40, end = '', flush=True)
        gx_output.c_log(f"Contributor URL: {contributor.get('html_url')}", rtype="profiling")
        gx_output.c_log(f"Owned repositories: https://github.com/{contributor_login}?tab=repositories", rtype="profiling")

        if contributor.get('name') != None:
            gx_output.c_log(f"[Name: {contributor.get('name')}] obtained from the user's profile.", rtype="personal")

        if contributor.get('twitter_username') != None:
            gx_output.c_log(f"[X/Twitter account: {contributor.get('twitter_username')}] obtained from the user's profile.", rtype="personal")
        if contributor.get('bio') != None:
            bio = contributor.get('bio').replace("\r\n"," | ")
            gx_output.c_log(f"[Bio: {bio}] obtained from the profile.", rtype="personal")
        if contributor.get('company') != None:
            gx_output.c_log(f"[Company: {contributor.get('company')}] obtained from the user's profile.", rtype="personal")
        if contributor.get('blog') != None and len(contributor.get('blog')) > 0:
            gx_output.c_log(f"[Blog: {contributor.get('blog')}] obtained from the user's profile.", rtype="personal")
        if contributor.get('location') != None:
            gx_output.c_log(f"[Location: {contributor.get('location')}] obtained from the user's profile.", rtype="personal")
        if contributor.get('hireable') != None:
            gx_output.c_log(f"[Hireable: The user has set 'Available for Hire'] in their GitHub profile.", rtype="personal")

        if contributor.get('email') != None:
            gx_output.c_log(f"[{contributor.get('email')}] obtained from the user's profile.", rtype="emails")
            gx_context.linkIdentifier("EMAIL", [contributor.get('email')], contributor_login)

        contributor_created_at_time = gh_time.parse_date(contributor.get('created_at'))
        days_since_account_creation = (datetime.now(timezone.utc) - contributor_created_at_time).days 

        # Let's keep track of when the accounts were created.
        gx_context.linkIdentifier("DAYS_SINCE_CREATION", [days_since_account_creation], contributor_login)

        message = f"{days_since_account_creation} days old"
        if days_since_account_creation > 365:
            years = "{:.2f}".format(days_since_account_creation / 365)
            message = f"{years} years old"

        gx_output.c_log(f"Contributor account created: {contributor.get('created_at')}, is {message}.", rtype="profiling")

        if contributor.get('updated_at') != None:
            days_since_updated = (datetime.now(timezone.utc) - gh_time.parse_date(contributor.get('updated_at'))).days 
            gx_output.c_log(f"The account was last updated at {contributor.get('updated_at')}, {days_since_updated} days ago.", rtype="profiling")
            # Let's keep track of when the accounts were last updated.
            gx_context.linkIdentifier("DAYS_SINCE_UPDATED", [days_since_updated], contributor_login)

        if contributor.get('site_admin') != False:
            gx_output.c_log(f"The account may be an administrator. It has 'site_admin' set to True", rtype="profiling")

        commits = gh_api.fetch_commits(repository, author=contributor.get('login'))
        # The REST API does not always work reliable when filtering commits by author. 
        # We create a username@users.noreply.github.com as an alternative author.
        if commits != None:
            if len(commits) == 0:
                commits = gh_api.fetch_commits(repository, author=contributor.get('login')+"@users.noreply.github.com")

            if len(commits) > 0:
                commits_message = f", at {commits[0]['commit']['author']['date']}."
                oldest_commit = commits[-1]['commit']['author']['date']
                if len(commits) > 1:
                    commits_message = f", first one at {oldest_commit} and last one at {commits[0]['commit']['author']['date']}."
                gx_output.c_log(f'Made (to this repo) {len(commits)} commits{commits_message}', rtype="commits")

        signed_commits = []
        failed_verifications = []
        signature_attributes = []
        dates_mismatch_commits_account = []
        dates_mismatch_commits_repository  = []
        commit_times = defaultdict(int)
        weekday_commits = defaultdict(int)  # 0=Monday, 6=Sunday
        weekend_commits = 0
        weekday_only_commits = 0
        gx_output.stdout(f"\r[{c_users_index}/{len(c_users)}] Analyzing {len(commits)} commits and any signing keys for {contributor.get('login')}"+' '*40, end = '', flush=True)
        for commit in commits:
            c = commit["commit"]

            v_reason = c["verification"]["reason"]
            if c["verification"]["verified"] == True:
                try:
                    if "BEGIN SSH SIGNATURE" in c["verification"]["signature"]:
                        signature_attributes.append(gx_ugly_ssh_parser.ugly_inhouse_ssh_signature_block(c["verification"]["signature"]))
                    else:
                        signature_attributes.append(gx_ugly_openpgp_parser.ugly_inhouse_openpgp_block(c["verification"]["signature"]))
                except Exception as ex:
                    gx_output.c_log(f"Failed at parsing a signature, not strange due to our ugly parsing code. Here's some more data. {c['verification']['signature']} - {ex}", rtype="debug")

                if v_reason != "valid":
                    gx_output.c_log(f"Unexpected condition - verified commit set to True and reason != 'valid'. Reason is: {v_reason} - Report to dev!", rtype="debug")
                else:
                    signed_commits.append(c)
            elif v_reason != "unsigned":
                if v_reason == "bad_email": 
                    gx_output.c_log(f"The email in the signature doesn't match the 'committer' email: {commit['html_url']}", rtype="signatures")
                elif v_reason == "unverified_email": 
                    gx_output.c_log(f"The committer email in the signature was not Verified in the account: {commit['html_url']}", rtype="signatures")
                elif v_reason == "expired_key": 
                    gx_output.c_log(f"The key that made the signature expired: {commit['html_url']}", rtype="signatures")
                elif v_reason == "not_signing_key": 
                    gx_output.c_log(f"The PGP key used in the signature did not include the 'signing' flag: {commit['html_url']}", rtype="signatures")
                elif v_reason == "gpgverify_error" or v_reason == "gpgverify_unavailable": 
                    gx_output.c_log(f"There was an error communicating with the signature verification service: {commit['html_url']}", rtype="signatures")
                elif v_reason == "unknown_signature_type": 
                    gx_output.c_log(f"A non-PGP signature was found in the commit: {commit['html_url']}", rtype="signatures")
                elif v_reason == "no_user": 
                    gx_output.c_log(f"The email address in 'committer' does not belong to a User: {commit['html_url']}", rtype="signatures")
                elif v_reason == "unknown_key": 
                    gx_output.c_log(f"The key used to sign the commit is not in their profile and can't be verified: {commit['html_url']}", rtype="signatures")
                elif v_reason == "malformed_signature" or v_reason == "invalid": 
                    gx_output.c_log(f"The signature was malformed and a parsing error took place: {commit['html_url']}", rtype="signatures")
                failed_verifications.append(c)

            if c["author"]["email"] not in contributor_emails:
                gx_output.c_log(f"[{c['author']['email']}] obtained from commit author field.", rtype="emails")
                contributor_emails.append(c["author"]["email"])
                gx_context.linkIdentifier("EMAIL", [c["author"]["email"]], contributor_login)

            # Extract co-authors from commit message
            commit_message = c.get('message', '')
            coauthor_pattern = r'Co-authored-by:\s*([^<]+?)\s*<([^>]+)>'
            coauthors = re.findall(coauthor_pattern, commit_message, re.IGNORECASE)

            if len(coauthors) > 0:
                for coauthor_name, coauthor_email in coauthors:
                    coauthor_name = coauthor_name.strip()
                    coauthor_email = coauthor_email.strip()

                    # Track co-author email
                    if coauthor_email not in contributor_emails:
                        gx_output.c_log(f"[{coauthor_email}] obtained from Co-authored-by in commit message.", rtype="emails", contributor=contributor_login)
                        contributor_emails.append(coauthor_email)
                        gx_context.linkIdentifier("EMAIL", [coauthor_email], contributor_login)

                    gx_output.c_log(f"Commit co-authored with [{coauthor_name} <{coauthor_email}>]: {commit['html_url']}", rtype="commits", contributor=contributor_login)

                    # Link co-author name and email for pattern detection
                    gx_context.linkIdentifier("COAUTHOR_EMAIL", [coauthor_email], contributor_login)
                    gx_context.linkIdentifier("COAUTHOR_NAME", [coauthor_name], contributor_login)

                    # Create a pair identifier to find shared co-authorship relationships
                    coauthor_pair = tuple(sorted([contributor_login, coauthor_email]))
                    gx_context.linkIdentifier("COAUTHOR_PAIR", [f"{coauthor_pair[0]}+{coauthor_pair[1]}"], contributor_login)

            commit_date = gh_time.parse_date(c['author']['date'])
            if commit_date < contributor_created_at_time:
                dates_mismatch_commits_account.append(c)

            if commit_date < repository_created_at_time:
                dates_mismatch_commits_repository.append(c)

            # Let's group by commit hour, we may have an insight here.
            commit_times[commit_date.hour] += 1

            # Track weekday patterns for temporal analysis
            day_of_week = commit_date.weekday()  # 0=Monday, 6=Sunday
            weekday_commits[day_of_week] += 1
            if day_of_week >= 5:  # Saturday or Sunday
                weekend_commits += 1
            else:
                weekday_only_commits += 1

        if len(dates_mismatch_commits_account) > 0:
            gx_output.c_log(f"WARNING: UNRELIABLE COMMIT DATES (Older than Account, which was created on {contributor.get('created_at')}) in {len(dates_mismatch_commits_account)} commits by [{contributor_login}]. Potential tampering, account re-use, or Rebase. List at: {repository.get('html_url')}/commits/?author={contributor_login}&until={contributor.get('created_at')}", rtype="commits")
            gx_output.c_log(f"View commits with unreliable DATES here: {repository.get('html_url')}/commits/?author={contributor_login}&until={contributor.get('created_at')}", rtype="commits")
            gx_context.linkIdentifier("DATE_MISMATCH_COMMITS_ACCOUNT", [len(dates_mismatch_commits_account)], contributor_login)

        if len(dates_mismatch_commits_repository) > 0:
            gx_output.c_log(f"WARNING: UNRELIABLE COMMIT DATES (Older than Repository, which was created on {repository.get('created_at')}) in {len(dates_mismatch_commits_repository)} commits by [{contributor_login}]. Potential tampering, account re-use, or Rebase. List at: {repository.get('html_url')}/commits/?author={contributor_login}&until={contributor.get('created_at')}", rtype="commits")
            gx_context.linkIdentifier("DATE_MISMATCH_COMMITS_REPOSITORY", [len(dates_mismatch_commits_repository)], contributor_login)

        if len(commit_times) > 0:
            # Let's link these commit hours to this contributor, and we'll do extra analysis in the associations X-Ray
            gx_context.linkIdentifier("COMMIT_HOURS", commit_times, contributor_login)

            total_commits = len(commits)
            formatted_output = f"Commit Hours for [{total_commits}] commits:"
            sorted_commit_times = sorted(commit_times.items(), key=lambda item: item[1], reverse=True)
            
            for commit_hour, count in sorted_commit_times:
                percentage = (count / total_commits) * 100
                range_label = gx_definitions.COMMIT_HOURS[commit_hour]
                formatted_output += f" [{range_label}: {count} ({percentage:.2f}%)]"

            gx_output.c_log(formatted_output, rtype="commits")

        # Temporal pattern analysis
        total_commits_for_user = len(commits)
        if total_commits_for_user > 0:
            # Analyze weekday/weekend patterns
            weekend_percentage = (weekend_commits / total_commits_for_user) * 100
            weekday_percentage = (weekday_only_commits / total_commits_for_user) * 100

            if weekend_percentage > 80 and total_commits_for_user >= 20:
                gx_output.c_log(f"Commit timing: {weekend_percentage:.1f}% of commits occur on weekends (outside typical work days).", rtype="commits")
                gx_context.linkIdentifier("COMMIT_PATTERN", ["weekend_focused"], contributor_login)
            elif weekday_percentage > 90 and total_commits_for_user >= 20:
                gx_output.c_log(f"Commit timing: {weekday_percentage:.1f}% of commits occur Mon-Fri (during typical work days).", rtype="commits")
                gx_context.linkIdentifier("COMMIT_PATTERN", ["weekday_focused"], contributor_login)

            # Detect unusual 24/7 commit distribution (potential bot activity)
            active_hours = len([hour for hour, count in commit_times.items() if count > 0])
            if active_hours >= 22:
                gx_output.c_log(f"WARNING: Unusual commit distribution for [{contributor_login}] - commits spread across {active_hours} different hours of the day (potential automated activity). Review hourly breakdown in commits section.", rtype="commits", contributor=contributor_login)
                gx_context.linkIdentifier("SUSPICIOUS_24_7_ACTIVITY", [active_hours], contributor_login)

            # Find primary active hours (8-hour window with most commits)
            max_window_commits = 0
            primary_window_start = 0

            for start_hour in range(24):
                window_commits = sum(commit_times.get((start_hour + i) % 24, 0) for i in range(8))
                if window_commits > max_window_commits:
                    max_window_commits = window_commits
                    primary_window_start = start_hour

            primary_window_label = f"{primary_window_start:02d}:00-{(primary_window_start+8)%24:02d}:00 UTC"
            gx_context.linkIdentifier("PRIMARY_ACTIVE_HOURS", [primary_window_label], contributor_login)

            # Location-based timezone analysis
            profile_location = contributor.get('location', '')
            inferred_tz = None
            if profile_location:
                inferred_tz = infer_timezone_from_location(profile_location)
                if inferred_tz:
                    gx_output.c_log(f"Profile location [{profile_location}] suggests timezone: {inferred_tz}", rtype="profiling")
                    gx_context.linkIdentifier("INFERRED_TIMEZONE", [inferred_tz], contributor_login)

                    # Convert UTC commit window to local time and analyze
                    try:
                        # Parse timezone offset (e.g., "UTC-5" -> -5, "UTC+5.5" -> 5.5)
                        tz_offset = float(inferred_tz.replace('UTC', ''))

                        # Convert primary window start from UTC to local time
                        local_start = (primary_window_start + tz_offset) % 24
                        local_end = (local_start + 8) % 24

                        # Determine if local hours indicate normal or unusual activity
                        # Check both start and end times of the 8-hour window
                        # Work hours: roughly 6am-8pm (6:00-20:00)
                        # Evening: 8pm-10pm (20:00-22:00)
                        # Night: 10pm-6am (22:00-6:00)

                        if 22 <= local_start or local_start < 6:  # Starts during night (10pm-6am)
                            gx_output.c_log(f"Profile location [{profile_location}] suggests {inferred_tz}, but primary activity window ({int(local_start)}:00-{int(local_end)}:00 {inferred_tz}) indicates night-time commits. Location may not match actual timezone or contributor works unusual hours.", rtype="commits")
                        elif local_end >= 22 or local_start > local_end:  # Extends to/past 10pm or wraps past midnight
                            gx_output.c_log(f"Profile location [{profile_location}] suggests {inferred_tz}. Primary activity window ({int(local_start)}:00-{int(local_end)}:00 {inferred_tz}) includes evening/late night hours.", rtype="commits")
                        elif local_end > 20:  # Extends past 8pm but before 10pm
                            gx_output.c_log(f"Profile location [{profile_location}] suggests {inferred_tz}. Primary activity window ({int(local_start)}:00-{int(local_end)}:00 {inferred_tz}) includes evening hours.", rtype="commits")
                        else:  # Window is mostly within typical work hours (6am-8pm)
                            gx_output.c_log(f"Profile location [{profile_location}] suggests {inferred_tz}. Primary activity window ({int(local_start)}:00-{int(local_end)}:00 {inferred_tz}) aligns with typical work hours.", rtype="commits")
                    except (ValueError, AttributeError):
                        # If timezone parsing fails, skip analysis
                        pass

            # Only show UTC window if no timezone was inferred
            if not inferred_tz:
                gx_output.c_log(f"Primary commit window: {primary_window_label} (8-hour period with most commits)", rtype="commits")

        # PGP Signature attributes: We have precise Key IDs used in signatures + details on signature creation time and algorithm
        unique_pgp_pka = set(attribute.get('pgp_publicKeyAlgorithm') for attribute in signature_attributes if attribute.get('pgp_publicKeyAlgorithm') is not None)
        unique_pgp_st = set(attribute.get('pgp_sig_type') for attribute in signature_attributes if attribute.get('pgp_sig_type') is not None)
        unique_pgp_ha = set(attribute.get('pgp_hashAlgorithm') for attribute in signature_attributes if attribute.get('pgp_hashAlgorithm') is not None)
        unique_pgp_sct = set(attribute.get('pgp_signature_creation_time') for attribute in signature_attributes if attribute.get('pgp_signature_creation_time') is not None)
        unique_pgp_keyids = set(attribute.get('pgp_keyid') for attribute in signature_attributes if attribute.get('pgp_keyid') is not None)

        # We don't link SSH Key IDs because SSH keys are unique across GitHub; PGP keys can be added to more than 1 account.
        gx_context.linkIdentifier("PGP_KEYID", unique_pgp_keyids, contributor_login)
        gx_context.linkIdentifier("PGP_PKA", unique_pgp_pka, contributor_login)
        gx_context.linkIdentifier("PGP_HA", unique_pgp_ha, contributor_login)
        gx_context.linkIdentifier("PGP_SCT", unique_pgp_sct, contributor_login)

        # SSH Signature attributes: We don't have a Key ID so far, but we do have the signature algorithms - hey, it's something! right? right??
        unique_ssh_sa = set(attribute.get('ssh_signature_algorithm') for attribute in signature_attributes if attribute.get('ssh_signature_algorithm') is not None)
        if len(unique_ssh_sa) > 0: gx_output.c_log(f"SSH signatures used Algorithms: [{unique_ssh_sa}] obtained from parsing signature blobs", rtype="keys")
        gx_context.linkIdentifier("SSH_SA", unique_ssh_sa, contributor_login)

        # Let's add signature attributes output.
        if len(unique_pgp_pka) > 0: gx_output.c_log(f"PGP signatures used publicKeyAlgorithms: [{unique_pgp_pka}] obtained from parsing signature blobs", rtype="keys")
        # Based on our testing, Signature Type appears to be always 0 in GitHub: Signature of a binary document - Let's only log if it differs.
        if len(unique_pgp_st) > 0:
            for sigtype in unique_pgp_st:
                if sigtype != "Signature of a binary document": 
                    gx_output.c_log(f"PGP signatures used an atypical signature Type: [{sigtype}] obtained from parsing signature blobs", rtype="keys")
                    # Let's also link the atypical sigtype to the user just in case we spot more accounts using it.
                    gx_context.linkIdentifier("PGP_SIG_TYPE", [sigtype], contributor_login)
        if len(unique_pgp_ha) > 0: gx_output.c_log(f"PGP signatures used hash Algorithms: [{unique_pgp_ha}] obtained from parsing signature blobs", rtype="keys")


        # https://docs.github.com/en/rest/users/gpg-keys?apiVersion=2022-11-28#list-gpg-keys-for-a-user
        # GitHub calls them GPG keys, but we're going to refer to them as PGP for the OpenPGP standard
        pgp_keys = gh_api.fetch_gpg_keys(contributor_login)
        if pgp_keys != None and len(pgp_keys) > 0:
            primary_key_ids = [key.get('key_id') for key in pgp_keys]
            gx_output.c_log(f"{len(pgp_keys)} Primary PGP Keys in this contributor's profile: {str(primary_key_ids)}", rtype="keys")
            gx_output.c_log(f"PGP Keys: https://api.github.com/users/{contributor_login}/gpg_keys", rtype="keys")

        for primary_key in pgp_keys:
            # Let's parse and drain info from raw_key fields in primary keys
            if primary_key.get('raw_key') != None:
                key_attributes = gx_ugly_openpgp_parser.ugly_inhouse_openpgp_block(primary_key.get('raw_key'))
                if key_attributes.get('malformed_beginning') != None:
                    malformed_beginning = key_attributes.get('malformed_beginning').replace('\r\n',' | ')
                    gx_output.c_log(f"Bogus data found at the beginning of a PGP Key containing: {malformed_beginning}", rtype="user_input")
                if key_attributes.get('malformed_ending') != None:
                    malformed_ending = key_attributes.get('malformed_ending').replace('\r\n',' | ')
                    gx_output.c_log(f"Bogus data found at the end of a PGP Key containing: {malformed_ending}", rtype="user_input")
                if key_attributes.get('userId') != None:
                    gx_output.c_log(f"[{key_attributes.get('userId')}] obtained from parsing PGP Key ID {primary_key.get('key_id')}", rtype="personal")
                if key_attributes.get('armored_version') != None:
                    armored_version = key_attributes.get('armored_version').replace('\r\n',' | ')
                    gx_output.c_log(f"[Version: {armored_version}] obtained from parsing PGP Key ID {primary_key.get('key_id')}", rtype="keys")
                    gx_context.linkIdentifier("KEY_ARMORED_VERSION", [armored_version], contributor_login)
                if key_attributes.get('armored_comment') != None:
                    armored_comment = key_attributes.get('armored_comment').replace('\r\n',' | ')
                    gx_output.c_log(f"[Comment: {armored_comment}] obtained from parsing PGP Key ID {primary_key.get('key_id')}", rtype="keys")
                    gx_context.linkIdentifier("KEY_ARMORED_COMMENT", [armored_comment], contributor_login)

            # Let's add to the colab+key relationship all primary and subkeys from the user profile
            primary_key_id = primary_key.get('key_id')

            # Link this Primary Key ID to the contributor
            if primary_key_id: gx_context.linkIdentifier("PGP_KEYID", [primary_key_id], contributor_login)

            if primary_key.get('name') != None:
                gx_output.c_log(f"Primary key name typed by user for key {primary_key_id}: [{primary_key.get('name')}]", rtype="user_input")

            for email in primary_key.get('emails'):
                if email.get('email') not in contributor_emails:
                    message = "(shows as Verified)" if email.get('verified') == True else "(shows as Not Verified)"
                    gx_output.c_log(f"[{email.get('email')}] {message} obtained from primary Key with ID {primary_key_id}", rtype="emails")
                    contributor_emails.append(email.get('email'))
                    # There's a Verified: False or True field, we link it disregarding if its verified.
                    gx_context.linkIdentifier("EMAIL", [email['email']], contributor_login)
 
            for sub_key in primary_key["subkeys"]:
                sub_key_id = sub_key.get('key_id')
                if sub_key_id: gx_context.linkIdentifier("PGP_KEYID", [sub_key_id], contributor_login)

                if sub_key.get('name') != None:
                    gx_output.c_log(f"Subkey name typed by user for key {sub_key_id}: {sub_key.get('name')}", rtype="user_input")

                for email in sub_key.get('emails'):
                    if email not in contributor_emails: 
                        gx_output.c_log(f"[{email}] obtained from subKey with ID {sub_key_id}", rtype="emails")
                        contributor_emails.append(email)
                        gx_context.linkIdentifier("EMAIL", [email], contributor_login)
 
                if sub_key.get('expires_at') != None:
                    kexpiration = gh_time.parse_date(sub_key.get('expires_at'))
                    if kexpiration < datetime.now(timezone.utc):
                        message = '(EXPIRED)'
                    else:
                        message = f'(EXPIRES in {(kexpiration-datetime.now(timezone.utc)).days} days)'
                else:
                    message = '(DOES NOT EXPIRE)'

                gx_output.c_log(f"PGP Subkey {sub_key.get('key_id')} in profile. Created at: {sub_key.get('created_at')} - Expires: {sub_key.get('expires_at')} {message}", rtype="keys")
                days_since_creation = (datetime.now(timezone.utc) - gh_time.parse_date(sub_key.get('created_at'))).days 
                gx_context.linkIdentifier("PGP_SUBKEY_CREATED_AT", [days_since_creation], contributor_login)

            gx_output.c_log(f'Primary Key details: {primary_key}', rtype="debug")


        # SSH Signing keys 
        # https://docs.github.com/en/rest/users/ssh-signing-keys?apiVersion=2022-11-28#list-ssh-signing-keys-for-a-user
        ssh_signing_keys = gh_api.fetch_ssh_signing_keys(contributor_login)
        if ssh_signing_keys != None and len(ssh_signing_keys) > 0:
            gx_output.c_log(f"{len(ssh_signing_keys)} SSH Keys used for Signatures in this contributor's profile", rtype="keys")
            gx_output.c_log(f"SSH Signing Keys: https://api.github.com/users/{contributor_login}/ssh_signing_keys", rtype="keys")

        for ssh_signing_key in ssh_signing_keys:
            algorithm = gx_ugly_ssh_parser.ugly_inhouse_ssh_key(ssh_signing_key.get('key'))
            gx_output.c_log(f"SSH Signing Key title typed by user for Key ID [{ssh_signing_key.get('id')}]: [{ssh_signing_key.get('title')}]", rtype="user_input")
            algorithm = f"of type [{algorithm}] " if algorithm != None else ""
            gx_output.c_log(f"SSH Signing Key ID [{ssh_signing_key.get('id')}] {algorithm}in profile, created at {ssh_signing_key.get('created_at')}.", rtype="keys")
            days_since_creation = (datetime.now(timezone.utc) - gh_time.parse_date(ssh_signing_key.get('created_at'))).days 
            gx_context.linkIdentifier("SSH_SIGNING_KEY_CREATED_AT", [days_since_creation], contributor_login)

        # SSH Authentication keys
        ssh_auth_keys = gh_api.fetch_ssh_auth_keys(contributor_login)
        if len(ssh_auth_keys) > 0:
            gx_output.c_log(f"{len(ssh_auth_keys)} SSH Authentication Keys in this contributor's profile", rtype="keys")
            gx_output.c_log(f"SSH Authentication Keys: https://api.github.com/users/{contributor_login}/keys", rtype="keys")

        # We don't keep track of duplicate/cloned keys for authentication SSH keys because GitHub won't allow them
        # https://docs.github.com/en/authentication/troubleshooting-ssh/error-key-already-in-use
        for ssh_auth_key in ssh_auth_keys:
            algorithm = gx_ugly_ssh_parser.ugly_inhouse_ssh_key(ssh_auth_key.get('key'))
            algorithm = f"of type [{algorithm}] " if algorithm != None else ""
            gx_output.c_log(f"SSH Authentication Key ID [{ssh_auth_key.get('id')}] {algorithm}in profile.", rtype="keys")

        gx_output.c_log(f"All commits (for this Repo): {repository.get('html_url')}/commits/?author={contributor_login}", rtype="commits")
        # Unique key ids for now only holds keys we've extracted from commit signatures
        if len(unique_pgp_keyids) > 0:
            # https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#constructing-a-search-query
            # Unfortunately GitHub requires (for other users than our own) to provide (non-regex) input keywords in order to
            # return results in the commits API which accept filtering such as is:signed - and input keywords restrict our results.
            gx_output.c_log(f"{len(unique_pgp_keyids)} Keys ({unique_pgp_keyids}) were used by this contributor when signing commits.", rtype="keys")
            github_keys_used = [keyid for keyid in unique_pgp_keyids if keyid in gx_definitions.GITHUB_WEB_EDITOR_SIGNING_KEYS]
            if len(github_keys_used) > 0:
                gx_output.c_log(f"{len(github_keys_used)} of the keys used to sign commits belong to GitHub's Web editor {github_keys_used}", rtype="keys")

        if len(commits) == len(signed_commits):
            gx_output.c_log(f"Contributor has signed all of their {len(signed_commits)} total commits (to this repo).", rtype="signatures")

        if len(failed_verifications) > 0:
            gx_output.c_log(f"Contributor has failed signature verifications in {len(failed_verifications)} of their total {len(signed_commits)} signed commits.", rtype="signatures")

        if len(signed_commits) == 0 and len(failed_verifications) == 0:
            gx_output.c_log(f"Contributor has not signed any of their {len(commits)} commits (in this repo).", rtype="signatures")

        if len(signed_commits) == 0 and len(failed_verifications) > 0:
            gx_output.c_log(f"Contributor has {len(failed_verifications)} failed attempts at signing commits and 0 succesful commits signed out of their {len(commits)} total commits.", rtype="signatures")

        if len(signed_commits) > 0 and len(signed_commits) < len(commits):
            gx_output.c_log(f"Contributor has a mix of {len(signed_commits)} signed vs. {len(commits)-len(signed_commits)} unsigned commits (in this repo).", rtype="signatures")

        for scommit in signed_commits: 
            if scommit['verification']['reason'] != 'valid': print(scommit) # This shouldn't happen

        public_repos = int(contributor.get('public_repos'))
        if public_repos > 0:
            gx_output.c_log(f"Contributor has {public_repos} total public repos.", rtype="profiling")

        gx_output.c_log(f"Contributor has {contributor.get('followers')} followers.", rtype="profiling")


        matching_anonymous = [user for user in c_anon if user['email'] in contributor_emails]
        if len(matching_anonymous) > 0:
            gx_output.c_log(f"One of {contributor_login} emails matched the following anonymous users: {matching_anonymous}", rtype="profiling")


        gx_output.stdout(f"\r[{c_users_index}/{len(c_users)}] Collecting recent (90d) public events for {contributor.get('login')}"+' '*40, end = '', flush=True)

        # Get Public Events generated by this account, if any. GitHub offers up to 90 days of data, which might still be useful.
        public_events = gh_api.fetch_contributor_events(contributor)
        if len(public_events) > 0:
            gh_public_events.log_events(public_events, gx_output, for_repository=False)

        c_users_index += 1 
        c_ended_at = datetime.now()
        gx_output.c_log(f"X-Ray on contributor ended at {c_ended_at} - {(c_ended_at-c_started_at).seconds} seconds elapsed", rtype="metrics")

    # Let's first create a dictionary merging by email - this is because duplicate anonymous are "normal" or regularly seen
    # GitHub checks if any of (email OR name) differ and if so treats the anonymous user as different
    # Add all of these under Anonymous contributor output
    unique_anonymous = {}
    for ac in c_anon:
        email = ac.get('email','ERROR_PULLING_ANON_EMAIL')
        if email not in unique_anonymous:
            unique_anonymous[email] = []
        unique_anonymous[email].append(ac.get('name','ERROR_PULLING_ANON_NAME'))

    commits_url = f"Find commits with: https://api.github.com/search/commits?q=repo:{repository.get('full_name')}+author-email:PLACE_EMAIL_HERE"
    gx_output.a_log(commits_url, anonymous="#", rtype="urls")
    for k,v in unique_anonymous.items():
        gx_output.a_log(f'{k} - {v}', anonymous="#", rtype="anonymous")

    gx_output.stdout('\rContributors have been analyzed..'+' '*60, flush=True)

    return True
