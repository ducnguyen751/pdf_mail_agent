import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError # Import ConfigurationError
from dotenv import load_dotenv

# Lấy URI kết nối từ biến môi trường
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    raise ConfigurationError("MONGO_URI environment variable not set.")


client = MongoClient(mongo_uri)

database_name = os.getenv("MONGO_DB_NAME", "your_default_db_name") #

# Lấy đối tượng database bằng cách chỉ định tên rõ ràng
try:
    db = client[database_name]
except Exception as e:
    # Xử lý lỗi nếu tên database không hợp lệ hoặc các vấn đề kết nối khác
    print(f"Error connecting to database '{database_name}': {e}")
    raise # Ném lại ngoại lệ sau khi in thông báo lỗi

# Chỉ mục để tăng tốc truy vấn (bỏ ghi chú nếu bạn muốn sử dụng)
# try:
#     db.users.create_index([('role', 1)])
#     print("Index on 'role' created successfully.")
# except Exception as e:
#     print(f"Error creating index on 'role': {e}")


def find_users_by_roles(roles: list):
    """
    Tìm kiếm người dùng dựa trên danh sách các vai trò.

    Args:
        roles: Một danh sách các chuỗi đại diện cho các vai trò.

    Returns:
        Một danh sách các dictionary chứa thông tin email, name, và role của người dùng.
    """
    if not roles:
        return [] # Trả về danh sách rỗng nếu không có vai trò nào được cung cấp

    try:
        users = list(
            db.users.find(
                {"role": {"$in": roles}},
                {"_id": 0, "email": 1, "name": 1, "role": 1}
            )
        )
        return users
    except Exception as e:
        print(f"Error finding users by roles: {e}")
        return [] # Trả về danh sách rỗng và in lỗi nếu có vấn đề xảy ra
