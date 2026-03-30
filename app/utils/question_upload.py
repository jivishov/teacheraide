"""
Question Upload Module

Handles parsing of previously generated QTI packages and YAML files,
allowing users to upload and import questions into the Review & Download section.
"""

import zipfile
import io
import xml.etree.ElementTree as ET
import logging
from typing import Tuple, List, Dict, Optional
import re


class QuestionUploadParser:
    """Parses uploaded question files (QTI packages) and extracts questions."""

    QTI_NS = {"qti": "http://www.imsglobal.org/xsd/imsqti_v2p2"}
    MAX_UNCOMPRESSED_FILE_SIZE = 50 * 1024 * 1024
    MAX_TOTAL_UNCOMPRESSED_SIZE = 200 * 1024 * 1024

    def __init__(self):
        self.questions_xml: List[str] = []
        self.media_files: Dict[str, bytes] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def parse_qti_package(self, file_bytes: bytes) -> Tuple[List[str], Dict[str, bytes], List[str]]:
        """
        Parse a QTI package (zip file) and extract question XMLs and media files.

        Args:
            file_bytes: The raw bytes of the uploaded zip file

        Returns:
            Tuple of (questions_xml_list, media_files_dict, errors_list)
        """
        questions, media, errors, _warnings = self.parse_qti_package_with_report(file_bytes)
        return questions, media, errors

    def parse_qti_package_with_report(
        self,
        file_bytes: bytes,
    ) -> Tuple[List[str], Dict[str, bytes], List[str], List[str]]:
        """
        Parse a QTI package and return both errors and non-fatal warnings.

        Returns:
            Tuple of (questions_xml_list, media_files_dict, errors_list, warnings_list)
        """
        self.questions_xml = []
        self.media_files = {}
        self.errors = []
        self.warnings = []

        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), 'r') as zf:
                file_infos = [info for info in zf.infolist() if not info.is_dir()]
                total_uncompressed_size = sum(info.file_size for info in file_infos)
                if total_uncompressed_size > self.MAX_TOTAL_UNCOMPRESSED_SIZE:
                    total_mb = total_uncompressed_size / (1024 * 1024)
                    limit_mb = self.MAX_TOTAL_UNCOMPRESSED_SIZE / (1024 * 1024)
                    self.errors.append(
                        f"ZIP package is too large when extracted ({total_mb:.1f}MB > {limit_mb:.0f}MB limit)."
                    )
                    return [], {}, self.errors, self.warnings

                logging.info(f"QTI package contains {len(file_infos)} files")

                for info in file_infos:
                    filename = info.filename
                    if info.file_size > self.MAX_UNCOMPRESSED_FILE_SIZE:
                        file_mb = info.file_size / (1024 * 1024)
                        limit_mb = self.MAX_UNCOMPRESSED_FILE_SIZE / (1024 * 1024)
                        self.errors.append(
                            f"File {filename} is too large when extracted ({file_mb:.1f}MB > {limit_mb:.0f}MB limit)."
                        )
                        return [], {}, self.errors, self.warnings

                    # Handle media files
                    if filename.startswith('media/') or '/media/' in filename:
                        try:
                            media_content = zf.read(filename)
                            # Extract just the filename without path
                            media_name = filename.split('/')[-1]
                            if media_name:
                                self.media_files[media_name] = media_content
                                logging.info(f"Extracted media file: {media_name}")
                        except Exception as e:
                            self.errors.append(f"Failed to read media file {filename}: {str(e)}")

                    # Handle XML question files (skip manifest and assessment files)
                    elif filename.endswith('.xml'):
                        # Skip manifest and test structure files
                        if 'manifest' in filename.lower() or 'assessmenttest' in filename.lower():
                            continue

                        try:
                            xml_content = zf.read(filename).decode('utf-8')
                            # Validate it's a question item (has assessmentItem)
                            if self._is_valid_question_xml(xml_content):
                                self.questions_xml.append(xml_content)
                                logging.info(f"Extracted question from: {filename}")
                            else:
                                self.warnings.append(
                                    f"Skipped non-question XML file: {filename}"
                                )
                                logging.debug(f"Skipped non-question XML: {filename}")
                        except Exception as e:
                            self.errors.append(f"Failed to parse {filename}: {str(e)}")

        except zipfile.BadZipFile:
            self.errors.append("Invalid ZIP file format. Please upload a valid QTI package.")
        except Exception as e:
            self.errors.append(f"Error processing file: {str(e)}")

        logging.info(
            "Parsed %s questions, %s media files, %s errors, %s warnings",
            len(self.questions_xml),
            len(self.media_files),
            len(self.errors),
            len(self.warnings),
        )
        return self.questions_xml, self.media_files, self.errors, self.warnings

    def _is_valid_question_xml(self, xml_content: str) -> bool:
        """Check if XML content represents a valid QTI question item."""
        try:
            root = ET.fromstring(xml_content)
            # Check for assessmentItem element (with or without namespace)
            tag_name = root.tag
            if 'assessmentItem' in tag_name:
                return True
            return False
        except ET.ParseError:
            return False

    def parse_single_xml(self, xml_content: str) -> Tuple[List[str], List[str]]:
        """
        Parse a single XML file that may contain one or more questions.

        Args:
            xml_content: The XML content as string

        Returns:
            Tuple of (questions_xml_list, errors_list)
        """
        questions = []
        errors = []

        try:
            if self._is_valid_question_xml(xml_content):
                questions.append(xml_content)
            else:
                errors.append("Invalid QTI question format")
        except Exception as e:
            errors.append(f"Error parsing XML: {str(e)}")

        return questions, errors


def validate_uploaded_file(filename: str, file_bytes: bytes) -> Tuple[bool, str, str]:
    """
    Validate an uploaded file and determine its type.

    Args:
        filename: Original filename
        file_bytes: File content as bytes

    Returns:
        Tuple of (is_valid, file_type, error_message)
        file_type is one of: "qti_package", "xml", "unknown"
    """
    if not filename or not file_bytes:
        return False, "unknown", "No file provided"

    filename_lower = filename.lower()

    # Check for ZIP/QTI package
    if filename_lower.endswith('.zip'):
        # Verify it's actually a ZIP file
        if file_bytes[:4] == b'PK\x03\x04' or file_bytes[:4] == b'PK\x05\x06':
            return True, "qti_package", ""
        else:
            return False, "unknown", "File has .zip extension but is not a valid ZIP file"

    # Check for XML file
    if filename_lower.endswith('.xml'):
        try:
            content = file_bytes.decode('utf-8')
            ET.fromstring(content)
            return True, "xml", ""
        except UnicodeDecodeError:
            return False, "unknown", "XML file is not valid UTF-8"
        except ET.ParseError as e:
            return False, "unknown", f"Invalid XML format: {str(e)}"

    return False, "unknown", f"Unsupported file type. Please upload a .zip (QTI package) or .xml file."


def process_uploaded_questions(
    filename: str,
    file_bytes: bytes
) -> Tuple[List[str], Dict[str, bytes], List[str]]:
    """
    Main entry point for processing uploaded question files.

    Args:
        filename: Original filename of the uploaded file
        file_bytes: Raw file content

    Returns:
        Tuple of (questions_xml_list, media_files_dict, errors_list)
    """
    questions, media, errors, _warnings = process_uploaded_questions_with_report(
        filename=filename,
        file_bytes=file_bytes,
    )
    return questions, media, errors


def process_uploaded_questions_with_report(
    filename: str,
    file_bytes: bytes
) -> Tuple[List[str], Dict[str, bytes], List[str], List[str]]:
    """
    Process uploaded question files with warning details.

    Returns:
        Tuple of (questions_xml_list, media_files_dict, errors_list, warnings_list)
    """
    # Validate file
    is_valid, file_type, error = validate_uploaded_file(filename, file_bytes)

    if not is_valid:
        return [], {}, [error], []

    parser = QuestionUploadParser()

    if file_type == "qti_package":
        return parser.parse_qti_package_with_report(file_bytes)
    elif file_type == "xml":
        xml_content = file_bytes.decode('utf-8')
        questions, errors = parser.parse_single_xml(xml_content)
        return questions, {}, errors, []
    else:
        return [], {}, ["Unsupported file type"], []


def get_upload_summary(questions_xml: List[str]) -> Dict[str, int]:
    """
    Generate a summary of uploaded questions by type.

    Args:
        questions_xml: List of question XML strings

    Returns:
        Dictionary with question type counts
    """
    ns = {"qti": "http://www.imsglobal.org/xsd/imsqti_v2p2"}
    summary = {"MCQ": 0, "MRQ": 0, "TF": 0, "FIB": 0, "Essay": 0, "Match": 0, "Order": 0, "Unknown": 0}

    for xml_str in questions_xml:
        try:
            root = ET.fromstring(xml_str)
            q_type = _detect_question_type(root, ns)
            if q_type in summary:
                summary[q_type] += 1
            else:
                summary["Unknown"] += 1
        except ET.ParseError:
            summary["Unknown"] += 1

    return summary


def _detect_question_type(root: ET.Element, ns: dict) -> str:
    """Detect the question type from XML root element."""
    # Check for T/F first (uses choiceInteraction but with baseType="boolean")
    resp_decl = root.find(".//qti:responseDeclaration", ns)
    if resp_decl is None:
        # Try without namespace
        resp_decl = root.find(".//responseDeclaration")

    if resp_decl is not None and resp_decl.get("baseType") == "boolean":
        return "TF"

    # Check for various interaction types
    if root.find(".//qti:choiceInteraction", ns) is not None or root.find(".//choiceInteraction") is not None:
        # Distinguish MCQ from MRQ by cardinality
        if resp_decl is not None and resp_decl.get("cardinality") == "multiple":
            return "MRQ"
        return "MCQ"

    if root.find(".//qti:textEntryInteraction", ns) is not None or root.find(".//textEntryInteraction") is not None:
        return "FIB"

    if root.find(".//qti:extendedTextInteraction", ns) is not None or root.find(".//extendedTextInteraction") is not None:
        return "Essay"

    if root.find(".//qti:matchInteraction", ns) is not None or root.find(".//matchInteraction") is not None:
        return "Match"

    if root.find(".//qti:orderInteraction", ns) is not None or root.find(".//orderInteraction") is not None:
        return "Order"

    return "Unknown"
