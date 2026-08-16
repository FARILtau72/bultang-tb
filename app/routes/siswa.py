from flask import Blueprint, jsonify, render_template, request, redirect, url_for

from app.services.auth_service import admin_required
from app.core.config import JURUSAN
from app.core.models import (
    add_siswa,
    delete_siswa,
    edit_siswa,
    get_kelas_options,
    get_siswa_by_id,
    list_siswa,
    regenerate_qr_siswa,
)


siswa_bp = Blueprint("siswa", __name__)


@siswa_bp.route("/siswa")
@admin_required
def siswa_list():
    jurusan = (request.args.get("jurusan") or "").upper().strip()
    kelas = (request.args.get("kelas") or "").upper().strip()

    jurusan_filter = jurusan if jurusan in JURUSAN else None
    kelas_filter = kelas if kelas else None

    data_siswa = list_siswa(jurusan_filter, kelas_filter)
    kelas_options = get_kelas_options(jurusan_filter)

    return render_template(
        "siswa_list.html",
        siswa_list=data_siswa,
        jurusan_options=JURUSAN,
        kelas_options=kelas_options,
        filters={"jurusan": jurusan_filter or "", "kelas": kelas_filter or ""},
    )


@siswa_bp.route("/siswa/tambah", methods=["GET", "POST"])
@admin_required
def siswa_add():
    error_message = None
    created_siswa = None

    selected_jurusan = (request.form.get("jurusan") or JURUSAN[0]).upper()
    kelas_options = get_kelas_options(selected_jurusan)

    form_data = {
        "nis": request.form.get("nis", "").strip(),
        "nama": request.form.get("nama", "").strip(),
        "jurusan": selected_jurusan,
        "kelas": (request.form.get("kelas") or "").upper(),
    }

    if request.method == "POST":
        try:
            created_siswa = add_siswa(
                nis=form_data["nis"],
                nama=form_data["nama"],
                jurusan=form_data["jurusan"],
                kelas=form_data["kelas"],
            )
            form_data = {
                "nis": "",
                "nama": "",
                "jurusan": selected_jurusan,
                "kelas": "",
            }
        except ValueError as exc:
            error_message = str(exc)

    return render_template(
        "siswa_add.html",
        jurusan_options=JURUSAN,
        kelas_options=kelas_options,
        created_siswa=created_siswa,
        error_message=error_message,
        form_data=form_data,
    )


@siswa_bp.route("/api/kelas")
@admin_required
def api_kelas():
    jurusan = (request.args.get("jurusan") or "").upper().strip()
    kelas_options = get_kelas_options(jurusan if jurusan in JURUSAN else None)

    return jsonify({"jurusan": jurusan, "kelas": kelas_options})


@siswa_bp.route("/siswa/<int:siswa_id>/regenerate_qr", methods=["POST"])
@admin_required
def regenerate_qr(siswa_id: int):
    siswa = regenerate_qr_siswa(siswa_id)
    if not siswa:
        return jsonify({"status": "error", "message": "Data siswa tidak ditemukan."}), 404

    return jsonify(
        {
            "status": "success",
            "message": f"QR untuk {siswa['nama']} berhasil diperbarui.",
            "siswa": siswa,
        }
    )


@siswa_bp.route("/siswa/<int:siswa_id>/edit", methods=["GET", "POST"])
@admin_required
def siswa_edit(siswa_id: int):
    siswa = get_siswa_by_id(siswa_id)
    if not siswa:
        return "Data siswa tidak ditemukan.", 404

    error_message = None
    success_message = None

    selected_jurusan = (request.form.get("jurusan") or siswa["jurusan"]).upper()
    kelas_options = get_kelas_options(selected_jurusan)

    form_data = {
        "nis": request.form.get("nis", siswa["nis"]).strip(),
        "nama": request.form.get("nama", siswa["nama"]).strip(),
        "jurusan": selected_jurusan,
        "kelas": (request.form.get("kelas") or siswa["kelas"]).upper(),
    }

    if request.method == "POST":
        try:
            siswa = edit_siswa(
                siswa_id=siswa_id,
                nis=form_data["nis"],
                nama=form_data["nama"],
                jurusan=form_data["jurusan"],
                kelas=form_data["kelas"],
            )
            success_message = f"Data {siswa['nama']} berhasil diperbarui."
            form_data = {
                "nis": siswa["nis"],
                "nama": siswa["nama"],
                "jurusan": siswa["jurusan"],
                "kelas": siswa["kelas"],
            }
        except ValueError as exc:
            error_message = str(exc)

    return render_template(
        "siswa_edit.html",
        siswa=siswa,
        jurusan_options=JURUSAN,
        kelas_options=kelas_options,
        form_data=form_data,
        error_message=error_message,
        success_message=success_message,
    )


@siswa_bp.route("/siswa/<int:siswa_id>/delete", methods=["POST"])
@admin_required
def siswa_delete(siswa_id: int):
    siswa = get_siswa_by_id(siswa_id)
    if not siswa:
        return jsonify({"status": "error", "message": "Data siswa tidak ditemukan."}), 404

    try:
        delete_siswa(siswa_id)
        return jsonify(
            {
                "status": "success",
                "message": f"Data {siswa['nama']} berhasil dihapus.",
                "redirect": url_for("siswa.siswa_list"),
            }
        )
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
