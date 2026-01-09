from gitxray.include import gx_definitions

def run(gx_context, gx_output, gh_api):
    gx_output.stdout("Checking for potential associations across accounts by cross-referencing all gathered data...")

    collisions = gx_context.getCollisions()

    for colType, colValue in collisions:
        affected_accounts = collisions.get((colType, colValue))
        if not affected_accounts: continue
        msg = None

        if colType == "PGP_KEYID" and (colValue not in gx_definitions.GITHUB_WEB_EDITOR_SIGNING_KEYS):
                msg = f"WARNING: A Personal/Private PGP Key with ID {colValue} found shared by accounts: {affected_accounts}."
        elif colType == "PGP_SCT":
            msg = f"PGP Signature Creation Time ({colValue}) shared by accounts: {affected_accounts}."
        elif colType == "PGP_SUBKEY_CREATED_AT":
            msg = f"The following contributor accounts have PGP Subkeys that were created in the same day: {affected_accounts}."
        elif colType == "SSH_SIGNING_KEY_CREATED_AT":
            msg = f"The following contributor accounts have SSH signing keys that were created in the same day: {affected_accounts}."
        elif colType == "KEY_ARMORED_VERSION":
            msg = f"Exact same Version field extracted from a Key for accounts: {affected_accounts}: {colValue}."
        elif colType == "KEY_ARMORED_COMMENT":
            msg = f"Exact same Comment field extracted from a Key for accounts: {affected_accounts}: {colValue}."
        elif colType == "EMAIL":
            msg = f"Email {colValue} shared by accounts: {affected_accounts}."
        elif colType == "COAUTHOR_EMAIL":
            msg = f"Co-author email [{colValue}] appears in commits by: {affected_accounts}."
        elif colType == "COAUTHOR_NAME":
            msg = f"Co-author name [{colValue}] appears in commits by: {affected_accounts}."
        elif colType == "COAUTHOR_PAIR":
            msg = f"Shared co-authorship relationship: {colValue.replace('+', ' & ')} appears across commits by: {affected_accounts}."
        elif colType == "PRIMARY_ACTIVE_HOURS":
            msg = f"Primary active hours [{colValue}] shared by accounts: {affected_accounts} - suggests coordinated activity or same operator."
        elif colType == "COMMIT_PATTERN":
            if colValue == "weekend_focused":
                msg = f"Weekend-focused commit pattern shared by accounts: {affected_accounts} (commits outside typical work days)."
            elif colValue == "weekday_focused":
                msg = f"Weekday-focused commit pattern shared by accounts: {affected_accounts} (commits during typical work days)."
        elif colType == "INFERRED_TIMEZONE":
            msg = f"Inferred timezone [{colValue}] shared by accounts: {affected_accounts}."
        elif colType == "SUSPICIOUS_24_7_ACTIVITY":
            msg = f"WARNING: Unusual commit distribution detected for accounts: {affected_accounts} - commits spread across {colValue} different hours of the day (potential automated activity)."
        elif colType == "DAYS_SINCE_CREATION":
            msg = f"The following contributor accounts were created in the same day, precisely {colValue} days ago: {affected_accounts}."
        elif colType == "DAYS_SINCE_UPDATED" :
            msg = f"The following contributor accounts were last updated in the same day, precisely {colValue} days ago: {affected_accounts}."

        if msg != None: 
            gx_output.r_log(msg, rtype="association")
            for account in affected_accounts: gx_output.c_log(msg, rtype="association", contributor=account)

        # Now check some more which add lots of noise, we only want these in r_log, not per contributor.
        msg = None
        if colType == "PGP_HA":
            msg = f"PGP Hash Algorithm ({colValue}) shared by accounts: {affected_accounts}."
        elif colType == "PGP_PKA":
            msg = f"PGP Public Key Algorithm ({colValue}) shared by accounts: {affected_accounts}."
        elif colType == "PGP_KEYID" and colValue in gx_definitions.GITHUB_WEB_EDITOR_SIGNING_KEYS:
            msg = f"GitHub's Web Editor (Key ID: {colValue}) was used by accounts: {affected_accounts}."
        elif colType == "PGP_SIG_TYPE":
            msg = f"PGP Signature Type ({colValue}) shared by accounts: {affected_accounts}."
        elif colType == "SSH_SA":
            msg = f"SSH Signature Algorithm ({colValue}) shared by accounts: {affected_accounts}."

        if msg != None: 
            gx_output.r_log(msg, rtype="association")

    return True
