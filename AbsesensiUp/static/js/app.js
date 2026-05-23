const AbsensiApp = (() => {
    function getSweetAlert() {
        return window.Swal || null;
    }

    async function showAlert(title, text, icon = "info") {
        const swal = getSweetAlert();
        if (swal) {
            await swal.fire({
                title,
                text,
                icon,
                confirmButtonText: "OK",
                confirmButtonColor: "#121212",
                customClass: {
                    popup: "swal-neobrutal",
                    confirmButton: "swal-neobrutal-btn",
                },
            });
            return;
        }

        window.alert(text || title);
    }

    async function confirmDanger({ title, text, confirmButtonText = "Ya, hapus" }) {
        const swal = getSweetAlert();
        if (!swal) {
            return window.confirm(`${title}\n\n${text}`);
        }

        const result = await swal.fire({
            title,
            text,
            icon: "warning",
            showCancelButton: true,
            confirmButtonText,
            cancelButtonText: "Batal",
            confirmButtonColor: "#d64545",
            cancelButtonColor: "#121212",
            reverseButtons: true,
            customClass: {
                popup: "swal-neobrutal",
                confirmButton: "swal-neobrutal-btn-danger",
                cancelButton: "swal-neobrutal-btn",
            },
        });

        return Boolean(result.isConfirmed);
    }

    async function showScanAlert(type, title, text) {
        const swal = getSweetAlert();
        if (swal) {
            await swal.fire({
                title,
                text,
                icon: type,
                timer: type === "success" ? 1800 : undefined,
                timerProgressBar: type === "success",
                showConfirmButton: type !== "success",
                confirmButtonColor: "#121212",
                customClass: {
                    popup: "swal-neobrutal",
                    confirmButton: "swal-neobrutal-btn",
                },
            });
            return;
        }

        showToast(text || title, type === "error" ? "danger" : type);
    }

    function ensureToastContainer() {
        let container = document.querySelector(".toast-container-app");
        if (!container) {
            container = document.createElement("div");
            container.className = "toast-container-app";
            document.body.appendChild(container);
        }
        return container;
    }

    function showToast(message, type = "info") {
        const classMap = {
            success: "text-bg-success",
            warning: "text-bg-warning",
            danger: "text-bg-danger",
            info: "text-bg-primary",
        };

        const toast = document.createElement("div");
        toast.className = `toast align-items-center border-0 ${classMap[type] || classMap.info}`;
        toast.setAttribute("role", "alert");
        toast.setAttribute("aria-live", "assertive");
        toast.setAttribute("aria-atomic", "true");
        toast.innerHTML =
            '<div class="d-flex">' +
            `<div class="toast-body">${message}</div>` +
            '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>' +
            "</div>";

        const container = ensureToastContainer();
        container.appendChild(toast);

        const instance = bootstrap.Toast.getOrCreateInstance(toast, { delay: 2600 });
        instance.show();
        toast.addEventListener("hidden.bs.toast", () => toast.remove());
    }

    async function populateKelas(jurusanSelectId, kelasSelectId, selectedKelas = "", includeAllOption = false) {
        const jurusanSelect = document.getElementById(jurusanSelectId);
        const kelasSelect = document.getElementById(kelasSelectId);
        if (!jurusanSelect || !kelasSelect) {
            return;
        }

        const jurusan = jurusanSelect.value || "";

        try {
            const response = await fetch(`/api/kelas?jurusan=${encodeURIComponent(jurusan)}`);
            const result = await response.json();
            const kelas = Array.isArray(result.kelas) ? result.kelas : [];

            kelasSelect.innerHTML = "";
            if (includeAllOption) {
                kelasSelect.add(new Option("Semua Kelas", ""));
            }

            for (const item of kelas) {
                const option = new Option(item, item);
                if (selectedKelas && selectedKelas === item) {
                    option.selected = true;
                }
                kelasSelect.add(option);
            }

            if (!selectedKelas && kelas.length > 0 && !includeAllOption) {
                kelasSelect.value = kelas[0];
            }
        } catch (error) {
            console.error("Gagal memuat data kelas.", error);
            showToast("Gagal memuat daftar kelas.", "danger");
        }
    }

    function initRegenerateButtons() {
        document.querySelectorAll(".btn-regenerate").forEach((button) => {
            button.addEventListener("click", async () => {
                const siswaId = button.getAttribute("data-id");
                if (!siswaId) {
                    return;
                }

                const oldHtml = button.innerHTML;
                button.disabled = true;
                button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

                try {
                    const response = await fetch(`/siswa/${siswaId}/regenerate_qr`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                    });
                    const result = await response.json();

                    if (!response.ok || result.status === "error") {
                        showToast(result.message || "Gagal regenerate QR.", "danger");
                    } else {
                        showToast(result.message, "success");
                        window.location.reload();
                    }
                } catch (error) {
                    console.error(error);
                    showToast("Terjadi kesalahan saat regenerate QR.", "danger");
                } finally {
                    button.disabled = false;
                    button.innerHTML = oldHtml;
                }
            });
        });
    }

    function bindJurusanKelas(jurusanSelector, kelasSelector, selectedKelas = "", includeAllOption = false) {
        const jurusanSelect = document.querySelector(jurusanSelector);
        const kelasSelect = document.querySelector(kelasSelector);

        if (!jurusanSelect || !kelasSelect) {
            return;
        }

        const jurusanId = jurusanSelect.id;
        const kelasId = kelasSelect.id;

        populateKelas(jurusanId, kelasId, selectedKelas, includeAllOption);
        jurusanSelect.addEventListener("change", () => {
            populateKelas(jurusanId, kelasId, "", includeAllOption);
        });
    }

    return {
        populateKelas,
        initRegenerateButtons,
        bindJurusanKelas,
        showToast,
        showAlert,
        confirmDanger,
        showScanAlert,
    };
})();

window.AbsensiApp = AbsensiApp;
window.App = {
    showToast: AbsensiApp.showToast,
    bindJurusanKelas: AbsensiApp.bindJurusanKelas,
    showAlert: AbsensiApp.showAlert,
    confirmDanger: AbsensiApp.confirmDanger,
    showScanAlert: AbsensiApp.showScanAlert,
};
