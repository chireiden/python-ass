#!/usr/bin/env python

from io import StringIO
from pathlib import Path
from textwrap import dedent

import pytest

import ass

folder = Path(__file__).parent


class TestDocument:

    test_ass = Path(folder, "test.ass")

    def test_parse_dump(self):
        with self.test_ass.open("r", encoding='utf_8_sig') as f:
            contents = f.read()

        doc = ass.parse(StringIO(contents))
        out = StringIO()
        doc.dump_file(out)

        assert out.getvalue().strip() == contents.strip()

    def test_parse_encoding(self):
        with self.test_ass.open("r", encoding='utf_8') as f:
            with pytest.raises(ValueError):
                ass.parse(f)

        with self.test_ass.open("r", encoding='ascii') as f:
            with pytest.raises(ValueError):
                ass.parse(f)

    def test_dump_encoding(self):
        for encoding in ('utf_8_sig', 'utf-8-sig'):
            with self.test_ass.open("r", encoding=encoding) as f:
                doc = ass.parse(f)

            with self.test_ass.open("r", encoding=encoding.upper()) as f:
                doc = ass.parse(f)

        import tempfile
        with tempfile.TemporaryFile(mode='w', encoding='utf_8') as f:
            with pytest.warns(UserWarning):
                doc.dump_file(f)


class TestSections:

    def test_default_sections(self):
        doc = ass.Document()
        assert len(doc.sections) == 3
        assert doc.fields is doc.info
        assert len(doc.fields) == 0
        assert len(doc.styles) == 0
        assert len(doc.events) == 0

    def test_scipt_info(self):
        TEST_SCRIPT_INFO = dedent("""\
            [Script Info]
            ScriptType: v4.00+
            PlayResX: 500
            PlayResY: 500""")

        doc = ass.Document.parse_string(TEST_SCRIPT_INFO)
        doc.info["PlayResY"] = 50
        doc.info["Arbitrary Field"] = "hi"

        assert len(doc.sections) == 3
        assert doc.info["PlayResX"] == 500
        assert doc.play_res_y == 50
        doc.play_res_y = 5
        assert doc.play_res_y == 5

        copy = doc.info.copy()
        copy["PlayResX"] = 1
        assert copy["Arbitrary Field"] == "hi"
        assert doc.play_res_x == 500

    def test_styles(self):
        pass

    def test_events(self):
        pass

    TEST_CUSTOM = dedent("""\
        [Custom Section]
        Line: 1
        Line: 2
        Line: 3
        Another Line: 20""")

    @pytest.fixture
    def line_section(self):
        doc = ass.Document.parse_string(self.TEST_CUSTOM)
        return doc.sections["Custom Section"]

    def test_custom_line_section_parse(self):
        doc = ass.Document.parse_string(self.TEST_CUSTOM)
        assert "custom section" in doc.sections
        assert "Custom Section" in doc.sections
        assert doc.sections["Custom Section"].name == "Custom Section"

    def test_custom_line_section_read(self, line_section):
        assert len(line_section) == 4
        line = line_section[0]
        assert isinstance(line, ass.Unknown)
        assert line.TYPE == "Line"
        assert line.value == "1"
        assert line_section[-1].value == "20"

    def test_custom_line_section_write(self, line_section):
        line_section.add_line("Test", "test")
        assert len(line_section) == 5
        line_section[:3] = line_section[:2]  # remove 3rd line with a slice
        assert [x.value for x in line_section] == ["1", "2", "20", "test"]

    def test_custom_line_section_dump(self, line_section):
        assert "\n".join(line_section.dump()) == self.TEST_CUSTOM
