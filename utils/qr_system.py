import qrcode

def generate_qr(student_id):
    img = qrcode.make(str(student_id))
    path = f"qr_{student_id}.png"
    img.save(path)
    return path