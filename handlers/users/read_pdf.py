import os
from pypdf import PdfReader, PdfWriter


def find_page_by_group(pdf_path, group_name):
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    for page_num in range(total_pages):
        page = reader.pages[page_num]
        text = page.extract_text()
        if group_name in text:
            return page_num + 1  # Return the page number where the group is found (+1 for human-readable numbering)

    return None  # Return None if the group name was not found

def save_page_as_pdf(pdf_path, page_num, output_dir, output_filename):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.add_page(reader.pages[page_num - 1])  # page_num is 1-based
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, output_filename)
    with open(output_path, 'wb') as output_pdf:
        writer.write(output_pdf)
    return output_path

def get_group_page_pdf(pdf_path, group_name, output_dir=".", output_filename=None):
    page_num = find_page_by_group(pdf_path, group_name)

    if page_num is not None:
        if output_filename is None:
            output_filename = f"{group_name}.pdf"  # Output filename for the new PDF

        output_path = save_page_as_pdf(pdf_path, page_num, output_dir, output_filename)
        print(f"Group '{group_name}' found on page {page_num}. New PDF saved as {output_path}")
        return output_path
    else:
        print(f"Group '{group_name}' not found in the PDF.")
        return None





def get_next_row_text_with_pages(pdf_path, search_word):
    """Return a list of dictionaries with the next row after the search word from all pages of the PDF."""
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    next_rows = []

    # Loop through each page in the PDF
    for page_num in range(total_pages):
        page = reader.pages[page_num]
        text = page.extract_text()

        # Split the text into lines
        lines = text.split('\n')

        # Find the search word and get the next line
        for i, line in enumerate(lines):

            if search_word in line:
                if i + 1 < len(lines):  # Ensure there is a next line
                    next_row = lines[i + 1].strip()
                    next_rows.append({"name": next_row, "page": page_num + 1})  # Add next line with page number

    if not next_rows:
        return [{"message": "Search word not found in the PDF."}]
    print(next_rows)
    return next_rows

