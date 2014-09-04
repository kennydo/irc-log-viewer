from flask import current_app


WILDCARD = '*'


def email_can_read_channel_logs(email, znc_username, channel):
    """Returns whether the given ``email`` has permission to access
    ``znc_username``'s logs for ``channel``.

    :param str email: e-mail address of the web user
    :param str znc_username: ZNC username
    :param str channel: name of an IRC channel
    :return: True if ``email`` has permission to read the log, else False
    """
    acl_rules = current_app.config.get('ZNC_ACL')
    if not acl_rules:
        current_app.logger.error("No ACL rules found")
        raise ValueError('ZNC_ACL config variable was not defined')

    if not email:
        email = WILDCARD

    for action, rule_email, rule_username, rule_channel in acl_rules:
        if rule_email != WILDCARD and rule_email != email:
            continue

        if rule_username != WILDCARD and rule_username != znc_username:
            continue

        if rule_channel != WILDCARD and rule_channel != channel:
            continue

        return action.strip().lower() == 'allow'

    return ValueError(
        "Found no applicable rules in ZNC_ACL for "
        "email={0} on znc_username={1} and channel={2}".format(
            email, znc_username, channel
        )
    )