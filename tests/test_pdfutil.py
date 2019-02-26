from PyPDF2 import PdfFileReader
import pytest

from barnhunt.pdfutil import (
    concat_pdfs,
    two_up,
    )


def test_concat_pdfs(tmpdir, test1_pdf, test2_pdf):
    output_fn = str(tmpdir.join('foo/output.pdf'))
    input_fns = [str(test1_pdf), str(test2_pdf)]
    concat_pdfs(input_fns, output_fn)
    assert page_count(output_fn) == 2
    assert pdf_title(output_fn) == 'Test File #1'


def test_concat_pdfs_one_pdf(tmpdir, test1_pdf):
    output_fn = str(tmpdir.join('single.pdf'))
    concat_pdfs([str(test1_pdf)], output_fn)
    assert page_count(output_fn) == 1
    assert pdf_title(output_fn) == 'Test File #1'


def test_concat_pdfs_no_pdfs(tmpdir):
    output_fn = str(tmpdir.join('empty.pdf'))
    with pytest.raises(ValueError):
        concat_pdfs([], output_fn)


def test_two_up_two_pages(tmpdir, test1_pdf, test2_pdf):
    out_path = tmpdir.join('output.pdf')
    in_files = [test1_pdf.open('rb'), test2_pdf.open('rb')]
    with out_path.open('wb') as out_file:
        two_up(in_files, out_file)
    assert page_count(str(out_path)) == 1


def test_two_up_three_pages(tmpdir, test1_pdf, test2_pdf):
    out_path = tmpdir.join('output.pdf')
    in_files = [
        test1_pdf.open('rb'),
        test1_pdf.open('rb'),
        test2_pdf.open('rb'),
        ]
    with out_path.open('wb') as out_file:
        two_up(in_files, out_file)
    assert page_count(str(out_path)) == 2


def page_count(pdf_fn):
    pdf = PdfFileReader(open(pdf_fn, 'rb'))
    return len(pdf.pages)


def pdf_title(pdf_fn):
    pdf = PdfFileReader(open(pdf_fn, 'rb'))
    return pdf.documentInfo.title
