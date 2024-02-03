import io
from base64 import b64decode
from pypdf import PdfWriter, PdfReader, PageObject, Transformation


def merge_labels(b64_labels: list, outpath: str):
    """
    Merge DPD labels to use less paper when printing. There can be up to 4 labels on one page.
    Save merged pdf file in outpath.
    """
    assert b64_labels
    pages = []
    for idx, b64_label in enumerate(b64_labels):
        label = b64decode(b64_label, validate=True)
        label_io = io.BytesIO(label)
        reader = PdfReader(label_io)
        assert len(reader.pages) == 1
        pdf_page = reader.pages[0]
        if not pages or idx % 4 == 0:
            new_page = PageObject.create_blank_page(width=pdf_page.mediabox.right,
                                                    height=pdf_page.mediabox.top)
            pages.append(new_page)

        match idx % 4:
            case 0:
                pass
            case 1:
                pdf_page.add_transformation(
                    Transformation().translate(pdf_page.mediabox.right / 2, 0))
                pdf_page.mediabox = pages[-1].mediabox  # ensure it is visible
            case 2:
                pdf_page.add_transformation(
                    Transformation().translate(0, -pdf_page.mediabox.top / 2))
                pdf_page.mediabox = pages[-1].mediabox  # ensure it is visible
            case 3:
                pdf_page.add_transformation(
                    Transformation().translate(pdf_page.mediabox.right / 2,
                                               -pdf_page.mediabox.top / 2))
                pdf_page.mediabox = pages[-1].mediabox  # ensure it is visible

        pages[-1].merge_page(pdf_page)

    pdf_writer = PdfWriter()
    for page in pages:
        pdf_writer.add_page(page)
    with open(outpath, "wb") as f:
        pdf_writer.write(f)
