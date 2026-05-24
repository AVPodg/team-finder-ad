# Максимальная длина имени проекта
MAX_PROJECT_NAME_LENGTH = 200

# Максимальная длина статуса (максимум среди STATUS_CHOICES)
STATUS_MAX_LENGTH = max(len(status[0]) for status in (
    ("open", "Open"),
    ("closed", "Closed"),
))

PROJECTS_PER_PAGE = 12
SEARCH_QUERY_MAX_LENGTH = 100