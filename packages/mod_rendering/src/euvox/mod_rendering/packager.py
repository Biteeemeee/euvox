import io
import zipfile


def package_zip(files: dict[str, str], mod_name: str) -> bytes:
    """Pack a dict of {relative_path: text_content} into a ZIP archive."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in sorted(files.items()):
            zf.writestr(f"{mod_name}/{path}", content)
    return buf.getvalue()


def list_zip_members(data: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return zf.namelist()


def read_zip_member(data: bytes, member: str) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return zf.read(member).decode()
