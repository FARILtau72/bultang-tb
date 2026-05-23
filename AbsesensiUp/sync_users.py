from app import app, db
from models import User, Siswa
from werkzeug.security import generate_password_hash

def sync_users():
    with app.app_context():
        # 1. Buat/Buka Admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            print("✅ Admin dibuat (user: admin, pass: admin123)")
        else:
            print("ℹ️  Admin sudah ada.")

        # 2. Sinkronisasi Siswa ke Tabel User
        semua_siswa = Siswa.query.all()
        count_baru = 0
        
        for siswa in semua_siswa:
            # Cek apakah user dengan username = NIS sudah ada
            user = User.query.filter_by(username=siswa.nis).first()
            
            if not user:
                # Jika belum ada, buat akun baru
                # Password default diset sama dengan NIS (bisa diganti logicnya)
                new_user = User(
                    username=siswa.nis,
                    password_hash=generate_password_hash(siswa.nis), 
                    is_admin=False
                )
                db.session.add(new_user)
                count_baru += 1
        
        db.session.commit()
        print(f"✅ Selesai! {count_baru} akun siswa baru ditambahkan.")
        print("💡 Login Siswa: Username = NIS, Password = NIS")

if __name__ == "__main__":
    sync_users()