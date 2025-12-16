import bcrypt

password = "Sph*2025".encode("utf-8")

hashed = bcrypt.hashpw(password, bcrypt.gensalt(12))

print(hashed.decode())
