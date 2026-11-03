"""Constants for the house wiki."""

DOMAIN = "house_wiki"

CONF_REPO = "repo"
CONF_BRANCH = "branch"
CONF_INCLUDE = "include"
CONF_MENTION_IN = "mention_in"
CONF_MENTION_TERMS = "mention_terms"
CONF_EXCLUDE = "exclude"

# Defaults hold nothing personal; the household's own terms are set in the entry's options.
DEFAULT_BRANCH = "main"
DEFAULT_INCLUDE = "smarthome/"
DEFAULT_MENTION_IN = ""
DEFAULT_MENTION_TERMS = ""
DEFAULT_EXCLUDE = "CLAUDE.md\n/people/\n/briefs/"
