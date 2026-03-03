import argparse
import csv
import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path

GOODREADS_EXPORT_FILE = "goodreads_library_export.csv"
PARSED_OUTPUT_FILE = "books.json"
ONLY_BOOKS_WITH_REVIEWS = True


def get_goodreads_book_image(book_id: str) -> str:
    url = f"https://www.goodreads.com/book/show/{book_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"error fetching book data: {str(e)}"

    soup = BeautifulSoup(response.text, 'html.parser')
    image_tag = soup.find("meta", property="og:image")
    image_url = image_tag["content"] if image_tag else "N/A"

    return image_url


def get_books(filename: str) -> dict:
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        books = {}
        for row in reader:
            book = {
                'book_id': row['Book Id'],
                'title': row['Title'],
                'author': row['Author'],
                'my_rating': row['My Rating'],
                'average_rating': row['Average Rating'],
                'Number of Pages': row['Number of Pages'],
                'date_added': row['Date Added'],
                'date_read': row['Date Read'],
                'bookshelves': row['Bookshelves'],
                'exclusive_shelf': row['Exclusive Shelf'],
                'review': row['My Review'],
                'private_notes': row['Private Notes'],
            }
            books[row['Book Id']] = book
    print(f"Loaded {len(books)} books")
    return books


def pollinate_books_with_images(books: dict) -> dict:
    for book_id, book in books.items():
        image_url = get_goodreads_book_image(book_id)
        if "error fetching book data" not in image_url:
            book['image_thumbnail'] = image_url
        else:
            print(f"Failed to fetch data for book ID {book_id}: {image_url}")
            book['image_thumbnail'] = ''
    return books


def get_books_with_reviews(books: dict) -> dict:
    books_with_reviews = {}
    for book_id, book in books.items():
        if book['review'].strip():
            books_with_reviews[book_id] = book
    print(f"Filtered {len(books_with_reviews)} books with reviews")
    return pollinate_books_with_images(books_with_reviews)


def write_to_json_file(books: dict, filename: str):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(books, file, ensure_ascii=False, indent=4)
    print(f"Wrote {len(books)} books to {filename}")


def read_parsed_data(filename: str) -> dict:
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    print(f"Loaded {len(data)} books from {filename}")
    return data


def clean_goodreads_review(review: str) -> str:
    # replace line breaks, convert bold and italics
    # also escapes any other curly braces to prevent template engine issues
    if not review:
        return ""

    clean = re.sub(r'<br\s*/?>', '\n', review)
    clean = re.sub(r'<b>(.*?)</b>', r'**\1**', clean)
    clean = re.sub(r'<i>(.*?)</i>', r'*\1*', clean)

    clean = clean.replace("{", "{{").replace("}", "}}")

    return clean.strip()


def write_to_markdown_file(books: dict):
    with open("template.md", 'r', encoding='utf-8') as file:
        file_content_template = file.read()

    for book_id, book in books.items():
        book['source'] = f"https://www.goodreads.com/book/show/{book_id}"
        book['review'] = clean_goodreads_review(book['review'])
        if book['private_notes']:
            book['private_notes'] = clean_goodreads_review(book['private_notes'])
        title = book['title']
        # if title contains ":" replace it with " - ".
        # android does not allow ":" in file names and this will make syncthing to work properly across all platforms.
        title = title.replace(":", " - ")
        output = file_content_template.format_map(book)

        file_path_str = f"books/{title}.md"
        file_path = Path(file_path_str)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(output)
        print(f"Wrote book '{title}' to {file_path}")


def parse_books():
    print("Starting parsing process...")
    books = get_books(GOODREADS_EXPORT_FILE)
    if ONLY_BOOKS_WITH_REVIEWS:
        books = get_books_with_reviews(books)
    else:
        books = pollinate_books_with_images(books)
    write_to_json_file(books, PARSED_OUTPUT_FILE)
    print("Parsing complete!")


def convert_books():
    print("Starting conversion process...")
    parsed_data = read_parsed_data(PARSED_OUTPUT_FILE)
    write_to_markdown_file(parsed_data)
    print("Conversion complete!")


def main():
    parser = argparse.ArgumentParser(description="Goodreads to Obsidian converter")
    parser.add_argument(
        "action",
        choices=["parse", "convert"],
        help="Action to perform: 'parse' to extract data from CSV into JSON, 'convert' to generate markdown files that can be copy pasted into Obsidian"
    )

    args = parser.parse_args()

    if args.action == "parse":
        parse_books()
    elif args.action == "convert":
        convert_books()


if __name__ == '__main__':
    main()
