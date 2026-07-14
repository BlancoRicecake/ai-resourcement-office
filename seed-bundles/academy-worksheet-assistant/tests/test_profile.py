# -*- coding: utf-8 -*-
import importlib.util
import os
import sys
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from lib.profile import empty_alignment, validate_alignment, validate_catalog, validate_profile


def load_setup_module():
    spec = importlib.util.spec_from_file_location("academy_setup", os.path.join(ROOT, "setup.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SetupTests(unittest.TestCase):
    def test_build_profile_is_subject_agnostic(self):
        setup = load_setup_module()
        profile = setup.build_profile({
            "subject": "사용자 선택 과목", "school_level": "중학교", "grade": "1",
            "exam_year": "2026", "curriculum": "사용자 지정 교육과정",
            "curriculum_source": "official.pdf", "default_school": "예시학교",
            "publisher": "예시출판", "textbook_title": "예시교재",
            "output_formats": "hwp,pdf", "layout_notes": "2단",
        })
        self.assertEqual(profile["knowledge_status"], "pending")
        self.assertEqual(profile["subject"], "사용자 선택 과목")
        self.assertEqual(validate_profile(profile), [])

    def test_unsupported_output_is_rejected(self):
        setup = load_setup_module()
        values = {
            "subject": "수학", "school_level": "중학교", "grade": "1", "exam_year": "2026",
            "curriculum": "예시", "output_formats": "docx", "curriculum_source": None,
            "default_school": None, "publisher": None, "textbook_title": None, "layout_notes": None,
        }
        with self.assertRaises(ValueError):
            setup.build_profile(values)


class KnowledgeGateTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "subject": "수학", "school_level": "중학교", "grade": "1", "exam_year": "2026",
            "curriculum": "예시 교육과정", "input_format": "pdf", "output_formats": ["hwp"],
        }
        self.catalog = {
            "subject": "수학", "curriculum": "예시 교육과정",
            "sources": [{"title": "공식 문서", "reference": "official.pdf"}],
            "units": [{"code": "U01", "title": "수와 연산", "standards": [{"code": "STD-01", "statement": "성취기준"}]}],
            "approval": {"status": "approved"},
        }

    def test_approved_catalog_passes(self):
        self.assertEqual(validate_catalog(self.catalog, self.profile), [])

    def test_pending_catalog_is_blocked(self):
        self.catalog["approval"]["status"] = "pending"
        self.assertTrue(any("승인" in error for error in validate_catalog(self.catalog, self.profile)))

    def test_alignment_uses_user_catalog(self):
        alignment = empty_alignment()
        alignment.update({
            "status": "confirmed", "unit_code": "U01", "standard_code": "STD-01",
            "confidence": 0.9, "evidence": ["발문 근거"], "review_required": False,
        })
        self.assertEqual(validate_alignment(alignment, self.catalog), [])


if __name__ == "__main__":
    unittest.main()
