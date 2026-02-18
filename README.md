# Goodreads to Obsidian

Convert your Goodreads library export into Obsidian-ready markdown notes.

## Usage

- First, export your Goodreads library as a CSV file and save it as `goodreads_library_export.csv` in the project root.
- To parse the library file and fetch book cover links, run `uv run python main.py parse`
- To convert the parsed data into markdown files with proper frontmatter, run `uv run python main.py convert`

## Notes

- Only books with reviews will be processed by default. There's a setting to include all books, but it may result in a
  large number of files if the library is huge.
- Book covers are automatically fetched from Goodreads
- Output files use the book title as filename
- The template markdown file is based on my existing notes and preferences.