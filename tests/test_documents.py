import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
from provider.documents import read_document, DocumentError


class DocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_reads_text_and_rejects_images(self):
        path = self.root / 'note.txt'
        path.write_text('خطة اليوم', encoding='utf-8')
        self.assertIn('خطة', read_document(path)['text'])
        image = self.root / 'photo.png'
        image.write_bytes(b'\x89PNG\r\n')
        with self.assertRaises(DocumentError):
            read_document(image)

    def test_reads_docx(self):
        path = self.root / 'letter.docx'
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr(
                'word/document.xml',
                '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>عقد توريد</w:t></w:r></w:p></w:body></w:document>',
            )
        path.write_bytes(buffer.getvalue())
        self.assertIn('عقد توريد', read_document(path)['text'])

    def test_rejects_empty_and_huge(self):
        empty = self.root / 'empty.txt'
        empty.write_text('   \n', encoding='utf-8')
        with self.assertRaises(DocumentError):
            read_document(empty)
        huge = self.root / 'huge.txt'
        huge.write_bytes(b'a' * (2_000_000 + 1))
        with self.assertRaises(DocumentError):
            read_document(huge)
