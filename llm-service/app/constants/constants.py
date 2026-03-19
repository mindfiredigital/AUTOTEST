"""Site extraction filtering constants.

Defines file extensions and path fragments that the page extractor should
ignore. Keep these lists small and explicit — they are used to quickly
skip binary, media, or asset endpoints that are not useful for text
analysis.
"""

# File extensions that indicate binary, media, archive or other non-HTML
# resources. The extractor should skip URLs that end with these extensions.
BLOCKED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".pdf",
    ".txt",
    ".csv",
    ".json",
    ".xml",
    ".zip",
    ".rar",
    ".7z",
    ".mp4",
    ".webm",
    ".avi",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".bin",
}


# Path substrings commonly present in asset, upload or download endpoints.
# If a URL contains any of these fragments, it is usually safe to skip it
# during crawl/page extraction to avoid non-content pages.
BLOCKED_PATH_KEYWORDS = {
    "/download/",
    "/uploads/",
    "/files/",
    "/assets/",
    "/static/",
    "/media/",
}