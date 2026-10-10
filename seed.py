import os
import secrets

from app.core.database import engine, SessionLocal, create_tables, Base
from app.models.user import User, Role
from app.models.material import Material, Category, Author, Tag, MaterialAuthor, MaterialCategory, MaterialTag
from app.core.security import hash_password
from app.services.material_service import generate_slug

def seed():
    create_tables()  # idempotent; replace with `alembic upgrade head` once migrations exist
    db = SessionLocal()

    if db.query(Role).first():
        print("Database already seeded; nothing to do.")
        db.close()
        return

    import app.models  # ensure all models are registered

    # Passwords come from the environment, otherwise user-friendly defaults are used.
    passwords = {}
    for name in ("ADMIN", "EDITOR", "MEMBER"):
        passwords[name] = os.getenv(f"SEED_{name}_PASSWORD") or f"{name.lower()}123456"

    # 1. Create Roles
    admin_role = Role(name="admin", description="Administrator")
    editor_role = Role(name="editor", description="Editor")
    member_role = Role(name="member", description="Standard Member")
    db.add_all([admin_role, editor_role, member_role])
    db.commit()
    
    # 2. Create Users
    admin_user = User(email="admin@library.com", username="admin", hashed_password=hash_password(passwords["ADMIN"]), is_active=True, is_verified=True)
    admin_user.roles.append(admin_role)
    
    editor_user = User(email="editor@library.com", username="editor", hashed_password=hash_password(passwords["EDITOR"]), is_active=True, is_verified=True)
    editor_user.roles.append(editor_role)
    
    member_user = User(email="member@library.com", username="member", hashed_password=hash_password(passwords["MEMBER"]), is_active=True, is_verified=True)
    member_user.roles.append(member_role)
    
    db.add_all([admin_user, editor_user, member_user])
    db.commit()

    # 3. Create Categories
    cat_names = ["Programming", "Mathematics", "Science", "Literature", "History", "Philosophy"]
    categories = []
    for cname in cat_names:
        cat = Category(name=cname, slug=cname.lower())
        categories.append(cat)
    db.add_all(categories)
    db.commit()

    # 4. Create Authors
    author_names = ["Alan Turing", "Ada Lovelace", "Isaac Newton", "Albert Einstein", "Marie Curie"]
    authors = []
    for aname in author_names:
        auth = Author(name=aname, slug=aname.lower().replace(" ", "-"), bio=f"Bio of {aname}")
        authors.append(auth)
    db.add_all(authors)
    db.commit()
    
    # 5. Create Tags
    tag_names = ["computer-science", "physics", "classic", "modern", "research", "tutorial", "guide", "paper", "book", "notes"]
    tags = []
    for tname in tag_names:
        t = Tag(name=tname, slug=tname)
        tags.append(t)
    db.add_all(tags)
    db.commit()
    
    # 6. Create Materials
    materials = []
    for i in range(10):
        m = Material(
            title=f"Sample Material {i}",
            slug=generate_slug(f"Sample Material {i}"),
            description=f"Description for sample material {i}",
            content_type="book" if i % 2 == 0 else "paper",
            language="en",
            publication_status="published",
            created_by=editor_user.id
        )
        materials.append(m)
    db.add_all(materials)
    db.commit()
    
    # Associate Authors, Categories, Tags
    for i, m in enumerate(materials):
        ma = MaterialAuthor(material_id=m.id, author_id=authors[i % len(authors)].id)
        mc = MaterialCategory(material_id=m.id, category_id=categories[i % len(categories)].id)
        mt = MaterialTag(material_id=m.id, tag_id=tags[i % len(tags)].id)
        db.add_all([ma, mc, mt])
    db.commit()
    
    print("Database seeded successfully.")
    for name, email in (("ADMIN", "admin@library.com"), ("EDITOR", "editor@library.com"), ("MEMBER", "member@library.com")):
        print(f"  {email}: {passwords[name]}")
    db.close()

if __name__ == "__main__":
    seed()
